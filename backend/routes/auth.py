from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from database import db, require_auth, get_current_user, security, logger, create_notification
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, PLATFORM_FEE_PERCENT, FRONTEND_URL
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from database import oauth_request_tokens, import_progress, EMERGENT_KEY
from models import *
from util.content_filter import detect_offplatform_payment, BLOCK_MESSAGE as OFFPLATFORM_BLOCK_MESSAGE, validate_username, validate_bio


router = APIRouter()

def _check_needs_migration(user: dict) -> bool:
    """BLOCK 492: Check if user needs to see the security migration modal.
    Trigger: has_seen_security_migration is explicitly False (set by Great Disconnect).
    One-and-done: once has_seen_security_migration is True or dismissed, never triggers again."""
    if user.get("has_seen_security_migration") is True:
        return False
    if user.get("discogs_migration_dismissed") is True:
        return False
    # BLOCK 492: If the flag was explicitly set to False (Great Disconnect), trigger modal
    if user.get("has_seen_security_migration") is False:
        return True
    # Legacy fallback: user has old discogs_username but not OAuth verified
    if user.get("discogs_username") and not user.get("discogs_oauth_verified"):
        return True
    return False


async def _build_user_response(user: dict) -> UserResponse:
    """Build UserResponse with computed counts."""
    uid = user["id"]
    collection_count = await db.records.count_documents({"user_id": uid})
    spin_count = await db.spins.count_documents({"user_id": uid})
    followers_count = await db.followers.count_documents({"following_id": uid})
    following_count = await db.followers.count_documents({"follower_id": uid})
    completed_trades = await db.trades.count_documents({
        "$or": [{"initiator_id": uid}, {"responder_id": uid}],
        "status": "COMPLETED"
    })
    completed_sales = await db.listings.count_documents({"user_id": uid, "status": "SOLD"})
    completed_transactions = completed_trades + completed_sales
    return UserResponse(
        id=uid,
        email=user.get("email", ""),
        username=user["username"],
        first_name=user.get("first_name"),
        avatar_url=user.get("avatar_url"),
        bio=user.get("bio"),
        setup=user.get("setup"),
        location=user.get("location"),
        favorite_genre=user.get("favorite_genre"),
        city=user.get("city"),
        region=user.get("region"),
        country=user.get("country"),
        state=user.get("state"),
        postal_code=user.get("postal_code"),
        created_at=user.get("created_at", ""),
        collection_count=collection_count,
        spin_count=spin_count,
        followers_count=followers_count,
        following_count=following_count,
        completed_transactions=completed_transactions,
        onboarding_completed=user.get("onboarding_completed", False),
        founding_member=user.get("founding_member", False),
        is_admin=user.get("is_admin", False),
        email_verified=user.get("email_verified", True),
        title_label=user.get("title_label"),
        instagram_username=user.get("instagram_username"),
        tiktok_username=user.get("tiktok_username"),
        golden_hive=user.get("golden_hive", False),
        golden_hive_verified=user.get("golden_hive_verified", False),
        golden_hive_status=user.get("golden_hive_status"),
        is_private=user.get("is_private", False),
        dm_setting=user.get("dm_setting", "everyone"),
        discogs_oauth_verified=user.get("discogs_oauth_verified", False),
        needs_discogs_migration=_check_needs_migration(user),
        discogs_migration_dismissed=user.get("discogs_migration_dismissed", False),
        discogs_import_intent=user.get("discogs_import_intent", "PENDING"),
        has_connected_discogs=user.get("has_connected_discogs", False),
        current_streak=user.get("current_streak", 0),
        longest_streak=user.get("longest_streak", 0),
        total_spin_days=user.get("total_spin_days", 0),
        last_spin_date=user.get("last_spin_date"),
    )

# ============== AUTH ROUTES ==============

@router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    normalized_email = user_data.email.strip().lower()
    
    # Check if email exists (case-insensitive)
    existing_email = await db.users.find_one({"email": normalized_email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    existing_username = await db.users.find_one({"username": user_data.username.lower()})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Validate username content (profanity + payment references)
    is_valid, error_msg = validate_username(user_data.username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": normalized_email,
        "username": user_data.username.lower(),
        "password_hash": hash_password(user_data.password),
        "avatar_url": f"https://api.dicebear.com/7.x/miniavs/svg?seed={user_data.username}",
        "bio": None,
        "setup": None,
        "location": None,
        "favorite_genre": None,
        "onboarding_completed": False,
        "created_at": now
    }
    
    # Founding member check (first 500 users)
    total_users = await db.users.count_documents({})
    if total_users < 500:
        user_doc["founding_member"] = True
    else:
        user_doc["founding_member"] = False
    
    await db.users.insert_one(user_doc)

    # Auto-subscribe new user to the Weekly Wax Report
    await db.newsletter_subscribers.insert_one({
        "email": normalized_email,
        "subscribed": True,
        "source": "registration",
        "subscribed_at": now,
    })

    token = create_token(user_id, username=username, email=normalized_email)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=normalized_email,
            username=user_data.username.lower(),
            avatar_url=user_doc["avatar_url"],
            bio=None,
            setup=None,
            location=None,
            favorite_genre=None,
            created_at=now,
            collection_count=0,
            spin_count=0,
            followers_count=0,
            following_count=0,
            onboarding_completed=False,
            founding_member=user_doc.get("founding_member", False),
        )
    )

@router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    import re as _re
    from services.rate_limiter import rate_limiter, get_client_ip
    rate_limiter.check(f"login:{get_client_ip(request)}", max_requests=15, window_seconds=300)

    identifier = credentials.email.strip().lower()
    password = credentials.password  # Never strip passwords — hash must match exactly

    # DEBUG: Log DB connection info
    user_count = await db.users.count_documents({})
    logger.info(f"LOGIN DEBUG: identifier='{identifier}' total_users_in_db={user_count} db_name={db.name}")

    # Try exact email match first
    lookup_method = "exact_email"
    user = await db.users.find_one({"email": identifier}, {"_id": 0})

    # Fallback: case-insensitive email match (escaped for regex safety)
    if not user:
        lookup_method = "regex_email"
        escaped = _re.escape(identifier)
        user = await db.users.find_one(
            {"email": {"$regex": f"^{escaped}$", "$options": "i"}},
            {"_id": 0}
        )

    # Fallback: username match (allows login by username)
    if not user:
        lookup_method = "exact_username"
        user = await db.users.find_one({"username": identifier}, {"_id": 0})
        if not user:
            lookup_method = "regex_username"
            user = await db.users.find_one(
                {"username": {"$regex": f"^{_re.escape(identifier)}$", "$options": "i"}},
                {"_id": 0}
            )

    if not user:
        logger.warning(f"LOGIN FAIL [user_not_found]: identifier='{identifier}' tried_methods=exact_email,regex_email,exact_username,regex_username")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Deep bcrypt diagnostic logging
    stored_hash = user.get("password_hash", "")
    logger.info(f"LOGIN VERIFY: user='{user.get('username')}' found_via={lookup_method} hash_type={type(stored_hash).__name__} hash_len={len(stored_hash)} hash_prefix={stored_hash[:7]} password_type={type(password).__name__} password_len={len(password)}")

    if not verify_password(password, stored_hash):
        logger.warning(f"LOGIN FAIL [wrong_password]: user='{user.get('username')}' email='{user.get('email')}' hash_prefix={stored_hash[:7]} hash_len={len(stored_hash)}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["id"], username=user.get("username", ""), email=user.get("email", ""))
    logger.info(f"LOGIN SUCCESS: user='{user.get('username')}' email='{user.get('email')}'")
    return TokenResponse(access_token=token, user=await _build_user_response(user))

@router.post("/admin/login-diagnostic")
async def login_diagnostic(data: dict, user: Dict = Depends(require_auth)):
    """Admin-only: diagnose login issues for a given identifier."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    import re as _re
    identifier = data.get("identifier", "").strip().lower()
    result = {"identifier": identifier, "checks": []}

    # Check 1: exact email match
    u = await db.users.find_one({"email": identifier}, {"_id": 0, "id": 1, "email": 1, "username": 1, "password_hash": 1})
    result["checks"].append({"method": "exact_email", "found": u is not None, "email": u.get("email") if u else None})

    # Check 2: regex email match
    if not u:
        escaped = _re.escape(identifier)
        u = await db.users.find_one({"email": {"$regex": f"^{escaped}$", "$options": "i"}}, {"_id": 0, "id": 1, "email": 1, "username": 1, "password_hash": 1})
        result["checks"].append({"method": "regex_email", "found": u is not None, "email": u.get("email") if u else None})

    # Check 3: username match
    if not u:
        u = await db.users.find_one({"username": identifier}, {"_id": 0, "id": 1, "email": 1, "username": 1, "password_hash": 1})
        result["checks"].append({"method": "username", "found": u is not None, "username": u.get("username") if u else None})

    if u:
        result["user_found"] = True
        result["email"] = u.get("email")
        result["username"] = u.get("username")
        result["hash_prefix"] = u.get("password_hash", "")[:7]
        result["hash_length"] = len(u.get("password_hash", ""))
        # Verify test password if provided
        test_pw = data.get("test_password")
        if test_pw:
            result["password_match"] = verify_password(test_pw, u.get("password_hash", ""))
    else:
        result["user_found"] = False

    return result


# ============== PASSWORD RESET ==============

@router.post("/auth/forgot-password")
async def forgot_password(data: dict):
    """Send a password reset link to the user's email."""
    from services.rate_limiter import rate_limiter
    identifier = (data.get("email") or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username is required")

    rate_limiter.check(f"forgot:{identifier}", max_requests=3, window_seconds=600)

    import re as _re
    # Look up user by email or username (same 4-step as login)
    user = await db.users.find_one({"email": identifier}, {"_id": 0})
    if not user:
        user = await db.users.find_one(
            {"email": {"$regex": f"^{_re.escape(identifier)}$", "$options": "i"}}, {"_id": 0}
        )
    if not user:
        user = await db.users.find_one({"username": identifier}, {"_id": 0})
        if not user:
            user = await db.users.find_one(
                {"username": {"$regex": f"^{_re.escape(identifier)}$", "$options": "i"}}, {"_id": 0}
            )

    # Always return success (don't reveal whether email exists)
    if not user:
        logger.info(f"Forgot password: no user for '{identifier}' — returning silent OK")
        return {"status": "ok", "message": "If an account exists, a reset link has been sent."}

    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.password_resets.delete_many({"user_id": user["id"]})
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "token": token,
        "created_at": now,
    })

    reset_url = f"{FRONTEND_URL}/reset-password/{token}"
    from templates.base import wrap_email
    body = f"""
    <p style="font-size:16px;color:#2A1A06;line-height:1.6;">
      Hi <strong>{user.get('username', '')}</strong>, we received a request to reset your password.
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{reset_url}" style="display:inline-block;padding:14px 32px;background:#E8A820;color:#2A1A06;text-decoration:none;border-radius:999px;font-weight:600;font-size:16px;">
        Reset My Password
      </a>
    </div>
    <p style="font-size:13px;color:#8A6B4A;text-align:center;">
      This link expires in 1 hour. If you didn't request this, you can safely ignore this email.
    </p>
    """
    html = wrap_email(body)
    from services.email_service import send_email_fire_and_forget
    await send_email_fire_and_forget(user["email"], "Reset your Honey Groove password", html)
    logger.info(f"Password reset email sent to {user['email']} for user {user.get('username')}")

    return {"status": "ok", "message": "If an account exists, a reset link has been sent."}


@router.post("/auth/reset-password")
async def reset_password(data: dict):
    """Reset password using a valid token."""
    token = (data.get("token") or "").strip()
    new_password = data.get("password") or ""

    if not token:
        raise HTTPException(status_code=400, detail="Reset token is required")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    doc = await db.password_resets.find_one({"token": token}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    created = datetime.fromisoformat(doc["created_at"])
    if datetime.now(timezone.utc) - created > timedelta(hours=1):
        await db.password_resets.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="This reset link has expired. Please request a new one.")

    new_hash = hash_password(new_password)
    await db.users.update_one({"id": doc["user_id"]}, {"$set": {"password_hash": new_hash}})
    await db.password_resets.delete_many({"user_id": doc["user_id"]})

    user = await db.users.find_one({"id": doc["user_id"]}, {"_id": 0, "username": 1, "email": 1})
    logger.info(f"Password reset completed for user '{user.get('username')}' ({user.get('email')})")

    return {"status": "ok", "message": "Password reset successfully. You can now log in."}


# ── Claim-Invite: token-based account claim (bypasses forgot-password) ──────

async def _find_invite_token(token: str):
    """Case-insensitive token lookup — email clients sometimes alter casing."""
    doc = await db.invite_tokens.find_one({"token": token}, {"_id": 0})
    if not doc:
        doc = await db.invite_tokens.find_one({"token": token.lower()}, {"_id": 0})
    if not doc:
        doc = await db.invite_tokens.find_one(
            {"token": {"$regex": f"^{token}$", "$options": "i"}}, {"_id": 0}
        )
    return doc


@router.get("/auth/validate-invite")
async def validate_invite(token: str = Query(...)):
    """Validate an invite token and return the associated email.
    Read-only — does NOT burn the token. Token is only burned on successful claim."""
    doc = await _find_invite_token(token)
    if not doc:
        logger.warning(f"INVITE TOKEN ERROR [Token Not Found]: token='{token[:12]}...' — no match in DB (tried exact, lowercase, regex)")
        raise HTTPException(status_code=400, detail="Invalid or expired invite link.")
    created = datetime.fromisoformat(doc["created_at"])
    age = datetime.now(timezone.utc) - created
    if age > timedelta(days=7):
        logger.warning(f"INVITE TOKEN ERROR [Token Expired]: token='{token[:12]}...' email='{doc['email']}' created={doc['created_at']} age={age.days}d")
        raise HTTPException(status_code=400, detail="This invite link has expired. Request a fresh one below.")
    logger.info(f"INVITE TOKEN VALID: token='{token[:12]}...' email='{doc['email']}' age={age.days}d{age.seconds//3600}h")
    return {"email": doc["email"], "is_existing": doc.get("is_existing", False)}


@router.post("/auth/resend-invite")
async def resend_invite(data: dict):
    """Generate a fresh invite token and send a new invite email."""
    from services.email_service import send_email
    email = (data.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Check if user exists to determine existing vs new
    user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1, "username": 1})
    is_existing = user is not None

    # Invalidate any existing tokens for this email
    await db.invite_tokens.delete_many({"email": email})

    # Generate fresh token with 7-day expiry
    new_token = str(uuid.uuid4())
    await db.invite_tokens.insert_one({
        "token": new_token,
        "email": email,
        "is_existing": is_existing,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    claim_url = f"{FRONTEND_URL}/invite/{new_token}"
    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#FAF6EE;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1A1A1A;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF6EE;">
<tr><td align="center" style="padding:24px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
<tr><td align="center" style="background-color:#FDE68A;padding:28px 24px 20px;">
<img src="https://www.thehoneygroove.com/logo-wordmark.png" alt="the Honey Groove" width="220" style="display:block;height:auto;"/>
</td></tr>
<tr><td style="padding:32px 28px 12px;">
<h1 style="font-size:22px;font-weight:700;color:#915527;margin:0 0 20px;line-height:1.3;">Your fresh invite is here!</h1>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0 0 16px;">
Looks like the first invite got a little sticky! No worries&mdash;we've generated a fresh link just for you. Click the button below to set your password and claim your spot in the Hive. We've got a record waiting for you!
</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:8px 0 28px;">
<a href="{claim_url}" target="_blank"
   style="display:inline-block;background-color:#915527;color:#FDE68A;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;">
Join Now
</a>
</td></tr>
</table>
<p style="font-size:13px;line-height:1.6;color:#888;margin:0 0 16px;">This link expires in 7 days. If you didn't request this, you can safely ignore this email.</p>
<p style="font-size:15px;line-height:1.7;color:#333;margin:0;">Best,<br/><strong style="color:#915527;">Katie</strong><br/><span style="font-size:13px;color:#888;">Founder, The Honey Groove&trade;</span></p>
</td></tr>
<tr><td align="center" style="padding:20px 28px 24px;border-top:1px solid #F0E6D6;">
<p style="font-size:11px;color:#AAAAAA;margin:0;line-height:1.5;">&copy; 2026 The Honey Groove&trade; &middot; the vinyl social club, finally.</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""

    sent = await send_email(email, "Your fresh invite is here! \U0001f36f", html, reply_to="hello@thehoneygroove.com")
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email. Please try again.")

    logger.info(f"Resent invite to {email} (token: {new_token[:8]}...)")
    return {"status": "sent", "message": "A fresh invite link has been sent to your email."}


@router.post("/auth/claim-invite")
async def claim_invite(data: dict):
    """Claim an invite: set password and log in immediately."""
    token = (data.get("token") or "").strip()
    password = data.get("password") or ""
    if not token:
        raise HTTPException(status_code=400, detail="Invite token is required")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    doc = await _find_invite_token(token)
    if not doc:
        logger.warning(f"INVITE CLAIM ERROR [Token Not Found]: token='{token[:12]}...' — no match in DB")
        raise HTTPException(status_code=400, detail="Invalid or expired invite link.")
    created = datetime.fromisoformat(doc["created_at"])
    age = datetime.now(timezone.utc) - created
    if age > timedelta(days=7):
        logger.warning(f"INVITE CLAIM ERROR [Token Expired]: token='{token[:12]}...' email='{doc['email']}' age={age.days}d")
        raise HTTPException(status_code=400, detail="This invite link has expired. Request a fresh one below.")

    email = doc["email"].lower().strip()
    user = await db.users.find_one({"email": email}, {"_id": 0})

    if user:
        # Existing user: update password, mark verified, & force onboarding
        new_hash = hash_password(password)
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"password_hash": new_hash, "is_verified": True, "onboarding_completed": False}},
        )
        user["is_verified"] = True
        user["onboarding_completed"] = False
    else:
        # New user: create account
        user_id = str(uuid.uuid4())
        username = email.split("@")[0].lower().replace(".", "").replace("+", "")[:20]
        # Ensure unique username
        while await db.users.find_one({"username": username}):
            username = username[:16] + str(uuid.uuid4())[:4]
        user = {
            "id": user_id,
            "email": email,
            "username": username,
            "password_hash": hash_password(password),
            "display_name": "",
            "bio": "",
            "avatar_url": "",
            "is_verified": True,
            "is_admin": False,
            "onboarding_completed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one({**user})
        user.pop("_id", None)

    # Burn the token
    await db.invite_tokens.delete_one({"token": token})

    # Issue JWT
    jwt_token = create_token(user["id"], username=user.get("username", ""), email=user.get("email", ""))
    logger.info(f"Invite claimed by {email} (user {user.get('username')})")

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user.get("username", ""),
            "display_name": user.get("display_name", ""),
            "avatar_url": user.get("avatar_url", ""),
            "is_admin": user.get("is_admin", False),
            "onboarding_completed": user.get("onboarding_completed", False),
        },
    }
async def get_me(user: Dict = Depends(require_auth)):
    return await _build_user_response(user)

@router.put("/auth/me", response_model=UserResponse)
async def update_me(update_data: UserUpdate, user: Dict = Depends(require_auth)):
    update_fields = {}
    if update_data.username:
        existing = await db.users.find_one({"username": update_data.username.lower(), "id": {"$ne": user["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        # Validate username content (profanity + payment references)
        is_valid, error_msg = validate_username(update_data.username)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        update_fields["username"] = update_data.username.lower()
    for field in ("bio", "avatar_url", "city", "region", "country", "state", "postal_code", "setup", "location", "favorite_genre", "instagram_username", "tiktok_username", "first_name"):
        val = getattr(update_data, field, None)
        if val is not None:
            # Full bio validation: payment mentions + contact info leaks
            if field == "bio":
                is_valid, error_msg = validate_bio(val)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=error_msg)
            update_fields[field] = val
    if update_data.onboarding_completed is not None:
        update_fields["onboarding_completed"] = update_data.onboarding_completed
    if update_data.has_connected_discogs is not None:
        update_fields["has_connected_discogs"] = update_data.has_connected_discogs
    if update_data.is_private is not None:
        update_fields["is_private"] = update_data.is_private
    if update_data.dm_setting is not None and update_data.dm_setting in ("everyone", "following", "requests"):
        update_fields["dm_setting"] = update_data.dm_setting
    if update_fields:
        await db.users.update_one({"id": user["id"]}, {"$set": update_fields})
    updated = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    return await _build_user_response(updated)


# ============== BLOCK 491: DEBUG RESET MIGRATION FLAG ==============

@router.post("/debug/reset-migration")
async def debug_reset_migration(user: Dict = Depends(require_auth)):
    """BLOCK 491/569: Dev-only tool to reset migration flags so the modal re-triggers.
    Only allowed for admin users (tied to is_admin flag, not username)."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Debug tool restricted to authorized users")

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "has_seen_security_migration": False,
            "discogs_oauth_verified": False,
            "discogs_migration_dismissed": False,
        }}
    )
    logger.info(f"BLOCK 491: Migration flags reset for user {user['id']} ({user.get('username')})")
    return {"message": "Migration flags reset. Reload to trigger modal."}


# ============== EMAIL VERIFICATION ==============

@router.get("/auth/verify-email")
async def verify_email(token: str = Query(...)):
    """Verify a user's email address via token."""
    vdoc = await db.email_verifications.find_one({"token": token}, {"_id": 0})
    if not vdoc:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")
    # Check expiry (24 hours)
    created = datetime.fromisoformat(vdoc["created_at"])
    if datetime.now(timezone.utc) - created > timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Verification link has expired. Please request a new one.")
    await db.users.update_one({"id": vdoc["user_id"]}, {"$set": {"email_verified": True}})
    await db.email_verifications.delete_many({"user_id": vdoc["user_id"]})
    return {"status": "ok", "message": "Email verified successfully!"}


@router.post("/auth/resend-verification")
async def resend_verification(user: Dict = Depends(require_auth)):
    """Resend verification email."""
    from services.rate_limiter import rate_limiter
    rate_limiter.check(f"resend_verify:{user['id']}", max_requests=3, window_seconds=900)

    if user.get("email_verified", True):
        return {"status": "ok", "message": "Email already verified"}

    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.email_verifications.delete_many({"user_id": user["id"]})
    await db.email_verifications.insert_one({
        "user_id": user["id"],
        "token": token,
        "created_at": now,
    })

    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    from templates.base import wrap_email
    body = f"""
    <p style="font-size:16px;color:#2A1A06;line-height:1.6;">
      Click the button below to verify your email address and start exploring.
    </p>
    <div style="text-align:center;margin:28px 0;">
      <a href="{verify_url}" style="display:inline-block;padding:14px 32px;background:#E8A820;color:#2A1A06;text-decoration:none;border-radius:999px;font-weight:600;font-size:16px;">
        Verify My Email
      </a>
    </div>
    <p style="font-size:13px;color:#8A6B4A;text-align:center;">
      This link expires in 24 hours. If you didn't create an account, you can ignore this email.
    </p>
    """
    html = wrap_email(body)
    from services.email_service import send_email_fire_and_forget
    await send_email_fire_and_forget(user["email"], "Verify your Honey Groove account. \U0001F41D", html)

    return {"status": "ok", "message": "Verification email sent"}


@router.post("/auth/change-email")
async def request_email_change(data: dict, user: Dict = Depends(require_auth)):
    """Request an email change. Sends confirmation to the new address."""
    from services.rate_limiter import rate_limiter
    rate_limiter.check(f"change_email:{user['id']}", max_requests=3, window_seconds=900)

    new_email = data.get("new_email", "").strip().lower()
    if not new_email or "@" not in new_email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if new_email == user.get("email", "").lower():
        raise HTTPException(status_code=400, detail="That's already your current email.")
    existing = await db.users.find_one({"email": new_email}, {"_id": 0, "id": 1})
    if existing:
        raise HTTPException(status_code=400, detail="This email is already in use by another account.")

    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.email_change_requests.delete_many({"user_id": user["id"]})
    await db.email_change_requests.insert_one({
        "user_id": user["id"],
        "new_email": new_email,
        "token": token,
        "created_at": now,
    })

    confirm_url = f"{FRONTEND_URL}/confirm-email-change?token={token}"
    from templates.emails import email_change_confirmation
    from services.email_service import send_email_fire_and_forget
    tmpl = email_change_confirmation(user.get("username", ""), confirm_url)
    await send_email_fire_and_forget(new_email, tmpl["subject"], tmpl["html"])
    logger.info(f"Email change requested for user {user['id']} → {new_email} | confirm: {confirm_url}")

    return {"status": "ok", "message": "Confirmation email sent to your new address. Check your inbox."}


@router.get("/auth/confirm-email-change")
async def confirm_email_change(token: str = Query(...)):
    """Confirm an email change via token."""
    doc = await db.email_change_requests.find_one({"token": token}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=400, detail="Invalid or expired confirmation link.")
    created = datetime.fromisoformat(doc["created_at"])
    if datetime.now(timezone.utc) - created > timedelta(hours=24):
        await db.email_change_requests.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="This confirmation link has expired. Please request a new email change.")
    # Check new email isn't taken in the meantime
    existing = await db.users.find_one({"email": doc["new_email"], "id": {"$ne": doc["user_id"]}}, {"_id": 0, "id": 1})
    if existing:
        await db.email_change_requests.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="This email is now in use by another account.")
    await db.users.update_one({"id": doc["user_id"]}, {"$set": {"email": doc["new_email"]}})
    await db.email_change_requests.delete_many({"user_id": doc["user_id"]})
    return {"status": "ok", "message": "Your email has been updated successfully!"}




# ============== USER ROUTES ==============

@router.get("/users/discover/suggestions")
async def get_suggested_users(user: Dict = Depends(require_auth)):
    """Get suggested users to follow (users not already followed)"""
    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0}).to_list(1000)
    following_ids = [f["following_id"] for f in following]
    following_ids.append(user["id"])
    
    all_users = await db.users.find(
        {"id": {"$nin": following_ids}},
        {"_id": 0, "password_hash": 0}
    ).to_list(50)
    
    suggestions = []
    for u in all_users:
        record_count = await db.records.count_documents({"user_id": u["id"]})
        suggestions.append({
            "id": u["id"],
            "username": u["username"],
            "avatar_url": u.get("avatar_url"),
            "bio": u.get("bio"),
            "record_count": record_count,
            "is_following": False
        })
    
    suggestions.sort(key=lambda x: x["record_count"], reverse=True)
    return suggestions[:20]

@router.get("/users/search")
async def search_users_q(query: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    users = await db.users.find(
        {"username": {"$regex": query, "$options": "i"}},
        {"_id": 0, "password_hash": 0}
    ).limit(20).to_list(20)
    result = []
    for u in users:
        is_following = await db.followers.find_one({"follower_id": user["id"], "following_id": u["id"]}) is not None
        result.append({
            "id": u["id"],
            "username": u["username"],
            "avatar_url": u.get("avatar_url"),
            "bio": u.get("bio"),
            "is_following": is_following
        })
    return result

@router.get("/users/{username}")
async def get_user_profile(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if either user has blocked the other
    if current_user and current_user["id"] != user["id"]:
        block = await db.blocks.find_one({
            "$or": [
                {"blocker_id": user["id"], "blocked_id": current_user["id"]},
                {"blocker_id": current_user["id"], "blocked_id": user["id"]}
            ]
        })
        if block:
            raise HTTPException(status_code=403, detail="This profile is not available.")
    
    is_own = current_user and current_user["id"] == user["id"]
    is_private = user.get("is_private", False)
    
    # Determine if viewer is an approved follower
    is_approved_follower = False
    follow_request_status = None
    if current_user and not is_own:
        follower_doc = await db.followers.find_one({"follower_id": current_user["id"], "following_id": user["id"]})
        is_approved_follower = follower_doc is not None
        if not is_approved_follower and is_private:
            req = await db.follow_requests.find_one({"from_id": current_user["id"], "to_id": user["id"], "status": "pending"})
            if req:
                follow_request_status = "pending"
    
    resp = await _build_user_response(user)
    if not is_own:
        resp.email = ""
    
    # Build extended response with privacy info
    result = resp.dict()
    result["is_private"] = is_private
    result["dm_setting"] = user.get("dm_setting", "everyone")
    result["is_approved_follower"] = is_approved_follower
    result["follow_request_status"] = follow_request_status
    result["profile_locked"] = is_private and not is_approved_follower and not is_own
    
    # Records in common — always calculate for non-own profiles
    if current_user and not is_own:
        viewer_records = await db.records.find({"user_id": current_user["id"], "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}).to_list(5000)
        viewer_discogs = {r["discogs_id"] for r in viewer_records if r.get("discogs_id")}
        if viewer_discogs:
            their_records = await db.records.find({"user_id": user["id"], "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}).to_list(5000)
            their_discogs = {r["discogs_id"] for r in their_records if r.get("discogs_id")}
            result["records_in_common"] = len(viewer_discogs & their_discogs)
        else:
            result["records_in_common"] = 0

    # For locked profiles, include additional mutual signals
    if result["profile_locked"] and current_user:
        # Mutual followers (people the viewer follows who also follow this user)
        viewer_following = await db.followers.find({"follower_id": current_user["id"]}, {"_id": 0, "following_id": 1}).to_list(500)
        viewer_following_ids = {f["following_id"] for f in viewer_following}
        mutual_followers = await db.followers.find({"following_id": user["id"], "follower_id": {"$in": list(viewer_following_ids)}}, {"_id": 0, "follower_id": 1}).to_list(5)
        mutual_names = []
        for mf in mutual_followers[:3]:
            mu = await db.users.find_one({"id": mf["follower_id"]}, {"_id": 0, "username": 1})
            if mu:
                mutual_names.append(mu["username"])
        result["mutual_followers"] = mutual_names
    
    return result


@router.delete("/auth/account")
async def delete_account(user: Dict = Depends(require_auth)):
    """Permanently delete a user account and all associated data."""
    uid = user["id"]
    now = datetime.now(timezone.utc).isoformat()

    # Log deletion for admin records
    await db.account_deletions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "username": user.get("username"),
        "email": user.get("email"),
        "deleted_at": now,
    })

    # Cancel any active Stripe holds
    if STRIPE_API_KEY:
        try:
            import stripe
            stripe.api_key = STRIPE_API_KEY
            active_trades = await db.trades.find(
                {"$or": [{"initiator_id": uid}, {"responder_id": uid}],
                 "status": {"$in": ["HOLD_PENDING", "SHIPPING", "CONFIRMING"]}},
                {"_id": 0}
            ).to_list(100)
            for trade in active_trades:
                for hold in (trade.get("holds") or []):
                    pi_id = hold.get("payment_intent_id")
                    if pi_id:
                        try:
                            stripe.PaymentIntent.cancel(pi_id)
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Stripe hold cancellation error during account deletion: {e}")

    # Delete all user data across collections
    await db.records.delete_many({"user_id": uid})
    await db.posts.delete_many({"user_id": uid})
    await db.spins.delete_many({"user_id": uid})
    await db.iso_items.delete_many({"user_id": uid})
    await db.listings.delete_many({"user_id": uid})
    await db.likes.delete_many({"user_id": uid})
    await db.comments.delete_many({"user_id": uid})
    await db.followers.delete_many({"$or": [{"follower_id": uid}, {"following_id": uid}]})
    await db.notifications.delete_many({"$or": [{"user_id": uid}, {"from_user_id": uid}]})
    await db.trades.delete_many({"$or": [{"initiator_id": uid}, {"responder_id": uid}]})
    await db.trade_messages.delete_many({"user_id": uid})
    await db.dm_conversations.delete_many({"$or": [{"user1_id": uid}, {"user2_id": uid}]})
    await db.dm_messages.delete_many({"sender_id": uid})
    await db.hauls.delete_many({"user_id": uid})
    await db.prompt_responses.delete_many({"user_id": uid})
    await db.bingo_cards.delete_many({"user_id": uid})
    await db.bingo_marks.delete_many({"user_id": uid})
    await db.mood_boards.delete_many({"user_id": uid})
    await db.wax_reports.delete_many({"user_id": uid})
    await db.collection_values.delete_many({"user_id": uid})
    await db.newsletter_subscribers.delete_many({"email": user.get("email")})
    await db.blocks.delete_many({"$or": [{"blocker_id": uid}, {"blocked_id": uid}]})

    # Finally delete the user
    await db.users.delete_one({"id": uid})

    return {"detail": "account deleted"}

