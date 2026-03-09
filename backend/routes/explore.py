from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from database import db, require_auth, get_current_user, security, logger, create_notification, get_hidden_user_ids
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT
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


router = APIRouter()

# ============== BUZZING NOW (Trending) ROUTES ==============

@router.get("/buzzing")
async def get_buzzing_records(current_user: Optional[Dict] = Depends(get_current_user), limit: int = 10):
    """Get trending/buzzing records based on recent spins"""
    hidden_ids = await get_hidden_user_ids()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    match_filter = {"created_at": {"$gte": week_ago}}
    if hidden_ids:
        match_filter["user_id"] = {"$nin": hidden_ids}
    
    pipeline = [
        {"$match": match_filter},
        {"$group": {"_id": "$record_id", "spin_count": {"$sum": 1}}},
        {"$sort": {"spin_count": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "records",
            "localField": "_id",
            "foreignField": "id",
            "as": "record"
        }},
        {"$unwind": "$record"},
        {"$replaceRoot": {
            "newRoot": {
                "$mergeObjects": ["$record", {"trending_spins": "$spin_count"}]
            }
        }},
        {"$project": {"_id": 0}}
    ]
    
    result = await db.spins.aggregate(pipeline).to_list(limit)
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
    if target_user.get("email"):
        tpl = email_tpl.new_follow(u.get("username", "?"), f"{FRONTEND_URL}/profile/{u.get('username','')}")
        await send_email_fire_and_forget(target_user["email"], tpl["subject"], tpl["html"])

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
    
    isos = await db.iso_items.find({"user_id": target["id"], "status": {"$ne": "WISHLIST"}}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return isos


@router.get("/users/{username}/dreaming")
async def get_user_dreaming(username: str):
    """Get a user's wishlist/dreaming items."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    items = await db.iso_items.find({"user_id": target["id"], "status": "WISHLIST"}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return items

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
    hidden_ids = await get_hidden_user_ids()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    spin_match = {"created_at": {"$gte": cutoff}}
    if hidden_ids:
        spin_match["user_id"] = {"$nin": hidden_ids}
    pipeline = [
        {"$match": spin_match},
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
                    "cover_url": item.get("cover_image"),
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
    """Get collectors and listings in the same city/region"""
    hidden_ids = await get_hidden_user_ids()
    my_city = user.get("city", "").strip().lower()
    my_region = user.get("region", "").strip().lower()
    if not my_city and not my_region:
        return {"collectors": [], "listings": [], "needs_location": True}

    query = {"id": {"$ne": user["id"]}, "username": {"$ne": "demo"}, "email": {"$not": {"$regex": "(example|test)\\.com$", "$options": "i"}}}
    if hidden_ids:
        query["id"] = {"$ne": user["id"], "$nin": hidden_ids}
    conditions = []
    if my_city:
        conditions.append({"city": {"$regex": f"^{my_city}$", "$options": "i"}})
    if my_region:
        conditions.append({"region": {"$regex": f"^{my_region}$", "$options": "i"}})
    if conditions:
        query["$or"] = conditions

    nearby_users = await db.users.find(query, {"_id": 0, "password_hash": 0}).limit(collector_limit).to_list(collector_limit)
    collectors = []
    for u in nearby_users:
        rec_count = await db.records.count_documents({"user_id": u["id"]})
        listing_count = await db.listings.count_documents({"user_id": u["id"], "status": "ACTIVE"})
        collectors.append({
            "id": u["id"], "username": u.get("username"), "avatar_url": u.get("avatar_url"),
            "city": u.get("city"), "region": u.get("region"),
            "collection_count": rec_count, "active_listings": listing_count,
        })

    nearby_ids = [u["id"] for u in nearby_users]
    listings = []
    if nearby_ids:
        listings = await db.listings.find(
            {"user_id": {"$in": nearby_ids}, "status": "ACTIVE"}, {"_id": 0}
        ).sort("created_at", -1).limit(listing_limit).to_list(listing_limit)
        for l in listings:
            seller = next((u for u in collectors if u["id"] == l["user_id"]), None)
            l["user"] = {"username": seller["username"], "city": seller.get("city")} if seller else None

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
    """Suggest collectors based on collection overlap (shared artists)"""
    hidden_ids = await get_hidden_user_ids()
    my_records = await db.records.find({"user_id": user["id"]}, {"_id": 0, "artist": 1}).to_list(500)
    my_artists = list({r["artist"] for r in my_records})

    # Hard filter: never show demo/test/hidden users
    user_exclude = {"username": {"$ne": "demo"}, "email": {"$not": {"$regex": "(example|test)\\.com$", "$options": "i"}}, "is_hidden": {"$ne": True}, "is_test": {"$ne": True}}

    if not my_artists:
        return await db.users.find(
            {"id": {"$ne": user["id"], "$nin": hidden_ids}, **user_exclude}, {"_id": 0, "password_hash": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)

    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0, "following_id": 1}).to_list(500)
    following_ids = {f["following_id"] for f in following}
    following_ids.add(user["id"])
    all_exclude_ids = list(following_ids | set(hidden_ids))

    pipeline = [
        {"$match": {"artist": {"$in": my_artists[:20]}, "user_id": {"$nin": all_exclude_ids}}},
        {"$group": {"_id": "$user_id", "overlap": {"$sum": 1}}},
        {"$match": {"overlap": {"$gte": 3}}},
        {"$sort": {"overlap": -1}},
        {"$limit": limit},
    ]
    agg = await db.records.aggregate(pipeline).to_list(limit)
    user_ids = [a["_id"] for a in agg]
    overlap_map = {a["_id"]: a["overlap"] for a in agg}
    if not user_ids:
        return []
    users = await db.users.find({"id": {"$in": user_ids}, **user_exclude}, {"_id": 0, "password_hash": 0}).to_list(limit)
    for u in users:
        u["shared_artists"] = overlap_map.get(u["id"], 0)
    users.sort(key=lambda x: x.get("shared_artists", 0), reverse=True)
    return users


@router.get("/explore/active-isos")
async def get_active_iso_matches(user: Dict = Depends(require_auth)):
    """Get ISO matches for the current user - listings matching their wantlist"""
    hidden_ids = await get_hidden_user_ids()
    isos = await db.iso_items.find({"user_id": user["id"], "status": "OPEN"}, {"_id": 0}).to_list(50)
    if not isos:
        return []
    matches = []
    for iso in isos:
        query = {"status": "ACTIVE", "user_id": {"$ne": user["id"], "$nin": hidden_ids}, "user_id": {"$ne": user["id"]}}
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

    # Calculate score
    shared_artist_count = len(my_artists & their_artists)
    shared_wish_artist_count = len(my_wish_artists & their_wish_artists)
    total_artists = len(my_artists | their_artists) or 1
    total_wish_artists = len(my_wish_artists | their_wish_artists) or 1

    artist_score = shared_artist_count / total_artists
    record_score = len(shared_discogs) / max(len(my_discogs | their_discogs), 1)
    wish_score = shared_wish_artist_count / total_wish_artists

    score = round((artist_score * 50 + record_score * 30 + wish_score * 20) * 100)
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

    # Get all other users who have records
    other_user_ids = set()
    async for rec in db.records.find({"user_id": {"$ne": my_id}, "discogs_id": {"$ne": None}}, {"_id": 0, "user_id": 1}):
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

        # Priority: common realities >= 3, then owns wishlist items, then score
        priority = len(shared_discogs) * 10 + len(owns_my_wish) * 5 + score

        results.append({
            "user_id": uid,
            "score": score,
            "label": "Record Soulmates" if score >= 90 else None,
            "common_count": len(shared_discogs),
            "wishlist_match_count": len(owns_my_wish),
            "shared_covers": shared_covers,
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
