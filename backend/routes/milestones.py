"""Collector Milestones — achievement detection and community celebration feed."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict
from datetime import datetime, timezone
import uuid

from database import db, require_auth, get_current_user, logger

router = APIRouter()

MILESTONES = {
    "collection_10":  {"label": "First 10 Records", "emoji": "🎶", "threshold": 10},
    "collection_25":  {"label": "25 Records Deep",  "emoji": "🎵", "threshold": 25},
    "collection_50":  {"label": "50 Record Club",   "emoji": "🏅", "threshold": 50},
    "collection_100": {"label": "Century Club",      "emoji": "💯", "threshold": 100},
    "collection_250": {"label": "250 Crates",        "emoji": "📦", "threshold": 250},
    "collection_500": {"label": "500 Vaults",        "emoji": "🏆", "threshold": 500},
    "first_spin":     {"label": "First Spin",        "emoji": "🎸"},
    "streak_7":       {"label": "7-Day Streak",      "emoji": "🔥"},
    "streak_30":      {"label": "30-Day Streak",     "emoji": "⚡"},
    "first_haul":     {"label": "First Haul",        "emoji": "🛍️"},
    "first_room":     {"label": "Joined First Room", "emoji": "🍯"},
}


async def _award_milestone(user_id: str, milestone_type: str) -> Optional[Dict]:
    """Award a milestone if not already earned. Returns the milestone doc or None."""
    if milestone_type not in MILESTONES:
        return None
    existing = await db.milestones.find_one({"userId": user_id, "type": milestone_type})
    if existing:
        return None
    m = MILESTONES[milestone_type]
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "userId": user_id,
        "type": milestone_type,
        "label": m["label"],
        "emoji": m["emoji"],
        "achieved_at": now,
        "react_count": 0,
    }
    try:
        await db.milestones.insert_one(doc)
        logger.info(f"Milestone awarded: {user_id} → {milestone_type}")
    except Exception:
        return None  # Duplicate key — already awarded
    return doc


async def check_collection_milestones(user_id: str, new_count: int):
    """Called after a record is added. Awards any newly crossed collection size milestones."""
    for key, m in MILESTONES.items():
        if not key.startswith("collection_"):
            continue
        threshold = m.get("threshold", 0)
        if new_count >= threshold:
            await _award_milestone(user_id, key)


async def check_spin_milestones(user_id: str):
    """Called after a spin post is created. Awards first_spin milestone."""
    spin_count = await db.spins.count_documents({"user_id": user_id})
    if spin_count == 1:
        await _award_milestone(user_id, "first_spin")


async def check_haul_milestone(user_id: str):
    """Called after a haul post is created. Awards first_haul milestone."""
    haul_count = await db.posts.count_documents({"user_id": user_id, "post_type": "haul"})
    if haul_count == 1:
        await _award_milestone(user_id, "first_haul")


async def check_room_milestone(user_id: str):
    """Called after joining a room. Awards first_room milestone."""
    room_count = await db.room_members.count_documents({"userId": user_id})
    if room_count == 1:
        await _award_milestone(user_id, "first_room")


@router.get("/milestones/feed")
async def get_milestones_feed(limit: int = 20):
    """Return recent milestones across all users, most recent first."""
    milestones = await db.milestones.find(
        {}, {"_id": 0}
    ).sort("achieved_at", -1).limit(limit).to_list(limit)

    user_ids = list({m["userId"] for m in milestones})
    users = await db.users.find(
        {"id": {"$in": user_ids}},
        {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
    ).to_list(len(user_ids) if user_ids else 1)
    users_map = {u["id"]: u for u in users}

    result = []
    for m in milestones:
        user = users_map.get(m["userId"])
        if not user:
            continue
        result.append({
            "id": m["id"],
            "type": m["type"],
            "label": m["label"],
            "emoji": m["emoji"],
            "achieved_at": m["achieved_at"],
            "react_count": m.get("react_count", 0),
            "username": user.get("username"),
            "avatar_url": user.get("avatar_url"),
        })
    return result


@router.post("/milestones/{milestone_id}/react")
async def react_to_milestone(milestone_id: str, current_user: Dict = Depends(require_auth)):
    """React with congrats to a milestone."""
    milestone = await db.milestones.find_one({"id": milestone_id}, {"_id": 0})
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    await db.milestones.update_one(
        {"id": milestone_id},
        {"$inc": {"react_count": 1}}
    )
    return {"success": True}
