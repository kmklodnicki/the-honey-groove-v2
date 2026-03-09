"""
BLOCK 3.4: Report a Problem System
Unified reporting for listings, sellers, orders, and platform bugs.
Rate limited to 5 reports per user per 24 hours.
"""
import logging
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from database import db
from routes.auth import require_auth
from services.email_service import send_email

logger = logging.getLogger("reports")
router = APIRouter(prefix="/reports", tags=["reports"])

REPORT_REASONS = {
    "listing": [
        "Incorrect grading",
        "Misleading photos",
        "Counterfeit / bootleg",
        "Wrong pressing",
        "Item not as described",
        "Suspected scam",
        "Other",
    ],
    "seller": [
        "Misleading listings",
        "Poor grading practices",
        "Suspected fraud",
        "Harassment",
        "Other",
    ],
    "order": [
        "Item never shipped",
        "Item not as described",
        "Damage during shipping",
        "Wrong item received",
    ],
    "bug": [
        "UI / display issue",
        "Feature not working",
        "Performance problem",
        "Other",
    ],
    "feedback": [
        "General Feedback",
    ],
}


async def _check_rate_limit(user_id: str):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    count = await db.reports.count_documents({
        "reporter_user_id": user_id,
        "created_at": {"$gte": cutoff},
    })
    if count >= 5:
        raise HTTPException(status_code=429, detail="Rate limit reached (5 reports per 24 hours)")


@router.get("/reasons/{target_type}")
async def get_report_reasons(target_type: str):
    reasons = REPORT_REASONS.get(target_type)
    if not reasons:
        raise HTTPException(status_code=400, detail=f"Invalid target type: {target_type}")
    return {"reasons": reasons}


@router.post("/submit")
async def submit_report(body: Dict, user: Dict = Depends(require_auth)):
    """Submit a report for a listing, seller, order, or bug."""
    target_type = body.get("target_type")
    if target_type not in REPORT_REASONS:
        raise HTTPException(status_code=400, detail=f"Invalid target_type. Must be one of: {list(REPORT_REASONS.keys())}")

    reason = body.get("reason", "")
    if not reason:
        raise HTTPException(status_code=400, detail="Reason is required")

    await _check_rate_limit(user["id"])

    report_id = uuid.uuid4().hex[:16]
    doc = {
        "report_id": report_id,
        "reporter_user_id": user["id"],
        "reporter_username": user.get("username", ""),
        "target_type": target_type,
        "target_id": body.get("target_id"),
        "reason": reason,
        "notes": body.get("notes", ""),
        "page_url": body.get("page_url", ""),
        "browser_info": body.get("browser_info", ""),
        "screenshot_url": body.get("screenshot_url"),
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "admin_action": None,
        "resolved_at": None,
        "resolved_by": None,
    }
    await db.reports.insert_one(doc)

    # Send email notification to admin
    type_label = "General Feedback" if target_type == "feedback" else "Bug Report"
    email_html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
      <h2 style="color:#C8861A">New {type_label}</h2>
      <p><strong>From:</strong> @{user.get('username', 'unknown')}</p>
      <p><strong>Type:</strong> {type_label}</p>
      {'<p><strong>Reason:</strong> ' + reason + '</p>' if target_type != 'feedback' else ''}
      <p><strong>Message:</strong></p>
      <div style="background:#FAF6EE;padding:12px;border-radius:8px;margin:8px 0">{doc['notes']}</div>
      <p style="font-size:12px;color:#888">Page: {doc.get('page_url', 'N/A')}</p>
      <p style="font-size:12px;color:#888">Submitted: {doc['created_at']}</p>
    </div>
    """
    asyncio.create_task(send_email(
        "thello@thehoneygroove.com",
        f"[Honey Groove] New {type_label} from @{user.get('username', 'unknown')}",
        email_html,
    ))

    return {"report_id": report_id, "status": "OPEN", "message": "Report submitted. Our team will review it shortly."}


# ============== ADMIN ENDPOINTS ==============

@router.get("/admin/queue")
async def get_report_queue(
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    user: Dict = Depends(require_auth)
):
    """Admin: Get reports queue with optional filters."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    query = {}
    if target_type:
        query["target_type"] = target_type
    if status:
        query["status"] = status

    reports_list = await db.reports.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)

    for report in reports_list:
        reporter_id = report.get("reporter_user_id")
        if reporter_id:
            reporter = await db.users.find_one(
                {"id": reporter_id},
                {"_id": 0, "username": 1, "avatar_url": 1}
            )
            report["reporter"] = reporter or {}
        else:
            report["reporter"] = {}

        target_id = report.get("target_id")
        if report.get("target_type") == "listing" and target_id:
            listing = await db.listings.find_one({"id": target_id}, {"_id": 0, "artist": 1, "album": 1, "status": 1})
            report["target_info"] = listing or {}
        elif report.get("target_type") == "seller" and target_id:
            seller = await db.users.find_one({"id": target_id}, {"_id": 0, "username": 1})
            report["target_info"] = seller or {}
        elif report.get("target_type") == "order" and target_id:
            order = await db.payment_transactions.find_one({"id": target_id}, {"_id": 0, "artist": 1, "album": 1, "amount": 1})
            report["target_info"] = order or {}
        else:
            report["target_info"] = {}

    return reports_list


@router.post("/admin/{report_id}/action")
async def admin_report_action(report_id: str, body: Dict, user: Dict = Depends(require_auth)):
    """Admin: Take action on a report."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    action = body.get("action")
    valid_actions = ["REVIEWING", "DISMISSED", "RESOLVED", "REMOVE_LISTING", "WARN_SELLER", "SUSPEND_SELLER"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

    report = await db.reports.find_one({"report_id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    now = datetime.now(timezone.utc).isoformat()
    update = {
        "admin_action": action,
        "admin_notes": body.get("notes", ""),
        "resolved_by": user["id"],
    }

    if action in ["DISMISSED", "RESOLVED", "REMOVE_LISTING", "WARN_SELLER", "SUSPEND_SELLER"]:
        update["status"] = "RESOLVED"
        update["resolved_at"] = now
    elif action == "REVIEWING":
        update["status"] = "REVIEWING"

    if action == "REMOVE_LISTING" and report.get("target_id"):
        await db.listings.update_one({"id": report["target_id"]}, {"$set": {"status": "REMOVED_BY_ADMIN"}})

    if action == "WARN_SELLER" and report.get("target_id"):
        from routes.notifications import create_notification
        await create_notification(
            report["target_id"], "ADMIN_WARNING",
            "Account Warning",
            "Your account has received a warning due to a reported issue. Please review our community guidelines.",
            {"report_id": report_id}
        )

    if action == "SUSPEND_SELLER" and report.get("target_id"):
        await db.users.update_one({"id": report["target_id"]}, {"$set": {"is_suspended": True, "suspended_at": now}})

    await db.reports.update_one({"report_id": report_id}, {"$set": update})
    return {"message": f"Report action '{action}' applied successfully."}



@router.get("/admin/feedback")
async def get_feedback_reports(
    mode: Optional[str] = None,
    user: Dict = Depends(require_auth)
):
    """Admin: Get bug reports and general feedback with optional type filter."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    query = {"target_type": {"$in": ["bug", "feedback"]}}
    if mode == "bug":
        query["target_type"] = "bug"
    elif mode == "feedback":
        query["target_type"] = "feedback"

    entries = await db.reports.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)

    for entry in entries:
        rid = entry.get("reporter_user_id")
        if rid:
            u = await db.users.find_one({"id": rid}, {"_id": 0, "username": 1, "avatar_url": 1, "email": 1})
            entry["reporter"] = u or {}
        else:
            entry["reporter"] = {}

    return {"entries": entries}
