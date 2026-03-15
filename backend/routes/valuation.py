from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from pathlib import Path
import asyncio
import io
import requests as http_requests

from database import db, require_auth, logger, create_notification, get_discogs_market_data

router = APIRouter()

CACHE_TTL_HOURS = 24
FONTS_DIR = Path(__file__).parent.parent / "fonts"


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
    # BLOCK 495: Calculate avg_value
    avg_value = round(total / total_records, 2) if total_records > 0 else 0
    return {
        "total_value": round(total, 2),
        "valued_count": valued,
        "total_count": total_records,
        "avg_value": avg_value,
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
        return {"total_value": 0, "valued_count": 0, "total_count": total_records, "avg_value": 0}
    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)
    total = sum(v["median_value"] for v in values if v.get("median_value"))
    total_records = await db.records.count_documents({"user_id": target["id"]})
    avg_value = round(total / total_records, 2) if total_records > 0 else 0
    return {
        "total_value": round(total, 2),
        "valued_count": len(values),
        "total_count": total_records,
        "avg_value": avg_value,
    }


@router.get("/valuation/wishlist")
async def get_wishlist_value(user: Dict = Depends(require_auth)):
    """Total estimated value of Actively Seeking (ISO) items only."""
    items = await db.iso_items.find(
        {"user_id": user["id"], "status": "OPEN", "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1}
    ).to_list(5000)
    discogs_ids = list({i["discogs_id"] for i in items if i.get("discogs_id")})
    total_count = await db.iso_items.count_documents({"user_id": user["id"], "status": "OPEN"})
    if not discogs_ids:
        return {"total_value": 0, "valued_count": 0, "total_count": total_count}

    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)

    total = sum(v["median_value"] for v in values if v.get("median_value"))
    return {
        "total_value": round(total, 2),
        "valued_count": len([v for v in values if v.get("median_value")]),
        "total_count": total_count,
    }


@router.get("/valuation/wishlist/{username}")
async def get_user_wishlist_value(username: str):
    """ISO Value for any user (Actively Seeking only, public)."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0, "id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    items = await db.iso_items.find(
        {"user_id": target["id"], "status": "OPEN", "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1}
    ).to_list(5000)
    discogs_ids = list({i["discogs_id"] for i in items if i.get("discogs_id")})
    total_count = await db.iso_items.count_documents({"user_id": target["id"], "status": "OPEN"})
    if not discogs_ids:
        return {"total_value": 0, "valued_count": 0, "total_count": total_count}
    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000)
    total = sum(v["median_value"] for v in values if v.get("median_value"))
    return {
        "total_value": round(total, 2),
        "valued_count": len([v for v in values if v.get("median_value")]),
        "total_count": total_count,
    }



# ===================== DREAM VALUE HELPERS =====================

async def _resolve_dream_item_value(discogs_id, user_manual_price=None):
    """3-tier value resolution: Discogs median -> Direct fetch -> Community valuation -> User manual price."""
    if discogs_id:
        cached = await db.collection_values.find_one({"release_id": discogs_id}, {"_id": 0, "median_value": 1})
        if cached and cached.get("median_value"):
            return cached["median_value"], "discogs"
        # BLOCK 428: Direct fetch from Discogs marketplace when cache misses
        try:
            data = get_discogs_market_data(discogs_id)
            if data:
                median = data.get("median_value") or data.get("low_value")
                if median and median > 0:
                    await db.collection_values.update_one(
                        {"release_id": discogs_id},
                        {"$set": {"release_id": discogs_id, "median_value": median, "low_value": data.get("low_value"), "source": "direct_fetch"}},
                        upsert=True
                    )
                    return median, "discogs"
        except Exception:
            pass
        community = await db.community_valuations.find_one({"release_id": discogs_id}, {"_id": 0, "average_value": 1})
        if community and community.get("average_value"):
            return community["average_value"], "community"
    if user_manual_price and user_manual_price > 0:
        return user_manual_price, "manual"
    return None, "pending"


async def _recalculate_dream_value(user_id: str):
    """Recalculate dream value for a user using 3-tier resolution.
    BLOCK 428: Forces direct Discogs market fetch for items missing cached values."""
    items = await db.iso_items.find(
        {"user_id": user_id, "status": "WISHLIST"},
        {"_id": 0, "discogs_id": 1, "manual_price": 1}
    ).to_list(5000)
    total_count = len(items)
    if total_count == 0:
        return {"total_value": 0, "valued_count": 0, "total_count": 0, "pending_count": 0}

    discogs_ids = list({i["discogs_id"] for i in items if i.get("discogs_id")})
    discogs_map = {}
    if discogs_ids:
        vals = await db.collection_values.find(
            {"release_id": {"$in": discogs_ids}}, {"_id": 0, "release_id": 1, "median_value": 1}
        ).to_list(5000)
        discogs_map = {v["release_id"]: v.get("median_value") for v in vals if v.get("median_value")}

    # BLOCK 428: Direct fetch for items missing from collection_values cache
    missing_from_cache = [did for did in discogs_ids if did not in discogs_map]
    if missing_from_cache:
        for did in missing_from_cache[:20]:  # Limit to avoid rate-limiting
            try:
                data = get_discogs_market_data(did)
                if data:
                    median = data.get("median_value") or data.get("low_value")
                    if median and median > 0:
                        discogs_map[did] = median
                        # Cache for future use
                        await db.collection_values.update_one(
                            {"release_id": did},
                            {"$set": {"release_id": did, "median_value": median, "low_value": data.get("low_value"), "source": "direct_fetch"}},
                            upsert=True
                        )
                        logger.info(f"Dream value: direct-fetched {did} → ${median}")
            except Exception as e:
                logger.warning(f"Dream value direct fetch failed for {did}: {e}")

    community_map = {}
    missing_ids = [did for did in discogs_ids if did not in discogs_map]
    if missing_ids:
        cvs = await db.community_valuations.find(
            {"release_id": {"$in": missing_ids}}, {"_id": 0, "release_id": 1, "average_value": 1}
        ).to_list(5000)
        community_map = {c["release_id"]: c.get("average_value") for c in cvs if c.get("average_value")}

    total = 0.0
    valued = 0
    for item in items:
        did = item.get("discogs_id")
        val = discogs_map.get(did) or community_map.get(did) or (item.get("manual_price") if item.get("manual_price") and item["manual_price"] > 0 else None)
        if val:
            total += val
            valued += 1

    return {
        "total_value": round(total, 2),
        "valued_count": valued,
        "total_count": total_count,
        "pending_count": total_count - valued,
    }


def _trimmed_mean(values: list, trim_pct: float = 0.10) -> float:
    """Calculate trimmed mean, discarding top/bottom trim_pct (10% default for anti-inflation)."""
    if not values:
        return 0
    if len(values) <= 2:
        return sum(values) / len(values)
    sorted_vals = sorted(values)
    trim_count = max(1, int(len(sorted_vals) * trim_pct))
    trimmed = sorted_vals[trim_count:-trim_count] if len(sorted_vals) > trim_count * 2 else sorted_vals
    return sum(trimmed) / len(trimmed) if trimmed else 0


# ===================== DREAM VALUE ENDPOINTS =====================

@router.get("/valuation/dreamlist")
async def get_dreamlist_value(user: Dict = Depends(require_auth)):
    """Total estimated value of Dream Wishlist items (3-tier resolution)."""
    return await _recalculate_dream_value(user["id"])


@router.get("/valuation/dreamlist/{username}")
async def get_user_dreamlist_value(username: str):
    """Dream Wishlist Value for any user (WISHLIST only, public)."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0, "id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    return await _recalculate_dream_value(target["id"])


# ===================== PENDING ITEMS & MANUAL VALUATION =====================

from pydantic import BaseModel as _BaseModel

class ManualValueInput(_BaseModel):
    value: float

@router.get("/valuation/pending-items")
async def get_pending_items(user: Dict = Depends(require_auth)):
    """Return dream list items with no resolved price, enriched with community averages."""
    items = await db.iso_items.find(
        {"user_id": user["id"], "status": "WISHLIST"}, {"_id": 0}
    ).to_list(5000)

    discogs_ids = [i["discogs_id"] for i in items if i.get("discogs_id")]
    discogs_map = {}
    community_map = {}
    if discogs_ids:
        vals = await db.collection_values.find(
            {"release_id": {"$in": discogs_ids}}, {"_id": 0, "release_id": 1, "median_value": 1}
        ).to_list(5000)
        discogs_map = {v["release_id"]: v.get("median_value") for v in vals if v.get("median_value")}
        missing = [d for d in discogs_ids if d not in discogs_map]
        if missing:
            cvs = await db.community_valuations.find(
                {"release_id": {"$in": missing}}, {"_id": 0}
            ).to_list(5000)
            community_map = {c["release_id"]: {"average_value": c.get("average_value"), "contribution_count": c.get("contribution_count", 0)} for c in cvs if c.get("average_value")}

    pending = []
    for item in items:
        did = item.get("discogs_id")
        has_discogs = did and did in discogs_map
        has_manual = item.get("manual_price") and item["manual_price"] > 0
        community_data = community_map.get(did)
        # Pending if no discogs value AND no manual price (community suggestions don't auto-resolve)
        if not has_discogs and not has_manual:
            entry = {
                "id": item["id"],
                "artist": item.get("artist", ""),
                "album": item.get("album", ""),
                "cover_url": item.get("cover_url"),
                "discogs_id": did,
                "manual_price": item.get("manual_price"),
            }
            if community_data:
                entry["hive_average"] = community_data["average_value"]
                entry["hive_count"] = community_data["contribution_count"]
            pending.append(entry)
    return pending


@router.put("/valuation/manual-value/{iso_id}")
async def set_manual_value(iso_id: str, body: ManualValueInput, user: Dict = Depends(require_auth)):
    """Set a manual price for a dream list item. Also contributes to community valuations."""
    if body.value <= 0:
        raise HTTPException(status_code=400, detail="Value must be positive")

    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]}, {"_id": 0})
    if not iso:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.iso_items.update_one(
        {"id": iso_id}, {"$set": {"manual_price": round(body.value, 2)}}
    )

    discogs_id = iso.get("discogs_id")
    if discogs_id:
        now = datetime.now(timezone.utc).isoformat()
        existing = await db.community_valuations.find_one({"release_id": discogs_id})
        if existing:
            contributions = existing.get("contributions", [])
            contributions = [c for c in contributions if c["user_id"] != user["id"]]
            contributions.append({"user_id": user["id"], "value": round(body.value, 2), "at": now})
            avg = _trimmed_mean([c["value"] for c in contributions])
            await db.community_valuations.update_one(
                {"release_id": discogs_id},
                {"$set": {
                    "contributions": contributions,
                    "average_value": round(avg, 2),
                    "contribution_count": len(contributions),
                    "updated_at": now,
                }}
            )
        else:
            await db.community_valuations.insert_one({
                "release_id": discogs_id,
                "contributions": [{"user_id": user["id"], "value": round(body.value, 2), "at": now}],
                "average_value": round(body.value, 2),
                "contribution_count": 1,
                "created_at": now,
                "updated_at": now,
            })

    result = await _recalculate_dream_value(user["id"])
    return {"message": "Value saved", "dream_value": result}


@router.post("/valuation/community-value/{discogs_id}")
async def submit_community_value(discogs_id: int, body: ManualValueInput, user: Dict = Depends(require_auth)):
    """Submit a community valuation for any record by discogs_id. Returns the new average."""
    if body.value <= 0:
        raise HTTPException(status_code=400, detail="Value must be positive")

    now = datetime.now(timezone.utc).isoformat()
    existing = await db.community_valuations.find_one({"release_id": discogs_id})
    if existing:
        contributions = existing.get("contributions", [])
        contributions = [c for c in contributions if c["user_id"] != user["id"]]
        contributions.append({"user_id": user["id"], "value": round(body.value, 2), "at": now})
        avg = _trimmed_mean([c["value"] for c in contributions])
        await db.community_valuations.update_one(
            {"release_id": discogs_id},
            {"$set": {
                "contributions": contributions,
                "average_value": round(avg, 2),
                "contribution_count": len(contributions),
                "updated_at": now,
            }}
        )
    else:
        avg = round(body.value, 2)
        await db.community_valuations.insert_one({
            "release_id": discogs_id,
            "contributions": [{"user_id": user["id"], "value": round(body.value, 2), "at": now}],
            "average_value": avg,
            "contribution_count": 1,
            "created_at": now,
            "updated_at": now,
        })

    return {"message": "Community value saved", "average_value": round(avg, 2)}


@router.get("/valuation/community-average/{discogs_id}")
async def get_community_average(discogs_id: int):
    """Get the community average value for a specific Discogs release."""
    doc = await db.community_valuations.find_one({"release_id": discogs_id}, {"_id": 0})
    if not doc or not doc.get("average_value"):
        return {"average_value": 0, "contribution_count": 0}
    return {
        "average_value": doc["average_value"],
        "contribution_count": doc.get("contribution_count", 0),
    }


# ===================== COLLECTION COMPLETIONIST WIZARD =====================

@router.get("/valuation/unvalued-queue")
async def get_unvalued_queue(user: Dict = Depends(require_auth)):
    """Returns collection records that have no market or community value — the wizard queue."""
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}},
        {"_id": 0, "id": 1, "discogs_id": 1, "title": 1, "artist": 1, "cover_url": 1, "year": 1}
    ).to_list(5000)
    if not records:
        return []

    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})

    # Fetch existing collection_values
    col_vals = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0, "release_id": 1, "median_value": 1}
    ).to_list(5000)
    valued_set = {v["release_id"] for v in col_vals if v.get("median_value") and v["median_value"] > 0}

    # Fetch community valuations
    community = await db.community_valuations.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0, "release_id": 1, "average_value": 1, "contribution_count": 1}
    ).to_list(5000)
    community_map = {c["release_id"]: c for c in community}

    queue = []
    for r in records:
        did = r.get("discogs_id")
        if not did or did in valued_set:
            continue
        # Check if community value exists (still show but include benchmark)
        cv = community_map.get(did)
        entry = {
            "id": r["id"],
            "discogs_id": did,
            "title": r.get("title", "Unknown"),
            "artist": r.get("artist", "Unknown"),
            "cover_url": r.get("cover_url"),
            "year": r.get("year"),
        }
        if cv and cv.get("average_value") and cv["average_value"] > 0:
            entry["hive_average"] = cv["average_value"]
            entry["hive_count"] = cv.get("contribution_count", 0)
        queue.append(entry)
    return queue


@router.post("/valuation/wizard-save/{discogs_id}")
async def wizard_save_value(discogs_id: int, body: ManualValueInput, user: Dict = Depends(require_auth)):
    """Save a value from the wizard: updates community valuations AND collection_values cache."""
    if body.value <= 0:
        raise HTTPException(status_code=400, detail="Value must be positive")

    now = datetime.now(timezone.utc).isoformat()

    # 1) Update community_valuations (trimmed mean)
    existing = await db.community_valuations.find_one({"release_id": discogs_id})
    if existing:
        contributions = existing.get("contributions", [])
        contributions = [c for c in contributions if c["user_id"] != user["id"]]
        contributions.append({"user_id": user["id"], "value": round(body.value, 2), "at": now})
        avg = _trimmed_mean([c["value"] for c in contributions])
        await db.community_valuations.update_one(
            {"release_id": discogs_id},
            {"$set": {
                "contributions": contributions,
                "average_value": round(avg, 2),
                "contribution_count": len(contributions),
                "updated_at": now,
            }}
        )
    else:
        avg = round(body.value, 2)
        await db.community_valuations.insert_one({
            "release_id": discogs_id,
            "contributions": [{"user_id": user["id"], "value": round(body.value, 2), "at": now}],
            "average_value": avg,
            "contribution_count": 1,
            "created_at": now,
            "updated_at": now,
        })

    # 2) Update collection_values so the record counts as "valued" in the summary
    await db.collection_values.update_one(
        {"release_id": discogs_id},
        {"$set": {
            "release_id": discogs_id,
            "median_value": round(avg, 2),
            "last_updated": now,
            "source": "community",
        }},
        upsert=True,
    )

    return {"message": "Value saved", "average_value": round(avg, 2)}


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


@router.get("/valuation/record-value/{discogs_id}")
async def get_single_record_value(discogs_id: int, user: Dict = Depends(require_auth)):
    """Return the cached median value for a single Discogs release."""
    val = await db.collection_values.find_one({"release_id": discogs_id}, {"_id": 0})
    if not val:
        return {"median_value": 0}
    return {"median_value": val.get("median_value", 0)}


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


@router.get("/valuation/record-values/{username}")
async def get_user_record_values(username: str):
    """Return a map of record_id -> median_value for any user's collection (public, global price cache)."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    records = await db.records.find(
        {"user_id": target["id"], "discogs_id": {"$ne": None}},
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


# ===================== TASTE REPORT IMAGE =====================

def _download_cover(url: str, size: int = 300) -> "Image.Image | None":
    """Download a cover image and resize it."""
    from PIL import Image
    try:
        resp = http_requests.get(url, timeout=8, headers={"User-Agent": "HoneyGrooveApp/1.0"})
        if resp.status_code == 200 and len(resp.content) > 100:
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            img = img.resize((size, size), Image.LANCZOS)
            return img
    except Exception as e:
        logger.error(f"Cover download failed: {e}")
    return None


def _round_corners(img: "Image.Image", radius: int) -> "Image.Image":
    from PIL import Image, ImageDraw
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    result = img.copy()
    result.putalpha(mask)
    return result


def _generate_taste_report_png(user_data: dict, report: dict, gems: list) -> bytes:
    """Generate a 1080x1920 Instagram Story PNG."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1080, 1920
    HONEY = (244, 185, 66)
    HONEY_SOFT = (249, 215, 118)
    CREAM = (255, 246, 230)
    BLACK = (31, 31, 31)
    WHITE = (255, 255, 255)
    DARK_BG = (24, 24, 24)
    SUBTLE = (100, 100, 100)

    img = Image.new("RGBA", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        heading_lg = ImageFont.truetype(str(FONTS_DIR / "DMSerifDisplay-Regular.ttf"), 72)
        heading_md = ImageFont.truetype(str(FONTS_DIR / "DMSerifDisplay-Regular.ttf"), 52)
        heading_sm = ImageFont.truetype(str(FONTS_DIR / "DMSerifDisplay-Regular.ttf"), 40)
        body_lg = ImageFont.truetype(str(FONTS_DIR / "Inter.ttf"), 36)
        body_md = ImageFont.truetype(str(FONTS_DIR / "Inter.ttf"), 28)
        body_sm = ImageFont.truetype(str(FONTS_DIR / "Inter.ttf"), 22)
        body_xs = ImageFont.truetype(str(FONTS_DIR / "Inter.ttf"), 18)
    except Exception:
        heading_lg = ImageFont.load_default()
        heading_md = heading_lg
        heading_sm = heading_lg
        body_lg = heading_lg
        body_md = heading_lg
        body_sm = heading_lg
        body_xs = heading_lg

    # --- Top accent bar ---
    draw.rectangle([(0, 0), (W, 8)], fill=HONEY)

    # --- Header ---
    y = 80
    draw.text((80, y), "HoneyGroove", fill=HONEY, font=heading_md)
    y += 70
    draw.text((80, y), "taste report", fill=SUBTLE, font=body_md)
    y += 50

    # --- Username + date ---
    username = user_data.get("username", "collector")
    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    draw.text((80, y), f"@{username}", fill=WHITE, font=body_lg)
    draw.text((80, y + 50), now_str, fill=SUBTLE, font=body_sm)
    y += 130

    # --- Divider line ---
    draw.line([(80, y), (W - 80, y)], fill=(50, 50, 50), width=2)
    y += 50

    # --- Total Value (hero stat) ---
    total_val = report.get("total_value", 0)
    draw.text((80, y), "estimated collection value", fill=SUBTLE, font=body_sm)
    y += 40
    val_str = f"${total_val:,.0f}"
    draw.text((80, y), val_str, fill=HONEY, font=heading_lg)
    y += 100

    # Sub-stats row
    valued = report.get("valued_count", 0)
    total = report.get("total_count", 0)
    over_100 = report.get("over_100_count", 0)

    col_w = (W - 160) // 3
    stats = [
        (str(total), "records"),
        (str(valued), "valued"),
        (str(over_100), "over $100"),
    ]
    for i, (val, label) in enumerate(stats):
        sx = 80 + i * col_w
        draw.text((sx, y), val, fill=WHITE, font=heading_sm)
        draw.text((sx, y + 55), label, fill=SUBTLE, font=body_xs)
    y += 120

    # --- Divider ---
    draw.line([(80, y), (W - 80, y)], fill=(50, 50, 50), width=2)
    y += 50

    # --- Most Valuable Record ---
    mv = report.get("most_valuable")
    if mv:
        draw.text((80, y), "most valuable record", fill=SUBTLE, font=body_sm)
        y += 45
        # Try to load cover art
        cover = None
        if mv.get("cover_url"):
            cover = _download_cover(mv["cover_url"], 200)
        if cover:
            cover_rounded = _round_corners(cover, 20)
            img.paste(cover_rounded, (80, y), cover_rounded)
            tx = 310
        else:
            tx = 80
        draw.text((tx, y + 20), mv.get("title", "Unknown")[:30], fill=WHITE, font=heading_sm)
        draw.text((tx, y + 75), mv.get("artist", "")[:35], fill=SUBTLE, font=body_md)
        mv_val = mv.get("median_value", 0)
        draw.text((tx, y + 120), f"${mv_val:,.2f}", fill=HONEY, font=heading_sm)
        y += 240
    else:
        y += 20

    # --- Divider ---
    draw.line([(80, y), (W - 80, y)], fill=(50, 50, 50), width=2)
    y += 50

    # --- Hidden Gems ---
    if gems:
        draw.text((80, y), "hidden gems", fill=SUBTLE, font=body_sm)
        y += 50
        for i, gem in enumerate(gems[:3]):
            # Number badge
            badge_x, badge_y = 80, y + 10
            draw.rounded_rectangle(
                [(badge_x, badge_y), (badge_x + 44, badge_y + 44)],
                radius=22, fill=HONEY
            )
            draw.text((badge_x + 14, badge_y + 6), str(i + 1), fill=BLACK, font=body_md)

            # Cover art
            cover = None
            if gem.get("cover_url"):
                cover = _download_cover(gem["cover_url"], 100)
            if cover:
                cover_r = _round_corners(cover, 12)
                img.paste(cover_r, (140, y), cover_r)
                tx = 260
            else:
                tx = 140

            # Text
            title = gem.get("title", "")[:28]
            artist = gem.get("artist", "")[:30]
            draw.text((tx, y + 10), title, fill=WHITE, font=body_md)
            draw.text((tx, y + 48), artist, fill=SUBTLE, font=body_sm)
            gem_val = gem.get("median_value", 0)
            draw.text((W - 250, y + 20), f"${gem_val:,.2f}", fill=HONEY_SOFT, font=body_lg)
            y += 120

    # --- Footer ---
    y = H - 160
    draw.line([(80, y), (W - 80, y)], fill=(50, 50, 50), width=2)
    y += 30
    draw.text((80, y), "the vinyl social club", fill=SUBTLE, font=body_sm)
    y += 35
    draw.text((80, y), "thehoneygroove.com", fill=HONEY, font=body_md)

    # --- Bottom accent bar ---
    draw.rectangle([(0, H - 8), (W, H)], fill=HONEY)

    # Export to PNG
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@router.get("/valuation/taste-report/image")
async def get_taste_report_image(user: Dict = Depends(require_auth)):
    """Generate and return a 1080x1920 Taste Report PNG."""
    # Gather data
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
    enriched = []

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
            enriched.append({
                "title": r.get("title"), "artist": r.get("artist"),
                "cover_url": r.get("cover_url"), "median_value": mv,
            })

    enriched.sort(key=lambda x: x["median_value"], reverse=True)
    total_records = await db.records.count_documents({"user_id": user["id"]})

    report = {
        "total_value": round(total_value, 2),
        "valued_count": len([v for v in values if v.get("median_value")]),
        "total_count": total_records,
        "over_100_count": over_100_count,
        "most_valuable": most_valuable,
    }

    png_bytes = _generate_taste_report_png(user, report, enriched[:3])
    return Response(content=png_bytes, media_type="image/png")


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


# ===================== PRIORITY RE-LINK (BLOCK 484) =====================

@router.post("/valuation/priority-relink")
async def priority_relink(user: Dict = Depends(require_auth)):
    """BLOCK 484: After OAuth re-auth, immediately fetch prices for the first 50 records.
    Skips records that already have fresh cached values."""
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1}
    ).sort("created_at", -1).to_list(50)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    if not discogs_ids:
        return {"message": "No records to relink", "fetched": 0, "total": 0}

    # Check which already have fresh values
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)).isoformat()
    fresh = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}, "last_updated": {"$gte": cutoff}},
        {"_id": 0, "release_id": 1}
    ).to_list(5000)
    fresh_ids = {d["release_id"] for d in fresh}
    stale_ids = [did for did in discogs_ids if did not in fresh_ids]

    if not stale_ids:
        return {"message": "All top 50 values are fresh", "fetched": 0, "total": len(discogs_ids)}

    # Fire background task for stale records
    asyncio.create_task(_background_refresh(user["id"], stale_ids))
    logger.info(f"Priority relink for {user['id']}: {len(stale_ids)} stale out of {len(discogs_ids)} records")
    return {"message": f"Re-linking {len(stale_ids)} records", "fetched": len(stale_ids), "total": len(discogs_ids)}


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



# ===================== PULSE: 90-DAY HOT RANGE =====================

@router.get("/valuation/pulse/{discogs_id}")
async def get_pulse(discogs_id: int, user: Dict = Depends(require_auth)):
    """
    Return the 90-day Pulse data for a Discogs release.
    Uses Discogs price suggestions as a proxy for recent sold comps.
    Returns hot_range (median +/- 15%) only if confidence >= 5 comps.
    """
    # Check cache first (reuse collection_values with pulse data)
    cached = await db.pulse_data.find_one({"release_id": discogs_id}, {"_id": 0})
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)).isoformat()
    if cached and cached.get("last_updated", "") >= cutoff:
        return cached

    # Fetch from Discogs
    from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_API_BASE
    import requests as _req
    headers_d = {"User-Agent": DISCOGS_USER_AGENT}
    params_d = {}
    if DISCOGS_TOKEN:
        params_d["token"] = DISCOGS_TOKEN

    pulse_doc = {
        "release_id": discogs_id,
        "median": None,
        "hot_low": None,
        "hot_high": None,
        "num_sold": 0,
        "confident": False,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    try:
        # Get price suggestions (based on recent sold data)
        resp = _req.get(
            f"{DISCOGS_API_BASE}/marketplace/price_suggestions/{discogs_id}",
            params=params_d, headers=headers_d, timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            # Count how many condition tiers have data (proxy for sold comps confidence)
            conditions_with_data = sum(1 for v in data.values() if isinstance(v, dict) and v.get("value"))
            vgp = data.get("Very Good Plus (VG+)", {})
            median_val = vgp.get("value")
            if median_val:
                median_val = round(float(median_val), 2)
                pulse_doc["median"] = median_val
                pulse_doc["hot_low"] = round(median_val * 0.85, 2)
                pulse_doc["hot_high"] = round(median_val * 1.15, 2)
                # Discogs price_suggestions uses community data;
                # conditions_with_data >= 3 typically means good confidence
                # We also check the release stats for num_for_sale
                resp2 = _req.get(
                    f"{DISCOGS_API_BASE}/releases/{discogs_id}",
                    params=params_d, headers=headers_d, timeout=10
                )
                num_sold = 0
                if resp2.status_code == 200:
                    r2data = resp2.json()
                    community = r2data.get("community", {})
                    num_sold = community.get("have", 0)
                pulse_doc["num_sold"] = num_sold
                pulse_doc["confident"] = conditions_with_data >= 3 and num_sold >= 5
    except Exception as e:
        logger.error(f"Pulse fetch error for {discogs_id}: {e}")

    await db.pulse_data.update_one(
        {"release_id": discogs_id}, {"$set": pulse_doc}, upsert=True
    )
    return pulse_doc


# ===================== BLOCK 476: VALUE RECOVERY ENGINE =====================

@router.post("/valuation/recovery/start")
async def start_value_recovery(user: Dict = Depends(require_auth)):
    """Trigger the Value Recovery Engine for the current user's collection.
    Uses OAuth tokens when available for higher rate limits."""
    from services.value_recovery import run_value_recovery, recovery_progress

    # Check if already running
    progress = recovery_progress.get(user["id"])
    if progress and progress.get("status") == "in_progress":
        return progress

    # Fire background task
    asyncio.create_task(run_value_recovery(user["id"]))
    return {"status": "started", "message": "Value Recovery Engine started"}


@router.get("/valuation/recovery/status")
async def get_value_recovery_status(user: Dict = Depends(require_auth)):
    """Get the current or last Value Recovery status."""
    from services.value_recovery import get_recovery_status
    return await get_recovery_status(user["id"])
