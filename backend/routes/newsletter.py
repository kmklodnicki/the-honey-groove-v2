"""Newsletter subscriber endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from datetime import datetime, timezone

from database import db, require_auth
from services.email_service import send_email_fire_and_forget

router = APIRouter()


@router.post("/newsletter/subscribe")
async def subscribe_newsletter(data: dict):
    """Subscribe to the newsletter (public or authenticated)."""
    email = (data.get("email") or "").strip().lower()
    source = data.get("source", "landing_page")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")
    existing = await db.newsletter_subscribers.find_one({"email": email})
    if existing:
        await db.newsletter_subscribers.update_one(
            {"email": email}, {"$set": {"subscribed": True, "source": source, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"subscribed": True, "email": email}
    doc = {"email": email, "subscribed": True, "source": source, "subscribed_at": datetime.now(timezone.utc).isoformat()}
    await db.newsletter_subscribers.insert_one({k: v for k, v in doc.items()})

    # Send newsletter signup confirmation email
    first_name = email.split("@")[0].capitalize()
    from templates.emails import newsletter_signup
    tpl = newsletter_signup(first_name)
    await send_email_fire_and_forget(email, tpl["subject"], tpl["html"])

    return {"subscribed": True, "email": email}


@router.post("/newsletter/unsubscribe")
async def unsubscribe_newsletter(data: dict, user: Dict = Depends(require_auth)):
    """Unsubscribe from the newsletter (authenticated)."""
    email = (data.get("email") or user.get("email", "")).strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    await db.newsletter_subscribers.update_one(
        {"email": email}, {"$set": {"subscribed": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"subscribed": False, "email": email}


@router.get("/newsletter/status")
async def get_newsletter_status(user: Dict = Depends(require_auth)):
    """Check if the authenticated user is subscribed."""
    email = user.get("email", "").lower()
    sub = await db.newsletter_subscribers.find_one({"email": email}, {"_id": 0})
    return {"subscribed": sub.get("subscribed", False) if sub else False, "email": email}
