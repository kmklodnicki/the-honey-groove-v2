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

# ============== LISTING ALERT ROUTES ==============

class ListingAlertCreate(BaseModel):
    discogs_id: int
    album_name: str
    variant_name: Optional[str] = None
    artist: Optional[str] = None
    cover_url: Optional[str] = None


@router.post("/listing-alerts")
async def create_listing_alert(data: ListingAlertCreate, user: Dict = Depends(require_auth)):
    """Subscribe to be notified when a specific release is listed in the Honeypot."""
    existing = await db.listing_alerts.find_one({
        "user_id": user["id"], "discogs_id": data.discogs_id, "status": "ACTIVE"
    })
    if existing:
        return {"message": "Already subscribed", "id": existing["id"]}

    alert_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": alert_id,
        "user_id": user["id"],
        "discogs_id": data.discogs_id,
        "album_name": data.album_name,
        "variant_name": data.variant_name,
        "artist": data.artist,
        "cover_url": data.cover_url,
        "status": "ACTIVE",
        "created_at": now,
    }
    await db.listing_alerts.insert_one(doc)
    return {"message": "Alert created", "id": alert_id}


@router.get("/listing-alerts")
async def get_listing_alerts(user: Dict = Depends(require_auth)):
    """Get all active listing alerts for the current user."""
    alerts = await db.listing_alerts.find(
        {"user_id": user["id"], "status": "ACTIVE"}, {"_id": 0}
    ).to_list(100)
    return alerts


@router.delete("/listing-alerts/{alert_id}")
async def delete_listing_alert(alert_id: str, user: Dict = Depends(require_auth)):
    """Unsubscribe from a listing alert."""
    result = await db.listing_alerts.delete_one({"id": alert_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert removed"}


# ============== NOTIFICATION ROUTES ==============

@router.get("/notifications")
async def get_notifications(limit: int = 15, skip: int = 0, user: Dict = Depends(require_auth)):
    """BLOCK 575: Paginated notifications with skip/limit."""
    notifs = await db.notifications.find(
        {"user_id": user["id"], "type": {"$ne": "dm"}}, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return notifs


@router.get("/notifications/unread-count")
async def get_unread_count(user: Dict = Depends(require_auth)):
    count = await db.notifications.count_documents({"user_id": user["id"], "read": False, "type": {"$ne": "dm"}})
    return {"count": count}


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: Dict = Depends(require_auth)):
    await db.notifications.update_one({"id": notification_id, "user_id": user["id"]}, {"$set": {"read": True}})
    return {"message": "Marked as read"}


@router.put("/notifications/read-all")
async def mark_all_read(user: Dict = Depends(require_auth)):
    await db.notifications.update_many({"user_id": user["id"], "read": False}, {"$set": {"read": True}})
    return {"message": "All marked as read"}


