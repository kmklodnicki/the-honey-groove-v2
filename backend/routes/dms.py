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

# ============== DIRECT MESSAGES ROUTES ==============

class DMCreate(BaseModel):
    recipient_id: str
    text: str
    context: Optional[Dict[str, Any]] = None  # {type: "iso"|"trade"|"listing", record_name, action_text}

class DMSend(BaseModel):
    text: str

@router.post("/dm/conversations")
async def create_or_get_conversation(data: DMCreate, user: Dict = Depends(require_auth)):
    """Create a new conversation or get existing one between two users, send initial message"""
    if data.recipient_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot message yourself")
    recipient = await db.users.find_one({"id": data.recipient_id}, {"_id": 0, "password_hash": 0})
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")

    pair = sorted([user["id"], data.recipient_id])
    conv = await db.dm_conversations.find_one({"participant_ids": pair}, {"_id": 0})

    now = datetime.now(timezone.utc).isoformat()
    if not conv:
        conv = {
            "id": str(uuid.uuid4()),
            "participant_ids": pair,
            "participants": {},
            "context": data.context,
            "last_message": None,
            "last_message_at": now,
            "created_at": now,
        }
        await db.dm_conversations.insert_one(conv)

    # Send the first message
    msg = {
        "id": str(uuid.uuid4()),
        "conversation_id": conv["id"],
        "sender_id": user["id"],
        "text": data.text,
        "read": False,
        "created_at": now,
    }
    await db.dm_messages.insert_one(msg)
    await db.dm_conversations.update_one({"id": conv["id"]}, {"$set": {
        "last_message": data.text, "last_message_at": now,
        "context": data.context or conv.get("context"),
    }})

    # Notify recipient
    await create_notification(data.recipient_id, "dm", "New message",
        f"@{user['username']} sent you a message", {"conversation_id": conv["id"], "sender_id": user["id"]})

    return {"conversation_id": conv["id"]}


@router.get("/dm/conversations")
async def list_conversations(user: Dict = Depends(require_auth)):
    """List all conversations for the current user"""
    convs = await db.dm_conversations.find(
        {"participant_ids": user["id"]}, {"_id": 0}
    ).sort("last_message_at", -1).to_list(100)

    user_ids = set()
    for c in convs:
        for pid in c["participant_ids"]:
            user_ids.add(pid)
    users_map = {}
    if user_ids:
        users_list = await db.users.find({"id": {"$in": list(user_ids)}}, {"_id": 0, "password_hash": 0}).to_list(200)
        users_map = {u["id"]: {"id": u["id"], "username": u.get("username"), "avatar_url": u.get("avatar_url")} for u in users_list}

    result = []
    for c in convs:
        other_id = [pid for pid in c["participant_ids"] if pid != user["id"]]
        other_user = users_map.get(other_id[0]) if other_id else None
        unread = await db.dm_messages.count_documents({"conversation_id": c["id"], "sender_id": {"$ne": user["id"]}, "read": False})
        result.append({
            "id": c["id"],
            "other_user": other_user,
            "last_message": c.get("last_message"),
            "last_message_at": c.get("last_message_at"),
            "context": c.get("context"),
            "unread_count": unread,
        })
    return result


@router.get("/dm/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: Dict = Depends(require_auth)):
    """Get a conversation with messages"""
    conv = await db.dm_conversations.find_one({"id": conversation_id, "participant_ids": user["id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await db.dm_messages.find({"conversation_id": conversation_id}, {"_id": 0}).sort("created_at", 1).to_list(200)

    # Mark messages from other user as read
    await db.dm_messages.update_many(
        {"conversation_id": conversation_id, "sender_id": {"$ne": user["id"]}, "read": False},
        {"$set": {"read": True}}
    )

    other_id = [pid for pid in conv["participant_ids"] if pid != user["id"]]
    other_user = None
    if other_id:
        u = await db.users.find_one({"id": other_id[0]}, {"_id": 0, "password_hash": 0})
        if u:
            other_user = {"id": u["id"], "username": u.get("username"), "avatar_url": u.get("avatar_url")}

    return {
        "id": conv["id"],
        "other_user": other_user,
        "context": conv.get("context"),
        "messages": messages,
    }


@router.post("/dm/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, data: DMSend, user: Dict = Depends(require_auth)):
    """Send a message in an existing conversation"""
    conv = await db.dm_conversations.find_one({"id": conversation_id, "participant_ids": user["id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    now = datetime.now(timezone.utc).isoformat()
    msg = {
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "sender_id": user["id"],
        "text": data.text,
        "read": False,
        "created_at": now,
    }
    await db.dm_messages.insert_one(msg)
    await db.dm_conversations.update_one({"id": conversation_id}, {"$set": {"last_message": data.text, "last_message_at": now}})

    # Notify the other participant
    other_id = [pid for pid in conv["participant_ids"] if pid != user["id"]]
    if other_id:
        await create_notification(other_id[0], "dm", "New message",
            f"@{user['username']}: {data.text[:60]}", {"conversation_id": conversation_id, "sender_id": user["id"]})

    return {"id": msg["id"], "text": msg["text"], "sender_id": msg["sender_id"], "created_at": msg["created_at"]}


@router.get("/dm/unread-count")
async def dm_unread_count(user: Dict = Depends(require_auth)):
    """Get total unread DM count"""
    count = await db.dm_messages.count_documents({"sender_id": {"$ne": user["id"]}, "read": False,
        "conversation_id": {"$in": [c["id"] for c in await db.dm_conversations.find({"participant_ids": user["id"]}, {"_id": 0, "id": 1}).to_list(200)]}
    })
    return {"count": count}


@router.get("/dm/conversation-with/{user_id}")
async def get_conversation_with_user(user_id: str, user: Dict = Depends(require_auth)):
    """Check if a conversation exists with a specific user"""
    pair = sorted([user["id"], user_id])
    conv = await db.dm_conversations.find_one({"participant_ids": pair}, {"_id": 0})
    if conv:
        return {"conversation_id": conv["id"]}
    return {"conversation_id": None}


@router.get("/users/by-id/{user_id}")
async def get_user_by_id(user_id: str, user: Dict = Depends(require_auth)):
    """Get basic user info by ID"""
    target = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": target["id"], "username": target.get("username"), "avatar_url": target.get("avatar_url")}


