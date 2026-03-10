"""Unified global search — records, collectors, posts, listings, variants."""
from fastapi import APIRouter, Query, Depends
from typing import Dict, List, Optional
from datetime import datetime, timezone
import asyncio
import os
import requests as req

from database import db, require_auth, get_current_user, search_discogs, get_hidden_user_ids, logger

router = APIRouter()

DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN", "")
DISCOGS_HEADERS = {"User-Agent": "WaxLog/1.0"}


def _fetch_artist_image_from_discogs(name: str) -> Optional[str]:
    """Search Discogs for an artist and return their image URL."""
    try:
        params = {"token": DISCOGS_TOKEN, "q": name, "type": "artist", "per_page": 1}
        r = req.get("https://api.discogs.com/database/search", params=params, headers=DISCOGS_HEADERS, timeout=8)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                return results[0].get("cover_image") or results[0].get("thumb") or None
    except Exception as e:
        logger.error(f"Discogs artist image fetch error for '{name}': {e}")
    return None


async def _get_artist_image(name: str) -> Optional[str]:
    """Get artist image URL with MongoDB cache."""
    cached = await db.artist_images.find_one({"name_lower": name.lower()}, {"_id": 0, "image_url": 1})
    if cached:
        return cached.get("image_url")

    # Fetch from Discogs
    url = await asyncio.to_thread(_fetch_artist_image_from_discogs, name)
    await db.artist_images.update_one(
        {"name_lower": name.lower()},
        {"$set": {"name_lower": name.lower(), "name": name, "image_url": url, "fetched_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return url


import re as _re_module


def _normalize_artist_name(name: str) -> str:
    """Normalize an artist name for deduplication."""
    # lowercase, strip whitespace, remove trailing punctuation
    n = name.lower().strip()
    n = _re_module.sub(r'[,;.!?]+$', '', n).strip()
    return n


def _split_artists(artist_field: str) -> list[str]:
    """Split a multi-artist field into individual canonical artist names."""
    if not artist_field:
        return []
    # Split on comma, ampersand, " and ", " with ", " feat. ", " ft. ", " featuring "
    parts = _re_module.split(r'\s*[,&]\s*|\s+(?:and|with|feat\.?|ft\.?|featuring)\s+', artist_field, flags=_re_module.IGNORECASE)
    # Return non-empty trimmed names
    return [p.strip() for p in parts if p.strip()]


def _score(text: str, words: list[str]) -> int:
    """Score a text string against search words. Higher = better match."""
    if not text:
        return 0
    low = text.lower()
    query_full = " ".join(words)
    score = 0
    if low == query_full:
        score += 100
    elif low.startswith(query_full):
        score += 70
    else:
        for w in words:
            if low == w:
                score += 60
            elif low.startswith(w):
                score += 40
            elif f" {w}" in f" {low}":
                score += 25
            elif w in low:
                score += 10
    return score


def _variant_score(rec: dict, words: list[str]) -> int:
    """Variant-first scoring: variant > color > album > artist."""
    query_full = " ".join(words)
    s = 0
    variant = (rec.get("color_variant") or "").lower()
    artist = (rec.get("artist") or "").lower()
    title = (rec.get("title") or "").lower()

    # Exact variant match — highest priority
    if variant and variant == query_full:
        s += 200
    elif variant:
        s += _score(rec.get("color_variant", ""), words) * 2

    # Album match
    if title == query_full:
        s += 80
    else:
        s += _score(rec.get("title", ""), words)

    # Artist match
    if artist == query_full:
        s += 60
    else:
        s += _score(rec.get("artist", ""), words) * 0.7

    # Bonus for having a real variant
    if variant and variant != "black" and any(w in variant for w in words):
        s += 50

    return int(s)


def _record_score(rec: dict, words: list[str]) -> int:
    artist = rec.get("artist", "").lower()
    title = rec.get("title", "").lower()
    query_full = " ".join(words)
    score = 0
    if artist == query_full:
        score += 100
    else:
        score += _score(rec.get("artist", ""), words)
    if title == query_full:
        score += 80
    else:
        score += _score(rec.get("title", ""), words) * 0.8
    return score


def _user_score(u: dict, words: list[str]) -> int:
    return _score(u.get("username", ""), words) + _score(u.get("bio", ""), words) * 0.5


def _post_score(p: dict, words: list[str]) -> int:
    return _score(p.get("caption", "") or p.get("content", ""), words)


def _listing_score(listing: dict, words: list[str]) -> int:
    artist = listing.get("artist", "").lower()
    album = listing.get("album", "").lower()
    query_full = " ".join(words)
    score = 50
    if artist == query_full:
        score += 100
    else:
        score += _score(listing.get("artist", ""), words)
    if album == query_full:
        score += 80
    else:
        score += _score(listing.get("album", ""), words) * 0.8
    return score


def _build_regex_filter(q: str) -> dict:
    words = q.strip().split()
    patterns = []
    for w in words:
        patterns.append({"$regex": w, "$options": "i"})
    return patterns


def _slugify(text: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


# ========== Variant-first search ==========

@router.get("/search/variants")
async def search_variants(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    user: Optional[Dict] = Depends(get_current_user),
):
    """Variant-first search across all records. Returns deduplicated variants with slug URLs."""
    words = [w.lower() for w in q.strip().split() if len(w) >= 1]
    if not words:
        return {"variants": [], "albums": [], "artists": [], "has_more": False}

    regex_patterns = _build_regex_filter(q)
    def field_or(field: str):
        return [{field: p} for p in regex_patterns]

    # Search across artist, title, color_variant, catno
    rec_filter = {"$or": field_or("artist") + field_or("title") + field_or("color_variant") + field_or("catno")}
    fetch_limit = skip + limit + 100
    raw = await db.records.find(rec_filter, {"_id": 0}).limit(fetch_limit).to_list(fetch_limit)

    # Deduplicate by discogs_id → keep best per variant
    seen = {}
    for r in raw:
        did = r.get("discogs_id")
        key = did or r.get("id")
        if key not in seen:
            seen[key] = r

    unique = list(seen.values())
    scored = sorted(unique, key=lambda r: _variant_score(r, words), reverse=True)

    # Split into: variants (have color_variant), albums (grouped by title)
    variants_out = []
    album_groups = {}
    artist_set = {}

    for r in scored:
        artist = r.get("artist", "")
        title = r.get("title", "")
        variant = r.get("color_variant", "")

        # Track unique artists — split multi-artist fields into individual names
        individual_artists = _split_artists(artist)
        for ind_name in individual_artists:
            norm = _normalize_artist_name(ind_name)
            if norm and norm not in artist_set:
                artist_set[norm] = {
                    "name": ind_name,  # preserve original casing from first occurrence
                    "score": _score(ind_name, words),
                    "record_count": 1,
                }
            elif norm and norm in artist_set:
                artist_set[norm]["record_count"] = artist_set[norm].get("record_count", 1) + 1
                # Update score if this occurrence scores higher
                new_score = _score(ind_name, words)
                if new_score > artist_set[norm]["score"]:
                    artist_set[norm]["score"] = new_score

        # Track albums
        a_low = artist.lower().strip()
        album_key = f"{a_low}|{title.lower().strip()}"
        if album_key not in album_groups:
            album_groups[album_key] = {
                "artist": artist, "title": title,
                "cover_url": r.get("cover_url"), "year": r.get("year"),
                "discogs_id": r.get("discogs_id"),
                "variant_count": 0,
            }
        album_groups[album_key]["variant_count"] += 1

        # Build variant entry
        slug_artist = _slugify(artist)
        slug_album = _slugify(title)
        slug_variant = _slugify(variant) if variant else "standard"
        variants_out.append({
            "discogs_id": r.get("discogs_id"),
            "artist": artist,
            "album": title,
            "variant": variant or "Standard Black Vinyl",
            "cover_url": r.get("cover_url"),
            "year": r.get("year"),
            "label": r.get("label"),
            "slug": f"/vinyl/{slug_artist}/{slug_album}/{slug_variant}",
            "score": _variant_score(r, words),
        })

    page = variants_out[skip:skip + limit]
    has_more = len(variants_out) > skip + limit

    # Top albums (sorted by variant count)
    albums = sorted(album_groups.values(), key=lambda a: a["variant_count"], reverse=True)[:8]
    for a in albums:
        a["slug"] = f"/vinyl/{_slugify(a['artist'])}/{_slugify(a['title'])}/standard"

    # Top artists — sort by record count on HoneyGroove, then search relevance, then alphabetical
    artists_sorted = sorted(
        artist_set.values(),
        key=lambda a: (a.get("record_count", 1), a["score"], a["name"].lower()),
        reverse=True,
    )[:6]
    artist_images = await asyncio.gather(*[_get_artist_image(a["name"]) for a in artists_sorted])
    artists_out = [
        {"name": a["name"], "image_url": img}
        for a, img in zip(artists_sorted, artist_images)
    ]

    return {
        "variants": page,
        "albums": albums,
        "artists": artists_out,
        "has_more": has_more,
        "total": len(variants_out),
    }


# ========== Discovery endpoints ==========

@router.get("/search/discover")
async def search_discover(user: Optional[Dict] = Depends(get_current_user)):
    """Return discovery sections for the empty search state."""
    import asyncio

    async def trending():
        """Most-owned variants."""
        pipeline = [
            {"$match": {"discogs_id": {"$ne": None}, "color_variant": {"$ne": None}}},
            {"$group": {
                "_id": "$discogs_id",
                "count": {"$sum": 1},
                "artist": {"$first": "$artist"},
                "title": {"$first": "$title"},
                "variant": {"$first": "$color_variant"},
                "cover_url": {"$first": "$cover_url"},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        results = []
        async for doc in db.records.aggregate(pipeline):
            results.append({
                "discogs_id": doc["_id"],
                "artist": doc.get("artist"),
                "album": doc.get("title"),
                "variant": doc.get("variant"),
                "cover_url": doc.get("cover_url"),
                "collectors": doc["count"],
                "slug": f"/vinyl/{_slugify(doc.get('artist'))}/{_slugify(doc.get('title'))}/{_slugify(doc.get('variant'))}",
            })
        return results

    async def rare():
        """Variants with high rarity score from Discogs cache."""
        results = []
        async for doc in db.discogs_releases.find(
            {"community_have": {"$gt": 0, "$lte": 200}, "community_want": {"$gt": 50}},
            {"_id": 0, "discogs_id": 1, "artist": 1, "title": 1, "color_variant": 1,
             "cover_url": 1, "community_have": 1, "community_want": 1}
        ).sort("community_want", -1).limit(10):
            results.append({
                "discogs_id": doc.get("discogs_id"),
                "artist": doc.get("artist"),
                "album": doc.get("title"),
                "variant": doc.get("color_variant"),
                "cover_url": doc.get("cover_url"),
                "collectors": doc.get("community_have", 0),
                "wantlist": doc.get("community_want", 0),
                "slug": f"/vinyl/{_slugify(doc.get('artist'))}/{_slugify(doc.get('title'))}/{_slugify(doc.get('color_variant'))}",
            })
        return results

    async def most_wanted():
        """Variants with most ISO demand."""
        pipeline = [
            {"$match": {"status": {"$in": ["OPEN", "WISHLIST"]}, "discogs_id": {"$ne": None}}},
            {"$group": {
                "_id": "$discogs_id",
                "count": {"$sum": 1},
                "artist": {"$first": "$artist"},
                "album": {"$first": "$album"},
                "cover_url": {"$first": "$cover_url"},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        results = []
        async for doc in db.iso_items.aggregate(pipeline):
            # Get variant name from records
            rec = await db.records.find_one({"discogs_id": doc["_id"]}, {"_id": 0, "color_variant": 1})
            variant = rec.get("color_variant", "") if rec else ""
            results.append({
                "discogs_id": doc["_id"],
                "artist": doc.get("artist"),
                "album": doc.get("album"),
                "variant": variant,
                "cover_url": doc.get("cover_url"),
                "seeking": doc["count"],
                "slug": f"/vinyl/{_slugify(doc.get('artist'))}/{_slugify(doc.get('album'))}/{_slugify(variant)}",
            })
        return results

    async def recently_added():
        """Recently added variants."""
        results = []
        async for doc in db.records.find(
            {"discogs_id": {"$ne": None}, "color_variant": {"$ne": None}},
            {"_id": 0, "discogs_id": 1, "artist": 1, "title": 1, "color_variant": 1, "cover_url": 1, "created_at": 1}
        ).sort("created_at", -1).limit(10):
            results.append({
                "discogs_id": doc.get("discogs_id"),
                "artist": doc.get("artist"),
                "album": doc.get("title"),
                "variant": doc.get("color_variant"),
                "cover_url": doc.get("cover_url"),
                "slug": f"/vinyl/{_slugify(doc.get('artist'))}/{_slugify(doc.get('title'))}/{_slugify(doc.get('color_variant'))}",
            })
        return results

    t, ra, mw, rec = await asyncio.gather(trending(), rare(), most_wanted(), recently_added())
    return {
        "trending": t,
        "rare": ra,
        "most_wanted": mw,
        "recently_added": rec,
    }


# ========== Original unified search (kept for backward compat) ==========


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

    # Batch fetch record counts, following status, and seller status (+20 boost)
    user_ids = [u["id"] for u in scored_users]
    rec_counts = {}
    seller_ids_set = set()
    if user_ids:
        pipeline = [
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        ]
        async for doc in db.records.aggregate(pipeline):
            rec_counts[doc["_id"]] = doc["count"]
        # Check which users are active sellers (Inner Hive Seller boost)
        seller_docs = await db.listings.find(
            {"user_id": {"$in": user_ids}, "status": "ACTIVE"},
            {"_id": 0, "user_id": 1}
        ).to_list(100)
        seller_ids_set = {d["user_id"] for d in seller_docs}

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
        "is_seller": u["id"] in seller_ids_set,
    } for u in scored_users]
    # Re-sort with Inner Hive Seller boost (+20)
    collectors_out.sort(
        key=lambda c: _user_score(
            next((u for u in scored_users if u["id"] == c["id"]), {}), words
        ) + (20 if c["is_seller"] else 0),
        reverse=True
    )

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

    # If local records are few, auto-fetch Discogs in parallel as fallback
    discogs_fallback = []
    if len(records_out) < 5:
        import asyncio
        try:
            discogs_raw = await asyncio.to_thread(search_discogs, q)
            seen_d = {r.get("discogs_id") for r in records_out if r.get("discogs_id")}
            discogs_fallback = [r for r in (discogs_raw or [])[:8] if r.get("discogs_id") not in seen_d]
        except Exception:
            pass

    return {
        "records": records_out,
        "collectors": collectors_out,
        "posts": posts_out,
        "listings": listings_out,
        "discogs_fallback": discogs_fallback,
    }


@router.get("/search/discogs")
async def search_discogs_external(q: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    """Search Discogs catalog (external API). Separated for non-blocking use."""
    import asyncio
    results = await asyncio.to_thread(search_discogs, q)
    return results[:20]


@router.get("/search/records")
async def search_records_paginated(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    user: Dict = Depends(require_auth),
):
    """Paginated record search across local collections + Discogs for infinite scroll."""
    words = [w.lower() for w in q.strip().split() if len(w) >= 1]
    if not words:
        return {"records": [], "has_more": False}

    regex_patterns = _build_regex_filter(q)
    def field_or(field: str):
        return [{field: p} for p in regex_patterns]

    # Fetch more than needed for scoring then paginate
    fetch_limit = skip + limit + 50
    rec_filter = {"$or": field_or("artist") + field_or("title")}
    raw_records = await db.records.find(rec_filter, {"_id": 0}).limit(fetch_limit).to_list(fetch_limit)

    # Deduplicate by discogs_id
    seen = set()
    unique = []
    for r in raw_records:
        did = r.get("discogs_id")
        key = did if did else r.get("id")
        if key not in seen:
            seen.add(key)
            unique.append(r)

    scored = sorted(unique, key=lambda r: _record_score(r, words), reverse=True)
    page = scored[skip:skip + limit]
    has_more = len(scored) > skip + limit

    records_out = [{
        "discogs_id": r.get("discogs_id"),
        "title": r.get("title", ""),
        "artist": r.get("artist", ""),
        "cover_url": r.get("cover_url"),
        "year": r.get("year"),
        "format": r.get("format"),
        "label": r.get("label"),
        "color_variant": r.get("color_variant"),
        "source": "collection",
    } for r in page]

    return {"records": records_out, "has_more": has_more}
