"""Admin routes — invite codes, beta signups, platform settings."""
from fastapi import APIRouter, HTTPException, Depends
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

from database import db, require_auth, logger

router = APIRouter()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")


# ─── Helpers ───

async def require_admin(user: Dict = Depends(require_auth)) -> Dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def generate_invite_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "HG-" + "".join(random.choices(chars, k=8))


async def send_beta_notification_email(signup: dict):
    """Send email notification for new beta signup via Resend."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email notification")
        return
    try:
        import resend
        resend.api_key = RESEND_API_KEY

        html = f"""
        <div style="font-family: Georgia, serif; max-width: 500px; margin: 0 auto; padding: 24px;">
            <h2 style="color: #2A1A06; font-size: 24px;">new beta signup</h2>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr><td style="padding: 8px 0; color: #8A6B4A; font-size: 14px;">name</td>
                    <td style="padding: 8px 0; color: #2A1A06; font-size: 16px;">{signup['first_name']}</td></tr>
                <tr><td style="padding: 8px 0; color: #8A6B4A; font-size: 14px;">email</td>
                    <td style="padding: 8px 0; color: #2A1A06; font-size: 16px;">{signup['email']}</td></tr>
                <tr><td style="padding: 8px 0; color: #8A6B4A; font-size: 14px;">instagram</td>
                    <td style="padding: 8px 0; color: #2A1A06; font-size: 16px;">@{signup['instagram_handle']}</td></tr>
                <tr><td style="padding: 8px 0; color: #8A6B4A; font-size: 14px;">most excited about</td>
                    <td style="padding: 8px 0; color: #2A1A06; font-size: 16px;">{signup['feature_interest']}</td></tr>
            </table>
            <p style="color: #8A6B4A; font-size: 13px; font-style: italic;">the honey groove beta</p>
        </div>
        """

        params = {
            "from": SENDER_EMAIL,
            "to": ["hello@thehoneygroove.com"],
            "subject": "new beta signup \U0001F41D",
            "html": html,
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Beta signup notification sent for {signup['email']}")
    except Exception as e:
        logger.error(f"Failed to send beta notification email: {e}")


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


# ════════════════════════════════════════════
# BETA SIGNUPS
# ════════════════════════════════════════════

class BetaSignupCreate(BaseModel):
    first_name: str
    email: str
    instagram_handle: str
    feature_interest: str


class BetaSignupNoteUpdate(BaseModel):
    notes: str


@router.post("/beta/signup")
async def create_beta_signup(data: BetaSignupCreate):
    """Public endpoint — no auth required."""
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
    return signups


@router.patch("/admin/beta-signups/{signup_id}/notes")
async def update_beta_signup_notes(signup_id: str, data: BetaSignupNoteUpdate, user: Dict = Depends(require_admin)):
    result = await db.beta_signups.update_one({"id": signup_id}, {"$set": {"notes": data.notes}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Signup not found")
    return {"status": "ok"}


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
async def register_with_invite(data: InviteRegister):
    """Register a new account using an invite code."""
    from database import hash_password, create_token

    # Validate invite code
    code_doc = await db.invite_codes.find_one({"code": data.code.strip().upper()}, {"_id": 0})
    if not code_doc or code_doc.get("status") != "unused":
        raise HTTPException(status_code=400, detail="This invite code is invalid or has already been used.")

    # Check email / username uniqueness
    if await db.users.find_one({"email": data.email.lower()}):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await db.users.find_one({"username": data.username.lower()}):
        raise HTTPException(status_code=400, detail="Username already taken")

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
        "created_at": now,
    }
    await db.users.insert_one(user_doc)

    # Mark code as used
    await db.invite_codes.update_one(
        {"code": data.code.strip().upper()},
        {"$set": {"status": "used", "used_by": user_id, "used_at": now}},
    )

    token = create_token(user_id)
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
        },
    }
