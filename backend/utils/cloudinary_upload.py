"""Cloudinary upload utility. Streams image buffers directly to Cloudinary.
Falls back to Emergent object storage when Cloudinary is not configured."""
import os
import io
import uuid
import logging
import cloudinary
import cloudinary.uploader

logger = logging.getLogger("cloudinary_upload")

# Read credentials from environment
CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME") or os.environ.get("CLOUDINARY_NAME", "")
API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

_configured = False

if CLOUD_NAME and API_KEY and API_SECRET:
    cloudinary.config(
        cloud_name=CLOUD_NAME,
        api_key=API_KEY,
        api_secret=API_SECRET,
        secure=True,
    )
    _configured = True
    logger.info(f"Cloudinary configured: cloud={CLOUD_NAME[:6]}...")
else:
    logger.warning("Cloudinary credentials missing — uploads will use fallback storage")


def is_cloudinary_configured() -> bool:
    return _configured


def upload_image_buffer(data: bytes, folder: str = "uploads", public_id: str = None) -> dict:
    """Upload an image buffer to Cloudinary.

    Returns dict with 'secure_url' and 'public_id'.
    Raises Exception if Cloudinary is not configured.
    """
    if not _configured:
        raise RuntimeError("Cloudinary not configured")

    pid = public_id or str(uuid.uuid4())
    result = cloudinary.uploader.upload(
        io.BytesIO(data),
        folder=folder,
        public_id=pid,
        resource_type="image",
        overwrite=True,
        invalidate=True,
    )
    return {
        "secure_url": result["secure_url"],
        "public_id": result["public_id"],
        "url": result["secure_url"],
    }


def delete_image(public_id: str) -> bool:
    """Delete an image from Cloudinary by public_id."""
    if not _configured:
        return False
    try:
        result = cloudinary.uploader.destroy(public_id, invalidate=True)
        return result.get("result") == "ok"
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {e}")
        return False
