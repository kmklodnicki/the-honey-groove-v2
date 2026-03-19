"""Beekeeper admin panel routes — room moderation, metrics, honey drop, user management."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta

from database import db, require_auth, create_notification, logger

router = APIRouter()


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
async def search_users(q: str = "", limit: int = 20, admin: Dict = Depends(require_admin)):
    """Search users by username or email."""
    if not q:
        users = await db.users.find(
            {},
            {"_id": 0, "id": 1, "username": 1, "email": 1, "golden_hive_verified": 1,
             "discogs_oauth_verified": 1, "created_at": 1, "is_banned": 1, "suspended_until": 1}
        ).sort("created_at", -1).limit(limit).to_list(limit)
    else:
        query = {"$or": [
            {"username": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
        ]}
        users = await db.users.find(
            query,
            {"_id": 0, "id": 1, "username": 1, "email": 1, "golden_hive_verified": 1,
             "discogs_oauth_verified": 1, "created_at": 1, "is_banned": 1, "suspended_until": 1}
        ).limit(limit).to_list(limit)

    # Enrich with record count
    for u in users:
        u["records_count"] = await db.records.count_documents({"user_id": u["id"]})

    return {"users": users, "total": len(users)}


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

    valid_actions = {"verify", "warn", "suspend", "ban", "grant-gold", "delete", "unban", "unsuspend"}
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
