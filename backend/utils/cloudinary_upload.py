"""Cloudinary upload utility. Streams image buffers directly to Cloudinary."""
import os
import io
import uuid
import re
import logging
import cloudinary
import cloudinary.uploader

logger = logging.getLogger("cloudinary_upload")

_configured = False

def _configure_cloudinary():
    """Parse and configure Cloudinary credentials from environment variables."""
    global _configured

    # 1. Try CLOUDINARY_URL first: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
    cloud_url = os.environ.get("CLOUDINARY_URL", "")
    # Handle accidental "CLOUDINARY_URL=cloudinary://..." prefix
    if cloud_url.startswith("CLOUDINARY_URL="):
        cloud_url = cloud_url.replace("CLOUDINARY_URL=", "", 1)
    cloud_url = cloud_url.strip()

    match = re.match(r'cloudinary://(\d+):([^@]+)@(.+)', cloud_url)
    if match:
        api_key = match.group(1)
        api_secret = match.group(2)
        cloud_name = match.group(3)
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        _configured = True
        logger.info(f"Cloudinary configured from CLOUDINARY_URL: cloud={cloud_name}, key={api_key[:4]}..., secret={api_secret[:4]}...{api_secret[-4:]}")
        return

    # 2. Try individual env vars
    CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME") or os.environ.get("CLOUDINARY_NAME", "")
    API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
    API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")
    if CLOUD_NAME and API_KEY and API_SECRET:
        cloudinary.config(
            cloud_name=CLOUD_NAME,
            api_key=API_KEY,
            api_secret=API_SECRET,
            secure=True,
        )
        _configured = True
        logger.info(f"Cloudinary configured from individual env vars: cloud={CLOUD_NAME}, key={API_KEY[:4]}...")
        return

    logger.warning("Cloudinary credentials missing — checked CLOUDINARY_URL, CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET")

_configure_cloudinary()


def is_cloudinary_configured() -> bool:
    return _configured


def upload_image_buffer(data: bytes, folder: str = "uploads", public_id: str = None) -> dict:
    if not _configured:
        raise RuntimeError("Cloudinary not configured")
    pid = public_id or str(uuid.uuid4())
    try:
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
    except Exception as e:
        # Log the actual config being used for debugging signature errors
        cfg = cloudinary.config()
        logger.error(f"Cloudinary upload failed: {e}")
        logger.error(f"  cloud_name={cfg.cloud_name}, api_key={cfg.api_key[:4] if cfg.api_key else 'NONE'}..., api_secret={'set' if cfg.api_secret else 'NONE'}")
        raise


def delete_image(public_id: str) -> bool:
    if not _configured:
        return False
    try:
        result = cloudinary.uploader.destroy(public_id, invalidate=True)
        return result.get("result") == "ok"
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {e}")
        return False
