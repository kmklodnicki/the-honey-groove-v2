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


router = APIRouter()

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
        avatar_url=user.get("avatar_url"),
        bio=user.get("bio"),
        setup=user.get("setup"),
        location=user.get("location"),
        favorite_genre=user.get("favorite_genre"),
        city=user.get("city"),
        region=user.get("region"),
        country=user.get("country"),
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
    )

# ============== AUTH ROUTES ==============

@router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    existing_username = await db.users.find_one({"username": user_data.username.lower()})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
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
        "email": user_data.email,
        "subscribed": True,
        "source": "registration",
        "subscribed_at": now,
    })

    token = create_token(user_id)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
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
    from services.rate_limiter import rate_limiter, get_client_ip
    rate_limiter.check(f"login:{get_client_ip(request)}", max_requests=15, window_seconds=300)

    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check email verification — skip, users have full access immediately
    token = create_token(user["id"])
    return TokenResponse(access_token=token, user=await _build_user_response(user))

@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: Dict = Depends(require_auth)):
    return await _build_user_response(user)

@router.put("/auth/me", response_model=UserResponse)
async def update_me(update_data: UserUpdate, user: Dict = Depends(require_auth)):
    update_fields = {}
    if update_data.username:
        existing = await db.users.find_one({"username": update_data.username.lower(), "id": {"$ne": user["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_fields["username"] = update_data.username.lower()
    for field in ("bio", "avatar_url", "city", "region", "country", "setup", "location", "favorite_genre", "instagram_username", "tiktok_username"):
        val = getattr(update_data, field, None)
        if val is not None:
            update_fields[field] = val
    if update_data.onboarding_completed is not None:
        update_fields["onboarding_completed"] = update_data.onboarding_completed
    if update_fields:
        await db.users.update_one({"id": user["id"]}, {"$set": update_fields})
    updated = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    return await _build_user_response(updated)



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

    verify_url = f"https://thehoneygroove.com/verify-email?token={token}"
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

@router.get("/users/{username}", response_model=UserResponse)
async def get_user_profile(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    resp = await _build_user_response(user)
    if not (current_user and current_user["id"] == user["id"]):
        resp.email = ""
    return resp


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

    # Finally delete the user
    await db.users.delete_one({"id": uid})

    return {"detail": "account deleted"}

