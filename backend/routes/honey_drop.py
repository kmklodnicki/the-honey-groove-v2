"""Honey Drop — daily featured record endpoint."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta

from database import db, require_auth, get_current_user, logger

router = APIRouter()


@router.get("/honey-drop/today")
async def get_honey_drop_today(current_user: Optional[Dict] = Depends(get_current_user)):
    """Return today's featured record. Public."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    drop = await db.honey_drops.find_one({"date": today}, {"_id": 0})

    if not drop:
        # Auto-select: top trending record not featured in last 7 days
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_drops = await db.honey_drops.find(
            {"date": {"$gte": seven_days_ago}},
            {"_id": 0, "discogs_id": 1}
        ).to_list(7)
        recent_discogs_ids = [d["discogs_id"] for d in recent_drops if d.get("discogs_id")]

        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        pipeline = [
            {"$match": {"created_at": {"$gte": week_ago}}},
            {"$lookup": {
                "from": "records",
                "localField": "record_id",
                "foreignField": "id",
                "as": "record"
            }},
            {"$unwind": "$record"},
            {"$group": {
                "_id": "$record.discogs_id",
                "spin_count": {"$sum": 1},
                "record": {"$first": "$record"},
            }},
            {"$match": {"_id": {"$nin": recent_discogs_ids, "$ne": None}}},
            {"$sort": {"spin_count": -1}},
            {"$limit": 1},
        ]
        trending = await db.spins.aggregate(pipeline).to_list(1)
        if not trending:
            return None

        featured = trending[0]
        record = {k: v for k, v in featured["record"].items() if k != "_id"}
        discogs_id = featured["_id"]

        ownership_count = await db.records.count_documents({"discogs_id": discogs_id})
        value_doc = await db.collection_values.find_one(
            {"release_id": discogs_id}, {"_id": 0, "median_price": 1}
        )
        estimated_value = value_doc.get("median_price", 0) if value_doc else 0

        return {
            "record": record,
            "blurb": f"This {record.get('artist', '')} pressing has been making waves in the Hive.",
            "ownership_count": ownership_count,
            "estimated_value": estimated_value,
            "featured_date": today,
            "auto_selected": True,
        }

    # Manually curated drop
    record = drop.get("record_doc") or {}
    discogs_id = drop.get("discogs_id")

    ownership_count = 0
    estimated_value = 0
    if discogs_id:
        ownership_count = await db.records.count_documents({"discogs_id": discogs_id})
        value_doc = await db.collection_values.find_one(
            {"release_id": discogs_id}, {"_id": 0, "median_price": 1}
        )
        estimated_value = value_doc.get("median_price", 0) if value_doc else 0

    return {
        "record": record,
        "blurb": drop.get("blurb", ""),
        "ownership_count": ownership_count,
        "estimated_value": estimated_value,
        "featured_date": drop.get("date"),
        "auto_selected": False,
    }


@router.post("/honey-drop/set")
async def set_honey_drop(body: dict, current_user: Dict = Depends(require_auth)):
    """Admin-only: set the featured record for a given date."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    date = body.get("date")
    discogs_id = body.get("discogs_id")
    blurb = body.get("blurb", "")

    if not date or not discogs_id:
        raise HTTPException(status_code=400, detail="date and discogs_id required")

    record_doc = await db.records.find_one({"discogs_id": discogs_id}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()

    await db.honey_drops.update_one(
        {"date": date},
        {"$set": {
            "date": date,
            "discogs_id": discogs_id,
            "record_doc": record_doc or {},
            "blurb": blurb,
            "set_by": current_user["id"],
            "created_at": now,
        }},
        upsert=True
    )
    return {"success": True, "date": date}
