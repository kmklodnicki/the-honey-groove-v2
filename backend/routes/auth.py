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

# ============== AUTH ROUTES ==============

@router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    existing_username = await db.users.find_one({"username": user_data.username.lower()})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username.lower(),
        "password_hash": hash_password(user_data.password),
        "avatar_url": f"https://api.dicebear.com/7.x/miniavs/svg?seed={user_data.username}",
        "bio": None,
        "created_at": now
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            username=user_data.username.lower(),
            avatar_url=user_doc["avatar_url"],
            bio=None,
            created_at=now,
            collection_count=0,
            spin_count=0,
            followers_count=0,
            following_count=0
        )
    )

@router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"])
    
    # Get counts
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    spin_count = await db.spins.count_documents({"user_id": user["id"]})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})
    following_count = await db.followers.count_documents({"follower_id": user["id"]})
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            avatar_url=user.get("avatar_url"),
            bio=user.get("bio"),
            created_at=user["created_at"],
            collection_count=collection_count,
            spin_count=spin_count,
            followers_count=followers_count,
            following_count=following_count
        )
    )

@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: Dict = Depends(require_auth)):
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    spin_count = await db.spins.count_documents({"user_id": user["id"]})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})
    following_count = await db.followers.count_documents({"follower_id": user["id"]})
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        avatar_url=user.get("avatar_url"),
        bio=user.get("bio"),
        created_at=user["created_at"],
        collection_count=collection_count,
        spin_count=spin_count,
        followers_count=followers_count,
        following_count=following_count
    )

@router.put("/auth/me", response_model=UserResponse)
async def update_me(update_data: UserUpdate, user: Dict = Depends(require_auth)):
    update_fields = {}
    if update_data.username:
        existing = await db.users.find_one({"username": update_data.username.lower(), "id": {"$ne": user["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_fields["username"] = update_data.username.lower()
    if update_data.bio is not None:
        update_fields["bio"] = update_data.bio
    if update_data.avatar_url is not None:
        update_fields["avatar_url"] = update_data.avatar_url
    
    if update_fields:
        await db.users.update_one({"id": user["id"]}, {"$set": update_fields})
    
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    spin_count = await db.spins.count_documents({"user_id": user["id"]})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})
    following_count = await db.followers.count_documents({"follower_id": user["id"]})
    
    return UserResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        username=updated_user["username"],
        avatar_url=updated_user.get("avatar_url"),
        bio=updated_user.get("bio"),
        created_at=updated_user["created_at"],
        collection_count=collection_count,
        spin_count=spin_count,
        followers_count=followers_count,
        following_count=following_count
    )


# ============== USER ROUTES ==============

@router.get("/users/discover/suggestions")
async def get_suggested_users(user: Dict = Depends(require_auth)):
    """Get suggested users to follow (users not already followed)"""
    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0}).to_list(1000)
    following_ids = [f["following_id"] for f in following]
    following_ids.append(user["id"])
    
    all_users = await db.users.find(
        {"id": {"$nin": following_ids}},
        {"_id": 0, "password_hash": 0}
    ).to_list(50)
    
    suggestions = []
    for u in all_users:
        record_count = await db.records.count_documents({"user_id": u["id"]})
        suggestions.append({
            "id": u["id"],
            "username": u["username"],
            "avatar_url": u.get("avatar_url"),
            "bio": u.get("bio"),
            "record_count": record_count,
            "is_following": False
        })
    
    suggestions.sort(key=lambda x: x["record_count"], reverse=True)
    return suggestions[:20]

@router.get("/users/search")
async def search_users_q(query: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    users = await db.users.find(
        {"username": {"$regex": query, "$options": "i"}},
        {"_id": 0, "password_hash": 0}
    ).limit(20).to_list(20)
    result = []
    for u in users:
        is_following = await db.followers.find_one({"follower_id": user["id"], "following_id": u["id"]}) is not None
        result.append({
            "id": u["id"],
            "username": u["username"],
            "avatar_url": u.get("avatar_url"),
            "bio": u.get("bio"),
            "is_following": is_following
        })
    return result

@router.get("/users/{username}", response_model=UserResponse)
async def get_user_profile(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    spin_count = await db.spins.count_documents({"user_id": user["id"]})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})
    following_count = await db.followers.count_documents({"follower_id": user["id"]})
    
    return UserResponse(
        id=user["id"],
        email=user["email"] if current_user and current_user["id"] == user["id"] else "",
        username=user["username"],
        avatar_url=user.get("avatar_url"),
        bio=user.get("bio"),
        created_at=user["created_at"],
        collection_count=collection_count,
        spin_count=spin_count,
        followers_count=followers_count,
        following_count=following_count
    )

