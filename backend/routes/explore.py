from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from database import db, require_auth, get_current_user, security, logger, create_notification
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, PLATFORM_FEE_PERCENT, FRONTEND_URL
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from database import oauth_request_tokens, import_progress, EMERGENT_KEY
from models import *


router = APIRouter()

# ============== BUZZING NOW (Trending) ROUTES ==============

@router.get("/buzzing")
async def get_buzzing_records(current_user: Optional[Dict] = Depends(get_current_user), limit: int = 10):
    """Get trending/buzzing records based on recent spins"""
    # Get spins from last 7 days
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    pipeline = [
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {"_id": "$record_id", "spin_count": {"$sum": 1}}},
        {"$sort": {"spin_count": -1}},
        {"$limit": limit}
    ]
    
    trending = await db.spins.aggregate(pipeline).to_list(limit)
    
    result = []
    for item in trending:
        record = await db.records.find_one({"id": item["_id"]}, {"_id": 0})
        if record:
            result.append({
                **record,
                "buzz_count": item["spin_count"]
            })
    
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
                              {"follower_username": u.get("username")})

    return {"message": f"Now following {username}"}

@router.delete("/follow/{username}")
async def unfollow_user(username: str, user: Dict = Depends(require_auth)):
    target_user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.followers.delete_one({
        "follower_id": user["id"],
        "following_id": target_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Not following this user")
    
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
    
    return {"is_following": existing is not None}

@router.get("/users/{username}/followers")
async def get_followers(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    followers = await db.followers.find({"following_id": user["id"]}, {"_id": 0}).to_list(1000)
    
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
            result.append({
                "id": follower_user["id"],
                "username": follower_user["username"],
                "avatar_url": follower_user.get("avatar_url"),
                "bio": follower_user.get("bio"),
                "is_following": is_following
            })
    
    return result

@router.get("/users/{username}/following")
async def get_following(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0}).to_list(1000)
    
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
            result.append({
                "id": following_user["id"],
                "username": following_user["username"],
                "avatar_url": following_user.get("avatar_url"),
                "bio": following_user.get("bio"),
                "is_following": is_following
            })
    
    return result


# ============== PROFILE DATA ROUTES ==============

@router.get("/users/{username}/spins")
async def get_user_spins(username: str, limit: int = 50):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    spins = await db.spins.find({"user_id": target["id"]}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    result = []
    for spin in spins:
        record = await db.records.find_one({"id": spin["record_id"]}, {"_id": 0})
        if record:
            result.append({**spin, "record": record})
    return result

@router.get("/users/{username}/iso")
async def get_user_isos(username: str):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    isos = await db.iso_items.find({"user_id": target["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return isos

@router.get("/users/{username}/posts")
async def get_user_posts(username: str, current_user: Optional[Dict] = Depends(get_current_user), limit: int = 50):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    posts = await db.posts.find({"user_id": target["id"]}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    result = []
    uid = current_user["id"] if current_user else None
    for post in posts:
        resp = await build_post_response(post, uid)
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
    """Trending records: most spun + most added in last 14 days"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$record_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    spin_agg = await db.spins.aggregate(pipeline).to_list(limit)
    record_ids = [s["_id"] for s in spin_agg]
    counts = {s["_id"]: s["count"] for s in spin_agg}
    records = await db.records.find({"id": {"$in": record_ids}}, {"_id": 0}).to_list(limit)
    result = []
    for r in records:
        r["trending_spins"] = counts.get(r["id"], 0)
        result.append(r)
    result.sort(key=lambda x: x["trending_spins"], reverse=True)
    return result


@router.get("/explore/recent-hauls")
async def get_recent_hauls(limit: int = 10, user: Dict = Depends(require_auth)):
    """Recent haul posts from the community"""
    posts = await db.posts.find(
        {"post_type": "NEW_HAUL"}, {"_id": 0}
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
    """Suggest collectors based on collection overlap (shared artists)"""
    my_records = await db.records.find({"user_id": user["id"]}, {"_id": 0, "artist": 1}).to_list(500)
    my_artists = list({r["artist"] for r in my_records})
    if not my_artists:
        return await db.users.find(
            {"id": {"$ne": user["id"]}}, {"_id": 0, "password_hash": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)

    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0, "following_id": 1}).to_list(500)
    following_ids = {f["following_id"] for f in following}
    following_ids.add(user["id"])

    pipeline = [
        {"$match": {"artist": {"$in": my_artists[:20]}, "user_id": {"$nin": list(following_ids)}}},
        {"$group": {"_id": "$user_id", "overlap": {"$sum": 1}}},
        {"$sort": {"overlap": -1}},
        {"$limit": limit},
    ]
    agg = await db.records.aggregate(pipeline).to_list(limit)
    user_ids = [a["_id"] for a in agg]
    overlap_map = {a["_id"]: a["overlap"] for a in agg}
    if not user_ids:
        return []
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(limit)
    for u in users:
        u["shared_artists"] = overlap_map.get(u["id"], 0)
    users.sort(key=lambda x: x.get("shared_artists", 0), reverse=True)
    return users


@router.get("/explore/active-isos")
async def get_active_iso_matches(user: Dict = Depends(require_auth)):
    """Get ISO matches for the current user - listings matching their wantlist"""
    isos = await db.iso_items.find({"user_id": user["id"], "status": "OPEN"}, {"_id": 0}).to_list(50)
    if not isos:
        return []
    matches = []
    for iso in isos:
        query = {"status": "ACTIVE", "user_id": {"$ne": user["id"]}}
        query["$or"] = [
            {"artist": {"$regex": iso["artist"], "$options": "i"}, "album": {"$regex": iso["album"], "$options": "i"}},
        ]
        if iso.get("discogs_id"):
            query["$or"].append({"discogs_id": iso["discogs_id"]})
        listings = await db.listings.find(query, {"_id": 0}).limit(5).to_list(5)
        for l in listings:
            seller = await db.users.find_one({"id": l["user_id"]}, {"_id": 0, "password_hash": 0})
            l["user"] = {"id": seller["id"], "username": seller.get("username"), "avatar_url": seller.get("avatar_url")} if seller else None
            l["matched_iso"] = {"artist": iso["artist"], "album": iso["album"]}
            matches.append(l)
    return matches
