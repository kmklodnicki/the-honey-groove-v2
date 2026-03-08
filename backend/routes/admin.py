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

ADMIN_NOTIFY_EMAIL = "hello@thehoneygroove.com"


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
        verify_url = f"https://thehoneygroove.com/verify-email?token={verify_token}"
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
