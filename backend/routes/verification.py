"""
BLOCK 3.3: Verification Queue - The Gate
Users upload ID photos for Golden Hive verification.
Admin can review blurred previews, unblur, and approve/deny.
"""
import logging
import uuid
import io
import asyncio
from datetime import datetime, timezone
from typing import Dict
from PIL import Image, ImageFilter
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from database import db
from routes.auth import require_auth
from routes.admin import require_admin
from services.email_service import send_email

logger = logging.getLogger("verification")
router = APIRouter(prefix="/verification", tags=["verification"])


def _generate_blurred(image_bytes: bytes) -> bytes:
    """Generate a heavily blurred version of an image for admin preview."""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    # Heavy Gaussian blur - enough to obscure text/details
    blurred = img.filter(ImageFilter.GaussianBlur(radius=25))
    buf = io.BytesIO()
    blurred.save(buf, format="JPEG", quality=60)
    buf.seek(0)
    return buf.getvalue()


@router.post("/submit")
async def submit_verification(
    id_photo: UploadFile = File(...),
    user: Dict = Depends(require_auth)
):
    """User submits an ID photo for Golden Hive verification."""
    # Check if user has paid the verification fee
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "golden_hive": 1, "golden_hive_status": 1})
    if u and u.get("golden_hive"):
        raise HTTPException(status_code=400, detail="You are already Golden Hive verified")
    if not u or u.get("golden_hive_status") != "PAID_PENDING_UPLOAD":
        raise HTTPException(status_code=403, detail="Please complete the Golden ID verification payment first")

    # Check for existing pending request
    existing = await db.verification_requests.find_one(
        {"user_id": user["id"], "status": "PENDING"}, {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending verification request")

    # Read and validate image
    contents = await id_photo.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Upload original
    from database import put_object, FRONTEND_URL, APP_NAME
    from routes.collection import process_image
    from utils.cloudinary_upload import is_cloudinary_configured, upload_image_buffer

    try:
        processed_data, final_ct, final_ext = process_image(contents, id_photo.content_type or "image/jpeg", id_photo.filename)
    except Exception:
        processed_data, final_ct, final_ext = contents, "image/jpeg", "jpg"

    # Generate blurred version
    blurred_bytes = _generate_blurred(processed_data)

    if is_cloudinary_configured():
        try:
            orig_result = upload_image_buffer(processed_data, folder=f"honeygroove/verification/{user['id']}")
            original_url = orig_result["secure_url"]
            blur_result = upload_image_buffer(blurred_bytes, folder=f"honeygroove/verification/{user['id']}/blurred")
            blurred_url = blur_result["secure_url"]
        except Exception as e:
            logger.error(f"Cloudinary verification upload failed, using fallback: {e}")
            orig_path = f"{APP_NAME}/verification/{user['id']}/original_{uuid.uuid4().hex}.{final_ext}"
            result = put_object(orig_path, processed_data, final_ct)
            original_url = f"{FRONTEND_URL}/api/files/serve/{result['path']}"
            blur_path = f"{APP_NAME}/verification/{user['id']}/blurred_{uuid.uuid4().hex}.jpg"
            blur_result = put_object(blur_path, blurred_bytes, "image/jpeg")
            blurred_url = f"{FRONTEND_URL}/api/files/serve/{blur_result['path']}"
    else:
        orig_path = f"{APP_NAME}/verification/{user['id']}/original_{uuid.uuid4().hex}.{final_ext}"
        result = put_object(orig_path, processed_data, final_ct)
        original_url = f"{FRONTEND_URL}/api/files/serve/{result['path']}"
        blur_path = f"{APP_NAME}/verification/{user['id']}/blurred_{uuid.uuid4().hex}.jpg"
        blur_result = put_object(blur_path, blurred_bytes, "image/jpeg")
        blurred_url = f"{FRONTEND_URL}/api/files/serve/{blur_result['path']}"

    request_id = uuid.uuid4().hex[:16]
    doc = {
        "id": request_id,
        "user_id": user["id"],
        "username": user.get("username", ""),
        "original_image_url": original_url,
        "blurred_image_url": blurred_url,
        "status": "PENDING",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_at": None,
        "reviewed_by": None,
        "admin_notes": None,
    }
    await db.verification_requests.insert_one(doc)

    # Update user status from PAID_PENDING_UPLOAD to pending (admin review)
    await db.users.update_one({"id": user["id"]}, {"$set": {"golden_hive_status": "pending"}})

    return {
        "id": request_id,
        "status": "PENDING",
        "message": "Your verification request has been submitted. You'll be notified once reviewed.",
    }


@router.get("/status")
async def get_verification_status(user: Dict = Depends(require_auth)):
    """Get the current user's verification status."""
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "golden_hive": 1})
    if u and u.get("golden_hive"):
        return {"status": "APPROVED", "golden_hive": True}

    request = await db.verification_requests.find_one(
        {"user_id": user["id"]}, {"_id": 0, "original_image_url": 0, "blurred_image_url": 0}
    )
    if request:
        return {"status": request["status"], "golden_hive": False, "submitted_at": request.get("submitted_at")}
    return {"status": "NONE", "golden_hive": False}


# ============== ADMIN ENDPOINTS ==============

@router.get("/admin/queue")
async def get_verification_queue(user: Dict = Depends(require_admin)):
    """Admin: Get all pending verification requests."""
    requests = await db.verification_requests.find(
        {"status": "PENDING"}, {"_id": 0}
    ).sort("submitted_at", 1).to_list(100)

    # Enrich with user info
    for req in requests:
        u = await db.users.find_one({"id": req["user_id"]}, {"_id": 0, "username": 1, "profile_pic": 1, "email": 1, "country": 1})
        req["user"] = u or {}
        # Don't expose original URL in listing - only blurred
        req.pop("original_image_url", None)

    return requests


@router.get("/admin/queue/all")
async def get_all_verification_requests(user: Dict = Depends(require_admin)):
    """Admin: Get all verification requests (pending + reviewed)."""
    requests = await db.verification_requests.find(
        {}, {"_id": 0}
    ).sort("submitted_at", -1).to_list(200)

    for req in requests:
        u = await db.users.find_one({"id": req["user_id"]}, {"_id": 0, "username": 1, "profile_pic": 1, "email": 1})
        req["user"] = u or {}
        req.pop("original_image_url", None)

    return requests


@router.get("/admin/unblur/{request_id}")
async def unblur_verification(request_id: str, user: Dict = Depends(require_admin)):
    """Admin: Get the original (unblurred) image URL for a verification request."""
    req = await db.verification_requests.find_one({"id": request_id}, {"_id": 0, "original_image_url": 1})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"original_image_url": req["original_image_url"]}


@router.post("/admin/approve/{request_id}")
async def approve_verification(request_id: str, user: Dict = Depends(require_admin)):
    """Admin: Approve a verification request and grant Golden Hive status."""
    req = await db.verification_requests.find_one({"id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req["status"] != "PENDING":
        raise HTTPException(status_code=400, detail=f"Request is already {req['status']}")

    now = datetime.now(timezone.utc).isoformat()
    await db.verification_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "APPROVED", "reviewed_at": now, "reviewed_by": user["id"]}}
    )
    await db.users.update_one(
        {"id": req["user_id"]},
        {"$set": {"golden_hive": True, "golden_hive_at": now}}
    )

    # In-App: Golden celebration notification
    from routes.notifications import create_notification
    await create_notification(
        req["user_id"], "VERIFICATION_APPROVED",
        "Welcome to the Inner Circle!",
        "Your Golden ID has been approved. You're now a verified member of The Honey Groove.",
        {"request_id": request_id, "icon": "sparkle"}
    )

    # Email: Verification Success (async, non-blocking)
    target_user = await db.users.find_one({"id": req["user_id"]}, {"_id": 0})
    if target_user and target_user.get("email"):
        try:
            from templates.base import wrap_email
            html = wrap_email(f"""
                <h2 style="color:#D98C2F;font-family:serif;">You're Verified</h2>
                <p>Congratulations, <strong>@{target_user.get('username', 'collector')}</strong>!</p>
                <p>Your Golden Hive ID has been approved. You now have a trusted collector badge and access to premium features.</p>
                <p>Welcome to the Inner Circle.</p>
                <p style="color:#8A6B4A;font-size:12px;">— The Honey Groove Team</p>
            """)
            asyncio.create_task(send_email(target_user["email"], "The Honey Groove: You're Verified.", html))
        except Exception as e:
            logger.warning(f"Failed to send approval email: {e}")

    return {"message": "Verification approved. User granted Golden Hive status."}


@router.post("/admin/deny/{request_id}")
async def deny_verification(request_id: str, body: Dict = {}, user: Dict = Depends(require_admin)):
    """Admin: Deny a verification request with optional reason."""
    req = await db.verification_requests.find_one({"id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req["status"] != "PENDING":
        raise HTTPException(status_code=400, detail=f"Request is already {req['status']}")

    now = datetime.now(timezone.utc).isoformat()
    notes = body.get("notes", "") if isinstance(body, dict) else ""
    reason = body.get("reason", notes) if isinstance(body, dict) else ""
    await db.verification_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "DENIED", "reviewed_at": now, "reviewed_by": user["id"], "admin_notes": notes, "denial_reason": reason}}
    )

    # In-App: Denial notification with reason
    denial_msg = "We couldn't verify your ID at this time."
    if reason:
        denial_msg += f" Reason: {reason}."
    denial_msg += " Please check your submission or reach out for help."

    from routes.notifications import create_notification
    await create_notification(
        req["user_id"], "VERIFICATION_DENIED",
        "Verification Update",
        denial_msg,
        {"request_id": request_id, "reason": reason}
    )

    # Email: Verification Update (async, non-blocking)
    target_user = await db.users.find_one({"id": req["user_id"]}, {"_id": 0})
    if target_user and target_user.get("email"):
        try:
            from templates.base import wrap_email
            reason_html = f'<p style="background:#FFF8E1;padding:12px;border-radius:8px;border-left:4px solid #FFB300;"><strong>Reason:</strong> {reason}</p>' if reason else ''
            html = wrap_email(f"""
                <h2 style="color:#D98C2F;font-family:serif;">Verification Update</h2>
                <p>Hi <strong>@{target_user.get('username', 'collector')}</strong>,</p>
                <p>We weren't able to verify your Golden Hive ID at this time.</p>
                {reason_html}
                <p>You can re-submit your verification from your profile settings. If you have any questions, reach out to our support team.</p>
                <p style="color:#8A6B4A;font-size:12px;">— The Honey Groove Team</p>
            """)
            asyncio.create_task(send_email(target_user["email"], "The Honey Groove: Verification Update", html))
        except Exception as e:
            logger.warning(f"Failed to send denial email: {e}")

    return {"message": "Verification denied."}
