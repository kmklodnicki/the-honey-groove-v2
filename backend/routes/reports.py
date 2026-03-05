"""Report system — report posts, listings, and users."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from datetime import datetime, timezone
import uuid

from database import db, require_auth, logger

router = APIRouter()

REPORT_REASONS_POST = ["Spam", "Inappropriate content", "Incorrect information", "Harassment", "Other"]
REPORT_REASONS_LISTING = ["Spam", "Misleading description", "Prohibited item", "Other"]
REPORT_REASONS_USER = ["Spam", "Inappropriate behavior", "Harassment", "Other"]

@router.post("/reports")
async def create_report(data: dict, user: Dict = Depends(require_auth)):
    report_type = data.get("type")  # post, listing, user
    target_id = data.get("target_id")
    reason = data.get("reason")
    notes = data.get("notes", "")

    if not report_type or not target_id or not reason:
        raise HTTPException(status_code=400, detail="type, target_id, and reason are required")

    valid_reasons = {
        "post": REPORT_REASONS_POST,
        "listing": REPORT_REASONS_LISTING,
        "user": REPORT_REASONS_USER,
    }
    if report_type not in valid_reasons:
        raise HTTPException(status_code=400, detail="Invalid report type")
    if reason not in valid_reasons[report_type]:
        raise HTTPException(status_code=400, detail="Invalid reason for this report type")

    # Get content preview
    preview = ""
    if report_type == "post":
        post = await db.posts.find_one({"id": target_id}, {"_id": 0})
        preview = (post.get("caption") or post.get("content") or "")[:100] if post else ""
    elif report_type == "listing":
        listing = await db.listings.find_one({"id": target_id}, {"_id": 0})
        preview = listing.get("title", "")[:100] if listing else ""
    elif report_type == "user":
        target = await db.users.find_one({"id": target_id}, {"_id": 0, "username": 1})
        preview = f"@{target['username']}" if target else ""

    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    report_doc = {
        "id": report_id,
        "type": report_type,
        "target_id": target_id,
        "reporter_id": user["id"],
        "reporter_username": user.get("username"),
        "reason": reason,
        "notes": notes,
        "content_preview": preview,
        "status": "Pending",
        "created_at": now,
    }
    await db.reports.insert_one(report_doc)
    logger.info(f"Report created: {report_type} {target_id} by {user['username']}")
    return {"message": "thanks for letting us know. we'll review it shortly.", "id": report_id}


@router.get("/reports/admin")
async def admin_get_reports(user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    reports = await db.reports.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return reports


@router.put("/reports/admin/{report_id}")
async def admin_update_report(report_id: str, data: dict, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    status = data.get("status")
    if status not in ("Pending", "Reviewed", "Actioned", "Dismissed"):
        raise HTTPException(status_code=400, detail="Invalid status")
    await db.reports.update_one({"id": report_id}, {"$set": {"status": status}})
    return await db.reports.find_one({"id": report_id}, {"_id": 0})
