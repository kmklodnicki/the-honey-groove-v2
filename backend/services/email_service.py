"""Centralized email sending service via Resend."""

import os
import asyncio
import logging

logger = logging.getLogger("email_service")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "The Honey Groove <hello@thehoneygroove.com>")


async def send_email(to: str, subject: str, html: str, reply_to: str = None):
    """Send an email via Resend. Non-blocking, fire-and-forget safe."""
    if not RESEND_API_KEY or not to:
        logger.warning(f"Email skipped (no key or recipient): {subject}")
        return False
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        params = {
            "from": SENDER_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if reply_to:
            params["reply_to"] = reply_to
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email failed to {to}: {subject} — {e}")
        return False


async def send_email_fire_and_forget(to: str, subject: str, html: str, reply_to: str = None):
    """Wrap send_email in a task so callers don't await it."""
    asyncio.create_task(send_email(to, subject, html, reply_to))
