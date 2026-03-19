"""eBay Marketplace Account Deletion and Event Notification endpoints.

Required env vars:
  EBAY_VERIFICATION_TOKEN — shared secret configured in the eBay Developer Program portal
  BACKEND_URL             — canonical base URL used in challenge hash computation

eBay Developer Program docs:
  https://developer.ebay.com/marketplace-account-deletion
"""

import hashlib
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("ebay")
router = APIRouter()

EBAY_VERIFICATION_TOKEN = os.environ.get(
    "EBAY_VERIFICATION_TOKEN",
    "fbf73bb5f592c2c59363992217f0a7313f266ddb0da6ec7a48bd0ebc5c5c42e5",
)

BACKEND_URL = os.environ.get("BACKEND_URL", "https://the-honey-groove-v2.vercel.app")

DELETION_ENDPOINT = f"{BACKEND_URL}/api/ebay/account-deletion"
NOTIFICATIONS_ENDPOINT = f"{BACKEND_URL}/api/ebay/notifications"


def _challenge_response(challenge_code: str, endpoint_url: str) -> str:
    """SHA-256(challengeCode + verificationToken + endpointURL) as required by eBay."""
    payload = challenge_code + EBAY_VERIFICATION_TOKEN + endpoint_url
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ──────────────────────────────────────────────
# Marketplace Account Deletion
# ──────────────────────────────────────────────

@router.get("/ebay/account-deletion")
async def ebay_account_deletion_challenge(challenge_code: str):
    """eBay endpoint ownership verification — responds to GET ?challenge_code=<code>."""
    response = _challenge_response(challenge_code, DELETION_ENDPOINT)
    logger.info(f"eBay account-deletion challenge: {challenge_code[:8]}...")
    return JSONResponse({"challengeResponse": response})


@router.post("/ebay/account-deletion")
async def ebay_account_deletion(request: Request):
    """Receive eBay account deletion notification and purge any stored eBay user data."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    notification = payload.get("notification", {})
    data = notification.get("data", {})
    ebay_user_id = data.get("userId") or data.get("eBayUserId") or payload.get("userId")

    logger.info(f"eBay account deletion notification: userId={ebay_user_id}")

    # The Honey Groove does not store eBay user accounts — eBay pricing data is
    # consumed as anonymous market data only. Log the request for compliance audit.
    from database import db
    await db.ebay_deletion_log.insert_one({
        "ebay_user_id": ebay_user_id,
        "payload": payload,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "status": "processed — no eBay user data stored",
    })

    return JSONResponse(status_code=200, content={"status": "ok"})


# ──────────────────────────────────────────────
# Event Notifications (item sold, pricing)
# ──────────────────────────────────────────────

@router.get("/ebay/notifications")
async def ebay_notifications_challenge(challenge_code: str):
    """eBay endpoint ownership verification for the notifications endpoint."""
    response = _challenge_response(challenge_code, NOTIFICATIONS_ENDPOINT)
    logger.info(f"eBay notifications challenge: {challenge_code[:8]}...")
    return JSONResponse({"challengeResponse": response})


@router.post("/ebay/notifications")
async def ebay_notifications(request: Request):
    """Receive eBay item sold and pricing event notifications."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    metadata = payload.get("metadata", {})
    topic = metadata.get("topic") or payload.get("topic", "unknown")
    data = payload.get("notification", {}).get("data", {})

    logger.info(f"eBay notification received: topic={topic}")

    from database import db
    await db.ebay_events.insert_one({
        "topic": topic,
        "data": data,
        "raw": payload,
        "received_at": datetime.now(timezone.utc).isoformat(),
    })

    return JSONResponse(status_code=200, content={"status": "ok"})
