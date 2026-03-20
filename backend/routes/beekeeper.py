"""Beekeeper admin panel routes — room moderation, metrics, honey drop, user management,
and Spotify matching / CC0 backfill tooling."""
import os
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
import asyncio

from bson import ObjectId
from database import db, require_auth, create_notification, logger

router = APIRouter()

# ─── Spotify Matching State ─────────────────────────────────────────────────

_match_stop_event: Optional[asyncio.Event] = None
_match_task: Optional[asyncio.Task] = None
_match_run_result: Optional[dict] = None

_backfill_stop_event: Optional[asyncio.Event] = None
_backfill_task: Optional[asyncio.Task] = None


# ─── Auth ───

async def require_admin(user: Dict = Depends(require_auth)) -> Dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ─── Queue ───

@router.get("/beekeeper/queue/count")
async def get_queue_count(admin: Dict = Depends(require_admin)):
    """Badge count: pending rooms + open reports."""
    pending_rooms = await db.rooms.count_documents({"active": False, "status": {"$ne": "rejected"}})
    open_reports = await db.reports.count_documents({"status": "pending"})
    return {"total": pending_rooms + open_reports, "rooms": pending_rooms, "reports": open_reports}


@router.get("/beekeeper/queue")
async def get_queue(type: Optional[str] = None, admin: Dict = Depends(require_admin)):
    """Unified moderation queue: pending rooms + open reports."""
    items = []

    if type != "reports":
        # Pending rooms (active=False, not rejected)
        rooms = await db.rooms.find(
            {"active": False, "status": {"$ne": "rejected"}},
            {"_id": 0}
        ).sort("created_at", 1).to_list(100)

        for room in rooms:
            # Enrich with creator info
            creator = await db.users.find_one(
                {"id": room.get("createdBy")},
                {"_id": 0, "id": 1, "username": 1, "golden_hive": 1, "golden_hive_verified": 1, "created_at": 1}
            )
            items.append({
                "item_type": "room",
                "id": room.get("slug"),
                "data": room,
                "creator": creator or {},
                "submitted_at": room.get("created_at"),
            })

    if type != "rooms":
        # Open reports
        reports = await db.reports.find(
            {"status": "pending"},
            {"_id": 0}
        ).sort("created_at", 1).to_list(100)

        for report in reports:
            reporter = await db.users.find_one(
                {"id": report.get("reporter_user_id")},
                {"_id": 0, "id": 1, "username": 1}
            )
            items.append({
                "item_type": "report",
                "id": report.get("id"),
                "data": report,
                "reporter": reporter or {},
                "submitted_at": report.get("created_at"),
            })

    # Sort unified list by submitted_at asc
    items.sort(key=lambda x: x.get("submitted_at") or "")
    return {"items": items, "total": len(items)}


# ─── Room Moderation ───

@router.post("/beekeeper/rooms/{slug}/approve")
async def approve_room(slug: str, admin: Dict = Depends(require_admin)):
    """Approve a pending room: set active=True, notify creator."""
    room = await db.rooms.find_one({"slug": slug}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.get("active"):
        raise HTTPException(status_code=400, detail="Room is already active")

    now = datetime.now(timezone.utc).isoformat()
    await db.rooms.update_one(
        {"slug": slug},
        {"$set": {"active": True, "approved_at": now, "status": "approved"}}
    )

    # Notify creator
    creator_id = room.get("createdBy")
    if creator_id:
        await create_notification(
            user_id=creator_id,
            ntype="room_approved",
            title="Your room is live! 🍯",
            body=f"'{room.get('name')}' has been approved and is now live in The Nectar.",
            data={"slug": slug, "room_name": room.get("name")},
            sender_id=admin["id"],
        )

    return {"success": True, "slug": slug, "message": "Room approved and creator notified"}


@router.post("/beekeeper/rooms/{slug}/reject")
async def reject_room(slug: str, body: dict, admin: Dict = Depends(require_admin)):
    """Reject a pending room: set status=rejected, notify creator, reset rate limit."""
    room = await db.rooms.find_one({"slug": slug}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    reason = body.get("reason", "")
    note = body.get("note", "")
    now = datetime.now(timezone.utc).isoformat()

    await db.rooms.update_one(
        {"slug": slug},
        {"$set": {
            "status": "rejected",
            "rejection_reason": reason,
            "rejection_note": note,
            "rejected_at": now,
            # Reset created_at so the 30-day rate limit doesn't block a retry
            "created_at": datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat(),
        }}
    )

    # Notify creator
    creator_id = room.get("createdBy")
    if creator_id:
        reason_labels = {
            "duplicate": "a similar room already exists",
            "inappropriate": "the content doesn't meet our guidelines",
            "vague": "the room description needs more detail",
            "spam": "it was flagged as spam",
        }
        reason_text = reason_labels.get(reason, reason or "it didn't meet our guidelines")
        body_text = f"Your room '{room.get('name')}' wasn't approved because {reason_text}."
        if note:
            body_text += f" Note from admin: {note}"
        body_text += " You can submit a revised room anytime."

        await create_notification(
            user_id=creator_id,
            ntype="room_rejected",
            title="Room submission update",
            body=body_text,
            data={"slug": slug, "room_name": room.get("name"), "reason": reason},
            sender_id=admin["id"],
        )

    return {"success": True, "slug": slug, "message": "Room rejected and creator notified"}


@router.put("/beekeeper/rooms/{slug}/edit")
async def edit_and_approve_room(slug: str, body: dict, admin: Dict = Depends(require_admin)):
    """Edit room fields then auto-approve."""
    room = await db.rooms.find_one({"slug": slug}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    THEME_PRESETS = {
        "honey":    {"bgGradient": "linear-gradient(135deg, #FFF3E0, #FFE0B2)", "accentColor": "#C8861A", "textColor": "#2A1A06"},
        "midnight": {"bgGradient": "linear-gradient(135deg, #1A1A2E, #16213E)", "accentColor": "#7B68EE", "textColor": "#E8E8F0"},
        "forest":   {"bgGradient": "linear-gradient(135deg, #1B4332, #2D6A4F)", "accentColor": "#74C69D", "textColor": "#D8F3DC"},
        "rose":     {"bgGradient": "linear-gradient(135deg, #F8D7DA, #F1AEB5)", "accentColor": "#D98FA1", "textColor": "#3D1520"},
        "slate":    {"bgGradient": "linear-gradient(135deg, #2C3E50, #3D5166)", "accentColor": "#85A7C0", "textColor": "#ECF0F1"},
        "plum":     {"bgGradient": "linear-gradient(135deg, #4A235A, #6C3483)", "accentColor": "#D7BDE2", "textColor": "#F5EEF8"},
    }

    now = datetime.now(timezone.utc).isoformat()
    updates = {"active": True, "approved_at": now, "status": "approved", "edited_by_admin": True}

    if "name" in body and body["name"]:
        updates["name"] = body["name"].strip()[:60]
    if "description" in body:
        updates["tagline"] = (body["description"] or "").strip()[:280]
    if "theme_preset" in body and body["theme_preset"] in THEME_PRESETS:
        updates["theme_preset"] = body["theme_preset"]
        updates["theme"] = THEME_PRESETS[body["theme_preset"]]

    await db.rooms.update_one({"slug": slug}, {"$set": updates})

    # Notify creator
    creator_id = room.get("createdBy")
    if creator_id:
        room_name = updates.get("name", room.get("name"))
        await create_notification(
            user_id=creator_id,
            ntype="room_approved",
            title="Your room is live! 🍯",
            body=f"'{room_name}' has been approved (with minor edits) and is now live in The Nectar.",
            data={"slug": slug, "room_name": room_name},
            sender_id=admin["id"],
        )

    return {"success": True, "slug": slug, "message": "Room edited and approved"}


@router.get("/beekeeper/rooms/artist")
async def list_artist_rooms(admin: Dict = Depends(require_admin)):
    """Return all live artist rooms for nickname management."""
    rooms = await db.rooms.find(
        {"type": "artist", "active": True},
        {"_id": 0, "slug": 1, "name": 1, "nickname": 1, "emoji": 1, "theme": 1, "theme_preset": 1, "member_count": 1, "filter": 1}
    ).sort("member_count", -1).to_list(100)
    return rooms


@router.put("/beekeeper/rooms/{slug}/nickname")
async def set_room_nickname(slug: str, body: dict, admin: Dict = Depends(require_admin)):
    """Set or clear a display nickname on an artist room. Does not affect slug or match criteria."""
    room = await db.rooms.find_one({"slug": slug, "type": "artist"}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Artist room not found")

    nickname = (body.get("nickname") or "").strip()[:80]
    await db.rooms.update_one(
        {"slug": slug},
        {"$set": {"nickname": nickname or None}}
    )
    return {"success": True, "slug": slug, "nickname": nickname or None}


# ─── Honey Drop ───

@router.post("/beekeeper/honey-drop")
async def beekeeper_set_honey_drop(body: dict, admin: Dict = Depends(require_admin)):
    """Schedule a Honey Drop for a given date. Wraps /honey-drop/set logic."""
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
            "set_by": admin["id"],
            "created_at": now,
        }},
        upsert=True
    )
    return {"success": True, "date": date}


@router.get("/beekeeper/honey-drop/suggestions")
async def get_honey_drop_suggestions(admin: Dict = Depends(require_admin)):
    """Top records by want-to-own ratio (ISO wants / collection owns)."""
    pipeline = [
        # Get all ISO wants grouped by discogs_id
        {"$match": {"discogs_id": {"$ne": None}, "status": {"$in": ["active", "open"]}}},
        {"$group": {
            "_id": "$discogs_id",
            "want_count": {"$sum": 1},
            "sample_item": {"$first": "$$ROOT"},
        }},
        # Join with records to get own count
        {"$lookup": {
            "from": "records",
            "localField": "_id",
            "foreignField": "discogs_id",
            "as": "owners",
        }},
        {"$addFields": {
            "own_count": {"$size": "$owners"},
            "ratio": {
                "$cond": [
                    {"$eq": ["$own_count", 0]},
                    "$want_count",
                    {"$divide": ["$want_count", {"$add": ["$own_count", 1]}]}
                ]
            }
        }},
        {"$sort": {"ratio": -1}},
        {"$limit": 10},
        {"$project": {
            "_id": 0,
            "discogs_id": "$_id",
            "want_count": 1,
            "own_count": 1,
            "ratio": 1,
            "album": "$sample_item.album",
            "artist": "$sample_item.artist",
            "cover_url": "$sample_item.cover_url",
        }}
    ]

    try:
        suggestions = await db.iso_items.aggregate(pipeline).to_list(10)
        # Enrich with collection_values for estimated value
        for s in suggestions:
            val_doc = await db.collection_values.find_one(
                {"release_id": s.get("discogs_id")},
                {"_id": 0, "median_price": 1}
            )
            s["estimated_value"] = val_doc.get("median_price", 0) if val_doc else 0
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Honey drop suggestions error: {e}")
        return {"suggestions": []}


# ─── Metrics ───

@router.get("/beekeeper/metrics")
async def get_metrics(admin: Dict = Depends(require_admin)):
    """All 7 dashboard panels in one response."""
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    # Overview
    total_users = await db.users.count_documents({})
    active_7d = await db.posts.distinct("user_id", {"created_at": {"$gte": seven_days_ago}})
    active_30d = await db.posts.distinct("user_id", {"created_at": {"$gte": thirty_days_ago}})
    new_this_week = await db.users.count_documents({"created_at": {"$gte": seven_days_ago}})
    pending_rooms = await db.rooms.count_documents({"active": False, "status": {"$ne": "rejected"}})
    open_reports = await db.reports.count_documents({"status": "pending"})

    # Revenue
    gold_count = await db.users.count_documents({"golden_hive_verified": True})
    gold_mrr = gold_count * 5  # $5/month estimate
    sales_this_month = await db.payment_transactions.count_documents({"created_at": {"$gte": month_start}, "status": "completed"})
    gmv_pipeline = [
        {"$match": {"created_at": {"$gte": month_start}, "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    gmv_result = await db.payment_transactions.aggregate(gmv_pipeline).to_list(1)
    gmv = gmv_result[0]["total"] / 100 if gmv_result else 0  # cents → dollars

    # Engagement
    posts_7d = await db.posts.count_documents({"created_at": {"$gte": seven_days_ago}})
    # Streaks: users with prompt_responses in last 2 days = active streak proxy
    two_days_ago = (now - timedelta(days=2)).isoformat()
    active_streaks = await db.prompt_responses.distinct("user_id", {"created_at": {"$gte": two_days_ago}})
    longest_streak_doc = await db.users.find_one({"current_streak": {"$exists": True}}, sort=[("current_streak", -1)])
    longest_streak = (longest_streak_doc or {}).get("current_streak", 0)

    # Marketplace
    active_listings = await db.listings.count_documents({"status": "active", "is_test_listing": {"$ne": True}})
    sales_this_week = await db.listings.count_documents({"status": "sold", "updated_at": {"$gte": seven_days_ago}})
    active_disputes = await db.trades.count_documents({"status": "disputed"})

    # Growth
    signups_this_week = new_this_week
    onboarding_completed = await db.users.count_documents({"onboarding_completed": True})
    onboarding_rate = round(onboarding_completed / max(total_users, 1) * 100, 1)
    discogs_imported = await db.users.count_documents({"discogs_oauth_verified": True})
    manual_only = total_users - discogs_imported

    # Rooms
    total_active_rooms = await db.rooms.count_documents({"active": True})
    most_popular_room = await db.rooms.find_one({"active": True}, sort=[("member_count", -1)])
    room_posts_7d = await db.posts.count_documents({"post_type": "room", "created_at": {"$gte": seven_days_ago}})
    # Users at room limit (createdBy appears 3+ times in active rooms)
    rooms_at_limit_pipeline = [
        {"$match": {"active": True}},
        {"$group": {"_id": "$createdBy", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 3}}},
        {"$count": "total"}
    ]
    rooms_at_limit_result = await db.rooms.aggregate(rooms_at_limit_pipeline).to_list(1)
    users_at_room_limit = rooms_at_limit_result[0]["total"] if rooms_at_limit_result else 0

    # Email (platform settings)
    platform_settings = await db.platform_settings.find_one({}, {"_id": 0}) or {}

    return {
        "overview": {
            "total_users": total_users,
            "active_7d": len(active_7d),
            "active_30d": len(active_30d),
            "new_this_week": new_this_week,
            "queue_count": pending_rooms + open_reports,
        },
        "revenue": {
            "gold_count": gold_count,
            "gold_mrr_estimate": gold_mrr,
            "marketplace_gmv_month": round(gmv, 2),
            "sales_this_month": sales_this_month,
        },
        "engagement": {
            "posts_7d": posts_7d,
            "active_streaks": len(active_streaks),
            "longest_streak": longest_streak,
        },
        "marketplace": {
            "active_listings": active_listings,
            "sales_this_week": sales_this_week,
            "active_disputes": active_disputes,
        },
        "growth": {
            "signups_this_week": signups_this_week,
            "onboarding_completion_rate": onboarding_rate,
            "discogs_imported": discogs_imported,
            "manual_only": manual_only,
        },
        "rooms": {
            "total_active_rooms": total_active_rooms,
            "pending_rooms": pending_rooms,
            "most_popular_room": {
                "name": (most_popular_room or {}).get("name"),
                "slug": (most_popular_room or {}).get("slug"),
                "member_count": (most_popular_room or {}).get("member_count", 0),
            } if most_popular_room else None,
            "room_posts_7d": room_posts_7d,
            "users_at_room_limit": users_at_room_limit,
        },
        "email": {
            "teaser_views_total": platform_settings.get("teaser_views_total", 0),
            "teaser_views_week": platform_settings.get("teaser_views_week", 0),
            "newsletter_subscribers": await db.beta_signups.count_documents({}),
        },
    }


# ─── User Management ───

@router.get("/beekeeper/users")
async def search_users(
    q: str = "",
    skip: int = 0,
    limit: int = 50,
    filter: str = "",
    admin: Dict = Depends(require_admin)
):
    """Search users by username or email, with optional status filter and pagination."""
    query: dict = {}

    if q:
        query["$or"] = [
            {"username": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
        ]

    now_iso = datetime.now(timezone.utc).isoformat()
    if filter == "gold":
        query["golden_hive_verified"] = True
    elif filter == "verified":
        query["discogs_oauth_verified"] = True
    elif filter == "banned":
        query["is_banned"] = True
    elif filter == "suspended":
        query["suspended_until"] = {"$gt": now_iso}

    projection = {
        "_id": 0, "id": 1, "username": 1, "email": 1,
        "golden_hive_verified": 1, "discogs_oauth_verified": 1,
        "created_at": 1, "is_banned": 1, "suspended_until": 1,
    }

    total = await db.users.count_documents(query)
    users = await db.users.find(query, projection).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    # Enrich with record count
    for u in users:
        u["records_count"] = await db.records.count_documents({"user_id": u["id"]})

    return {"users": users, "total": total, "skip": skip, "limit": limit}


@router.get("/beekeeper/users/{user_id}")
async def get_user_detail(user_id: str, admin: Dict = Depends(require_admin)):
    """Full user detail with stats and moderation history."""
    user = await db.users.find_one(
        {"$or": [{"id": user_id}, {"username": user_id}]},
        {"_id": 0, "password_hash": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    uid = user["id"]
    records_count = await db.records.count_documents({"user_id": uid})
    posts_count = await db.posts.count_documents({"user_id": uid})
    listings_count = await db.listings.count_documents({"user_id": uid})
    trades_count = await db.trades.count_documents({"$or": [{"initiator_id": uid}, {"responder_id": uid}]})
    follower_count = await db.followers.count_documents({"following_id": uid})
    following_count = await db.followers.count_documents({"follower_id": uid})

    notifications_count = await db.notifications.count_documents({"user_id": uid})

    return {
        "user": user,
        "stats": {
            "records": records_count,
            "posts": posts_count,
            "listings": listings_count,
            "trades": trades_count,
            "followers": follower_count,
            "following": following_count,
        },
        "moderation": {
            "warnings": user.get("warnings", []),
            "suspended_until": user.get("suspended_until"),
            "is_banned": user.get("is_banned", False),
            "ban_reason": user.get("ban_reason"),
        }
    }


@router.post("/beekeeper/users/{user_id}/action")
async def user_action(user_id: str, body: dict, admin: Dict = Depends(require_admin)):
    """Perform a moderation action on a user."""
    action = body.get("action")
    note = body.get("note", "")
    duration_days = body.get("duration_days")

    valid_actions = {"verify", "remove-verify", "warn", "suspend", "ban", "grant-gold", "revoke-gold", "delete", "unban", "unsuspend"}
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}")

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    if action == "verify":
        await db.users.update_one({"id": user_id}, {"$set": {"discogs_oauth_verified": True}})
        return {"success": True, "action": action, "message": "User verified"}

    elif action == "remove-verify":
        await db.users.update_one({"id": user_id}, {"$unset": {"discogs_oauth_verified": ""}})
        return {"success": True, "action": action, "message": "Verified status removed"}

    elif action == "grant-gold":
        await db.users.update_one({"id": user_id}, {"$set": {
            "golden_hive": True,
            "golden_hive_verified": True,
            "golden_hive_status": "APPROVED",
        }})
        await create_notification(
            user_id=user_id,
            ntype="gold_granted",
            title="Welcome to the Golden Hive! 🍯",
            body="Your Gold membership has been activated. Enjoy all the perks!",
            data={},
            sender_id=admin["id"],
        )
        return {"success": True, "action": action, "message": "Gold granted"}

    elif action == "revoke-gold":
        await db.users.update_one({"id": user_id}, {"$unset": {
            "golden_hive": "",
            "golden_hive_verified": "",
            "golden_hive_status": "",
        }})
        return {"success": True, "action": action, "message": "Gold revoked"}

    elif action == "warn":
        warning = {"note": note, "issued_at": now_iso, "issued_by": admin["id"]}
        await db.users.update_one({"id": user_id}, {"$push": {"warnings": warning}})
        await create_notification(
            user_id=user_id,
            ntype="account_warning",
            title="Account warning",
            body=note or "Your account has received a warning from our moderation team.",
            data={"note": note},
            sender_id=admin["id"],
        )
        return {"success": True, "action": action, "message": "Warning issued"}

    elif action == "suspend":
        if not duration_days:
            raise HTTPException(status_code=400, detail="duration_days required for suspend")
        suspended_until = (now + timedelta(days=int(duration_days))).isoformat()
        await db.users.update_one({"id": user_id}, {"$set": {"suspended_until": suspended_until}})
        await create_notification(
            user_id=user_id,
            ntype="account_suspended",
            title="Account suspended",
            body=f"Your account has been suspended for {duration_days} days. {note}".strip(),
            data={"suspended_until": suspended_until, "duration_days": duration_days},
            sender_id=admin["id"],
        )
        return {"success": True, "action": action, "suspended_until": suspended_until}

    elif action == "unsuspend":
        await db.users.update_one({"id": user_id}, {"$unset": {"suspended_until": ""}})
        return {"success": True, "action": action, "message": "Suspension lifted"}

    elif action == "ban":
        await db.users.update_one({"id": user_id}, {"$set": {
            "is_banned": True,
            "banned_at": now_iso,
            "ban_reason": note,
        }})
        # Cancel active listings
        await db.listings.update_many(
            {"user_id": user_id, "status": "active"},
            {"$set": {"status": "cancelled", "cancelled_at": now_iso}}
        )
        await create_notification(
            user_id=user_id,
            ntype="account_banned",
            title="Account banned",
            body="Your account has been permanently banned for violating our community guidelines.",
            data={"reason": note},
            sender_id=admin["id"],
        )
        return {"success": True, "action": action, "message": "User banned"}

    elif action == "unban":
        await db.users.update_one({"id": user_id}, {"$unset": {"is_banned": "", "ban_reason": "", "banned_at": ""}})
        return {"success": True, "action": action, "message": "Ban lifted"}

    elif action == "delete":
        # Soft delete: anonymize user
        await db.users.update_one({"id": user_id}, {"$set": {
            "is_deleted": True,
            "deleted_at": now_iso,
            "email": f"deleted_{user_id}@deleted.invalid",
            "username": f"deleted_{user_id[:8]}",
        }})
        return {"success": True, "action": action, "message": "User soft-deleted"}

    return {"success": False, "message": "Unknown action"}


# ─── Spotify Matching ────────────────────────────────────────────────────────

@router.get("/beekeeper/spotify-matching/stats")
async def spotify_matching_stats(admin: Dict = Depends(require_admin)):
    """Coverage stats for Spotify album art matching."""
    pending = await db.releases.count_documents({"spotifyMatchStatus": "pending"})
    matched = await db.releases.count_documents({"spotifyMatchStatus": "matched"})
    unmatched = await db.releases.count_documents({"spotifyMatchStatus": "unmatched"})
    manual = await db.releases.count_documents({"spotifyMatchStatus": "manual_override"})
    total = pending + matched + unmatched + manual
    coverage_pct = round((matched + manual) / max(total, 1) * 100, 1)
    running = _match_task is not None and not _match_task.done()
    return {
        "pending": pending,
        "matched": matched,
        "unmatched": unmatched,
        "manual_override": manual,
        "total": total,
        "coveragePct": coverage_pct,
        "isRunning": running,
        "lastRunResult": _match_run_result,
    }


@router.post("/beekeeper/spotify-matching/start")
async def start_spotify_matching(admin: Dict = Depends(require_admin)):
    """Start batch Spotify matching in the background."""
    global _match_stop_event, _match_task, _match_run_result
    from services.spotify_service import batch_match_releases

    if _match_task and not _match_task.done():
        return {"success": False, "message": "Matching already running"}

    _match_stop_event = asyncio.Event()

    async def _run():
        global _match_run_result
        result = await batch_match_releases(_match_stop_event)
        _match_run_result = result
        now = datetime.now(timezone.utc).isoformat()
        await db.matching_runs.insert_one({**result, "type": "spotify", "completedAt": now})

    _match_task = asyncio.create_task(_run())
    return {"success": True, "message": "Spotify matching started"}


@router.post("/beekeeper/spotify-matching/stop")
async def stop_spotify_matching(admin: Dict = Depends(require_admin)):
    """Signal the running batch to stop gracefully."""
    global _match_stop_event
    if _match_stop_event:
        _match_stop_event.set()
    return {"success": True, "message": "Stop signal sent"}


@router.post("/beekeeper/spotify-matching/retry")
async def retry_spotify_matching(admin: Dict = Depends(require_admin)):
    """Re-queue all unmatched releases as pending and restart matching."""
    global _match_stop_event, _match_task, _match_run_result
    from services.spotify_service import batch_match_releases

    if _match_task and not _match_task.done():
        return {"success": False, "message": "Matching already running — stop it first"}

    requeued = await db.releases.update_many(
        {"spotifyMatchStatus": "unmatched"},
        {"$set": {"spotifyMatchStatus": "pending"}}
    )

    _match_stop_event = asyncio.Event()

    async def _run():
        global _match_run_result
        result = await batch_match_releases(_match_stop_event)
        _match_run_result = result
        now = datetime.now(timezone.utc).isoformat()
        await db.matching_runs.insert_one({**result, "type": "spotify_retry", "completedAt": now})

    _match_task = asyncio.create_task(_run())
    return {"success": True, "requeued": requeued.modified_count, "message": "Retry started"}


@router.post("/beekeeper/spotify-matching/manual/{release_id}")
async def manual_spotify_match(release_id: str, body: dict, admin: Dict = Depends(require_admin)):
    """Manually assign a Spotify album to a release by Spotify album ID or URL."""
    import re, requests as _req
    from services.spotify_service import get_spotify_token

    release = await db.releases.find_one({"discogsReleaseId": int(release_id)}, {"_id": 0})
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    spotify_input = body.get("spotifyAlbumId") or body.get("spotifyUrl") or ""
    # Extract album ID from URL if needed
    match = re.search(r"album/([A-Za-z0-9]+)", spotify_input)
    album_id = match.group(1) if match else spotify_input.strip()
    if not album_id:
        raise HTTPException(status_code=400, detail="spotifyAlbumId or spotifyUrl required")

    token = await get_spotify_token()
    if not token:
        raise HTTPException(status_code=503, detail="Spotify token unavailable")

    try:
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: _req.get(f"https://api.spotify.com/v1/albums/{album_id}",
                             headers={"Authorization": f"Bearer {token}"}, timeout=10)
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Spotify album not found: {resp.status_code}")
        album = resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    images = album.get("images", [])
    image_url = images[0]["url"] if images else None
    image_small = images[1]["url"] if len(images) > 1 else image_url
    now = datetime.now(timezone.utc).isoformat()

    await db.releases.update_one(
        {"discogsReleaseId": int(release_id)},
        {"$set": {
            "spotifyAlbumId": album_id,
            "spotifyImageUrl": image_url,
            "spotifyImageSmall": image_small,
            "spotifyMatchType": "manual",
            "spotifyMatchStatus": "manual_override",
            "spotifyMatchedAt": now,
        }}
    )
    return {"success": True, "albumId": album_id, "imageUrl": image_url}


@router.delete("/beekeeper/spotify-matching/manual/{release_id}")
async def clear_spotify_match(release_id: str, admin: Dict = Depends(require_admin)):
    """Clear a manual Spotify match, resetting the release to 'unmatched'."""
    result = await db.releases.update_one(
        {"discogsReleaseId": int(release_id)},
        {"$set": {
            "spotifyAlbumId": None,
            "spotifyImageUrl": None,
            "spotifyImageSmall": None,
            "spotifyMatchType": None,
            "spotifyMatchStatus": "unmatched",
            "spotifyMatchedAt": None,
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Release not found")
    return {"success": True}


@router.get("/cron/spotify-match")
async def cron_spotify_match(request: Request):
    """Vercel Cron Job endpoint — processes up to 40 pending Spotify matches per invocation.
    Authenticated via CRON_SECRET env var sent as Bearer token by Vercel.
    Runs every 10 minutes, resuming from where the previous run left off.
    """
    cron_secret = os.environ.get("CRON_SECRET", "")
    auth = request.headers.get("authorization", "")
    if not cron_secret or auth != f"Bearer {cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    from services.spotify_service import batch_match_releases

    pending = await db.releases.count_documents({"spotifyMatchStatus": "pending"})
    if pending == 0:
        return {"success": True, "message": "No pending releases", "processed": 0}

    stop_event = asyncio.Event()
    result = await batch_match_releases(stop_event, run_limit=40)
    logger.info(f"Cron Spotify match: {result}")
    return {"success": True, **result}


# ─── CC0 Backfill ────────────────────────────────────────────────────────────

@router.post("/beekeeper/cc0-backfill/start")
async def start_cc0_backfill(admin: Dict = Depends(require_admin)):
    """Backfill CC0 release data for all vault records that don't yet have a releases doc."""
    global _backfill_stop_event, _backfill_task
    from services.releases_service import upsert_release_cc0
    import asyncio as _asyncio
    from database import get_discogs_release

    if _backfill_task and not _backfill_task.done():
        return {"success": False, "message": "Backfill already running"}

    _backfill_stop_event = asyncio.Event()

    async def _run():
        # Find all distinct discogs_ids from records that have no releases doc
        all_ids_cursor = db.records.find({"discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1})
        all_ids = list({r["discogs_id"] async for r in all_ids_cursor})

        existing_ids_cursor = db.releases.find({}, {"_id": 0, "discogsReleaseId": 1})
        existing = {r["discogsReleaseId"] async for r in existing_ids_cursor}

        missing = [i for i in all_ids if i not in existing]
        logger.info(f"CC0 backfill: {len(missing)} releases to fetch")

        for discogs_id in missing:
            if _backfill_stop_event.is_set():
                break
            try:
                data = await _asyncio.get_event_loop().run_in_executor(None, get_discogs_release, discogs_id)
                if data:
                    await upsert_release_cc0(discogs_id, data)
            except Exception as e:
                logger.warning(f"CC0 backfill error for {discogs_id}: {e}")
            await _asyncio.sleep(1.0)  # 1 req/sec to respect Discogs rate limit

    _backfill_task = asyncio.create_task(_run())
    return {"success": True, "message": "CC0 backfill started"}


@router.get("/beekeeper/spotify-matching/releases")
async def get_releases_by_status(status: str = "unmatched", skip: int = 0, limit: int = 50, admin: Dict = Depends(require_admin)):
    """List releases filtered by spotifyMatchStatus."""
    valid = {"matched", "unmatched", "manual_override", "pending"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid}")
    projection = {"_id": 0, "discogsReleaseId": 1, "title": 1, "artists": 1, "barcode": 1, "year": 1,
                  "spotifyAlbumId": 1, "spotifyImageUrl": 1, "spotifyMatchedAt": 1}
    docs = await db.releases.find({"spotifyMatchStatus": status}, projection).skip(skip).limit(limit).to_list(limit)
    total = await db.releases.count_documents({"spotifyMatchStatus": status})
    return {"releases": docs, "total": total}


@router.get("/beekeeper/spotify-matching/unmatched")
async def get_unmatched_releases(skip: int = 0, limit: int = 50, admin: Dict = Depends(require_admin)):
    """List unmatched releases for the manual match UI."""
    docs = await db.releases.find(
        {"spotifyMatchStatus": "unmatched"},
        {"_id": 0, "discogsReleaseId": 1, "title": 1, "artists": 1, "barcode": 1, "year": 1}
    ).skip(skip).limit(limit).to_list(limit)
    return {"releases": docs, "total": await db.releases.count_documents({"spotifyMatchStatus": "unmatched"})}


@router.get("/beekeeper/spotify-matching/manual-overrides")
async def get_manual_override_releases(skip: int = 0, limit: int = 50, admin: Dict = Depends(require_admin)):
    """List manually matched releases so they can be reviewed or cleared."""
    docs = await db.releases.find(
        {"spotifyMatchStatus": "manual_override"},
        {"_id": 0, "discogsReleaseId": 1, "title": 1, "artists": 1, "year": 1,
         "spotifyAlbumId": 1, "spotifyImageUrl": 1, "spotifyMatchedAt": 1}
    ).sort("spotifyMatchedAt", -1).skip(skip).limit(limit).to_list(limit)
    return {"releases": docs, "total": await db.releases.count_documents({"spotifyMatchStatus": "manual_override"})}


# ─── Community Cover Moderation ───────────────────────────────────────────────

@router.get("/beekeeper/community-covers")
async def list_community_cover_submissions(status: str = "pending", skip: int = 0, limit: int = 50, admin: Dict = Depends(require_admin)):
    """List community cover photo submissions by status."""
    docs = await db.community_cover_submissions.find(
        {"status": status},
        {"_id": 0}
    ).sort("submittedAt", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.community_cover_submissions.count_documents({"status": status})
    return {"submissions": docs, "total": total}


@router.post("/beekeeper/community-covers/{submission_id}/approve")
async def approve_community_cover(submission_id: str, admin: Dict = Depends(require_admin)):
    """Approve a community cover submission — sets it as the release's community cover."""
    sub = await db.community_cover_submissions.find_one({"id": submission_id}, {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    now = datetime.now(timezone.utc).isoformat()

    # Set on releases collection
    await db.releases.update_one(
        {"discogsReleaseId": sub["discogsReleaseId"]},
        {"$set": {
            "communityCoverUrl": sub["imageUrl"],
            "communityCoverSmall": sub["imageSmall"],
            "communityCoverBy": sub["submittedBy"],
        }}
    )

    # Mark submission approved
    await db.community_cover_submissions.update_one(
        {"id": submission_id},
        {"$set": {"status": "approved", "reviewedAt": now, "reviewedBy": admin["id"]}}
    )
    return {"success": True}


@router.post("/beekeeper/community-covers/{submission_id}/reject")
async def reject_community_cover(submission_id: str, admin: Dict = Depends(require_admin)):
    """Reject a community cover submission. If it was previously approved, clears the community cover."""
    sub = await db.community_cover_submissions.find_one({"id": submission_id}, {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    now = datetime.now(timezone.utc).isoformat()

    # If this submission's image is currently the community cover, clear it
    if sub.get("status") == "approved":
        release = await db.releases.find_one({"discogsReleaseId": sub["discogsReleaseId"]}, {"_id": 0, "communityCoverUrl": 1})
        if release and release.get("communityCoverUrl") == sub["imageUrl"]:
            await db.releases.update_one(
                {"discogsReleaseId": sub["discogsReleaseId"]},
                {"$set": {"communityCoverUrl": None, "communityCoverSmall": None, "communityCoverBy": None}}
            )

    await db.community_cover_submissions.update_one(
        {"id": submission_id},
        {"$set": {"status": "rejected", "reviewedAt": now, "reviewedBy": admin["id"]}}
    )
    return {"success": True}


# ─── Discogs Migration (TOS Compliance) ──────────────────────────────────────

_migration_stop_event: Optional[asyncio.Event] = None
_migration_task: Optional[asyncio.Task] = None
_migration_status: dict = {
    "running": False,
    "processed": 0,
    "linked": 0,
    "spotify_triggered": 0,
    "tokens_deleted": 0,
    "usernames_cleared": 0,
    "images_cleared": 0,
    "errors": [],
    "started_at": None,
    "completed_at": None,
}


@router.get("/beekeeper/migration/discogs/status")
async def get_discogs_migration_status(admin: Dict = Depends(require_admin)):
    """Current status of the Discogs TOS compliance migration."""
    # Also report compliance counts
    discogs_url_in_records = await db.records.count_documents({
        "$or": [
            {"cover_url": {"$regex": "discogs", "$options": "i"}},
            {"imageUrl": {"$regex": "discogs", "$options": "i"}},
        ]
    })
    releases_with_images = await db.releases.count_documents({"images": {"$exists": True}})
    stored_tokens = await db.discogs_tokens.count_documents({})
    users_with_username = await db.users.count_documents({"discogs_username": {"$exists": True, "$ne": None}})

    return {
        **_migration_status,
        "compliance": {
            "discogs_urls_in_records": discogs_url_in_records,
            "releases_with_images_field": releases_with_images,
            "stored_oauth_tokens": stored_tokens,
            "users_with_discogs_username": users_with_username,
        },
    }


@router.post("/beekeeper/migration/discogs/start")
async def start_discogs_migration(admin: Dict = Depends(require_admin)):
    """Start the Discogs TOS compliance migration for all beta users.

    For each record with importSource='discogs_import' (or legacy records with a discogs_id
    but no releaseId), this task:
    1. Looks up or creates a releases document (CC0 data only).
    2. Updates the record with releaseId, discogsReleaseId, importSource.
    3. Clears any stored Discogs image URLs from records.
    4. Triggers Spotify matching for releases that have no match yet.

    Post-migration cleanup:
    - Deletes all documents in discogs_tokens.
    - Unsets discogs_username from all user documents.
    - Clears any cover_url / imageUrl fields pointing to Discogs CDN.
    """
    global _migration_task, _migration_stop_event

    if _migration_task and not _migration_task.done():
        return {"message": "Migration already running", **_migration_status}

    _migration_stop_event = asyncio.Event()
    _migration_status.update({
        "running": True,
        "processed": 0,
        "linked": 0,
        "spotify_triggered": 0,
        "tokens_deleted": 0,
        "usernames_cleared": 0,
        "images_cleared": 0,
        "errors": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    })
    _migration_task = asyncio.create_task(_run_discogs_migration(_migration_stop_event))
    return {"message": "Migration started", **_migration_status}


@router.post("/beekeeper/migration/discogs/stop")
async def stop_discogs_migration(admin: Dict = Depends(require_admin)):
    """Cancel an in-progress Discogs migration batch."""
    if _migration_stop_event:
        _migration_stop_event.set()
    return {"message": "Stop signal sent", **_migration_status}


# ─── Invites ───────────────────────────────────────────────────────────────

@router.get("/beekeeper/invites")
async def get_invite_overview(admin: Dict = Depends(require_admin)):
    """Beta signups + invite tokens + stats for the Invites tab."""
    from database import FRONTEND_URL

    # Beta signups enriched with code status
    signups = await db.beta_signups.find({}, {"_id": 0}).sort("submitted_at", -1).to_list(1000)
    for s in signups:
        code_id = s.get("invite_code_id")
        if code_id:
            code_doc = await db.invite_codes.find_one({"id": code_id}, {"_id": 0, "status": 1, "used_at": 1, "used_by": 1})
            if code_doc and code_doc.get("status") == "used":
                s["invite_status"] = "joined"
                s["invite_used_at"] = code_doc.get("used_at")
                if code_doc.get("used_by"):
                    u = await db.users.find_one({"id": code_doc["used_by"]}, {"_id": 0, "username": 1})
                    s["joined_username"] = u.get("username") if u else None

    # Recent direct invite tokens (token-based invites)
    tokens = await db.invite_tokens.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    for t in tokens:
        user = await db.users.find_one({"email": t["email"]}, {"_id": 0, "username": 1, "id": 1})
        t["claimed"] = user is not None
        t["username"] = user.get("username") if user else None

    total_signups = len(signups)
    invited = sum(1 for s in signups if s.get("invite_status") in ("sent", "joined"))
    joined = sum(1 for s in signups if s.get("invite_status") == "joined")
    pending_tokens = sum(1 for t in tokens if not t.get("claimed"))

    return {
        "signups": signups,
        "tokens": tokens,
        "stats": {
            "total_signups": total_signups,
            "invited": invited,
            "joined": joined,
            "pending_tokens": pending_tokens,
        },
    }


@router.post("/beekeeper/invites/send")
async def beekeeper_send_invite(data: dict, admin: Dict = Depends(require_admin)):
    """Send a fresh token-based invite link to any email address."""
    import uuid
    from database import FRONTEND_URL
    from services.email_service import send_email

    email = (data.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1, "username": 1})
    is_existing = user is not None

    await db.invite_tokens.delete_many({"email": email})

    new_token = str(uuid.uuid4())
    await db.invite_tokens.insert_one({
        "token": new_token,
        "email": email,
        "is_existing": is_existing,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_by": admin["id"],
    })

    claim_url = f"{FRONTEND_URL}/invite/{new_token}"
    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#FFFBF2;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#1E2A3A;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FFFBF2;">
<tr><td align="center" style="padding:24px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(30,42,58,0.08);">
<tr><td align="center" style="background-color:#1E2A3A;padding:28px 24px 20px;">
<img src="https://www.thehoneygroove.com/logo-wordmark.png" alt="the Honey Groove" width="200" style="display:block;height:auto;"/>
</td></tr>
<tr><td style="padding:32px 28px 12px;">
<h1 style="font-size:22px;font-weight:700;color:#D4A828;margin:0 0 20px;line-height:1.3;">You're invited to the Hive.</h1>
<p style="font-size:15px;line-height:1.7;color:#1E2A3A;margin:0 0 16px;">
Welcome to <strong>The Honey Groove</strong> — the social marketplace for vinyl collectors. Click below to claim your spot and start cataloguing your collection, connecting with diggers, and finding your next favorite record.
</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:8px 0 28px;">
<a href="{claim_url}" target="_blank"
   style="display:inline-block;background-color:#D4A828;color:#FFFFFF;font-size:16px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:999px;letter-spacing:0.3px;">
Join Now
</a>
</td></tr>
</table>
<p style="font-size:13px;line-height:1.6;color:#7A8694;margin:0 0 16px;">This link expires in 7 days. If you didn't request this, you can safely ignore this email.</p>
<p style="font-size:15px;line-height:1.7;color:#1E2A3A;margin:0;">Best,<br/><strong style="color:#D4A828;">Katie</strong><br/><span style="font-size:13px;color:#7A8694;">Founder, The Honey Groove&trade;</span></p>
</td></tr>
<tr><td align="center" style="padding:20px 28px 24px;border-top:1px solid #E5DBC8;">
<p style="font-size:11px;color:#7A8694;margin:0;line-height:1.5;">&copy; 2026 The Honey Groove&trade; &middot; the vinyl social club, finally.</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""

    sent = await send_email(email, "You're invited to The Honey Groove 🍯", html, reply_to="hello@thehoneygroove.com")
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email")

    logger.info(f"Beekeeper invite sent to {email} by {admin.get('username', admin['id'])}")
    return {"status": "sent", "email": email, "is_existing": is_existing}


@router.post("/beekeeper/invites/beta-signups/{signup_id}/send")
async def beekeeper_send_signup_invite(signup_id: str, admin: Dict = Depends(require_admin)):
    """Send invite code to a beta signup from the Invites tab."""
    from database import FRONTEND_URL
    from services.email_service import send_email
    import uuid, string, random

    signup = await db.beta_signups.find_one({"id": signup_id}, {"_id": 0})
    if not signup:
        raise HTTPException(status_code=404, detail="Signup not found")

    now = datetime.now(timezone.utc).isoformat()
    old_code = signup.get("invite_code_id")
    if old_code:
        await db.invite_codes.update_one(
            {"id": old_code, "status": "unused"},
            {"$set": {"status": "revoked", "revoked_at": now}},
        )

    chars = string.ascii_uppercase + string.digits
    code = "HG-" + "".join(random.choices(chars, k=8))
    code_doc = {
        "id": str(uuid.uuid4()),
        "code": code,
        "status": "unused",
        "created_at": now,
        "created_by": admin["id"],
        "used_by": None,
        "used_at": None,
        "sent_to": signup["email"],
        "sent_at": now,
        "beta_signup_id": signup_id,
    }
    await db.invite_codes.insert_one(code_doc)

    from templates.emails import invite_code as invite_code_tpl
    tpl = invite_code_tpl(signup.get("first_name", "there"), code)
    await send_email(signup["email"], tpl["subject"], tpl["html"], reply_to="hello@thehoneygroove.com")

    await db.beta_signups.update_one({"id": signup_id}, {"$set": {
        "invite_code_id": code_doc["id"],
        "invite_code": code,
        "invite_status": "sent",
        "invite_sent_at": now,
    }})

    return {"status": "sent", "invite_code": code, "email": signup["email"]}


async def _run_discogs_migration(stop_event: asyncio.Event):
    """Background: link all Discogs-imported records to the releases collection."""
    from database import get_discogs_release
    from services.releases_service import upsert_release_cc0
    from services.spotify_service import match_to_spotify

    global _migration_status

    try:
        # Find all records that were imported from Discogs but lack a releaseId
        cursor = db.records.find(
            {"$or": [
                {"importSource": "discogs_import", "releaseId": {"$exists": False}},
                {"source": "discogs_import", "releaseId": {"$exists": False}},
                {"discogs_id": {"$exists": True, "$ne": None}, "releaseId": {"$exists": False}},
            ]},
            {"_id": 0, "id": 1, "discogs_id": 1, "discogsReleaseId": 1},
        )
        records_to_migrate = await cursor.to_list(50000)

        for rec in records_to_migrate:
            if stop_event.is_set():
                break

            rid = rec.get("discogsReleaseId") or rec.get("discogs_id")
            if not rid:
                _migration_status["processed"] += 1
                continue

            try:
                # Look up existing release doc
                release_doc = await db.releases.find_one({"discogsReleaseId": rid})
                if not release_doc:
                    discogs_data = await asyncio.get_event_loop().run_in_executor(
                        None, get_discogs_release, rid
                    )
                    if discogs_data:
                        await upsert_release_cc0(rid, discogs_data)
                        release_doc = await db.releases.find_one({"discogsReleaseId": rid})
                    await asyncio.sleep(1.0)

                if release_doc:
                    release_id_str = str(release_doc["_id"])
                    update_fields: dict = {
                        "releaseId": release_id_str,
                        "discogsReleaseId": rid,
                        "importSource": "discogs_import",
                    }
                    # Clear Discogs image URLs if present
                    unset_fields: dict = {}
                    if rec.get("cover_url") and "discogs" in str(rec.get("cover_url", "")).lower():
                        unset_fields["cover_url"] = ""
                        _migration_status["images_cleared"] += 1
                    if rec.get("imageUrl") and "discogs" in str(rec.get("imageUrl", "")).lower():
                        unset_fields["imageUrl"] = ""
                        _migration_status["images_cleared"] += 1

                    op: dict = {"$set": update_fields}
                    if unset_fields:
                        op["$unset"] = unset_fields
                    await db.records.update_one({"id": rec["id"]}, op)
                    _migration_status["linked"] += 1

                    # Trigger Spotify matching if not yet attempted
                    if release_doc.get("spotifyMatchStatus") in (None, "pending"):
                        release_for_spotify = {k: v for k, v in release_doc.items() if k != "_id"}
                        asyncio.create_task(match_to_spotify(release_for_spotify))
                        _migration_status["spotify_triggered"] += 1

                _migration_status["processed"] += 1

            except Exception as e:
                err = f"record {rec.get('id', '?')}: {str(e)[:120]}"
                _migration_status["errors"].append(err)
                logger.warning(f"Migration error — {err}")
                _migration_status["processed"] += 1

        # ── Post-migration cleanup ────────────────────────────────────────────
        if not stop_event.is_set():
            # 1. Clear all stored OAuth tokens
            del_result = await db.discogs_tokens.delete_many({})
            _migration_status["tokens_deleted"] = del_result.deleted_count

            # 2. Unset discogs_username from all user docs
            unset_result = await db.users.update_many(
                {"discogs_username": {"$exists": True}},
                {"$unset": {"discogs_username": ""}},
            )
            _migration_status["usernames_cleared"] = unset_result.modified_count

            # 3. Clear any remaining Discogs CDN image URLs from records
            discogs_image_records = await db.records.count_documents({
                "$or": [
                    {"cover_url": {"$regex": "discogs", "$options": "i"}},
                    {"imageUrl": {"$regex": "discogs", "$options": "i"}},
                ]
            })
            if discogs_image_records > 0:
                await db.records.update_many(
                    {"cover_url": {"$regex": "discogs", "$options": "i"}},
                    {"$unset": {"cover_url": ""}},
                )
                await db.records.update_many(
                    {"imageUrl": {"$regex": "discogs", "$options": "i"}},
                    {"$unset": {"imageUrl": ""}},
                )
                _migration_status["images_cleared"] += discogs_image_records

            logger.info(
                f"Discogs migration complete: {_migration_status['processed']} processed, "
                f"{_migration_status['linked']} linked, {_migration_status['tokens_deleted']} tokens deleted"
            )

        _migration_status["running"] = False
        _migration_status["completed_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        logger.error(f"Discogs migration failed: {e}")
        _migration_status["running"] = False
        _migration_status["errors"].append(f"Fatal: {str(e)[:200]}")
        _migration_status["completed_at"] = datetime.now(timezone.utc).isoformat()


@router.get("/beekeeper/compliance/discogs")
async def discogs_compliance_check(admin: Dict = Depends(require_admin)):
    """Compliance audit: returns counts of any remaining Discogs Restricted Data in the DB.
    All counts should be zero after a successful migration.
    """
    records_with_discogs_url = await db.records.count_documents({
        "$or": [
            {"cover_url": {"$regex": r"i\.discogs\.com|st\.discogs\.com", "$options": "i"}},
            {"imageUrl": {"$regex": r"i\.discogs\.com|st\.discogs\.com", "$options": "i"}},
        ]
    })
    releases_with_images = await db.releases.count_documents({"images": {"$exists": True}})
    stored_tokens = await db.discogs_tokens.count_documents({})
    users_with_username = await db.users.count_documents({
        "discogs_username": {"$exists": True, "$ne": None}
    })

    all_clear = (
        records_with_discogs_url == 0
        and releases_with_images == 0
        and stored_tokens == 0
    )

    return {
        "all_clear": all_clear,
        "records_with_discogs_image_urls": records_with_discogs_url,
        "releases_with_images_field": releases_with_images,
        "stored_oauth_tokens": stored_tokens,
        "users_with_discogs_username": users_with_username,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/beekeeper/compliance/cleanup")
async def run_compliance_cleanup(admin: Dict = Depends(require_admin)):
    """Synchronously purge all Discogs Restricted Data from the database.

    Runs the three cleanup steps inline (no background task) so it works
    reliably in serverless environments:
    1. Delete all documents in discogs_tokens.
    2. Unset discogs_username from all user documents.
    3. Clear cover_url / imageUrl fields pointing to Discogs CDN from records.
    """
    tokens_deleted = (await db.discogs_tokens.delete_many({})).deleted_count

    usernames_cleared = (await db.users.update_many(
        {"discogs_username": {"$exists": True}},
        {"$unset": {"discogs_username": ""}},
    )).modified_count

    await db.records.update_many(
        {"cover_url": {"$regex": r"i\.discogs\.com|st\.discogs\.com", "$options": "i"}},
        {"$unset": {"cover_url": ""}},
    )
    await db.records.update_many(
        {"imageUrl": {"$regex": r"i\.discogs\.com|st\.discogs\.com", "$options": "i"}},
        {"$unset": {"imageUrl": ""}},
    )
    images_checked = await db.records.count_documents({
        "$or": [
            {"cover_url": {"$regex": r"i\.discogs\.com|st\.discogs\.com", "$options": "i"}},
            {"imageUrl": {"$regex": r"i\.discogs\.com|st\.discogs\.com", "$options": "i"}},
        ]
    })

    logger.info(
        f"Compliance cleanup: {tokens_deleted} tokens deleted, "
        f"{usernames_cleared} usernames cleared, images remaining: {images_checked}"
    )

    return {
        "tokens_deleted": tokens_deleted,
        "usernames_cleared": usernames_cleared,
        "images_remaining": images_checked,
        "cleaned_at": datetime.now(timezone.utc).isoformat(),
    }


# ─── Testimonials ─────────────────────────────────────────────────────────────

def _serialize_testimonial(t: dict) -> dict:
    t["id"] = str(t.pop("_id"))
    if t.get("linkedUserId"):
        t["linkedUserId"] = str(t["linkedUserId"])
    return t


# Public: landing page fetches active testimonials (no auth required)
@router.get("/testimonials")
async def get_public_testimonials():
    cursor = db.testimonials.find(
        {"isActive": True},
        sort=[("sortOrder", 1)],
    )
    results = []
    async for doc in cursor:
        results.append(_serialize_testimonial(doc))
    return results


# Admin: all testimonials
@router.get("/beekeeper/testimonials")
async def list_all_testimonials(admin: Dict = Depends(require_admin)):
    cursor = db.testimonials.find({}, sort=[("sortOrder", 1)])
    results = []
    async for doc in cursor:
        results.append(_serialize_testimonial(doc))
    return results


# Admin: create
@router.post("/beekeeper/testimonials")
async def create_testimonial(body: dict, admin: Dict = Depends(require_admin)):
    required = {"quote", "username", "avatarLetter"}
    if not required.issubset(body.keys()):
        raise HTTPException(400, "Missing required fields: quote, username, avatarLetter")
    if len(body.get("quote", "")) > 300:
        raise HTTPException(400, "quote must be 300 characters or fewer")

    # Auto-assign sortOrder at the end
    last = await db.testimonials.find_one({}, sort=[("sortOrder", -1)])
    next_order = (last["sortOrder"] + 1) if last else 1

    doc = {
        "quote": body["quote"].strip(),
        "username": body["username"].strip(),
        "label": body.get("label", "beta collector").strip(),
        "avatarLetter": (body.get("avatarLetter") or "?")[0].upper(),
        "avatarUrl": body.get("avatarUrl"),
        "recordCount": int(body.get("recordCount", 0)),
        "isActive": bool(body.get("isActive", True)),
        "sortOrder": int(body.get("sortOrder", next_order)),
        "createdAt": datetime.now(timezone.utc),
        "linkedUserId": ObjectId(body["linkedUserId"]) if body.get("linkedUserId") else None,
        "linkedUsername": body.get("linkedUsername"),
    }
    result = await db.testimonials.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_testimonial(doc)


# Admin: update
@router.put("/beekeeper/testimonials/{tid}")
async def update_testimonial(tid: str, body: dict, admin: Dict = Depends(require_admin)):
    try:
        oid = ObjectId(tid)
    except Exception:
        raise HTTPException(400, "Invalid testimonial id")

    allowed = {"quote", "username", "label", "avatarLetter", "avatarUrl",
               "recordCount", "isActive", "sortOrder", "linkedUserId", "linkedUsername"}
    update = {}
    for k, v in body.items():
        if k not in allowed:
            continue
        if k == "quote" and len(v) > 300:
            raise HTTPException(400, "quote must be 300 characters or fewer")
        if k == "avatarLetter" and v:
            v = v[0].upper()
        if k == "linkedUserId":
            v = ObjectId(v) if v else None
        update[k] = v

    if not update:
        raise HTTPException(400, "No valid fields to update")

    result = await db.testimonials.update_one({"_id": oid}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(404, "Testimonial not found")
    doc = await db.testimonials.find_one({"_id": oid})
    return _serialize_testimonial(doc)


# Admin: delete
@router.delete("/beekeeper/testimonials/{tid}")
async def delete_testimonial(tid: str, admin: Dict = Depends(require_admin)):
    try:
        oid = ObjectId(tid)
    except Exception:
        raise HTTPException(400, "Invalid testimonial id")
    result = await db.testimonials.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(404, "Testimonial not found")
    return {"deleted": True}


# Admin: reorder (accepts {orderedIds: [id1, id2, ...]})
@router.put("/beekeeper/testimonials-reorder")
async def reorder_testimonials(body: dict, admin: Dict = Depends(require_admin)):
    ordered_ids = body.get("orderedIds", [])
    if not ordered_ids:
        raise HTTPException(400, "orderedIds is required")
    for i, tid in enumerate(ordered_ids):
        try:
            oid = ObjectId(tid)
        except Exception:
            raise HTTPException(400, f"Invalid id: {tid}")
        await db.testimonials.update_one({"_id": oid}, {"$set": {"sortOrder": i + 1}})
    return {"reordered": len(ordered_ids)}


# Admin: pull from Hive — top engaged posts for testimonial sourcing
@router.get("/beekeeper/testimonials/hive-posts")
async def get_hive_posts_for_testimonials(admin: Dict = Depends(require_admin)):
    cursor = db.posts.find(
        {"post_type": {"$in": ["note", "spin", "haul"]}},
        sort=[("likes_count", -1)],
    ).limit(20)
    results = []
    async for doc in cursor:
        user = await db.users.find_one({"_id": doc.get("user_id")}, {"username": 1, "avatar_url": 1, "record_count": 1})
        results.append({
            "postId": str(doc["_id"]),
            "text": doc.get("content") or doc.get("text") or "",
            "likesCount": doc.get("likes_count", 0),
            "username": f"@{user['username']}" if user else "@unknown",
            "avatarLetter": (user.get("username", "?")[0].upper()) if user else "?",
            "avatarUrl": user.get("avatar_url") if user else None,
            "recordCount": user.get("record_count", 0) if user else 0,
            "linkedUserId": str(doc.get("user_id")) if doc.get("user_id") else None,
        })
    return results


# Admin: seed the 5 initial testimonials (idempotent — skips if collection non-empty)
@router.post("/beekeeper/testimonials/seed")
async def seed_testimonials(admin: Dict = Depends(require_admin)):
    existing = await db.testimonials.count_documents({})
    if existing > 0:
        return {"seeded": 0, "message": "Collection already has testimonials"}

    seeds = [
        {"quote": "I have been waiting for something like this. Discogs is for cataloging, eBay is for selling, but nothing was for the community. The Honey Groove is where I actually want to hang out.", "username": "@crazy_vinyl_13", "label": "beta collector", "avatarLetter": "C", "recordCount": 187, "isActive": True, "sortOrder": 1},
        {"quote": "The Wax Report personality cards are addicting. I share mine every Monday morning and my followers keep asking how to join.", "username": "@crateking", "label": "founding collector", "avatarLetter": "C", "recordCount": 312, "isActive": True, "sortOrder": 2},
        {"quote": "6% fees? I was paying almost 13% on other platforms. I moved all my listings here the first week. The Mutual Hold system makes trading feel safe for the first time ever.", "username": "@waxvault99", "label": "beta collector", "avatarLetter": "W", "recordCount": 94, "isActive": True, "sortOrder": 3},
        {"quote": "The Daily Prompt got me posting every day. 23 day streak and counting. This is the first vinyl app that actually feels alive.", "username": "@deepgrooves", "label": "Gold Collector", "avatarLetter": "D", "recordCount": 241, "isActive": True, "sortOrder": 4},
        {"quote": "I found three records from my Dream List through ISOs here in the first month. The matching system actually works.", "username": "@pressingsonly", "label": "beta collector", "avatarLetter": "P", "recordCount": 156, "isActive": True, "sortOrder": 5},
    ]
    now = datetime.now(timezone.utc)
    for s in seeds:
        s["createdAt"] = now
        s["avatarUrl"] = None
        s["linkedUserId"] = None
    await db.testimonials.insert_many(seeds)
    await db.testimonials.create_index([("isActive", 1), ("sortOrder", 1)])
    return {"seeded": len(seeds)}
