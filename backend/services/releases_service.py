"""CC0 release data persistence. Extracts only freely-usable (CC0) fields from
Discogs API responses and upserts them into the `releases` collection.
Discogs images are classified as Restricted Data and are intentionally excluded."""
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from database import db, get_discogs_release, logger


async def upsert_release_cc0(discogs_id: int, discogs_data: dict) -> dict:
    """Extract only CC0 fields from Discogs data and upsert into releases collection.

    Does NOT touch spotifyMatchStatus if it is already set on an existing document.
    Does NOT store cover_url / thumb_url (Restricted Data under Discogs TOS).
    """
    now = datetime.now(timezone.utc).isoformat()

    artists = discogs_data.get("artist", "")
    if isinstance(artists, str):
        artists = [a.strip() for a in artists.split(",") if a.strip()] if artists else []

    # Collect all barcodes
    barcodes = []
    raw_barcode = discogs_data.get("barcode")
    if raw_barcode:
        if isinstance(raw_barcode, str):
            barcodes = [raw_barcode]
        elif isinstance(raw_barcode, list):
            barcodes = raw_barcode

    cc0_fields = {
        "discogsReleaseId": discogs_id,
        "title": discogs_data.get("title"),
        "artists": artists,
        "labels": discogs_data.get("label", []) if isinstance(discogs_data.get("label"), list) else (
            [discogs_data["label"]] if discogs_data.get("label") else []
        ),
        "formats": discogs_data.get("format", []) if isinstance(discogs_data.get("format"), list) else (
            [discogs_data["format"]] if discogs_data.get("format") else []
        ),
        "tracklist": discogs_data.get("tracklist", []),
        "year": discogs_data.get("year"),
        "country": discogs_data.get("country"),
        "genres": discogs_data.get("genre", []) if isinstance(discogs_data.get("genre"), list) else (
            [discogs_data["genre"]] if discogs_data.get("genre") else []
        ),
        "styles": discogs_data.get("style", []) if isinstance(discogs_data.get("style"), list) else [],
        "barcode": barcodes,
        "notes": discogs_data.get("notes"),
        "discogsUrl": f"https://www.discogs.com/release/{discogs_id}",
        "dataFetchedAt": now,
    }

    # Only set spotifyMatchStatus to "pending" on new inserts
    existing = await db.releases.find_one({"discogsReleaseId": discogs_id}, {"_id": 0, "spotifyMatchStatus": 1})
    if not existing or not existing.get("spotifyMatchStatus"):
        cc0_fields["spotifyMatchStatus"] = "pending"

    await db.releases.update_one(
        {"discogsReleaseId": discogs_id},
        {"$set": cc0_fields},
        upsert=True,
    )

    doc = await db.releases.find_one({"discogsReleaseId": discogs_id}, {"_id": 0})
    return doc or cc0_fields


async def get_or_fetch_release(discogs_id: int) -> Optional[dict]:
    """Return release from DB; fetch from Discogs API and persist if missing or stale (>30 days)."""
    if not discogs_id:
        return None

    doc = await db.releases.find_one({"discogsReleaseId": discogs_id}, {"_id": 0})

    stale = False
    if doc and doc.get("dataFetchedAt"):
        try:
            fetched_at = datetime.fromisoformat(doc["dataFetchedAt"].replace("Z", "+00:00"))
            stale = (datetime.now(timezone.utc) - fetched_at) > timedelta(days=30)
        except Exception:
            stale = True

    if not doc or stale:
        try:
            import asyncio
            discogs_data = await asyncio.get_event_loop().run_in_executor(
                None, get_discogs_release, discogs_id
            )
            if discogs_data:
                doc = await upsert_release_cc0(discogs_id, discogs_data)
        except Exception as e:
            logger.warning(f"get_or_fetch_release failed for {discogs_id}: {e}")

    return doc
