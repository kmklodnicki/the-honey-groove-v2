"""Unified global search — records, collectors, posts, listings, variants."""
from fastapi import APIRouter, Query, Depends
from typing import Dict, List, Optional
from datetime import datetime, timezone
import asyncio
import os
import requests as req

from database import db, require_auth, get_current_user, search_discogs, get_hidden_user_ids, logger, get_discogs_release

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
    n = name.lower().strip()
    n = _re_module.sub(r'[,;.!?]+$', '', n).strip()
    return n


def _split_artists(artist_field: str) -> list[str]:
    """Split a multi-artist field into individual canonical artist names."""
    if not artist_field:
        return []
    parts = _re_module.split(r'\s*[,&]\s*|\s+(?:and|with|feat\.?|ft\.?|featuring)\s+', artist_field, flags=_re_module.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]


# ─── Collector Synonym Expansion ───
SYNONYMS = {
    "rsd": ["record store day", "rsd"],
    "record store day": ["record store day", "rsd"],
    "color": ["colored vinyl", "colored", "colour"],
    "colored": ["colored vinyl", "colored", "colour"],
    "coloured": ["colored vinyl", "colored", "colour"],
    "limited": ["limited edition", "limited"],
    "ltd": ["limited edition", "limited"],
    "exclusive": ["exclusive", "indie exclusive", "webstore exclusive", "tour exclusive"],
    "anniversary": ["anniversary", "anniversary edition"],
    "deluxe": ["deluxe", "deluxe edition"],
    "signed": ["signed", "autographed"],
    "picture disc": ["picture disc"],
    "pic disc": ["picture disc"],
    "clear": ["clear", "crystal clear", "transparent"],
    "transparent": ["transparent", "translucent", "clear"],
    "splatter": ["splatter", "splattered"],
    "marbled": ["marbled", "marble"],
    "swirl": ["swirl", "swirled"],
    "glow": ["glow", "glow in the dark", "glow-in-the-dark"],
    "obi": ["obi", "obi strip"],
    "gatefold": ["gatefold"],
    "180g": ["180 gram", "180g"],
    "180": ["180 gram", "180g"],
    "1st": ["first pressing", "first", "1st"],
    "first pressing": ["first pressing", "first", "1st"],
    "repress": ["repress", "reissue", "repressing"],
    "reissue": ["reissue", "repress"],
    "test pressing": ["test pressing", "test press"],
    "promo": ["promo", "promotional"],
    "debut": ["debut", "self-titled", "self titled", "first album"],
    "self-titled": ["self-titled", "self titled", "debut"],
}

COLLECTOR_KEYWORDS = {
    "rsd", "record store day", "limited", "exclusive", "indie exclusive",
    "tour exclusive", "webstore exclusive", "signed", "autographed",
    "picture disc", "colored", "coloured", "splatter", "marbled", "swirl",
    "clear", "transparent", "translucent", "obi", "gatefold", "180g",
    "180 gram", "first pressing", "test pressing", "promo", "anniversary",
    "deluxe", "numbered", "glow", "repress", "reissue",
}


def _expand_synonyms(words: list[str]) -> list[str]:
    """Expand search words with collector synonyms."""
    expanded = list(words)
    query_lower = " ".join(words)
    # Check multi-word synonyms first
    for trigger, synonyms in SYNONYMS.items():
        if trigger in query_lower:
            for syn in synonyms:
                syn_words = syn.split()
                for sw in syn_words:
                    if sw not in expanded:
                        expanded.append(sw)
    # Check individual words
    for w in words:
        if w in SYNONYMS:
            for syn in SYNONYMS[w]:
                syn_words = syn.split()
                for sw in syn_words:
                    if sw not in expanded:
                        expanded.append(sw)
    return expanded


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


def _variant_score_v2(rec: dict, original_words: list[str], expanded_words: list[str]) -> int:
    """Collector-intent scoring: variant keywords > exact variant > artist+variant > artist+album."""
    query_full = " ".join(original_words)
    s = 0
    variant = (rec.get("color_variant") or "").lower()
    artist = (rec.get("artist") or "").lower()
    title = (rec.get("title") or "").lower()
    notes = (rec.get("notes") or "").lower()
    label = ""
    raw_label = rec.get("label")
    if isinstance(raw_label, list):
        label = " ".join(raw_label).lower()
    elif isinstance(raw_label, str):
        label = raw_label.lower()
    catno = (rec.get("catno") or "").lower()
    year_str = str(rec.get("year") or "")

    # Detect collector-intent words in the query
    # First, detect multi-word collector phrases
    query_joined = " ".join(original_words)
    MULTI_WORD_COLLECTOR_PHRASES = [
        "record store day", "test pressing", "first pressing",
        "picture disc", "glow in the dark", "indie exclusive",
        "tour exclusive", "webstore exclusive",
    ]
    matched_phrase_words = set()
    for phrase in MULTI_WORD_COLLECTOR_PHRASES:
        if phrase in query_joined:
            for pw in phrase.split():
                matched_phrase_words.add(pw)

    collector_words = [w for w in original_words if w in COLLECTOR_KEYWORDS or w in SYNONYMS or w in matched_phrase_words]
    non_collector_words = [w for w in original_words if w not in collector_words]

    # Build combined text for keyword searching
    raw_format = rec.get("format")
    format_text = " ".join(raw_format).lower() if isinstance(raw_format, list) else (raw_format or "").lower()

    # ── 1. Exact variant match (highest priority: 300) ──
    if variant and variant == query_full:
        s += 300
    elif variant:
        v_score = _score(variant, original_words)
        s += v_score * 3  # variant matches weighted 3x

    # ── 2. Collector keyword matches in variant / notes / format (250 bonus each) ──
    for cw in collector_words:
        syns = SYNONYMS.get(cw, [cw])
        for syn in syns:
            if syn in variant:
                s += 200
                break
            if syn in notes:
                s += 150
                break
            if syn in format_text:
                s += 150
                break
            if syn in label:
                s += 80
                break

    # ── 3. Artist match ──
    if non_collector_words:
        artist_query = " ".join(non_collector_words)
        if artist == artist_query:
            s += 120
        elif artist_query in artist:
            s += 80
        else:
            s += _score(artist, non_collector_words)
    elif artist == query_full:
        s += 60
    else:
        s += int(_score(artist, original_words) * 0.7)

    # ── 4. Album title match ──
    if title == query_full:
        s += 80
    else:
        s += _score(title, original_words)

    # ── 4b. Self-titled album boost ──
    # Only boost when album title IS the artist name (exact self-titled match)
    is_self_titled = title and artist and title == artist
    if is_self_titled:
        # If query matches the artist, the self-titled album is a strong hit
        if non_collector_words:
            artist_query = " ".join(non_collector_words)
            if artist_query == artist or artist_query in artist:
                s += 60  # Self-titled album for queried artist
        # Extra boost for "debut" / "self-titled" queries
        query_lower = " ".join(original_words)
        if "debut" in query_lower or "self-titled" in query_lower or "self titled" in query_lower:
            s += 120

    # ── 5. Year match ──
    for w in original_words:
        if w.isdigit() and len(w) == 4 and w == year_str:
            s += 100

    # ── 6. Notes + format match for expanded terms ──
    for ew in expanded_words:
        if ew in notes:
            s += 30
        if ew in variant:
            s += 20
        if ew in format_text:
            s += 20

    # ── 7. Bonus for non-standard variants ──
    if variant and variant not in ("", "black", "standard", "none"):
        s += 15

    # ── 8. Community demand bonus (if available) ──
    want = rec.get("community_want", 0)
    if want > 100:
        s += 25
    elif want > 50:
        s += 15
    elif want > 10:
        s += 5

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
        score += int(_score(rec.get("title", ""), words) * 0.8)
    return score


def _user_score(u: dict, words: list[str]) -> int:
    return _score(u.get("username", ""), words) + int(_score(u.get("bio", ""), words) * 0.5)


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
        score += int(_score(listing.get("album", ""), words) * 0.8)
    return score


def _build_regex_filter(q: str) -> list:
    words = q.strip().split()
    patterns = []
    for w in words:
        patterns.append({"$regex": _re_module.escape(w), "$options": "i"})
    return patterns


def _build_expanded_regex(expanded_words: list[str]) -> list:
    """Build regex patterns from expanded synonym words."""
    patterns = []
    for w in expanded_words:
        patterns.append({"$regex": _re_module.escape(w), "$options": "i"})
    return patterns


def _slugify(text: str) -> str:
    return _re_module.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


# ========== Variant-first search ==========

@router.get("/search/variants")
async def search_variants(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    user: Optional[Dict] = Depends(get_current_user),
):
    """Collector-intent variant search across records + discogs_releases."""
    # Filter stop words and deduplicate
    STOP_WORDS = {"the", "a", "an", "by", "of", "and", "or", "in", "on", "at", "to", "for", "is", "it", "from"}
    seen_words = set()
    original_words = []
    for w in q.strip().split():
        wl = w.lower()
        if len(wl) >= 1 and wl not in STOP_WORDS and wl not in seen_words:
            seen_words.add(wl)
            original_words.append(wl)
    if not original_words:
        return {"variants": [], "albums": [], "artists": [], "has_more": False, "total": 0}

    expanded_words = _expand_synonyms(original_words)
    regex_orig = _build_regex_filter(q)
    regex_expanded = _build_expanded_regex(expanded_words)

    def field_or(field: str, patterns: list):
        return [{field: p} for p in patterns]

    # ── Search records collection (user collections) ──
    rec_filter = {"$or":
        field_or("artist", regex_orig)
        + field_or("title", regex_orig)
        + field_or("color_variant", regex_expanded)
        + field_or("catno", regex_orig)
        + field_or("notes", regex_expanded)
    }
    fetch_limit = skip + limit + 200
    raw_records = await db.records.find(rec_filter, {"_id": 0}).limit(fetch_limit).to_list(fetch_limit)

    # ── Search discogs_releases collection (rich metadata) ──
    discogs_filter = {"$or":
        field_or("artist", regex_orig)
        + field_or("title", regex_orig)
        + field_or("color_variant", regex_expanded)
        + field_or("catno", regex_orig)
        + field_or("notes", regex_expanded)
        + field_or("label", regex_orig)
    }
    raw_discogs = await db.discogs_releases.find(discogs_filter, {"_id": 0}).limit(fetch_limit).to_list(fetch_limit)

    # ── Merge & deduplicate by discogs_id (prefer discogs_releases for richer data) ──
    merged = {}
    # First pass: records (user collections)
    for r in raw_records:
        did = r.get("discogs_id")
        key = did or r.get("id")
        if key and key not in merged:
            merged[key] = r
    # Second pass: discogs_releases (overwrite with richer data if available)
    for r in raw_discogs:
        did = r.get("discogs_id")
        if not did:
            continue
        if did in merged:
            # Merge: keep discogs_release fields as they're richer, but preserve user collection fields
            existing = merged[did]
            merged[did] = {**existing, **{k: v for k, v in r.items() if v and (not existing.get(k) or k in ("notes", "label", "catno", "community_have", "community_want", "genre", "style"))}}
        else:
            merged[did] = r

    unique = list(merged.values())
    scored = sorted(unique, key=lambda r: _variant_score_v2(r, original_words, expanded_words), reverse=True)

    # ── Discogs API fallback: enrich results when local data is sparse ──
    # Triggers when: few local results, collector-intent keywords, year in query, or possible self-titled
    collector_words = [w for w in original_words if w in COLLECTOR_KEYWORDS or w in SYNONYMS]
    year_words = [w for w in original_words if w.isdigit() and len(w) == 4]
    # Check if query might be a self-titled album (all non-year words = artist name)
    non_year_words = [w for w in original_words if not (w.isdigit() and len(w) == 4)]
    need_discogs = len(unique) < 15 or len(collector_words) > 0 or len(year_words) > 0 or len(non_year_words) <= 3

    if need_discogs:
        try:
            # Multi-query strategy for broader Discogs coverage
            queries_to_try = [q]

            # If query looks like "Artist + keywords", also search for self-titled album
            non_collector_non_year = [w for w in original_words
                                      if w not in COLLECTOR_KEYWORDS
                                      and w not in SYNONYMS
                                      and not (w.isdigit() and len(w) == 4)]
            if non_collector_non_year and (collector_words or year_words):
                artist_part = " ".join(non_collector_non_year)
                # Search for self-titled: "Artist Artist vinyl"
                queries_to_try.append(f"{artist_part} {artist_part} vinyl")
                # Search for artist + format keywords
                if year_words:
                    queries_to_try.append(f"{artist_part} {' '.join(year_words)} vinyl")

            seen_dids = {r.get("discogs_id") for r in unique if r.get("discogs_id")}
            all_new_discogs = []

            for dq in queries_to_try:
                discogs_raw = await asyncio.to_thread(search_discogs, dq)
                for dr in (discogs_raw or [])[:20]:
                    did = dr.get("discogs_id")
                    if did and did not in seen_dids:
                        seen_dids.add(did)
                        all_new_discogs.append(dr)

            if all_new_discogs:
                # Cache new Discogs releases for future searches
                for dr in all_new_discogs:
                    did = dr.get("discogs_id")
                    if did:
                        await db.discogs_releases.update_one(
                            {"discogs_id": did},
                            {"$setOnInsert": {
                                **dr,
                                "cached_at": datetime.now(timezone.utc).isoformat(),
                            }},
                            upsert=True,
                        )

                scored.extend(all_new_discogs)
                scored = sorted(scored, key=lambda r: _variant_score_v2(r, original_words, expanded_words), reverse=True)
        except Exception as e:
            logger.error(f"Discogs fallback search error: {e}")

    # ── Build output: variants, albums, artists ──
    variants_out = []
    album_groups = {}
    artist_set = {}

    for r in scored:
        artist = r.get("artist", "")
        title = r.get("title", "")
        variant = r.get("color_variant", "")

        # Track unique artists
        individual_artists = _split_artists(artist)
        for ind_name in individual_artists:
            norm = _normalize_artist_name(ind_name)
            if norm and norm not in artist_set:
                artist_set[norm] = {
                    "name": ind_name,
                    "score": _score(ind_name, original_words),
                    "record_count": 1,
                }
            elif norm and norm in artist_set:
                artist_set[norm]["record_count"] = artist_set[norm].get("record_count", 1) + 1
                new_score = _score(ind_name, original_words)
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

        # Build variant entry with collector context
        slug_artist = _slugify(artist)
        slug_album = _slugify(title)
        slug_variant = _slugify(variant) if variant else "standard"

        # Extract collector tags from notes + variant + format descriptions
        notes = (r.get("notes") or "").lower()
        variant_lower = (r.get("color_variant") or "").lower()
        raw_format = r.get("format")
        format_str = " ".join(raw_format).lower() if isinstance(raw_format, list) else (raw_format or "").lower()
        tag_source = f"{notes} {variant_lower} {format_str}"
        tags = []
        if "record store day" in tag_source or "rsd" in tag_source:
            tags.append("RSD")
        if "limited" in tag_source:
            tags.append("Limited")
        if "exclusive" in tag_source:
            tags.append("Exclusive")
        if "numbered" in tag_source:
            tags.append("Numbered")
        if "signed" in tag_source or "autograph" in tag_source:
            tags.append("Signed")
        if "test pressing" in tag_source:
            tags.append("Test Pressing")
        if "tour" in tag_source:
            tags.append("Tour")

        # Extract label as string
        raw_label = r.get("label")
        label_str = ", ".join(raw_label) if isinstance(raw_label, list) else (raw_label or "")

        # Hydrate cover: fallback to Discogs API if cover_url is missing
        cover = r.get("cover_url")
        if not cover and r.get("discogs_id"):
            try:
                release_data = await asyncio.to_thread(get_discogs_release, r["discogs_id"])
                if release_data and release_data.get("cover_url"):
                    cover = release_data["cover_url"]
            except Exception:
                pass
        # Last resort: find a sibling record with the same artist+title that has a cover
        if not cover:
            sibling = await db.records.find_one(
                {"artist": r.get("artist"), "title": r.get("title"), "cover_url": {"$ne": None, "$ne": ""}},
                {"_id": 0, "cover_url": 1}
            )
            if sibling and sibling.get("cover_url"):
                cover = sibling["cover_url"]

        # Count local platform collectors (users who have this record)
        local_collectors = 0
        did = r.get("discogs_id")
        if did:
            local_collectors = await db.records.count_documents({"discogs_id": did})

        variants_out.append({
            "discogs_id": did,
            "artist": artist,
            "album": title,
            "variant": variant or "Standard Black Vinyl",
            "cover_url": cover,
            "year": r.get("year"),
            "label": label_str,
            "catno": r.get("catno"),
            "collectors": local_collectors or r.get("community_have", 0),
            "wantlist": r.get("community_want", 0),
            "tags": tags,
            "slug": f"/vinyl/{slug_artist}/{slug_album}/{slug_variant}",
            "score": _variant_score_v2(r, original_words, expanded_words),
        })

    page = variants_out[skip:skip + limit]
    has_more = len(variants_out) > skip + limit

    # Top albums (sorted by variant count)
    albums = sorted(album_groups.values(), key=lambda a: a["variant_count"], reverse=True)[:8]
    for a in albums:
        a["slug"] = f"/vinyl/{_slugify(a['artist'])}/{_slugify(a['title'])}/standard"

    # Top artists
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


# ── User / Collector Search ──────────────────────────────────────────────────

@router.get("/search/users")
async def search_users(
    q: str = Query("", min_length=1),
    limit: int = Query(10, ge=1, le=30),
    user: Optional[Dict] = Depends(get_current_user),
):
    """Search for collectors by username or display name."""
    q = q.strip()
    if not q:
        return {"users": []}

    # Build exclusion list
    exclude_ids = set(await get_hidden_user_ids())
    if user:
        from database import get_all_blocked_ids
        blocked = await get_all_blocked_ids(user["id"])
        exclude_ids.update(blocked)
        exclude_ids.add(user["id"])  # Don't show yourself

    # Text search on username and display_name
    regex = {"$regex": q, "$options": "i"}
    query_filter = {
        "$and": [
            {"$or": [{"username": regex}, {"display_name": regex}]},
            {"id": {"$nin": list(exclude_ids)}},
        ]
    }

    users_raw = await db.users.find(
        query_filter,
        {"_id": 0, "id": 1, "username": 1, "display_name": 1, "avatar_url": 1, "profile_locked": 1}
    ).limit(limit).to_list(limit)

    # Get record counts for matched users
    user_ids = [u["id"] for u in users_raw]
    results = []

    # Viewer's discogs_ids for "records in common" (only if logged in)
    viewer_dids = set()
    if user:
        viewer_recs = await db.records.find(
            {"user_id": user["id"], "discogs_id": {"$ne": None}},
            {"_id": 0, "discogs_id": 1}
        ).to_list(5000)
        viewer_dids = {r["discogs_id"] for r in viewer_recs}

    for u in users_raw:
        record_count = await db.records.count_documents({"user_id": u["id"]})

        common_count = 0
        if viewer_dids:
            their_recs = await db.records.find(
                {"user_id": u["id"], "discogs_id": {"$ne": None}},
                {"_id": 0, "discogs_id": 1}
            ).to_list(5000)
            their_dids = {r["discogs_id"] for r in their_recs}
            common_count = len(viewer_dids & their_dids)

        results.append({
            "id": u["id"],
            "username": u["username"],
            "display_name": u.get("display_name"),
            "avatar_url": u.get("avatar_url"),
            "record_count": record_count,
            "records_in_common": common_count,
        })

    return {"users": results}
