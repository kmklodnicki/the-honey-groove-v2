from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from database import db, require_auth, get_current_user, security, logger, create_notification, get_hidden_user_ids, get_all_blocked_ids
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT
from database import get_discogs_market_data
from utils.image_helpers import proxy_records_cover_urls
DISCOGS_API_BASE = "https://api.discogs.com"
import requests
from services.email_service import send_email_fire_and_forget
import templates.emails as email_tpl
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, PLATFORM_FEE_PERCENT, FRONTEND_URL
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from database import oauth_request_tokens, import_progress, EMERGENT_KEY
from models import *
from routes.hive import build_post_response


router = APIRouter()

# ============== BUZZING NOW (Trending) ROUTES ==============

@router.get("/buzzing")
async def get_buzzing_records(current_user: Optional[Dict] = Depends(get_current_user), limit: int = 10):
    """Get trending/buzzing records based on recent spins, deduplicated by album."""
    hidden_ids = await get_hidden_user_ids()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    match_filter = {"created_at": {"$gte": week_ago}}
    if hidden_ids:
        match_filter["user_id"] = {"$nin": hidden_ids}
    
    pipeline = [
        {"$match": match_filter},
        # Join with records to get album metadata
        {"$lookup": {
            "from": "records",
            "localField": "record_id",
            "foreignField": "id",
            "as": "record"
        }},
        {"$unwind": "$record"},
        # Group by lowercase artist+title so all pressings/variants merge
        {"$group": {
            "_id": {"$concat": [
                {"$toLower": {"$ifNull": ["$record.artist", ""]}},
                "|||",
                {"$toLower": {"$ifNull": ["$record.title", ""]}}
            ]},
            "spin_count": {"$sum": 1},
            "record": {"$first": "$record"},
        }},
        {"$sort": {"spin_count": -1}},
        {"$limit": limit},
        {"$replaceRoot": {
            "newRoot": {
                "$mergeObjects": ["$record", {"trending_spins": "$spin_count"}]
            }
        }},
        {"$project": {"_id": 0}}
    ]
    
    result = await db.spins.aggregate(pipeline).to_list(limit)
    proxy_records_cover_urls(result)
    return result


# ============== FOLLOW ROUTES ==============

@router.post("/follow/{username}")
async def follow_user(username: str, user: Dict = Depends(require_auth)):
    target_user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    existing = await db.followers.find_one({
        "follower_id": user["id"],
        "following_id": target_user["id"]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already following this user")
    
    # If target is private, create a follow request instead
    if target_user.get("is_private", False):
        existing_req = await db.follow_requests.find_one({
            "from_id": user["id"], "to_id": target_user["id"], "status": "pending"
        })
        if existing_req:
            return {"message": "Follow request already sent", "status": "requested"}
        
        now = datetime.now(timezone.utc).isoformat()
        await db.follow_requests.insert_one({
            "id": str(uuid.uuid4()),
            "from_id": user["id"],
            "to_id": target_user["id"],
            "status": "pending",
            "created_at": now
        })
        
        u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
        await create_notification(target_user["id"], "FOLLOW_REQUEST", "Follow request",
                                  f"@{u.get('username','?')} requested to follow you",
                                  {"from_username": u.get("username"), "from_id": user["id"]}, sender_id=user["id"])
        
        return {"message": "Follow request sent", "status": "requested"}
    
    follow_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    follow_doc = {
        "id": follow_id,
        "follower_id": user["id"],
        "following_id": target_user["id"],
        "created_at": now
    }
    
    await db.followers.insert_one(follow_doc)
    
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    await create_notification(target_user["id"], "NEW_FOLLOWER", "New follower",
                              f"@{u.get('username','?')} started following you",
                              {"follower_username": u.get("username")}, sender_id=user["id"])
    if target_user.get("email"):
        from database import should_send_notification_email
        if await should_send_notification_email(target_user["id"], sender_id=user["id"]):
            tpl = email_tpl.new_follow(u.get("username", "?"), f"{FRONTEND_URL}/profile/{u.get('username','')}")
            await send_email_fire_and_forget(target_user["email"], tpl["subject"], tpl["html"])

    return {"message": f"Now following {username}", "status": "following"}

@router.delete("/follow/{username}")
async def unfollow_user(username: str, user: Dict = Depends(require_auth)):
    target_user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.followers.delete_one({
        "follower_id": user["id"],
        "following_id": target_user["id"]
    })
    
    # Also clean up any pending follow requests
    await db.follow_requests.delete_many({"from_id": user["id"], "to_id": target_user["id"]})
    
    if result.deleted_count == 0:
        return {"message": "Cancelled follow request"}
    
    return {"message": f"Unfollowed {username}"}

@router.get("/follow/check/{username}")
async def check_following(username: str, user: Dict = Depends(require_auth)):
    target_user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = await db.followers.find_one({
        "follower_id": user["id"],
        "following_id": target_user["id"]
    })
    
    # Check if they follow us (reciprocal check)
    reverse = await db.followers.find_one({
        "follower_id": target_user["id"],
        "following_id": user["id"]
    })
    
    follow_request_pending = False
    if not existing:
        req = await db.follow_requests.find_one({"from_id": user["id"], "to_id": target_user["id"], "status": "pending"})
        follow_request_pending = req is not None
    
    return {"is_following": existing is not None, "follows_me": reverse is not None, "follow_request_pending": follow_request_pending}

@router.get("/users/{username}/followers")
async def get_followers(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    followers = await db.followers.find({"following_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    # Pre-fetch viewer's discogs IDs for "records in common"
    viewer_discogs = set()
    if current_user:
        viewer_records = await db.records.find({"user_id": current_user["id"], "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}).to_list(5000)
        viewer_discogs = {r["discogs_id"] for r in viewer_records if r.get("discogs_id")}
    
    result = []
    for f in followers:
        follower_user = await db.users.find_one({"id": f["follower_id"]}, {"_id": 0, "password_hash": 0})
        if follower_user:
            is_following = False
            if current_user:
                is_following = await db.followers.find_one({
                    "follower_id": current_user["id"],
                    "following_id": follower_user["id"]
                }) is not None
            
            records_in_common = 0
            if viewer_discogs and current_user and current_user["id"] != follower_user["id"]:
                their_records = await db.records.find({"user_id": follower_user["id"], "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}).to_list(5000)
                their_discogs = {r["discogs_id"] for r in their_records if r.get("discogs_id")}
                records_in_common = len(viewer_discogs & their_discogs)
            
            # Check if this user follows the viewer
            follows_me = False
            if current_user and current_user["id"] != follower_user["id"]:
                follows_me = await db.followers.find_one({
                    "follower_id": follower_user["id"],
                    "following_id": current_user["id"]
                }) is not None
            
            result.append({
                "id": follower_user["id"],
                "username": follower_user["username"],
                "avatar_url": follower_user.get("avatar_url"),
                "bio": follower_user.get("bio"),
                "is_following": is_following,
                "follows_me": follows_me,
                "records_in_common": records_in_common
            })
    
    return result

@router.get("/users/{username}/following")
async def get_following(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    # Pre-fetch viewer's discogs IDs for "records in common"
    viewer_discogs = set()
    if current_user:
        viewer_records = await db.records.find({"user_id": current_user["id"], "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}).to_list(5000)
        viewer_discogs = {r["discogs_id"] for r in viewer_records if r.get("discogs_id")}
    
    result = []
    for f in following:
        following_user = await db.users.find_one({"id": f["following_id"]}, {"_id": 0, "password_hash": 0})
        if following_user:
            is_following = False
            if current_user:
                is_following = await db.followers.find_one({
                    "follower_id": current_user["id"],
                    "following_id": following_user["id"]
                }) is not None
            
            records_in_common = 0
            if viewer_discogs and current_user and current_user["id"] != following_user["id"]:
                their_records = await db.records.find({"user_id": following_user["id"], "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}).to_list(5000)
                their_discogs = {r["discogs_id"] for r in their_records if r.get("discogs_id")}
                records_in_common = len(viewer_discogs & their_discogs)
            
            # Check if this user follows the viewer
            follows_me = False
            if current_user and current_user["id"] != following_user["id"]:
                follows_me = await db.followers.find_one({
                    "follower_id": following_user["id"],
                    "following_id": current_user["id"]
                }) is not None
            
            result.append({
                "id": following_user["id"],
                "username": following_user["username"],
                "avatar_url": following_user.get("avatar_url"),
                "bio": following_user.get("bio"),
                "is_following": is_following,
                "follows_me": follows_me,
                "records_in_common": records_in_common
            })
    
    return result


# ============== FOLLOW REQUEST ROUTES ==============

@router.get("/follow-requests")
async def get_follow_requests(user: Dict = Depends(require_auth)):
    """Get pending follow requests for the current user."""
    requests = await db.follow_requests.find({"to_id": user["id"], "status": "pending"}, {"_id": 0}).sort("created_at", -1).to_list(100)
    result = []
    for req in requests:
        from_user = await db.users.find_one({"id": req["from_id"]}, {"_id": 0, "password_hash": 0})
        if from_user:
            result.append({
                "id": req["id"],
                "from_user": {
                    "id": from_user["id"],
                    "username": from_user["username"],
                    "avatar_url": from_user.get("avatar_url"),
                    "bio": from_user.get("bio"),
                },
                "created_at": req["created_at"]
            })
    return result


@router.post("/follow-requests/{request_id}/accept")
async def accept_follow_request(request_id: str, user: Dict = Depends(require_auth)):
    """Accept a follow request, creating the follower relationship."""
    req = await db.follow_requests.find_one({"id": request_id, "to_id": user["id"], "status": "pending"}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Follow request not found")
    
    # Create follower relationship
    now = datetime.now(timezone.utc).isoformat()
    await db.followers.insert_one({
        "id": str(uuid.uuid4()),
        "follower_id": req["from_id"],
        "following_id": user["id"],
        "created_at": now
    })
    
    # Update request status
    await db.follow_requests.update_one({"id": request_id}, {"$set": {"status": "accepted"}})
    
    # Notify the requester
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    await create_notification(req["from_id"], "FOLLOW_REQUEST_ACCEPTED", "Follow request accepted",
                              f"@{u.get('username','?')} accepted your follow request",
                              {"username": u.get("username")})
    
    return {"status": "accepted"}


@router.post("/follow-requests/{request_id}/decline")
async def decline_follow_request(request_id: str, user: Dict = Depends(require_auth)):
    """Decline a follow request."""
    req = await db.follow_requests.find_one({"id": request_id, "to_id": user["id"], "status": "pending"}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Follow request not found")
    
    await db.follow_requests.update_one({"id": request_id}, {"$set": {"status": "declined"}})
    return {"status": "declined"}


# ============== BLOCK ROUTES ==============

@router.post("/block/{username}")
async def block_user(username: str, user: Dict = Depends(require_auth)):
    """Block a user. Blocked user cannot see blocker's profile, posts, or collections."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot block yourself")

    existing = await db.blocks.find_one({"blocker_id": user["id"], "blocked_id": target["id"]})
    if existing:
        return {"status": "already_blocked"}

    await db.blocks.insert_one({
        "id": str(uuid.uuid4()),
        "blocker_id": user["id"],
        "blocked_id": target["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Also unfollow in both directions
    await db.followers.delete_one({"follower_id": user["id"], "following_id": target["id"]})
    await db.followers.delete_one({"follower_id": target["id"], "following_id": user["id"]})

    return {"status": "blocked"}


@router.delete("/block/{username}")
async def unblock_user(username: str, user: Dict = Depends(require_auth)):
    """Unblock a previously blocked user."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.blocks.delete_one({"blocker_id": user["id"], "blocked_id": target["id"]})
    if result.deleted_count == 0:
        return {"status": "not_blocked"}
    return {"status": "unblocked"}


@router.get("/block/check/{username}")
async def check_block_status(username: str, user: Dict = Depends(require_auth)):
    """Check if current user has blocked a given user, or vice versa."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    i_blocked = await db.blocks.find_one({"blocker_id": user["id"], "blocked_id": target["id"]}) is not None
    they_blocked = await db.blocks.find_one({"blocker_id": target["id"], "blocked_id": user["id"]}) is not None

    return {"is_blocked": i_blocked, "is_blocked_by": they_blocked}


# ============== PROFILE DATA ROUTES ==============

# Helper: check block + privacy gating for profile data endpoints
async def _check_profile_access(target: Dict, current_user: Optional[Dict]):
    """Raises HTTPException if viewer cannot access target's profile data."""
    if current_user and current_user["id"] != target["id"]:
        block = await db.blocks.find_one({"$or": [{"blocker_id": target["id"], "blocked_id": current_user["id"]}, {"blocker_id": current_user["id"], "blocked_id": target["id"]}]})
        if block:
            raise HTTPException(status_code=403, detail="This profile is not available.")
        if target.get("is_private", False):
            is_follower = await db.followers.find_one({"follower_id": current_user["id"], "following_id": target["id"]})
            if not is_follower:
                raise HTTPException(status_code=403, detail="This account is private.")
    elif not current_user and target.get("is_private", False):
        raise HTTPException(status_code=403, detail="This account is private.")


@router.get("/users/{username}/spins")
async def get_user_spins(username: str, limit: int = 50, current_user: Optional[Dict] = Depends(get_current_user)):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    await _check_profile_access(target, current_user)
    
    spins = await db.spins.find({"user_id": target["id"]}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    result = []
    for spin in spins:
        record = await db.records.find_one({"id": spin["record_id"]}, {"_id": 0})
        if record:
            # Try to get caption/mood from spin doc first, then from corresponding post
            caption = spin.get("caption") or ""
            mood = spin.get("mood") or ""
            post_id = None
            if not caption and not mood:
                # Lookup the corresponding post
                post = await db.posts.find_one({
                    "user_id": target["id"],
                    "record_id": spin["record_id"],
                    "post_type": "NOW_SPINNING",
                    "created_at": spin["created_at"]
                }, {"_id": 0, "caption": 1, "mood": 1, "id": 1})
                if post:
                    caption = post.get("caption", "")
                    mood = post.get("mood", "")
                    post_id = post.get("id")
            else:
                post = await db.posts.find_one({"spin_id": spin["id"]}, {"_id": 0, "id": 1})
                post_id = post.get("id") if post else None
            result.append({**spin, "record": record, "caption": caption, "mood": mood, "post_id": post_id})
    return result

@router.get("/users/{username}/iso")
async def get_user_isos(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    await _check_profile_access(target, current_user)
    
    isos = await db.iso_items.find({"user_id": target["id"], "status": {"$ne": "WISHLIST"}}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return isos


@router.get("/users/{username}/dreaming")
async def get_user_dreaming(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    """Get a user's wishlist/dreaming items."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    await _check_profile_access(target, current_user)
    
    items = await db.iso_items.find({"user_id": target["id"], "status": "WISHLIST"}, {"_id": 0}).sort("created_at", -1).to_list(200)

    # Enrich with median Discogs values
    discogs_ids = [i["discogs_id"] for i in items if i.get("discogs_id")]
    value_map = {}
    if discogs_ids:
        values = await db.collection_values.find(
            {"release_id": {"$in": discogs_ids}}, {"_id": 0, "release_id": 1, "median_value": 1}
        ).to_list(len(discogs_ids))
        value_map = {v["release_id"]: v.get("median_value") for v in values if v.get("median_value")}
    for item in items:
        item["median_value"] = value_map.get(item.get("discogs_id"))

    return items

@router.get("/users/{username}/posts")
async def get_user_posts(username: str, current_user: Optional[Dict] = Depends(get_current_user), limit: int = 20, before: Optional[str] = None):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    await _check_profile_access(target, current_user)
    
    query = {"user_id": target["id"]}
    if before:
        query["created_at"] = {"$lt": before}
    posts = await db.posts.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    result = []
    uid = current_user["id"] if current_user else None
    for post in posts:
        resp = await build_post_response(post, uid)
        if resp:
            result.append(resp)
    return result


# ============== STATS ROUTES ==============

@router.get("/stats")
async def get_global_stats():
    users_count = await db.users.count_documents({})
    records_count = await db.records.count_documents({})
    spins_count = await db.spins.count_documents({})
    hauls_count = await db.hauls.count_documents({})
    
    return {
        "users": users_count,
        "records": records_count,
        "spins": spins_count,
        "hauls": hauls_count
    }

# Root endpoint
@router.get("/")
async def root():
    return {"message": "Welcome to HoneyGroove API", "version": "1.0.0"}



@router.get("/explore/trending")
async def get_trending_records(limit: int = 12, user: Dict = Depends(require_auth)):
    """Trending records: most spun + most added in last 14 days, deduplicated by album (artist+title)."""
    hidden_ids = await get_hidden_user_ids()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    spin_match = {"created_at": {"$gte": cutoff}}
    if hidden_ids:
        spin_match["user_id"] = {"$nin": hidden_ids}
    pipeline = [
        {"$match": spin_match},
        {"$lookup": {
            "from": "records",
            "localField": "record_id",
            "foreignField": "id",
            "as": "record"
        }},
        {"$unwind": "$record"},
        # Group by lowercase artist+title so all pressings/variants merge
        {"$group": {
            "_id": {"$concat": [
                {"$toLower": {"$ifNull": ["$record.artist", ""]}},
                "|||",
                {"$toLower": {"$ifNull": ["$record.title", ""]}}
            ]},
            "spin_count": {"$sum": 1},
            "record": {"$first": "$record"},
        }},
        {"$sort": {"spin_count": -1}},
        {"$limit": limit},
        {"$replaceRoot": {
            "newRoot": {
                "$mergeObjects": ["$record", {"trending_spins": "$spin_count"}]
            }
        }},
        {"$project": {"_id": 0}}
    ]
    result = await db.spins.aggregate(pipeline).to_list(limit)
    proxy_records_cover_urls(result)
    return result


@router.get("/explore/trending/{record_id}/posts")
async def get_trending_record_posts(record_id: str, limit: int = 20, user: Dict = Depends(require_auth)):
    """Get Now Spinning posts for a specific record"""
    hidden_ids = await get_hidden_user_ids()
    record = await db.records.find_one({"id": record_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    # Find all records with same discogs_id or same artist+title
    query = {"$or": [{"id": record_id}]}
    if record.get("discogs_id"):
        sibling_ids = await db.records.find({"discogs_id": record["discogs_id"]}, {"_id": 0, "id": 1}).to_list(200)
        query = {"$or": [{"id": {"$in": [s["id"] for s in sibling_ids]}}]}
    else:
        sibling_ids = await db.records.find(
            {"artist": record["artist"], "title": record["title"]}, {"_id": 0, "id": 1}
        ).to_list(200)
        query = {"$or": [{"id": {"$in": [s["id"] for s in sibling_ids]}}]}
    all_ids = [s["id"] for s in sibling_ids] if sibling_ids else [record_id]
    post_filter = {"post_type": "NOW_SPINNING", "record_id": {"$in": all_ids}}
    if hidden_ids:
        post_filter["user_id"] = {"$nin": hidden_ids}
    posts = await db.posts.find(
        post_filter, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    user_ids = list({p["user_id"] for p in posts})
    users_map = {}
    if user_ids:
        ul = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(200)
        users_map = {u["id"]: {"id": u["id"], "username": u.get("username"), "avatar_url": u.get("avatar_url")} for u in ul}
    for p in posts:
        p["user"] = users_map.get(p["user_id"])
    return {"record": record, "posts": posts}


@router.get("/explore/trending-in-collections")
async def get_trending_in_collections(limit: int = 20, user: Dict = Depends(require_auth)):
    """Most collected vinyl records on Discogs, cached for 24 hours."""
    import datetime as dt

    cache_key = "trending_in_collections_cache"
    cache = await db.cache.find_one({"key": cache_key}, {"_id": 0})

    now = dt.datetime.now(dt.timezone.utc)
    if cache and cache.get("expires_at"):
        try:
            expires = dt.datetime.fromisoformat(cache["expires_at"])
            if now < expires:
                return cache.get("data", [])[:limit]
        except Exception:
            pass

    # Cache miss or expired — fetch most collected from Discogs
    headers = {"User-Agent": DISCOGS_USER_AGENT}
    params = {
        "sort": "have",
        "sort_order": "desc",
        "format": "vinyl",
        "per_page": limit,
        "type": "release",
    }
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN

    data = []
    try:
        resp = requests.get(f"{DISCOGS_API_BASE}/database/search", params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            for item in resp.json().get("results", []):
                parts = item.get("title", "").split(" - ", 1)
                artist = parts[0].strip() if len(parts) > 1 else "Unknown"
                title = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                community = item.get("community", {})
                data.append({
                    "discogs_id": item.get("id"),
                    "artist": artist,
                    "title": title,
                    "year": item.get("year"),
                    "cover_url": None,  # Discogs cover_image is Restricted Data
                    "format": item.get("format", []),
                    "have": community.get("have", 0),
                    "want": community.get("want", 0),
                })
    except Exception as e:
        logger.error(f"Discogs trending-in-collections error: {e}")

    # Store in cache with 24-hour TTL
    expires_at = (now + dt.timedelta(hours=24)).isoformat()
    await db.cache.update_one(
        {"key": cache_key},
        {"$set": {"key": cache_key, "data": data, "expires_at": expires_at, "updated_at": now.isoformat()}},
        upsert=True,
    )

    # Clean up old fresh_pressings cache
    await db.cache.delete_one({"key": "fresh_pressings_cache"})

    return data[:limit]


@router.get("/explore/crown-jewels")
async def get_crown_jewels(limit: int = 12, user: Dict = Depends(require_auth)):
    """The rarest and most valuable records owned by Hive members.
    Dual-criteria: High Value (median price) + High Scarcity (low global have).
    """
    import datetime as dt

    cache_key = "crown_jewels_cache"
    cache = await db.cache.find_one({"key": cache_key}, {"_id": 0})

    now = dt.datetime.now(dt.timezone.utc)
    if cache and cache.get("expires_at"):
        try:
            expires = dt.datetime.fromisoformat(cache["expires_at"])
            if now < expires:
                return cache.get("data", [])[:limit]
        except Exception:
            pass

    # Aggregate: find records with discogs_id, group by discogs_id
    # Sort by owner_count descending to prioritize community-owned records
    # Filter out test data
    pipeline = [
        {"$match": {
            "discogs_id": {"$exists": True, "$ne": None},
            "title": {"$not": {"$regex": "^TEST", "$options": "i"}},
        }},
        {"$group": {
            "_id": "$discogs_id",
            "artist": {"$first": "$artist"},
            "title": {"$first": "$title"},
            "cover_url": {"$first": "$cover_url"},
            "pressing_notes": {"$first": "$pressing_notes"},
            "year": {"$first": "$year"},
            "owner_count": {"$sum": 1},
        }},
        {"$sort": {"owner_count": -1}},
        {"$limit": 150},
    ]
    records = await db.records.aggregate(pipeline).to_list(150)

    headers_discogs = {"User-Agent": DISCOGS_USER_AGENT}
    jewels = []
    for rec in records:
        discogs_id = rec["_id"]
        try:
            params = {}
            if DISCOGS_TOKEN:
                params["token"] = DISCOGS_TOKEN
            resp = requests.get(
                f"{DISCOGS_API_BASE}/releases/{discogs_id}",
                params=params, headers=headers_discogs, timeout=10,
            )
            if resp.status_code != 200:
                continue
            d = resp.json()
            community = d.get("community", {})
            have = community.get("have", 999999)
            want = community.get("want", 0)
            formats = d.get("formats", [])
            variant = ""
            for fmt in formats:
                descs = fmt.get("descriptions", [])
                variant = ", ".join(descs) if descs else ""

            # Fetch market value for dual-criteria scoring
            market = get_discogs_market_data(discogs_id)
            median_value = market.get("median_value", 0) if market else 0
            low_value = market.get("low_value") if market else None
            high_value = market.get("high_value") if market else None

            # Skip low-value records — Crown Jewels should be $20+
            effective_value = max(median_value, high_value or 0)
            if effective_value < 20:
                continue

            jewels.append({
                "discogs_id": discogs_id,
                "artist": rec.get("artist", "Unknown"),
                "title": rec.get("title", "Unknown"),
                "cover_url": rec.get("cover_url"),  # Only use stored URL (never Discogs CDN images — Restricted Data)
                "variant": variant or rec.get("pressing_notes", ""),
                "year": rec.get("year") or d.get("year"),
                "have": have,
                "want": want,
                "owner_count": rec.get("owner_count", 0),
                "estimated_value": median_value,
                "low_value": low_value,
                "high_value": high_value,
            })
        except Exception as e:
            logger.warning(f"Crown jewels Discogs fetch error for {discogs_id}: {e}")
            continue

    # Value-dominant sort: prioritize most expensive items
    # Value score: higher value = higher score (primary)
    # Scarcity score: lower have = higher score (secondary tiebreaker)
    max_have = max((j["have"] for j in jewels), default=1) or 1
    max_val = max((max(j["estimated_value"], j.get("high_value") or 0) for j in jewels), default=1) or 1
    for j in jewels:
        scarcity_score = 1 - (j["have"] / max_have)  # 0..1
        value_score = max(j["estimated_value"], j.get("high_value") or 0) / max_val   # 0..1
        j["elite_score"] = (scarcity_score * 0.2) + (value_score * 0.8)

    jewels.sort(key=lambda x: x.get("elite_score", 0), reverse=True)
    jewels = jewels[:limit]

    # Cache for 24 hours
    expires_at = (now + dt.timedelta(hours=24)).isoformat()
    await db.cache.update_one(
        {"key": cache_key},
        {"$set": {"key": cache_key, "data": jewels, "expires_at": expires_at, "updated_at": now.isoformat()}},
        upsert=True,
    )

    return jewels


@router.get("/explore/most-wanted")
async def get_most_wanted(limit: int = 20, user: Dict = Depends(require_auth)):
    """Top 20 most wanted records across all wantlists"""
    hidden_ids = await get_hidden_user_ids()
    iso_match = {"status": "OPEN"}
    if hidden_ids:
        iso_match["user_id"] = {"$nin": hidden_ids}
    pipeline = [
        {"$match": iso_match},
        {"$group": {
            "_id": {"artist": "$artist", "album": "$album"},
            "count": {"$sum": 1},
            "cover_url": {"$first": "$cover_url"},
            "discogs_id": {"$first": "$discogs_id"},
            "year": {"$first": "$year"},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    agg = await db.iso_items.aggregate(pipeline).to_list(limit)
    results = []
    for item in agg:
        results.append({
            "artist": item["_id"]["artist"],
            "album": item["_id"]["album"],
            "cover_url": item.get("cover_url"),
            "discogs_id": item.get("discogs_id"),
            "year": item.get("year"),
            "want_count": item["count"],
        })
    return results


@router.get("/explore/near-you")
async def get_near_you(user: Dict = Depends(require_auth), collector_limit: int = 20, listing_limit: int = 10):
    """Get collectors and listings nearby — US: match by state, Non-US: match by country"""
    hidden_ids = await get_hidden_user_ids()
    my_country = (user.get("country") or "").strip().upper()
    my_state = (user.get("state") or user.get("region") or "").strip()

    # Determine matching strategy
    if my_country == "US" and my_state:
        # US users: prioritize state matching
        match_field = "state"
        match_value = my_state
        # Also try region for backward compat
        match_query = {"$or": [
            {"state": {"$regex": f"^{my_state}$", "$options": "i"}},
            {"region": {"$regex": f"^{my_state}$", "$options": "i"}},
        ]}
    elif my_country and my_country != "US":
        # Non-US users: match by country
        match_field = "country"
        match_value = my_country
        match_query = {"country": {"$regex": f"^{my_country}$", "$options": "i"}}
    else:
        # Fallback to old region matching
        my_region = (user.get("region") or "").strip().lower()
        if not my_region:
            return {"collectors": [], "listings": [], "needs_location": True}
        match_query = {"region": {"$regex": f"^{my_region}$", "$options": "i"}}

    query = {"id": {"$ne": user["id"]}, "username": {"$ne": "demo"}, "email": {"$not": {"$regex": "(example|test)\\.com$", "$options": "i"}}, "is_internal": {"$ne": True}}
    if hidden_ids:
        query["id"] = {"$ne": user["id"], "$nin": hidden_ids}
    query.update(match_query)

    nearby_users = await db.users.find(query, {"_id": 0, "password_hash": 0}).limit(collector_limit).to_list(collector_limit)
    collectors = []
    for u in nearby_users:
        rec_count = await db.records.count_documents({"user_id": u["id"]})
        listing_count = await db.listings.count_documents({"user_id": u["id"], "status": "ACTIVE"})
        collectors.append({
            "id": u["id"], "username": u.get("username"), "avatar_url": u.get("avatar_url"),
            "region": u.get("state") or u.get("region"),
            "country": u.get("country"),
            "collection_count": rec_count, "active_listings": listing_count,
        })

    nearby_ids = [u["id"] for u in collectors]
    listings = []
    if nearby_ids:
        listings = await db.listings.find(
            {"user_id": {"$in": nearby_ids}, "status": "ACTIVE", "is_test_listing": {"$ne": True}}, {"_id": 0}
        ).sort("created_at", -1).limit(listing_limit).to_list(listing_limit)
        for l in listings:
            seller = next((u for u in collectors if u["id"] == l["user_id"]), None)
            l["user"] = {"username": seller["username"], "region": seller.get("region"), "country": seller.get("country")} if seller else None

    return {"collectors": collectors, "listings": listings, "needs_location": False}


@router.get("/explore/recent-hauls")
async def get_recent_hauls(limit: int = 10, user: Dict = Depends(require_auth)):
    """Recent haul posts from the community"""
    hidden_ids = await get_hidden_user_ids()
    haul_filter = {"post_type": "NEW_HAUL"}
    if hidden_ids:
        haul_filter["user_id"] = {"$nin": hidden_ids}
    posts = await db.posts.find(
        haul_filter, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    user_ids = list({p["user_id"] for p in posts})
    haul_ids = [p["haul_id"] for p in posts if p.get("haul_id")]
    users_map = {}
    if user_ids:
        ul = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(100)
        users_map = {u["id"]: {"id": u["id"], "username": u.get("username"), "avatar_url": u.get("avatar_url")} for u in ul}
    hauls_map = {}
    if haul_ids:
        hl = await db.hauls.find({"id": {"$in": haul_ids}}, {"_id": 0}).to_list(100)
        hauls_map = {h["id"]: h for h in hl}
    for p in posts:
        p["user"] = users_map.get(p["user_id"])
        p["haul"] = hauls_map.get(p.get("haul_id"))
    return posts


@router.get("/explore/suggested-collectors")
async def get_suggested_collectors(limit: int = 10, user: Dict = Depends(require_auth)):
    """Suggest collectors to follow, sorted by number of shared records (discogs_id overlap)."""
    hidden_ids = await get_hidden_user_ids()
    blocked_ids = await get_all_blocked_ids(user["id"])

    # Hard filter: never show demo/test/hidden users
    user_exclude = {"username": {"$ne": "demo"}, "email": {"$not": {"$regex": "(example|test)\\.com$", "$options": "i"}}, "is_hidden": {"$ne": True}, "is_test": {"$ne": True}}

    # Get current user's discogs IDs
    my_records = await db.records.find({"user_id": user["id"], "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}).to_list(5000)
    my_discogs = [r["discogs_id"] for r in my_records if r.get("discogs_id")]

    if not my_discogs:
        # Fallback: show newest users excluding followed
        following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0, "following_id": 1}).to_list(500)
        following_ids = {f["following_id"] for f in following}
        all_exclude = list(following_ids | set(hidden_ids) | set(blocked_ids) | {user["id"]})
        return await db.users.find(
            {"id": {"$nin": all_exclude}, "is_internal": {"$ne": True}, **user_exclude}, {"_id": 0, "password_hash": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)

    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0, "following_id": 1}).to_list(500)
    following_ids = {f["following_id"] for f in following}
    all_exclude_ids = list(following_ids | set(hidden_ids) | set(blocked_ids) | {user["id"]})

    # Aggregate: find users with the most shared records by discogs_id
    pipeline = [
        {"$match": {"discogs_id": {"$in": my_discogs}, "user_id": {"$nin": all_exclude_ids}}},
        {"$group": {"_id": "$user_id", "shared_count": {"$addToSet": "$discogs_id"}}},
        {"$project": {"_id": 1, "shared_records": {"$size": "$shared_count"}}},
        {"$match": {"shared_records": {"$gte": 1}}},
        {"$sort": {"shared_records": -1}},
        {"$limit": limit},
    ]
    agg = await db.records.aggregate(pipeline).to_list(limit)
    user_ids = [a["_id"] for a in agg]
    overlap_map = {a["_id"]: a["shared_records"] for a in agg}
    if not user_ids:
        return []
    users = await db.users.find({"id": {"$in": user_ids}, **user_exclude}, {"_id": 0, "password_hash": 0}).to_list(limit)
    for u in users:
        u["shared_artists"] = overlap_map.get(u["id"], 0)
        u["shared_records"] = overlap_map.get(u["id"], 0)
    users.sort(key=lambda x: x.get("shared_records", 0), reverse=True)
    return users


@router.get("/explore/you-might-love")
async def get_you_might_love(limit: int = 8, user: Dict = Depends(require_auth)):
    """Personalized record recommendations based on taste-match overlap."""
    uid = user["id"]
    is_gold = user.get("golden_hive") or user.get("golden_hive_verified")

    # Current user's collection
    my_records = await db.records.find(
        {"user_id": uid, "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1}
    ).to_list(5000)
    my_discogs = {r["discogs_id"] for r in my_records if r.get("discogs_id")}

    if not my_discogs:
        return []

    hidden_ids = await get_hidden_user_ids()
    blocked_ids = await get_all_blocked_ids(uid)
    all_exclude_ids = list(set(hidden_ids) | set(blocked_ids) | {uid})

    # Find similar collectors: users who share at least max(2, 30% of user's collection) records
    min_shared = max(2, int(len(my_discogs) * 0.3))
    pipeline = [
        {"$match": {"discogs_id": {"$in": list(my_discogs)}, "user_id": {"$nin": all_exclude_ids}}},
        {"$group": {"_id": "$user_id", "shared_count": {"$addToSet": "$discogs_id"}}},
        {"$project": {"_id": 1, "shared_records": {"$size": "$shared_count"}}},
        {"$match": {"shared_records": {"$gte": min_shared}}},
        {"$sort": {"shared_records": -1}},
        {"$limit": 30},
    ]
    similar = await db.records.aggregate(pipeline).to_list(30)
    similar_user_ids = [s["_id"] for s in similar]
    overlap_map = {s["_id"]: s["shared_records"] for s in similar}

    if not similar_user_ids:
        return []

    # Get records owned by similar collectors that the current user doesn't own
    candidate_pipeline = [
        {"$match": {
            "user_id": {"$in": similar_user_ids},
            "discogs_id": {"$nin": list(my_discogs), "$ne": None}
        }},
        {"$group": {
            "_id": "$discogs_id",
            "owner_count": {"$sum": 1},
            "record": {"$first": "$$ROOT"},
        }},
        {"$sort": {"owner_count": -1}},
        {"$limit": limit},
        {"$replaceRoot": {
            "newRoot": {"$mergeObjects": ["$record", {"owner_count": "$owner_count"}]}
        }},
        {"$project": {"_id": 0, "user_id": 0}},
    ]
    candidates = await db.records.aggregate(candidate_pipeline).to_list(limit)

    # Add reason tag and gold_only flag
    for idx, rec in enumerate(candidates):
        count = rec.get("owner_count", 1)
        rec["reason"] = f"Owned by {count} collector{'s' if count != 1 else ''} with your taste"
        rec["gold_only"] = (not is_gold) and (idx >= 4)

    return candidates


@router.get("/explore/active-isos")
async def get_active_iso_matches(user: Dict = Depends(require_auth)):
    """Get ISO matches for the current user - listings matching their wantlist"""
    hidden_ids = await get_hidden_user_ids()
    isos = await db.iso_items.find({"user_id": user["id"], "status": "OPEN"}, {"_id": 0}).to_list(50)
    if not isos:
        return []
    matches = []
    for iso in isos:
        query = {"status": "ACTIVE", "is_test_listing": {"$ne": True}, "user_id": {"$ne": user["id"], "$nin": hidden_ids}, "user_id": {"$ne": user["id"]}}
        if hidden_ids:
            query["user_id"] = {"$ne": user["id"], "$nin": hidden_ids}
        query["$or"] = [
            {"artist": {"$regex": iso["artist"], "$options": "i"}, "album": {"$regex": iso["album"], "$options": "i"}},
        ]
        if iso.get("discogs_id"):
            query["$or"].append({"discogs_id": iso["discogs_id"]})
        listings = await db.listings.find(query, {"_id": 0}).limit(5).to_list(5)
        for listing_item in listings:
            seller = await db.users.find_one({"id": listing_item["user_id"], "username": {"$ne": "demo"}, "is_hidden": {"$ne": True}}, {"_id": 0, "password_hash": 0})
            if not seller:
                continue
            listing_item["user"] = {"id": seller["id"], "username": seller.get("username"), "avatar_url": seller.get("avatar_url")}
            listing_item["matched_iso"] = {"artist": iso["artist"], "album": iso["album"]}
            matches.append(listing_item)
    return matches



@router.get("/users/{username}/taste-match")
async def get_taste_match(username: str, user: Dict = Depends(require_auth)):
    """Calculate taste match between current user and target user's collections/wishlists/ISOs."""
    target = await db.users.find_one({"username": username}, {"_id": 0, "id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target_id = target["id"]
    my_id = user["id"]

    if target_id == my_id:
        return {"score": 100, "label": None, "shared_reality": [], "shared_dreams": [], "swap_potential": []}

    # Fetch collections
    my_records = await db.records.find({"user_id": my_id}, {"_id": 0}).to_list(5000)
    their_records = await db.records.find({"user_id": target_id}, {"_id": 0}).to_list(5000)

    # Fetch wishlists/ISOs
    my_isos = await db.iso_items.find({"user_id": my_id}, {"_id": 0}).to_list(1000)
    their_isos = await db.iso_items.find({"user_id": target_id}, {"_id": 0}).to_list(1000)

    # Build lookup sets by discogs_id (most reliable) and artist
    my_discogs = {r["discogs_id"] for r in my_records if r.get("discogs_id")}
    their_discogs = {r["discogs_id"] for r in their_records if r.get("discogs_id")}
    my_artists = {r.get("artist", "").lower().strip() for r in my_records if r.get("artist")}
    their_artists = {r.get("artist", "").lower().strip() for r in their_records if r.get("artist")}

    my_wish_discogs = {i["discogs_id"] for i in my_isos if i.get("discogs_id")}
    their_wish_discogs = {i["discogs_id"] for i in their_isos if i.get("discogs_id")}
    my_wish_artists = {i.get("artist", "").lower().strip() for i in my_isos if i.get("artist")}
    their_wish_artists = {i.get("artist", "").lower().strip() for i in their_isos if i.get("artist")}

    # Shared Reality: records both own (by discogs_id)
    shared_discogs = my_discogs & their_discogs
    shared_reality = []
    seen_shared = set()
    for r in their_records:
        did = r.get("discogs_id")
        if did and did in shared_discogs and did not in seen_shared:
            seen_shared.add(did)
            shared_reality.append({"title": r.get("title"), "artist": r.get("artist"), "cover_url": r.get("cover_url"), "discogs_id": did})

    # Shared Dreams: both dreaming of same record
    shared_wish = my_wish_discogs & their_wish_discogs
    shared_dreams = []
    seen_dreams = set()
    for i in their_isos:
        did = i.get("discogs_id")
        if did and did in shared_wish and did not in seen_dreams:
            seen_dreams.add(did)
            shared_dreams.append({"title": i.get("album"), "artist": i.get("artist"), "cover_url": i.get("cover_url"), "discogs_id": did})

    # Swap Potential: they own what I'm dreaming of
    swap_discogs = my_wish_discogs & their_discogs
    swap_potential = []
    seen_swap = set()
    for r in their_records:
        did = r.get("discogs_id")
        if did and did in swap_discogs and did not in seen_swap:
            seen_swap.add(did)
            swap_potential.append({"title": r.get("title"), "artist": r.get("artist"), "cover_url": r.get("cover_url"), "discogs_id": did})

    # Calculate shared dream value from cached valuations
    shared_dream_value = 0.0
    shared_dream_discogs = my_wish_discogs & their_wish_discogs
    if shared_dream_discogs:
        async for val in db.collection_values.find({"release_id": {"$in": list(shared_dream_discogs)}}, {"_id": 0}):
            shared_dream_value += val.get("median_value", 0)

    # Calculate score — based only on owned collection overlap
    shared_artist_count = len(my_artists & their_artists)
    total_artists = len(my_artists | their_artists) or 1

    artist_score = shared_artist_count / total_artists
    record_score = len(shared_discogs) / max(len(my_discogs | their_discogs), 1)

    score = round((artist_score * 60 + record_score * 40) * 100)
    score = min(score, 100)

    label = None
    if score >= 90:
        label = "Record Soulmates"

    return {
        "score": score,
        "label": label,
        "shared_reality": shared_reality[:20],
        "shared_dreams": shared_dreams[:20],
        "swap_potential": swap_potential[:20],
        "shared_dream_value": round(shared_dream_value, 2),
    }



@router.get("/discover/my-kinda-people")
async def my_kinda_people(user: Dict = Depends(require_auth)):
    """Find users with high taste overlap for the 'My Kinda People' carousel."""
    my_id = user["id"]
    my_records = await db.records.find({"user_id": my_id}, {"_id": 0, "discogs_id": 1, "artist": 1, "cover_url": 1, "title": 1}).to_list(5000)
    my_isos = await db.iso_items.find({"user_id": my_id}, {"_id": 0, "discogs_id": 1}).to_list(1000)
    my_discogs = {r["discogs_id"] for r in my_records if r.get("discogs_id")}
    my_artists = {r.get("artist", "").lower().strip() for r in my_records if r.get("artist")}
    my_wish_discogs = {i["discogs_id"] for i in my_isos if i.get("discogs_id")}

    if not my_discogs and not my_artists:
        return []

    blocked_ids = set(await get_all_blocked_ids(my_id))

    # Get users the current user already follows
    following_ids = set()
    async for f in db.followers.find({"follower_id": my_id}, {"_id": 0, "following_id": 1}):
        following_ids.add(f["following_id"])

    # Get users who follow the current user (for "Follow Back" feature)
    follower_ids = set()
    async for f in db.followers.find({"following_id": my_id}, {"_id": 0, "follower_id": 1}):
        follower_ids.add(f["follower_id"])

    # Get all other users who have records (exclude self, blocked, and followed)
    exclude_ids = blocked_ids | following_ids
    other_user_ids = set()
    async for rec in db.records.find({"user_id": {"$ne": my_id}, "discogs_id": {"$ne": None}}, {"_id": 0, "user_id": 1}):
        if rec["user_id"] not in exclude_ids:
            other_user_ids.add(rec["user_id"])

    results = []
    for uid in list(other_user_ids)[:100]:  # cap for performance
        their_records = await db.records.find({"user_id": uid}, {"_id": 0, "discogs_id": 1, "artist": 1, "cover_url": 1, "title": 1}).to_list(5000)
        their_discogs = {r["discogs_id"] for r in their_records if r.get("discogs_id")}
        their_artists = {r.get("artist", "").lower().strip() for r in their_records if r.get("artist")}

        shared_discogs = my_discogs & their_discogs
        shared_artist_count = len(my_artists & their_artists)
        owns_my_wish = their_discogs & my_wish_discogs

        total_artists = len(my_artists | their_artists) or 1
        artist_score = shared_artist_count / total_artists
        record_score = len(shared_discogs) / max(len(my_discogs | their_discogs), 1)
        score = round((artist_score * 60 + record_score * 40) * 100)
        score = min(score, 100)

        if score < 20 and len(shared_discogs) < 1 and len(owns_my_wish) < 1:
            continue

        # Get shared album covers (up to 3)
        shared_covers = []
        for r in their_records:
            if r.get("discogs_id") in shared_discogs and r.get("cover_url"):
                shared_covers.append({"title": r.get("title"), "cover_url": r.get("cover_url")})
                if len(shared_covers) >= 3:
                    break

        # Priority: followers get a big boost, then common records, wishlist items, score
        follows_me = uid in follower_ids
        priority = (500 if follows_me else 0) + len(shared_discogs) * 10 + len(owns_my_wish) * 5 + score

        results.append({
            "user_id": uid,
            "score": score,
            "label": "Record Soulmates" if score >= 90 else None,
            "common_count": len(shared_discogs),
            "wishlist_match_count": len(owns_my_wish),
            "shared_covers": shared_covers,
            "follows_me": follows_me,
            "priority": priority,
        })

    results.sort(key=lambda x: x["priority"], reverse=True)
    results = results[:20]

    # Enrich with user data
    for r in results:
        u = await db.users.find_one({"id": r["user_id"]}, {"_id": 0, "id": 1, "username": 1, "display_name": 1, "avatar_url": 1, "founding_member": 1})
        if u:
            r["username"] = u.get("username")
            r["display_name"] = u.get("display_name")
            r["avatar_url"] = u.get("avatar_url")
            r["founding_member"] = u.get("founding_member", False)
        del r["user_id"]
        del r["priority"]

    return [r for r in results if r.get("username")]
