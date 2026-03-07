"""Unified global search — records, collectors, posts, listings."""
from fastapi import APIRouter, Query, Depends
from typing import Dict, List
from datetime import datetime, timezone

from database import db, require_auth, search_discogs, get_hidden_user_ids, logger

router = APIRouter()


def _score(text: str, words: list[str]) -> int:
    """Score a text string against search words. Higher = better match."""
    if not text:
        return 0
    low = text.lower()
    score = 0
    for w in words:
        if low == w:
            score += 100
        elif low.startswith(w):
            score += 60
        elif f" {w}" in f" {low}":
            score += 40
        elif w in low:
            score += 20
    return score


def _record_score(rec: dict, words: list[str]) -> int:
    return _score(rec.get("artist", ""), words) + _score(rec.get("title", ""), words)


def _user_score(u: dict, words: list[str]) -> int:
    return _score(u.get("username", ""), words) + _score(u.get("bio", ""), words) * 0.5


def _post_score(p: dict, words: list[str]) -> int:
    return _score(p.get("caption", "") or p.get("content", ""), words)


def _listing_score(listing: dict, words: list[str]) -> int:
    return _score(listing.get("artist", ""), words) + _score(listing.get("album", ""), words)


def _build_regex_filter(q: str) -> dict:
    """Build an OR regex filter matching any word in the query."""
    words = q.strip().split()
    patterns = []
    for w in words:
        patterns.append({"$regex": w, "$options": "i"})
    return patterns


@router.get("/search/unified")
async def unified_search(q: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    """Fast unified search across records, users, posts, and listings."""
    hidden_ids = await get_hidden_user_ids()
    words = [w.lower() for w in q.strip().split() if len(w) >= 1]
    if not words:
        return {"records": [], "collectors": [], "posts": [], "listings": []}

    regex_patterns = _build_regex_filter(q)

    # Build per-word OR conditions for each field
    def field_or(field: str):
        return [{ field: p } for p in regex_patterns]

    # --- Records (from user collections) ---
    rec_filter = {"$or": field_or("artist") + field_or("title")}
    records_cursor = db.records.find(rec_filter, {"_id": 0}).limit(50)
    raw_records = await records_cursor.to_list(50)

    # Deduplicate by discogs_id, pick first occurrence
    seen_discogs = set()
    unique_records = []
    for r in raw_records:
        did = r.get("discogs_id")
        key = did if did else r.get("id")
        if key not in seen_discogs:
            seen_discogs.add(key)
            unique_records.append(r)

    scored_records = sorted(unique_records, key=lambda r: _record_score(r, words), reverse=True)[:12]
    records_out = [{
        "discogs_id": r.get("discogs_id"),
        "title": r.get("title", ""),
        "artist": r.get("artist", ""),
        "cover_url": r.get("cover_url"),
        "year": r.get("year"),
        "format": r.get("format"),
        "label": r.get("label"),
        "catno": r.get("catno"),
        "country": r.get("country"),
        "color_variant": r.get("color_variant"),
        "source": "collection",
    } for r in scored_records]

    # --- Collectors ---
    user_filter = {
        "$or": field_or("username") + field_or("bio") + field_or("location"),
        "is_hidden": {"$ne": True},
    }
    if hidden_ids:
        user_filter["id"] = {"$nin": hidden_ids}
    raw_users = await db.users.find(
        user_filter, {"_id": 0, "password_hash": 0}
    ).limit(20).to_list(20)

    scored_users = sorted(raw_users, key=lambda u: _user_score(u, words), reverse=True)[:12]

    # Batch fetch record counts & following status
    user_ids = [u["id"] for u in scored_users]
    rec_counts = {}
    if user_ids:
        pipeline = [
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        ]
        async for doc in db.records.aggregate(pipeline):
            rec_counts[doc["_id"]] = doc["count"]

    following_set = set()
    if user_ids:
        follows = await db.followers.find(
            {"follower_id": user["id"], "following_id": {"$in": user_ids}},
            {"_id": 0, "following_id": 1}
        ).to_list(len(user_ids))
        following_set = {f["following_id"] for f in follows}

    collectors_out = [{
        "id": u["id"],
        "username": u["username"],
        "avatar_url": u.get("avatar_url"),
        "bio": u.get("bio"),
        "record_count": rec_counts.get(u["id"], 0),
        "is_following": u["id"] in following_set,
    } for u in scored_users]

    # --- Posts ---
    post_or = field_or("caption") + field_or("content")
    post_filter = {"$or": post_or}
    if hidden_ids:
        post_filter["user_id"] = {"$nin": hidden_ids}
    raw_posts = await db.posts.find(
        post_filter, {"_id": 0}
    ).sort("created_at", -1).limit(30).to_list(30)

    scored_posts = sorted(raw_posts, key=lambda p: _post_score(p, words), reverse=True)[:12]

    # Batch fetch post authors
    author_ids = list({p.get("user_id") for p in scored_posts if p.get("user_id")})
    authors = {}
    if author_ids:
        async for u in db.users.find({"id": {"$in": author_ids}}, {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}):
            authors[u["id"]] = u

    posts_out = [{
        "id": p.get("id"),
        "post_type": p.get("post_type") or p.get("type"),
        "caption": (p.get("caption") or p.get("content") or "")[:120],
        "created_at": p.get("created_at"),
        "user": authors.get(p.get("user_id")),
    } for p in scored_posts]

    # --- Listings ---
    listing_or = field_or("artist") + field_or("album") + field_or("description")
    listing_filter = {"status": "ACTIVE", "$or": listing_or}
    if hidden_ids:
        listing_filter["user_id"] = {"$nin": hidden_ids}
    raw_listings = await db.listings.find(
        listing_filter, {"_id": 0}
    ).sort("created_at", -1).limit(30).to_list(30)

    scored_listings = sorted(raw_listings, key=lambda item: _listing_score(item, words), reverse=True)[:12]

    # Batch fetch listing sellers
    seller_ids = list({ls.get("user_id") for ls in scored_listings if ls.get("user_id")})
    sellers = {}
    if seller_ids:
        async for u in db.users.find({"id": {"$in": seller_ids}}, {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}):
            sellers[u["id"]] = u

    listings_out = [{
        "id": ls.get("id"),
        "artist": ls.get("artist", ""),
        "album": ls.get("album", ""),
        "cover_url": ls.get("cover_url"),
        "price": ls.get("price"),
        "condition": ls.get("condition"),
        "listing_type": ls.get("listing_type"),
        "seller": sellers.get(ls.get("user_id")),
    } for ls in scored_listings]

    return {
        "records": records_out,
        "collectors": collectors_out,
        "posts": posts_out,
        "listings": listings_out,
    }


@router.get("/search/discogs")
async def search_discogs_external(q: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    """Search Discogs catalog (external API). Separated for non-blocking use."""
    import asyncio
    results = await asyncio.to_thread(search_discogs, q)
    return results[:20]
