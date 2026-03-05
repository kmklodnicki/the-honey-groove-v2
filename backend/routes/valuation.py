from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
import asyncio

from database import db, require_auth, logger, create_notification, get_discogs_market_data

router = APIRouter()

CACHE_TTL_HOURS = 24


async def _get_cached_value(discogs_id: int) -> Optional[Dict]:
    """Return cached value if fresh, else None."""
    doc = await db.collection_values.find_one({"release_id": discogs_id}, {"_id": 0})
    if not doc:
        return None
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)).isoformat()
    if doc.get("last_updated", "") >= cutoff:
        return doc
    return None


async def _fetch_and_cache(discogs_id: int) -> Optional[Dict]:
    """Fetch from Discogs, store in cache, return doc."""
    data = get_discogs_market_data(discogs_id)
    if not data:
        return None
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "release_id": discogs_id,
        "median_value": data["median_value"],
        "low_value": data["low_value"],
        "high_value": data["high_value"],
        "last_updated": now,
    }
    await db.collection_values.update_one(
        {"release_id": discogs_id}, {"$set": doc}, upsert=True
    )
    return doc


async def _ensure_cached(discogs_id: int) -> Optional[Dict]:
    """Get from cache or fetch live (never on page load — called from background)."""
    cached = await _get_cached_value(discogs_id)
    if cached:
        return cached
    return await _fetch_and_cache(discogs_id)


# ===================== COLLECTION VALUE =====================

@router.get("/valuation/collection")
async def get_collection_value(user: Dict = Depends(require_auth)):
    """Total estimated collection value from cached Discogs data."""
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1}
    ).to_list(5000)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    if not discogs_ids:
        return {"total_value": 0, "valued_count": 0, "total_count": len(records)}

    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)
    val_map = {v["release_id"]: v for v in values}

    total = 0.0
    valued = 0
    for did in discogs_ids:
        v = val_map.get(did)
        if v and v.get("median_value"):
            total += v["median_value"]
            valued += 1

    total_records = await db.records.count_documents({"user_id": user["id"]})
    return {
        "total_value": round(total, 2),
        "valued_count": valued,
        "total_count": total_records,
    }


@router.get("/valuation/collection/{username}")
async def get_user_collection_value(username: str):
    """Public collection value for any user."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    records = await db.records.find(
        {"user_id": target["id"], "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1}
    ).to_list(5000)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    if not discogs_ids:
        total_records = await db.records.count_documents({"user_id": target["id"]})
        return {"total_value": 0, "valued_count": 0, "total_count": total_records}
    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)
    total = sum(v["median_value"] for v in values if v.get("median_value"))
    total_records = await db.records.count_documents({"user_id": target["id"]})
    return {
        "total_value": round(total, 2),
        "valued_count": len(values),
        "total_count": total_records,
    }


# ===================== HIDDEN GEMS =====================

@router.get("/valuation/hidden-gems")
async def get_hidden_gems(user: Dict = Depends(require_auth), limit: int = 3):
    """Top N most valuable records in the user's collection."""
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}}, {"_id": 0}
    ).to_list(5000)
    if not records:
        return []
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)
    val_map = {v["release_id"]: v for v in values}

    enriched = []
    for r in records:
        v = val_map.get(r.get("discogs_id"))
        if v and v.get("median_value"):
            enriched.append({
                "id": r["id"],
                "title": r.get("title"),
                "artist": r.get("artist"),
                "cover_url": r.get("cover_url"),
                "discogs_id": r.get("discogs_id"),
                "year": r.get("year"),
                "median_value": v["median_value"],
                "low_value": v.get("low_value"),
                "high_value": v.get("high_value"),
            })
    enriched.sort(key=lambda x: x["median_value"], reverse=True)
    return enriched[:limit]


@router.get("/valuation/record-values")
async def get_record_values(user: Dict = Depends(require_auth)):
    """Return a map of record_id -> median_value for the user's collection."""
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}},
        {"_id": 0, "id": 1, "discogs_id": 1}
    ).to_list(5000)
    if not records:
        return {}
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)
    val_map = {v["release_id"]: v.get("median_value", 0) for v in values}
    result = {}
    for r in records:
        v = val_map.get(r.get("discogs_id"))
        if v:
            result[r["id"]] = v
    return result


@router.get("/valuation/hidden-gems/{username}")
async def get_user_hidden_gems(username: str, limit: int = 3):
    """Public hidden gems for any user."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    records = await db.records.find(
        {"user_id": target["id"], "discogs_id": {"$ne": None}}, {"_id": 0}
    ).to_list(5000)
    if not records:
        return []
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)
    val_map = {v["release_id"]: v for v in values}
    enriched = []
    for r in records:
        v = val_map.get(r.get("discogs_id"))
        if v and v.get("median_value"):
            enriched.append({
                "id": r["id"], "title": r.get("title"), "artist": r.get("artist"),
                "cover_url": r.get("cover_url"), "discogs_id": r.get("discogs_id"),
                "year": r.get("year"), "median_value": v["median_value"],
                "low_value": v.get("low_value"), "high_value": v.get("high_value"),
            })
    enriched.sort(key=lambda x: x["median_value"], reverse=True)
    return enriched[:limit]


# ===================== TASTE REPORT =====================

@router.get("/valuation/taste-report")
async def get_taste_report(user: Dict = Depends(require_auth)):
    """Value summary: total value, most valuable record, count over $100."""
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}}, {"_id": 0}
    ).to_list(5000)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)
    val_map = {v["release_id"]: v for v in values}

    total_value = 0.0
    over_100_count = 0
    most_valuable = None
    most_valuable_val = 0

    for r in records:
        v = val_map.get(r.get("discogs_id"))
        if v and v.get("median_value"):
            mv = v["median_value"]
            total_value += mv
            if mv > 100:
                over_100_count += 1
            if mv > most_valuable_val:
                most_valuable_val = mv
                most_valuable = {
                    "title": r.get("title"), "artist": r.get("artist"),
                    "cover_url": r.get("cover_url"), "median_value": mv,
                }

    total_records = await db.records.count_documents({"user_id": user["id"]})
    return {
        "total_value": round(total_value, 2),
        "valued_count": len([v for v in values if v.get("median_value")]),
        "total_count": total_records,
        "over_100_count": over_100_count,
        "most_valuable": most_valuable,
    }


# ===================== PRICING ASSIST =====================

@router.get("/valuation/pricing-assist/{discogs_id}")
async def pricing_assist(discogs_id: int, user: Dict = Depends(require_auth)):
    """Return cached price range for a Discogs release. Fetches if not cached."""
    cached = await _get_cached_value(discogs_id)
    if cached:
        return {
            "low": cached.get("low_value"),
            "high": cached.get("high_value"),
            "median": cached.get("median_value"),
            "stale": False,
        }
    # Fetch live for single release (user-triggered, OK for rate limits)
    doc = await _fetch_and_cache(discogs_id)
    if doc:
        return {
            "low": doc.get("low_value"),
            "high": doc.get("high_value"),
            "median": doc.get("median_value"),
            "stale": False,
        }
    return {"low": None, "high": None, "median": None, "stale": True}


# ===================== WANTLIST PRICE ALERTS =====================

@router.put("/valuation/wantlist/{iso_id}/price-alert")
async def set_price_alert(iso_id: str, body: dict, user: Dict = Depends(require_auth)):
    """Set a target price alert on a wantlist entry."""
    target_price = body.get("target_price")
    if target_price is not None:
        target_price = float(target_price)
    result = await db.iso_items.update_one(
        {"id": iso_id, "user_id": user["id"]},
        {"$set": {"price_alert": target_price}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Wantlist item not found")
    return {"message": "Price alert set", "target_price": target_price}


# ===================== BACKGROUND REFRESH =====================

@router.post("/valuation/refresh")
async def trigger_refresh(user: Dict = Depends(require_auth)):
    """Trigger a background refresh of Discogs values for the user's collection.
    Respects 24-hour cache TTL and 60 req/min rate limit."""
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1}
    ).to_list(5000)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    if not discogs_ids:
        return {"message": "No records with Discogs IDs", "queued": 0}

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)).isoformat()
    fresh = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}, "last_updated": {"$gte": cutoff}},
        {"_id": 0, "release_id": 1}
    ).to_list(5000)
    fresh_ids = {d["release_id"] for d in fresh}
    stale_ids = [did for did in discogs_ids if did not in fresh_ids]

    if not stale_ids:
        return {"message": "All values up to date", "queued": 0}

    asyncio.create_task(_background_refresh(user["id"], stale_ids))
    return {"message": f"Refreshing {len(stale_ids)} records in background", "queued": len(stale_ids)}


async def _background_refresh(user_id: str, discogs_ids: list):
    """Fetch market data for a list of release IDs, respecting rate limits."""
    fetched = 0
    for did in discogs_ids:
        try:
            await _fetch_and_cache(did)
            fetched += 1
        except Exception as e:
            logger.error(f"Refresh failed for {did}: {e}")
        # 60 req/min = 1 per second
        await asyncio.sleep(1.1)

    # After refresh, check wantlist price alerts
    await _check_price_alerts(user_id)
    logger.info(f"Background refresh for {user_id}: {fetched}/{len(discogs_ids)} fetched")


async def _check_price_alerts(user_id: str):
    """Check if any wantlist items have prices at or below the user's alert target."""
    isos = await db.iso_items.find(
        {"user_id": user_id, "status": "OPEN", "price_alert": {"$ne": None}},
        {"_id": 0}
    ).to_list(500)
    for iso in isos:
        target = iso.get("price_alert")
        did = iso.get("discogs_id")
        if not target or not did:
            continue
        cached = await db.collection_values.find_one({"release_id": did}, {"_id": 0})
        if not cached or not cached.get("low_value"):
            continue
        if cached["low_value"] <= target:
            # Check we haven't already notified recently
            recent = await db.notifications.find_one({
                "user_id": user_id,
                "type": "PRICE_ALERT",
                "data.iso_id": iso["id"],
                "created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}
            })
            if not recent:
                await create_notification(
                    user_id, "PRICE_ALERT",
                    "Price alert",
                    f"{iso['artist']} — {iso['album']} is available around ${cached['low_value']:.0f} on Discogs (your alert: ${target:.0f})",
                    {"iso_id": iso["id"], "discogs_id": did, "low_value": cached["low_value"]}
                )
