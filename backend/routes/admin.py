"""Admin routes — invite codes, beta signups, platform settings."""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import string
import random
import csv
import io
import asyncio
import os
import logging

from database import db, require_auth, logger, FRONTEND_URL
from services.email_service import send_email, send_email_fire_and_forget
from templates.emails import beta_waitlist, invite_code as invite_code_tpl

router = APIRouter()

ADMIN_NOTIFY_EMAIL = "katie@thehoneygroove.com"


# ─── Helpers ───

async def require_admin(user: Dict = Depends(require_auth)) -> Dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def generate_invite_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "HG-" + "".join(random.choices(chars, k=8))


async def send_beta_notification_email(signup: dict):
    """Send admin notification + user confirmation for beta signup."""
    # Admin notification (keep original format)
    from templates.base import wrap_email
    admin_html = f"""
    <p style="font-size:13px;color:#8A6B4A;"><strong>new beta signup</strong></p>
    <table style="width:100%;border-collapse:collapse;margin:8px 0;">
        <tr><td style="padding:6px 0;color:#8A6B4A;font-size:13px;">name</td><td style="padding:6px 0;color:#2A1A06;">{signup['first_name']}</td></tr>
        <tr><td style="padding:6px 0;color:#8A6B4A;font-size:13px;">email</td><td style="padding:6px 0;color:#2A1A06;">{signup['email']}</td></tr>
        <tr><td style="padding:6px 0;color:#8A6B4A;font-size:13px;">instagram</td><td style="padding:6px 0;color:#2A1A06;">@{signup['instagram_handle']}</td></tr>
        <tr><td style="padding:6px 0;color:#8A6B4A;font-size:13px;">interested in</td><td style="padding:6px 0;color:#2A1A06;">{signup['feature_interest']}</td></tr>
    </table>
    """
    await send_email(ADMIN_NOTIFY_EMAIL, "new beta signup \U0001F41D", wrap_email(admin_html))

    # User confirmation
    tpl = beta_waitlist(signup["first_name"])
    await send_email(signup["email"], tpl["subject"], tpl["html"])


# ════════════════════════════════════════════
# PLATFORM SETTINGS
# ════════════════════════════════════════════

class PlatformSettingUpdate(BaseModel):
    key: str
    value: float


@router.get("/admin/settings")
async def get_platform_settings(user: Dict = Depends(require_admin)):
    settings = await db.platform_settings.find({}, {"_id": 0}).to_list(100)
    return settings


@router.post("/admin/settings")
async def update_platform_setting(data: PlatformSettingUpdate, user: Dict = Depends(require_admin)):
    await db.platform_settings.update_one(
        {"key": data.key},
        {"$set": {"key": data.key, "value": data.value, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user["id"]}},
        upsert=True,
    )
    return {"status": "ok", "key": data.key, "value": data.value}


# ════════════════════════════════════════════
# INVITE CODES
# ════════════════════════════════════════════

class InviteCodeGenerate(BaseModel):
    count: int = 1


@router.post("/admin/invite-codes/generate")
async def generate_invite_codes(data: InviteCodeGenerate, user: Dict = Depends(require_admin)):
    count = min(data.count, 50)
    codes = []
    now = datetime.now(timezone.utc).isoformat()
    for _ in range(count):
        code = generate_invite_code()
        doc = {
            "id": str(uuid.uuid4()),
            "code": code,
            "status": "unused",
            "created_at": now,
            "created_by": user["id"],
            "used_by": None,
            "used_at": None,
        }
        await db.invite_codes.insert_one(doc)
        codes.append({"id": doc["id"], "code": code, "status": "unused", "created_at": now})
    return codes


@router.get("/admin/invite-codes")
async def list_invite_codes(user: Dict = Depends(require_admin)):
    codes = await db.invite_codes.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    # Enrich with used_by username
    for c in codes:
        if c.get("used_by"):
            u = await db.users.find_one({"id": c["used_by"]}, {"_id": 0, "username": 1, "email": 1})
            c["used_by_username"] = u.get("username") if u else None
            c["used_by_email"] = u.get("email") if u else None
    return codes


@router.delete("/admin/invite-codes/{code_id}")
async def delete_invite_code(code_id: str, user: Dict = Depends(require_admin)):
    result = await db.invite_codes.delete_one({"id": code_id, "status": "unused"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Code not found or already used")
    return {"status": "deleted"}


class InviteSend(BaseModel):
    code_id: str
    email: str
    first_name: str = "there"


@router.post("/admin/invite-codes/send")
async def send_invite_code_email(data: InviteSend, user: Dict = Depends(require_admin)):
    """Send an invite code email to a specific person."""
    code_doc = await db.invite_codes.find_one({"id": data.code_id, "status": "unused"}, {"_id": 0})
    if not code_doc:
        raise HTTPException(status_code=404, detail="Code not found or already used")
    tpl = invite_code_tpl(data.first_name, code_doc["code"])
    await send_email(data.email, tpl["subject"], tpl["html"], reply_to="hello@thehoneygroove.com")
    await db.invite_codes.update_one({"id": data.code_id}, {"$set": {"sent_to": data.email, "sent_at": datetime.now(timezone.utc).isoformat()}})
    return {"status": "sent", "email": data.email}


# ════════════════════════════════════════════
# BETA SIGNUPS
# ════════════════════════════════════════════

class BetaSignupCreate(BaseModel):
    first_name: str
    email: str
    instagram_handle: str
    feature_interest: str
    website: Optional[str] = None  # Honeypot field — bots fill this, humans don't


class BetaSignupNoteUpdate(BaseModel):
    notes: str


@router.post("/beta/signup")
async def create_beta_signup(data: BetaSignupCreate, request: Request):
    """Public endpoint — no auth required."""
    from services.rate_limiter import rate_limiter, get_client_ip
    rate_limiter.check(f"beta_signup:{get_client_ip(request)}", max_requests=3, window_seconds=3600)

    # Honeypot check — if hidden field is filled, silently reject (bot)
    if hasattr(data, 'website') and data.website:
        # Log the blocked submission
        await db.honeypot_blocks.insert_one({
            "id": str(uuid.uuid4()),
            "ip": get_client_ip(request),
            "email": data.email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"status": "ok", "message": "You're on the list!"}

    # Check for duplicate email
    existing = await db.beta_signups.find_one({"email": data.email.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="You've already signed up! We'll be in touch soon.")

    now = datetime.now(timezone.utc).isoformat()
    handle = data.instagram_handle.lstrip("@").strip()
    doc = {
        "id": str(uuid.uuid4()),
        "first_name": data.first_name.strip(),
        "email": data.email.lower().strip(),
        "instagram_handle": handle,
        "feature_interest": data.feature_interest,
        "submitted_at": now,
        "notes": "",
    }
    await db.beta_signups.insert_one(doc)

    # Send email notification (fire-and-forget)
    asyncio.create_task(send_beta_notification_email(doc))

    return {"status": "ok", "message": "You're on the list!"}


@router.get("/admin/beta-signups")
async def list_beta_signups(user: Dict = Depends(require_admin)):
    signups = await db.beta_signups.find({}, {"_id": 0}).sort("submitted_at", -1).to_list(10000)
    # Enrich with invite status: check if invite code was used (user joined)
    for s in signups:
        code_id = s.get("invite_code_id")
        if code_id:
            code_doc = await db.invite_codes.find_one({"id": code_id}, {"_id": 0, "status": 1, "used_at": 1, "used_by": 1})
            if code_doc and code_doc.get("status") == "used":
                s["invite_status"] = "used"
                s["invite_used_at"] = code_doc.get("used_at")
    return signups


@router.patch("/admin/beta-signups/{signup_id}/notes")
async def update_beta_signup_notes(signup_id: str, data: BetaSignupNoteUpdate, user: Dict = Depends(require_admin)):
    result = await db.beta_signups.update_one({"id": signup_id}, {"$set": {"notes": data.notes}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Signup not found")
    return {"status": "ok"}


@router.post("/admin/beta-signups/{signup_id}/send-invite")
async def send_invite_to_signup(signup_id: str, user: Dict = Depends(require_admin)):
    """Generate an invite code for a beta signup and send the invite email."""
    signup = await db.beta_signups.find_one({"id": signup_id}, {"_id": 0})
    if not signup:
        raise HTTPException(status_code=404, detail="Signup not found")

    now = datetime.now(timezone.utc).isoformat()

    # If there's an existing unused code for this signup, invalidate it
    old_code = signup.get("invite_code_id")
    if old_code:
        await db.invite_codes.update_one(
            {"id": old_code, "status": "unused"},
            {"$set": {"status": "revoked", "revoked_at": now}},
        )

    # Generate a new invite code
    code = generate_invite_code()
    code_doc = {
        "id": str(uuid.uuid4()),
        "code": code,
        "status": "unused",
        "created_at": now,
        "created_by": user["id"],
        "used_by": None,
        "used_at": None,
        "sent_to": signup["email"],
        "sent_at": now,
    }
    await db.invite_codes.insert_one(code_doc)

    # Send the invite email
    tpl = invite_code_tpl(signup["first_name"], code)
    await send_email(signup["email"], tpl["subject"], tpl["html"], reply_to="hello@thehoneygroove.com")

    # Update the signup record with invite tracking
    await db.beta_signups.update_one({"id": signup_id}, {"$set": {
        "invite_code_id": code_doc["id"],
        "invite_code": code,
        "invite_status": "sent",
        "invite_sent_at": now,
    }})

    return {
        "status": "sent",
        "invite_code": code,
        "invite_code_id": code_doc["id"],
        "invite_sent_at": now,
    }



@router.get("/admin/beta-signups/export")
async def export_beta_signups_csv(user: Dict = Depends(require_admin)):
    signups = await db.beta_signups.find({}, {"_id": 0}).sort("submitted_at", -1).to_list(10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["first_name", "email", "instagram_handle", "feature_interest", "submitted_at", "notes"])
    for s in signups:
        writer.writerow([s.get("first_name", ""), s.get("email", ""), s.get("instagram_handle", ""),
                         s.get("feature_interest", ""), s.get("submitted_at", ""), s.get("notes", "")])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=beta_signups.csv"},
    )


# ════════════════════════════════════════════
# INVITE CODE REGISTRATION (public)
# ════════════════════════════════════════════

class InviteRegister(BaseModel):
    code: str
    email: str
    password: str
    username: str


@router.post("/auth/register-invite")
async def register_with_invite(data: InviteRegister, request: Request):
    """Register a new account using an invite code — simplified for reliability."""
    from database import hash_password, create_token
    from services.rate_limiter import rate_limiter, get_client_ip

    try:
        rate_limiter.check(f"register:{get_client_ip(request)}", max_requests=5, window_seconds=900)
    except Exception as e:
        logger.error(f"Registration rate limit error: {e}")
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in 15 minutes.")

    # Step 1: Validate invite code
    try:
        code_doc = await db.invite_codes.find_one({"code": data.code.strip().upper()}, {"_id": 0})
        if not code_doc or code_doc.get("status") != "unused":
            logger.warning(f"Invalid invite code: {data.code} status={code_doc.get('status') if code_doc else 'NOT_FOUND'}")
            raise HTTPException(status_code=400, detail="This invite code is invalid or has already been used.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invite code lookup failed: {e}")
        raise HTTPException(status_code=500, detail="Could not validate invite code.")

    # Step 2: Check uniqueness
    try:
        if await db.users.find_one({"email": data.email.lower()}):
            raise HTTPException(status_code=400, detail="Email already registered")
        if await db.users.find_one({"username": data.username.lower()}):
            raise HTTPException(status_code=400, detail="Username already taken")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Uniqueness check failed: {e}")
        raise HTTPException(status_code=500, detail="Could not validate account details.")

    # Step 3: Create user
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    user_doc = {
        "id": user_id,
        "email": data.email.lower(),
        "username": data.username.lower(),
        "password_hash": hash_password(data.password),
        "avatar_url": f"https://api.dicebear.com/7.x/miniavs/svg?seed={data.username}",
        "bio": None,
        "setup": None,
        "location": None,
        "favorite_genre": None,
        "onboarding_completed": False,
        "founding_member": True,
        "email_verified": False,
        "created_at": now,
    }
    try:
        await db.users.insert_one(user_doc)
        logger.info(f"User created: @{data.username.lower()} ({data.email.lower()})")
    except Exception as e:
        logger.error(f"User insert failed: {e}")
        raise HTTPException(status_code=500, detail="Could not create account.")

    # Step 4: Mark code as used
    try:
        await db.invite_codes.update_one(
            {"code": data.code.strip().upper()},
            {"$set": {"status": "used", "used_by": user_id, "used_at": now}},
        )
    except Exception as e:
        logger.error(f"Code update failed (user already created): {e}")

    # Step 5: Generate token
    token = create_token(user_id)

    # Step 6: Send emails (non-blocking, never fails registration)
    try:
        verify_token = str(uuid.uuid4())
        await db.email_verifications.insert_one({
            "user_id": user_id,
            "token": verify_token,
            "created_at": now,
        })
        verify_url = f"{FRONTEND_URL}/verify-email?token={verify_token}"
        verify_html = f"""
        <div style="font-family: Georgia, serif; max-width: 480px; margin: 0 auto; padding: 40px 20px; background: #FAF6EE;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="font-size: 28px; color: #2A1A06; margin: 0;">Welcome to the Honey Groove</h1>
          </div>
          <p style="font-size: 16px; color: #8A6B4A; line-height: 1.6;">
            You're in! Click the button below to verify your email address and start exploring.
          </p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}" style="display: inline-block; padding: 14px 32px; background: #E8A820; color: #2A1A06; text-decoration: none; border-radius: 999px; font-weight: 600; font-size: 16px;">
              Verify My Email
            </a>
          </div>
          <p style="font-size: 13px; color: #8A6B4A99; text-align: center;">
            This link expires in 24 hours.
          </p>
        </div>
        """
        asyncio.create_task(send_email(data.email.lower(), "Verify your Honey Groove account. \U0001F41D", verify_html))
        from templates.emails import welcome as welcome_tpl
        asyncio.create_task(send_email(data.email.lower(), **(lambda t: {"subject": t["subject"], "html": t["html"]})(welcome_tpl(data.username.lower()))))
    except Exception as e:
        logger.error(f"Email send setup failed (registration still successful): {e}")

    logger.info(f"Registration complete: @{data.username.lower()} with code {data.code.strip().upper()}")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": data.email.lower(),
            "username": data.username.lower(),
            "avatar_url": user_doc["avatar_url"],
            "founding_member": True,
            "onboarding_completed": False,
            "email_verified": False,
        },
    }


# ═══════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════

@router.get("/admin/users")
async def list_users(
    search: str = "",
    role_filter: str = "all",
    user: Dict = Depends(require_admin),
):
    """List all users with optional search and role filter."""
    query = {}
    if search:
        regex = {"$regex": search, "$options": "i"}
        query["$or"] = [{"username": regex}, {"email": regex}]
    if role_filter == "admin":
        query["is_admin"] = True
    elif role_filter == "standard":
        query["$or"] = query.get("$or", [])
        query.setdefault("is_admin", {"$ne": True})

    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return [
        {
            "id": u["id"],
            "username": u.get("username"),
            "email": u.get("email"),
            "avatar_url": u.get("avatar_url"),
            "is_admin": u.get("is_admin", False),
            "created_at": u.get("created_at"),
            "title_label": u.get("title_label"),
            "golden_hive": u.get("golden_hive", False),
            "golden_hive_status": u.get("golden_hive_status"),
        }
        for u in users
    ]


class AdminRoleUpdate(BaseModel):
    user_id: str
    is_admin: bool


@router.post("/admin/users/role")
async def update_user_role(data: AdminRoleUpdate, user: Dict = Depends(require_admin)):
    """Grant or revoke admin access for a user."""
    if data.user_id == user["id"] and not data.is_admin:
        raise HTTPException(status_code=400, detail="You cannot remove your own admin access.")

    target = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users.update_one({"id": data.user_id}, {"$set": {"is_admin": data.is_admin}})
    action = "granted" if data.is_admin else "revoked"
    return {"detail": f"Admin access {action} for @{target.get('username')}"}



class SetTitleLabel(BaseModel):
    user_id: str
    title_label: Optional[str] = None

@router.put("/admin/users/title-label")
async def set_user_title_label(data: SetTitleLabel, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    target = await db.users.find_one({"id": data.user_id}, {"_id": 0, "username": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    label = data.title_label.strip() if data.title_label else None
    await db.users.update_one({"id": data.user_id}, {"$set": {"title_label": label}})
    return {"detail": f"Title label for @{target.get('username')} set to '{label or '(none)'}'" }


@router.delete("/admin/users/{user_id}")
async def remove_user(user_id: str, user: Dict = Depends(require_admin)):
    """Permanently remove a user and all their associated data."""
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot remove your own account.")

    target = await db.users.find_one({"id": user_id}, {"_id": 0, "username": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    username = target.get("username", "unknown")

    # Remove all associated data
    await db.posts.delete_many({"user_id": user_id})
    await db.comments.delete_many({"user_id": user_id})
    await db.likes.delete_many({"user_id": user_id})
    await db.followers.delete_many({"$or": [{"follower_id": user_id}, {"following_id": user_id}]})
    await db.records.delete_many({"user_id": user_id})
    await db.spins.delete_many({"user_id": user_id})
    await db.iso_items.delete_many({"user_id": user_id})
    await db.notifications.delete_many({"$or": [{"user_id": user_id}, {"from_user_id": user_id}]})
    await db.reports.delete_many({"reporter_user_id": user_id})
    await db.users.delete_one({"id": user_id})

    logger.info(f"Admin @{user.get('username')} removed user @{username} ({user_id})")
    return {"detail": f"User @{username} and all associated data have been removed."}


@router.post("/admin/users/{user_id}/temp-password")
async def admin_temp_password(user_id: str, user: Dict = Depends(require_admin)):
    """Generate a temporary password for a user, hash it, email it, and log the action."""
    from database import hash_password
    from templates.base import wrap_email

    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Use the Settings page to change your own password.")

    # Generate HG-XXXX-XX temp password
    digits = ''.join(random.choices(string.digits, k=4))
    suffix = ''.join(random.choices(string.ascii_uppercase, k=2))
    temp_pw = f"HG-{digits}-{suffix}"

    # Hash and save
    from database import hash_password
    hashed = hash_password(temp_pw)
    await db.users.update_one({"id": user_id}, {"$set": {"password_hash": hashed}})

    # Send email
    body = f"""
    <p style="font-size:16px;color:#2A1A06;line-height:1.6;">
      Hi <strong>{target.get('username', '')}</strong>,
    </p>
    <p style="font-size:15px;color:#2A1A06;line-height:1.6;">
      We've generated a temporary password to get you back into the hive:
    </p>
    <div style="text-align:center;margin:24px 0;">
      <span style="display:inline-block;padding:14px 28px;background:#FFF6E6;border:2px solid #DAA520;border-radius:12px;font-family:monospace;font-size:22px;font-weight:700;color:#2A1A06;letter-spacing:2px;">
        {temp_pw}
      </span>
    </div>
    <p style="font-size:14px;color:#5a4a3a;line-height:1.6;">
      Please log in and update your password in <strong>Settings</strong> immediately.
    </p>
    """
    html = wrap_email(body)
    await send_email_fire_and_forget(target["email"], "Your Honey Groove Temporary Password", html)

    # Audit log
    now = datetime.now(timezone.utc).isoformat()
    await db.admin_audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "temp_password_reset",
        "admin_id": user["id"],
        "admin_username": user.get("username"),
        "target_user_id": user_id,
        "target_username": target.get("username"),
        "target_email": target.get("email"),
        "created_at": now,
    })

    logger.info(f"Admin @{user.get('username')} sent temp password to @{target.get('username')} ({target.get('email')})")
    return {"detail": f"Temporary password sent to {target.get('email')}"}


# ============== GOLDEN HIVE ID ADMIN ==============


@router.get("/admin/golden-hive/pending")
async def admin_golden_hive_pending(user: Dict = Depends(require_admin)):
    """List all users with pending Golden Hive verification."""
    pending = await db.users.find(
        {"golden_hive_status": "pending"},
        {"_id": 0, "id": 1, "username": 1, "display_name": 1, "profile_photo": 1, "email": 1,
         "golden_hive_status": 1, "golden_hive_payment_at": 1, "golden_hive_payment_id": 1}
    ).to_list(100)
    return pending


@router.post("/admin/golden-hive/{user_id}/approve")
async def admin_golden_hive_approve(user_id: str, user: Dict = Depends(require_admin)):
    """Approve a Golden Hive ID verification."""
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.get("golden_hive_status") != "pending":
        raise HTTPException(status_code=400, detail="User is not pending verification")

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": user_id}, {"$set": {
        "golden_hive_verified": True,
        "golden_hive_status": "approved",
        "golden_hive_verified_at": now,
    }})

    from database import create_notification
    await create_notification(user_id, "GOLDEN_HIVE_APPROVED",
        "Golden Hive ID Approved!",
        "Congratulations! Your Golden Hive ID has been verified. You now have a trusted collector badge.",
        {})

    logger.info(f"Admin @{user.get('username')} approved Golden Hive for user {user_id}")
    return {"message": f"Golden Hive ID approved for @{target.get('username')}"}


@router.post("/admin/golden-hive/{user_id}/reject")
async def admin_golden_hive_reject(user_id: str, user: Dict = Depends(require_admin)):
    """Reject a Golden Hive ID verification (refund should be handled separately)."""
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users.update_one({"id": user_id}, {"$set": {
        "golden_hive_status": "rejected",
        "golden_hive_verified": False,
    }})

    from database import create_notification
    await create_notification(user_id, "GOLDEN_HIVE_REJECTED",
        "Golden Hive ID Review",
        "Your Golden Hive ID verification was not approved at this time. Please contact support for details.",
        {})

    logger.info(f"Admin @{user.get('username')} rejected Golden Hive for user {user_id}")
    return {"message": f"Golden Hive ID rejected for @{target.get('username')}"}



# ─── Global Metadata Scrub ───

@router.post("/admin/scrub-unofficial-metadata")
async def scrub_unofficial_metadata(user: Dict = Depends(require_admin)):
    """One-time scrub: re-fetch Discogs metadata for every record with a discogs_id
    and correct the is_unofficial flag based on format_descriptions."""
    from database import get_discogs_release
    import time

    cursor = db.records.find(
        {"discogs_id": {"$exists": True, "$ne": None}},
        {"_id": 0, "id": 1, "discogs_id": 1, "is_unofficial": 1, "title": 1, "artist": 1}
    )
    records = await cursor.to_list(length=None)
    total = len(records)
    updated = 0
    flagged = []
    unflagged = []
    errors = []

    # Batch with 1s delay every 25 records to respect Discogs rate limits
    for i, rec in enumerate(records):
        discogs_id = rec.get("discogs_id")
        if not discogs_id:
            continue

        try:
            release_data = get_discogs_release(int(discogs_id))
            if not release_data:
                errors.append({"id": rec["id"], "discogs_id": discogs_id, "reason": "no data returned"})
                continue

            format_descs = release_data.get("format_descriptions", [])
            # Smart Flag: check format_descriptions, notes, and format text
            import re as _re
            _unofficial_kw = _re.compile(r'\b(unofficial|bootleg|counterfeit)\b', _re.IGNORECASE)
            should_be_unofficial = "Unofficial Release" in format_descs
            if not should_be_unofficial:
                should_be_unofficial = any(_unofficial_kw.search(d) for d in format_descs)
            if not should_be_unofficial:
                notes = release_data.get("notes", "")
                if notes and _unofficial_kw.search(notes):
                    should_be_unofficial = True
            current_flag = rec.get("is_unofficial", False)

            if should_be_unofficial != current_flag:
                await db.records.update_one(
                    {"id": rec["id"]},
                    {"$set": {"is_unofficial": should_be_unofficial}}
                )
                updated += 1
                entry = {
                    "id": rec["id"],
                    "discogs_id": discogs_id,
                    "artist": rec.get("artist", ""),
                    "title": rec.get("title", ""),
                    "was": current_flag,
                    "now": should_be_unofficial,
                }
                if should_be_unofficial:
                    flagged.append(entry)
                else:
                    unflagged.append(entry)

        except Exception as e:
            errors.append({"id": rec["id"], "discogs_id": discogs_id, "reason": str(e)})

        # Rate limit: pause 1s every 25 records
        if (i + 1) % 25 == 0:
            await asyncio.sleep(1)

    logger.info(f"Metadata scrub complete: {total} scanned, {updated} updated, {len(errors)} errors")

    return {
        "total_scanned": total,
        "total_updated": updated,
        "newly_flagged_unofficial": flagged,
        "newly_unflagged": unflagged,
        "errors": errors[:50],
    }


# ─── OAuth Diagnostic ───

@router.post("/admin/oauth-status")
async def oauth_status(user: Dict = Depends(require_admin)):
    """Diagnostic endpoint: verify Discogs OAuth env vars are loaded and test the handshake."""
    from database import DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET, DISCOGS_REQUEST_TOKEN_URL, DISCOGS_USER_AGENT

    key_present = bool(DISCOGS_CONSUMER_KEY)
    secret_present = bool(DISCOGS_CONSUMER_SECRET)
    key_preview = f"{DISCOGS_CONSUMER_KEY[:4]}...{DISCOGS_CONSUMER_KEY[-4:]}" if key_present and len(DISCOGS_CONSUMER_KEY) > 8 else ("SET" if key_present else "MISSING")
    secret_preview = f"{DISCOGS_CONSUMER_SECRET[:4]}...{DISCOGS_CONSUMER_SECRET[-4:]}" if secret_present and len(DISCOGS_CONSUMER_SECRET) > 8 else ("SET" if secret_present else "MISSING")

    result = {
        "consumer_key_status": key_preview,
        "consumer_secret_status": secret_preview,
        "both_configured": key_present and secret_present,
        "handshake_test": None,
    }

    if key_present and secret_present:
        try:
            from requests_oauthlib import OAuth1Session
            oauth = OAuth1Session(
                client_key=DISCOGS_CONSUMER_KEY,
                client_secret=DISCOGS_CONSUMER_SECRET,
                callback_uri="https://thehoneygroove.com/api/discogs/oauth/callback",
                signature_method="HMAC-SHA1",
            )
            response = oauth.fetch_request_token(
                DISCOGS_REQUEST_TOKEN_URL,
                headers={"User-Agent": DISCOGS_USER_AGENT},
            )
            token = response.get("oauth_token", "")
            result["handshake_test"] = f"SUCCESS — request_token={token[:8]}..."
        except Exception as e:
            err = str(e)
            if hasattr(e, "response") and e.response is not None:
                err = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            result["handshake_test"] = f"FAILED — {err}"

    return result



# ─── Test Data Purge ───

@router.post("/admin/purge-test-data")
async def purge_test_data(user: Dict = Depends(require_admin)):
    """Production cleanup: remove all test listings, trades, and their related notifications/feed items.
    Identifies test data by: test accounts (@test.com, @example.com), or 'test'/'demo' in descriptions."""
    import re

    # 1. Identify test user IDs
    test_patterns = [
        {"email": {"$regex": r"@test\.com$", "$options": "i"}},
        {"email": {"$regex": r"@example\.com$", "$options": "i"}},
        {"email": {"$regex": r"test", "$options": "i"}},
        {"username": {"$regex": r"^test", "$options": "i"}},
    ]
    test_users = await db.users.find(
        {"$or": test_patterns},
        {"_id": 0, "id": 1, "email": 1, "username": 1}
    ).to_list(1000)
    test_user_ids = [u["id"] for u in test_users]

    # Never purge the known admin/founder accounts
    protected_ids = {"4072aaa7-1171-4cd2-9c8f-20dfca8fdc58"}
    test_user_ids = [uid for uid in test_user_ids if uid not in protected_ids]

    purge_report = {
        "test_users_found": [{"id": u["id"], "email": u["email"], "username": u["username"]} for u in test_users if u["id"] not in protected_ids],
        "listings_deleted": 0,
        "trade_requests_deleted": 0,
        "notifications_deleted": 0,
        "posts_deleted": 0,
    }

    if not test_user_ids:
        purge_report["message"] = "No test accounts found to purge."
        return purge_report

    # 2. Delete listings from test users
    listing_result = await db.listings.delete_many({"user_id": {"$in": test_user_ids}})
    purge_report["listings_deleted"] = listing_result.deleted_count

    # Also delete listings with 'test' in description
    test_desc_result = await db.listings.delete_many({
        "description": {"$regex": r"\btest\b", "$options": "i"},
        "user_id": {"$nin": list(protected_ids)},
    })
    purge_report["listings_deleted"] += test_desc_result.deleted_count

    # 3. Delete trade requests involving test users
    trade_result = await db.trade_requests.delete_many({
        "$or": [
            {"sender_id": {"$in": test_user_ids}},
            {"receiver_id": {"$in": test_user_ids}},
        ]
    })
    purge_report["trade_requests_deleted"] = trade_result.deleted_count

    # 4. Clean up notifications from/to test users
    notif_result = await db.notifications.delete_many({
        "$or": [
            {"user_id": {"$in": test_user_ids}},
            {"from_user_id": {"$in": test_user_ids}},
        ]
    })
    purge_report["notifications_deleted"] = notif_result.deleted_count

    # 5. Remove feed posts from test users
    post_result = await db.posts.delete_many({"user_id": {"$in": test_user_ids}})
    purge_report["posts_deleted"] = post_result.deleted_count

    logger.info(f"Test data purge by @{user.get('username')}: {purge_report}")
    return purge_report


# ─── Placeholder Image Sweep ───

@router.post("/admin/placeholder-sweep")
async def placeholder_sweep(user: Dict = Depends(require_admin)):
    """Sweep all records with missing/placeholder cover images and re-fetch from Discogs."""
    from database import get_discogs_release
    import time

    # Find records with no cover_url, empty cover_url, or known placeholder patterns
    cursor = db.records.find(
        {"$or": [
            {"cover_url": None},
            {"cover_url": ""},
            {"cover_url": {"$regex": "spacer\\.gif|placeholder", "$options": "i"}},
        ]},
        {"_id": 0, "id": 1, "discogs_id": 1, "title": 1, "artist": 1, "cover_url": 1}
    )
    records = await cursor.to_list(length=None)
    total = len(records)
    fixed = 0
    failed = 0
    fixed_records = []

    for i, rec in enumerate(records):
        discogs_id = rec.get("discogs_id")
        if not discogs_id:
            failed += 1
            continue

        try:
            release = get_discogs_release(int(discogs_id))
            new_url = release.get("cover_url") if release else None
            if new_url:
                await db.records.update_one(
                    {"id": rec["id"]},
                    {"$set": {"cover_url": new_url}}
                )
                fixed += 1
                fixed_records.append({
                    "id": rec["id"],
                    "title": rec.get("title"),
                    "artist": rec.get("artist"),
                    "old_url": rec.get("cover_url"),
                    "new_url": new_url[:80],
                })
            else:
                failed += 1
        except Exception as e:
            failed += 1

        if (i + 1) % 25 == 0:
            await asyncio.sleep(1)

    logger.info(f"Placeholder sweep: {total} found, {fixed} fixed, {failed} failed")
    return {
        "total_placeholders": total,
        "fixed": fixed,
        "failed": failed,
        "fixed_records": fixed_records[:30],
    }


@router.get("/admin/db-stats")
async def admin_db_stats(user: dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    collections = ["users", "posts", "records", "spins", "prompts", "prompt_responses",
                    "followers", "likes", "comments", "notifications", "iso_items",
                    "listings", "beta_signups", "invite_codes", "newsletter_subscribers"]
    stats = {}
    for coll in collections:
        stats[coll] = await db[coll].count_documents({})
    stats["_db_name"] = db.name
    return stats

