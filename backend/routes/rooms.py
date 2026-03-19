"""Honeycomb Rooms — themed community spaces."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
import uuid

from database import db, require_auth, get_current_user, logger

router = APIRouter()


# GET /rooms/suggested — must be declared BEFORE /{slug} to avoid FastAPI path clash
@router.get("/rooms/suggested")
async def get_suggested_rooms(limit: int = 6):
    """Return top rooms by member count."""
    rooms = await db.rooms.find(
        {"active": True},
        {"_id": 0}
    ).sort("member_count", -1).limit(limit).to_list(limit)
    return rooms


@router.get("/rooms/{slug}")
async def get_room(slug: str):
    """Return full room doc."""
    room = await db.rooms.find_one({"slug": slug}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.get("/rooms/{slug}/feed")
async def get_room_feed(slug: str, current_user: Dict = Depends(require_auth)):
    """Return posts matching the room's filter."""
    room = await db.rooms.find_one({"slug": slug}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room_filter = room.get("filter", {})
    room_type = room.get("type", "era")

    if room_type == "era":
        decade_start = room_filter.get("year", {}).get("$gte")
        decade_end = room_filter.get("year", {}).get("$lte")
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": 200},
            {"$lookup": {
                "from": "records",
                "localField": "record_id",
                "foreignField": "id",
                "as": "record"
            }},
            {"$unwind": {"path": "$record", "preserveNullAndEmptyArrays": False}},
            {"$addFields": {
                "record_year_int": {"$toInt": "$record.year"}
            }},
            {"$match": {
                "record_year_int": {"$gte": decade_start, "$lte": decade_end}
            }},
            {"$project": {"_id": 0, "record._id": 0}},
            {"$limit": 20},
        ]
    elif room_type == "artist":
        artist_name = room_filter.get("artist", {}).get("$regex", "")
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": 200},
            {"$lookup": {
                "from": "records",
                "localField": "record_id",
                "foreignField": "id",
                "as": "record"
            }},
            {"$unwind": {"path": "$record", "preserveNullAndEmptyArrays": False}},
            {"$match": {
                "record.artist": {"$regex": artist_name, "$options": "i"}
            }},
            {"$project": {"_id": 0, "record._id": 0}},
            {"$limit": 20},
        ]
    else:
        # Genre rooms: fall back to most-recent posts (no genre field yet)
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": 20},
            {"$project": {"_id": 0}},
        ]

    posts = await db.posts.aggregate(pipeline).to_list(20)
    return posts


@router.get("/rooms/{slug}/charts")
async def get_room_charts(slug: str):
    """Return top 5 most-posted records in the room."""
    room = await db.rooms.find_one({"slug": slug}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room_filter = room.get("filter", {})
    room_type = room.get("type", "era")

    if room_type == "era":
        decade_start = room_filter.get("year", {}).get("$gte")
        decade_end = room_filter.get("year", {}).get("$lte")
        pipeline = [
            {"$lookup": {
                "from": "records",
                "localField": "record_id",
                "foreignField": "id",
                "as": "record"
            }},
            {"$unwind": {"path": "$record", "preserveNullAndEmptyArrays": False}},
            {"$addFields": {"record_year_int": {"$toInt": "$record.year"}}},
            {"$match": {"record_year_int": {"$gte": decade_start, "$lte": decade_end}}},
            {"$group": {"_id": "$record_id", "count": {"$sum": 1}, "record": {"$first": "$record"}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
            {"$project": {"_id": 0, "record_id": "$_id", "count": 1, "record.title": 1, "record.artist": 1, "record.cover_url": 1, "record.year": 1}},
        ]
    elif room_type == "artist":
        artist_name = room_filter.get("artist", {}).get("$regex", "")
        pipeline = [
            {"$lookup": {
                "from": "records",
                "localField": "record_id",
                "foreignField": "id",
                "as": "record"
            }},
            {"$unwind": {"path": "$record", "preserveNullAndEmptyArrays": False}},
            {"$match": {"record.artist": {"$regex": artist_name, "$options": "i"}}},
            {"$group": {"_id": "$record_id", "count": {"$sum": 1}, "record": {"$first": "$record"}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
            {"$project": {"_id": 0, "record_id": "$_id", "count": 1, "record.title": 1, "record.artist": 1, "record.cover_url": 1, "record.year": 1}},
        ]
    else:
        pipeline = [
            {"$group": {"_id": "$record_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5},
            {"$lookup": {"from": "records", "localField": "_id", "foreignField": "id", "as": "record"}},
            {"$unwind": {"path": "$record", "preserveNullAndEmptyArrays": True}},
            {"$project": {"_id": 0, "record_id": "$_id", "count": 1, "record.title": 1, "record.artist": 1, "record.cover_url": 1}},
        ]

    charts = await db.posts.aggregate(pipeline).to_list(5)
    return charts


@router.get("/rooms/{slug}/members")
async def get_room_members(slug: str, current_user: Optional[Dict] = Depends(get_current_user)):
    """Return up to 20 members. Gold users see Top Collector badges (top 5 by relevant records)."""
    room = await db.rooms.find_one({"slug": slug}, {"_id": 0, "type": 1, "filter": 1})
    members = await db.room_members.find(
        {"slug": slug},
        {"_id": 0, "userId": 1, "joined_at": 1}
    ).sort("joined_at", 1).limit(20).to_list(20)

    user_ids = [m["userId"] for m in members]
    users_raw = await db.users.find(
        {"id": {"$in": user_ids}},
        {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
    ).to_list(20)

    is_gold = current_user and (
        current_user.get("golden_hive") or current_user.get("golden_hive_verified")
    )

    # Compute collection_count_in_room per member for Top Collector ranking
    room_type = room.get("type", "era") if room else "era"
    room_filter = room.get("filter", {}) if room else {}
    collector_counts = {}

    for uid in user_ids:
        try:
            if room_type == "era":
                decade_start = room_filter.get("year", {}).get("$gte", 0)
                decade_end = room_filter.get("year", {}).get("$lte", 9999)
                pipeline = [
                    {"$match": {"user_id": uid, "year": {"$ne": None}}},
                    {"$addFields": {"year_int": {"$toInt": "$year"}}},
                    {"$match": {"year_int": {"$gte": decade_start, "$lte": decade_end}}},
                    {"$count": "n"},
                ]
                result = await db.records.aggregate(pipeline).to_list(1)
                collector_counts[uid] = result[0]["n"] if result else 0
            elif room_type == "artist":
                artist_regex = room_filter.get("artist", {}).get("$regex", "")
                count = await db.records.count_documents({
                    "user_id": uid,
                    "artist": {"$regex": artist_regex, "$options": "i"}
                })
                collector_counts[uid] = count
            else:
                collector_counts[uid] = 0
        except Exception:
            collector_counts[uid] = 0

    # Sort by count desc, mark top 5
    sorted_ids = sorted(user_ids, key=lambda uid: collector_counts.get(uid, 0), reverse=True)
    top_5 = set(sorted_ids[:5])

    users_map = {u["id"]: u for u in users_raw}
    result = []
    for uid in user_ids:
        u = users_map.get(uid)
        if not u:
            continue
        u["is_top_collector"] = uid in top_5 and is_gold
        result.append(u)

    return result


@router.post("/rooms/{slug}/join")
async def join_room(slug: str, current_user: Dict = Depends(require_auth)):
    """Join a room. Free users limited to 3 rooms."""
    uid = current_user["id"]
    is_gold = current_user.get("golden_hive") or current_user.get("golden_hive_verified")

    if not is_gold:
        count = await db.room_members.count_documents({"userId": uid})
        if count >= 3:
            raise HTTPException(
                status_code=403,
                detail="Free members can join up to 3 rooms. Upgrade to Gold for unlimited.",
                headers={"X-Limit-Reached": "true"}
            )

    room = await db.rooms.find_one({"slug": slug})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    now = datetime.now(timezone.utc).isoformat()
    result = await db.room_members.update_one(
        {"slug": slug, "userId": uid},
        {"$setOnInsert": {"slug": slug, "userId": uid, "joined_at": now}},
        upsert=True
    )

    if result.upserted_id:
        await db.rooms.update_one({"slug": slug}, {"$inc": {"member_count": 1}})
        # Fire-and-forget milestone check
        try:
            from routes.milestones import check_room_milestone
            await check_room_milestone(uid)
        except Exception as e:
            logger.debug(f"Milestone check skipped: {e}")

    return {"joined": True}


@router.delete("/rooms/{slug}/leave")
async def leave_room(slug: str, current_user: Dict = Depends(require_auth)):
    """Leave a room."""
    uid = current_user["id"]
    result = await db.room_members.delete_one({"slug": slug, "userId": uid})
    if result.deleted_count > 0:
        await db.rooms.update_one({"slug": slug}, {"$inc": {"member_count": -1}})
    return {"left": True}


@router.get("/rooms/{slug}/membership")
async def get_membership(slug: str, current_user: Dict = Depends(require_auth)):
    """Check if the current user is a member of a room."""
    uid = current_user["id"]
    member = await db.room_members.find_one({"slug": slug, "userId": uid})
    return {"is_member": bool(member)}


@router.post("/rooms/create")
async def create_room(body: dict, current_user: Dict = Depends(require_auth)):
    """Gold-only: create a new Vibe or Collector room (pending moderation)."""
    is_gold = current_user.get("golden_hive") or current_user.get("golden_hive_verified")
    if not is_gold:
        raise HTTPException(
            status_code=403,
            detail="Gold membership required to create rooms.",
            headers={"X-Gold-Required": "true"}
        )

    room_type = body.get("type", "")
    if room_type not in ("vibe", "collector"):
        raise HTTPException(status_code=400, detail="type must be 'vibe' or 'collector'")

    name = (body.get("name") or "").strip()
    if not name or len(name) < 3 or len(name) > 60:
        raise HTTPException(status_code=400, detail="name must be 3–60 characters")

    description = (body.get("description") or "").strip()[:280]
    theme_preset = body.get("theme_preset") or "honey"
    emoji = (body.get("emoji") or "🍯").strip()

    uid = current_user["id"]

    # Rate limit: max 1 room created per user per 30 days
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent_count = await db.rooms.count_documents({
        "createdBy": uid,
        "created_at": {"$gte": thirty_days_ago}
    })
    if recent_count >= 1:
        raise HTTPException(
            status_code=429,
            detail="You can create one room per 30 days. Check back soon!"
        )

    # Build slug from name
    import re
    slug_base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
    slug = slug_base
    # Ensure slug uniqueness
    suffix = 2
    while await db.rooms.find_one({"slug": slug}):
        slug = f"{slug_base}-{suffix}"
        suffix += 1

    # Theme presets
    THEME_PRESETS = {
        "honey":    {"bgGradient": "linear-gradient(135deg, #FFF3E0, #FFE0B2)", "accentColor": "#C8861A", "textColor": "#2A1A06"},
        "midnight": {"bgGradient": "linear-gradient(135deg, #1A1A2E, #16213E)", "accentColor": "#7B68EE", "textColor": "#E8E8F0"},
        "forest":   {"bgGradient": "linear-gradient(135deg, #1B4332, #2D6A4F)", "accentColor": "#74C69D", "textColor": "#D8F3DC"},
        "rose":     {"bgGradient": "linear-gradient(135deg, #F8D7DA, #F1AEB5)", "accentColor": "#D98FA1", "textColor": "#3D1520"},
        "slate":    {"bgGradient": "linear-gradient(135deg, #2C3E50, #3D5166)", "accentColor": "#85A7C0", "textColor": "#ECF0F1"},
        "plum":     {"bgGradient": "linear-gradient(135deg, #4A235A, #6C3483)", "accentColor": "#D7BDE2", "textColor": "#F5EEF8"},
    }
    theme = THEME_PRESETS.get(theme_preset, THEME_PRESETS["honey"])

    now = datetime.now(timezone.utc).isoformat()
    room_doc = {
        "slug": slug,
        "name": name,
        "tagline": description,
        "type": room_type,
        "emoji": emoji,
        "theme": theme,
        "theme_preset": theme_preset,
        "filter": {},
        "member_count": 0,
        "active": False,  # Pending moderation
        "createdBy": uid,
        "created_at": now,
    }
    await db.rooms.insert_one(room_doc)

    return {
        "slug": slug,
        "pending": True,
        "message": "Your room has been submitted for review. We'll notify you when it goes live!"
    }
