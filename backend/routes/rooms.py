"""Honeycomb Rooms — themed community spaces."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict
from datetime import datetime, timezone
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
async def get_room_members(slug: str):
    """Return up to 20 members of a room sorted by join date."""
    members = await db.room_members.find(
        {"slug": slug},
        {"_id": 0, "userId": 1, "joined_at": 1}
    ).sort("joined_at", 1).limit(20).to_list(20)

    user_ids = [m["userId"] for m in members]
    users = await db.users.find(
        {"id": {"$in": user_ids}},
        {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
    ).to_list(20)
    return users


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
