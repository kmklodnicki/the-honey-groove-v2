"""Vinyl Variant & Value Pages — SEO-optimized canonical pages per variant.

Each variant gets a dedicated page at /vinyl/{artist}/{album}/{variant}
combining Discogs-authoritative record metadata with Honeygroove marketplace,
price, demand, and community data.

Data flow:
  1. URL slugs → find matching records in DB with discogs_id
  2. Fetch authoritative metadata from Discogs API (cached in discogs_releases collection)
  3. Layer on Honeygroove data: listings, sales, ownership, ISO demand, Hive posts
"""
from fastapi import APIRouter, Query, Depends
from fastapi.responses import HTMLResponse
from database import db, get_discogs_release, get_discogs_market_data, get_discogs_master_versions, get_discogs_master, logger, get_current_user, derive_variant_tag
from datetime import datetime, timezone
from utils.image_resolver import resolve_album_image
import asyncio
import os
import re
import json
import html as html_mod

# ── Smart Flag: detect unofficial via format descriptions, notes, and format text ──
UNOFFICIAL_KEYWORDS = re.compile(r'\b(unofficial|bootleg|counterfeit)\b', re.IGNORECASE)

def detect_unofficial(discogs_data: dict, db_records: list = None) -> bool:
    """Check if a release is unofficial via multiple signals."""
    # Signal 1: Exact match in format_descriptions (strongest)
    format_descriptions = discogs_data.get("format_descriptions", [])
    if "Unofficial Release" in format_descriptions:
        return True
    # Signal 2: Keyword search in format_descriptions text
    if any(UNOFFICIAL_KEYWORDS.search(desc) for desc in format_descriptions):
        return True
    # Signal 3: Keyword search in notes
    notes = discogs_data.get("notes", "")
    if notes and UNOFFICIAL_KEYWORDS.search(notes):
        return True
    # Signal 4: Keyword search in format text
    fmt = discogs_data.get("format")
    fmt_str = fmt[0] if isinstance(fmt, list) and fmt else (fmt or "")
    if fmt_str and UNOFFICIAL_KEYWORDS.search(fmt_str):
        return True
    # Signal 5: Check internal records
    if db_records and any(r.get("is_unofficial") for r in db_records):
        return True
    return False


router = APIRouter(prefix="/vinyl")

SITE_NAME = "The Honey Groove"
SITE_URL = os.environ.get("FRONTEND_URL", "")
DEFAULT_IMAGE = f"{SITE_URL}/og-image.png"
CACHE_TTL_HOURS = 24

# ── Rarity Score System (Discogs-sourced) ──
RARITY_TIERS = [
    (0, "Ultra Rare"),     # < 500 owners worldwide
    (500, "Rare"),         # 500 – 2,000
    (2001, "Uncommon"),    # 2,001 – 5,000
    (5001, "Common"),      # 5,001+
]


def calculate_rarity(have: int, want: int, num_for_sale: int) -> dict:
    """Global Variant Rarity based on Discogs community.have count for a specific release."""
    tier = "Common"
    if have < 500:
        tier = "Ultra Rare"
    elif have <= 2000:
        tier = "Rare"
    elif have <= 5000:
        tier = "Uncommon"
    return {
        "score": max(0, 5000 - have),
        "tier": tier,
        "discogs_owners": have,
        "discogs_wantlist": want,
        "listings_available": num_for_sale,
    }


def slugify(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[''`]", "", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def unslugify(slug: str) -> str:
    return slug.replace("-", " ").strip()


def _e(text):
    if text is None:
        return ""
    return html_mod.escape(str(text), quote=True)


async def _get_cached_discogs_release(discogs_id: int) -> dict:
    """Fetch Discogs release data, using a DB cache to avoid repeat API calls."""
    cached = await db.discogs_releases.find_one({"discogs_id": discogs_id}, {"_id": 0})
    if cached:
        fetched_at = cached.get("fetched_at", "")
        if fetched_at:
            try:
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)).total_seconds()
                if age < CACHE_TTL_HOURS * 3600:
                    return cached
            except (ValueError, TypeError):
                pass

    # Fetch fresh from Discogs API
    release_data = get_discogs_release(discogs_id)
    if release_data:
        cache_doc = {
            **release_data,
            "discogs_id": discogs_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.discogs_releases.update_one(
            {"discogs_id": discogs_id},
            {"$set": cache_doc},
            upsert=True,
        )
        return cache_doc

    # Return cached even if stale, better than nothing
    if cached:
        return cached
    return {}


def _slug_to_fuzzy_regex(slug: str) -> re.Pattern:
    """Build a fuzzy regex from a slug that matches regardless of special characters.
    e.g., 'speak-now-taylors-version' matches 'Speak Now (Taylor's Version)'"""
    words = slug.replace("-", " ").strip().split()
    # Each word must appear in order, with optional special chars between letters
    parts = []
    for word in words:
        # Allow optional special chars (apostrophes, parentheses, etc.) between chars
        fuzzy_word = r"[^\w]*".join(re.escape(c) for c in word)
        parts.append(fuzzy_word)
    # Words separated by any amount of non-word chars + spaces
    pattern = r"[\s\W]*".join(parts)
    return re.compile(pattern, re.IGNORECASE)


async def _resolve_discogs_id(artist_slug: str, album_slug: str, variant_slug: str):
    """Find a Discogs release ID from URL slugs by matching records in the DB."""
    artist_term = unslugify(artist_slug)
    album_term = unslugify(album_slug)
    variant_term = unslugify(variant_slug)

    artist_re = _slug_to_fuzzy_regex(artist_slug)
    album_re = _slug_to_fuzzy_regex(album_slug)
    variant_re = _slug_to_fuzzy_regex(variant_slug)

    # Search records collection
    records = await db.records.find(
        {
            "artist": artist_re,
            "title": album_re,
            "color_variant": variant_re,
            "discogs_id": {"$exists": True, "$ne": None},
        },
        {"_id": 0}
    ).to_list(100)

    if records:
        return records, records[0].get("discogs_id"), artist_term, album_term, variant_term

    # Fallback: try without variant match (broader search)
    records_no_variant = await db.records.find(
        {
            "artist": artist_re,
            "title": album_re,
            "discogs_id": {"$exists": True, "$ne": None},
        },
        {"_id": 0}
    ).to_list(100)

    if records_no_variant:
        return records_no_variant, records_no_variant[0].get("discogs_id"), artist_term, album_term, variant_term

    # Fallback: also search discogs_releases collection
    dr_records = await db.discogs_releases.find(
        {
            "artist": artist_re,
            "title": album_re,
            "discogs_id": {"$exists": True, "$ne": None},
        },
        {"_id": 0}
    ).to_list(100)

    if dr_records:
        return dr_records, dr_records[0].get("discogs_id"), artist_term, album_term, variant_term

    # No records found at all
    return [], None, artist_term, album_term, variant_term


def _variant_match(listing: dict, variant_term: str) -> bool:
    vt = variant_term.lower()
    for field in ["pressing_notes", "color_variant", "description"]:
        val = listing.get(field, "")
        if val and vt in val.lower():
            return True
    return False


def _build_seo_description(artist, album, variant, year, owners, iso_count, value, discogs_market):
    parts = [f"View the {variant} variant of {album} by {artist} on vinyl."]
    if year:
        parts.append(f"Released {year}.")
    if owners:
        parts.append(f"{owners} collector{'s' if owners != 1 else ''} own{'s' if owners == 1 else ''} this pressing.")
    if iso_count:
        parts.append(f"{iso_count} collector{'s' if iso_count != 1 else ''} searching for it.")
    if value.get("average_value"):
        parts.append(f"Average sale price: ${value['average_value']:.2f}.")
    elif discogs_market.get("median_value"):
        parts.append(f"Discogs median value: ${discogs_market['median_value']:.2f}.")
    return " ".join(parts)


@router.get("/{artist_slug}/{album_slug}/{variant_slug}")
async def get_variant_page(artist_slug: str, album_slug: str, variant_slug: str):
    """Return all data for a vinyl variant page, sourced from Discogs."""
    records, discogs_id, artist_term, album_term, variant_term = await _resolve_discogs_id(
        artist_slug, album_slug, variant_slug
    )

    # Fetch authoritative Discogs metadata
    discogs_data = {}
    discogs_market = {}
    if discogs_id:
        discogs_data = await _get_cached_discogs_release(discogs_id)
        market_raw = get_discogs_market_data(discogs_id)
        if market_raw:
            discogs_market = market_raw

    # Build variant overview from Discogs data first, fall back to internal records
    canonical_record = records[0] if records else {}

    # Discogs is authoritative for these fields
    artist = discogs_data.get("artist") or canonical_record.get("artist") or artist_term.title()
    album = discogs_data.get("title") or canonical_record.get("title") or album_term.title()
    variant = discogs_data.get("color_variant") or canonical_record.get("color_variant") or derive_variant_tag(None, discogs_data.get("country") or canonical_record.get("country"), discogs_data.get("format_descriptions", [])) or variant_term.title()
    year = discogs_data.get("year") or canonical_record.get("year")
    country = discogs_data.get("country") or canonical_record.get("country")
    notes = discogs_data.get("notes")

    # Cover image: releases collection (Spotify) → community upload → None
    # Discogs cover images are Restricted Data and must not be used
    cover_url = None
    if discogs_id:
        _rel = await db.releases.find_one(
            {"discogsReleaseId": discogs_id},
            {"_id": 0, "spotifyImageUrl": 1, "spotifyImageSmall": 1, "communityCoverUrl": 1}
        )
        if _rel:
            cover_url = (_rel.get("spotifyImageUrl") or _rel.get("communityCoverUrl"))
    if not cover_url and canonical_record.get("userPhotoUrl"):
        cover_url = canonical_record["userPhotoUrl"]

    # Label & catno from Discogs
    label_raw = discogs_data.get("label")
    if isinstance(label_raw, list):
        label = label_raw[0] if label_raw else None
    else:
        label = label_raw or canonical_record.get("label")

    catno = discogs_data.get("catno") or canonical_record.get("catno")
    barcode = discogs_data.get("barcode")

    # Format from Discogs
    format_raw = discogs_data.get("format")
    if isinstance(format_raw, list):
        fmt = format_raw[0] if format_raw else "Vinyl"
    else:
        fmt = format_raw or canonical_record.get("format") or "Vinyl"

    # BLOCK 592 + v2.8.3: Detect unofficial via Smart Flag (format, notes, keywords)
    is_unofficial = detect_unofficial(discogs_data, records)

    # Unique owners
    owner_ids = list(set(r.get("user_id") for r in records if r.get("user_id")))
    owners_count = len(owner_ids)

    owners = []
    if owner_ids:
        owners = await db.users.find(
            {"id": {"$in": owner_ids[:20]}},
            {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
        ).to_list(20)

    # Marketplace listings (use fuzzy regex for titles with special chars)
    artist_fuzzy_re = _slug_to_fuzzy_regex(artist_slug)
    album_fuzzy_re = _slug_to_fuzzy_regex(album_slug)

    listing_query = {"artist": artist_fuzzy_re, "album": album_fuzzy_re, "status": "ACTIVE"}
    active_listings = await db.listings.find(listing_query, {"_id": 0}).sort("created_at", -1).to_list(50)

    variant_listings = [item for item in active_listings if _variant_match(item, variant_term)]
    if not variant_listings:
        variant_listings = active_listings

    for listing in variant_listings:
        seller = await db.users.find_one(
            {"id": listing.get("user_id")},
            {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
        )
        listing["seller"] = seller

    # Internal sales data
    sold_query = {"artist": artist_fuzzy_re, "album": album_fuzzy_re, "status": "SOLD"}
    sold_listings = await db.listings.find(sold_query, {"_id": 0, "price": 1, "created_at": 1}).to_list(200)
    prices = [s["price"] for s in sold_listings if s.get("price")]

    internal_value = {
        "recent_sales_count": len(prices),
        "average_value": round(sum(prices) / len(prices), 2) if prices else None,
        "highest_sale": max(prices) if prices else None,
        "lowest_sale": min(prices) if prices else None,
    }

    # ISO demand
    iso_query = {"artist": artist_fuzzy_re, "album": album_fuzzy_re, "status": {"$in": ["OPEN", "WISHLIST"]}}
    iso_count = await db.iso_items.count_documents(iso_query)

    # Hive posts
    record_ids = [r["id"] for r in records if r.get("id")]
    discogs_ids = list(set(r.get("discogs_id") for r in records if r.get("discogs_id")))

    post_query = {"$or": []}
    if record_ids:
        post_query["$or"].append({"record_id": {"$in": record_ids}})
    if discogs_ids:
        post_query["$or"].append({"discogs_id": {"$in": discogs_ids}})

    posts = []
    post_count = 0
    if post_query["$or"]:
        post_count = await db.posts.count_documents(post_query)
        raw_posts = await db.posts.find(post_query, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
        for p in raw_posts:
            author = await db.users.find_one({"id": p.get("user_id")}, {"_id": 0, "username": 1, "avatar_url": 1})
            p["user"] = author
            posts.append(p)

    seo_desc = _build_seo_description(artist, album, variant, year, owners_count, iso_count, internal_value, discogs_market)

    # Rarity from Discogs community stats
    discogs_have = discogs_data.get("community_have", 0)
    discogs_want = discogs_data.get("community_want", 0)
    discogs_for_sale = discogs_data.get("num_for_sale", 0)
    master_id = discogs_data.get("master_id")

    # Market data fallback via master/sibling releases
    if not discogs_market and master_id:
        sibling_ids = await db.discogs_releases.find(
            {"master_id": master_id, "discogs_id": {"$ne": discogs_id}},
            {"_id": 0, "discogs_id": 1}
        ).limit(5).to_list(5)
        for sib in sibling_ids:
            try:
                sib_market = get_discogs_market_data(sib["discogs_id"])
                if sib_market:
                    discogs_market = sib_market
                    break
            except Exception:
                pass
        if not discogs_market:
            try:
                master_data = await asyncio.to_thread(get_discogs_master, master_id)
                if master_data:
                    main_id = master_data.get("main_release")
                    if main_id and main_id != discogs_id:
                        main_market = get_discogs_market_data(main_id)
                        if main_market:
                            discogs_market = main_market
                    if not discogs_market and master_data.get("lowest_price"):
                        lp = float(master_data["lowest_price"])
                        discogs_market = {"median_value": round(lp * 1.3, 2), "low_value": round(lp, 2), "high_value": round(lp * 2.0, 2)}
            except Exception:
                pass

    # Community stats aggregation from sibling releases when variant stats are thin
    stats_source = "variant"
    if discogs_have == 0 and discogs_want == 0 and master_id:
        pipeline = [
            {"$match": {"master_id": master_id, "community_have": {"$gt": 0}}},
            {"$group": {"_id": None, "total_have": {"$sum": "$community_have"}, "total_want": {"$sum": "$community_want"}, "total_for_sale": {"$sum": {"$ifNull": ["$num_for_sale", 0]}}}}
        ]
        agg = await db.discogs_releases.aggregate(pipeline).to_list(1)
        if agg and agg[0].get("total_have", 0) > 0:
            discogs_have = agg[0]["total_have"]
            discogs_want = agg[0].get("total_want", 0)
            discogs_for_sale = agg[0].get("total_for_sale", 0)
            stats_source = "master"

    rarity = calculate_rarity(discogs_have, discogs_want, discogs_for_sale)

    return {
        "variant_overview": {
            "artist": artist,
            "album": album,
            "variant": variant,
            "year": year,
            "cover_url": cover_url,
            "format": fmt,
            "label": label,
            "catalog_number": catno,
            "barcode": barcode,
            "pressing_country": country,
            "discogs_id": discogs_id,
            "is_unofficial": is_unofficial,
            "notes": notes[:300] if notes else None,
        },
        "rarity": rarity,
        "scarcity": {
            "discogs_have": discogs_have,
            "discogs_want": discogs_want,
            "discogs_for_sale": discogs_for_sale,
            "tier": rarity.get("tier"),
            "stats_source": stats_source,
            "master_id": master_id,
        },
        "marketplace": {
            "active_listings": variant_listings,
            "listing_count": len(variant_listings),
            "honey_lowest": min((l.get("price", float("inf")) for l in variant_listings if l.get("price")), default=None),
        },
        "value": {
            **internal_value,
            "discogs_median": discogs_market.get("median_value"),
            "discogs_low": discogs_market.get("low_value"),
            "discogs_high": discogs_market.get("high_value"),
        },
        "demand": {
            "owners_count": owners_count,
            "iso_count": iso_count,
            "post_count": post_count,
        },
        "community": {
            "internal_owners_count": owners_count,
            "discogs_have": discogs_have,
            "discogs_want": discogs_want,
        },
        "activity": {
            "owners": owners,
            "recent_posts": posts,
        },
        "seo": {
            "title": f"{artist} — {album} ({variant}) Vinyl Variant",
            "description": seo_desc,
            "canonical": f"/vinyl/{artist_slug}/{album_slug}/{variant_slug}",
            "image": cover_url or DEFAULT_IMAGE,
        },
        "data_source": {
            "discogs_release_id": discogs_id,
            "discogs_fetched": bool(discogs_data),
            "discogs_market_fetched": bool(discogs_market),
        },
    }


# ========== Lightweight rarity endpoint ==========

@router.get("/rarity/{discogs_id}")
async def get_rarity_by_discogs_id(discogs_id: int):
    """Return rarity score for a variant using Discogs community stats."""
    discogs_data = await _get_cached_discogs_release(discogs_id)

    have = discogs_data.get("community_have", 0) if discogs_data else 0
    want = discogs_data.get("community_want", 0) if discogs_data else 0
    num_for_sale = discogs_data.get("num_for_sale", 0) if discogs_data else 0

    rarity = calculate_rarity(have, want, num_for_sale)
    rarity["discogs_id"] = discogs_id
    if discogs_data:
        rarity["artist"] = discogs_data.get("artist")
        rarity["album"] = discogs_data.get("title")
        rarity["variant"] = discogs_data.get("color_variant")
    return rarity


# ========== Release-ID based Variant Detail ==========

@router.get("/release/{release_id}")
async def get_variant_by_release_id(release_id: int, force_refresh: bool = False):
    """Return variant detail data for a specific Discogs release ID.

    This ensures Owners, Wantlist, and Market Price are variant-specific,
    NOT master album stats. Pass ?force_refresh=true to bypass cache.
    """
    if force_refresh:
        # Invalidate cache to force a fresh pull
        await db.discogs_releases.delete_one({"discogs_id": release_id})
    discogs_data = await _get_cached_discogs_release(release_id)
    if not discogs_data:
        # Try to build a minimal response from internal records instead of giving up
        internal_rec = await db.records.find_one(
            {"discogs_id": release_id},
            {"_id": 0}
        )
        if internal_rec:
            discogs_data = {
                "artist": internal_rec.get("artist", "Unknown"),
                "title": internal_rec.get("title", "Unknown"),
                "color_variant": internal_rec.get("color_variant", "Standard"),
                "year": internal_rec.get("year"),
                "cover_url": internal_rec.get("cover_url"),
                "community_have": 0,
                "community_want": 0,
                "num_for_sale": 0,
            }
        else:
            return {"error": "Release not found on Discogs", "release_id": release_id}

    market_raw = get_discogs_market_data(release_id)
    discogs_market = market_raw if market_raw else {}

    # Market data fallback: try sibling releases or master when variant has no price data
    master_id = discogs_data.get("master_id")
    if not discogs_market and master_id:
        # Strategy 1: Find a sibling release in our DB that might have better data
        sibling_ids = await db.discogs_releases.find(
            {"master_id": master_id, "discogs_id": {"$ne": release_id}},
            {"_id": 0, "discogs_id": 1}
        ).limit(5).to_list(5)
        for sib in sibling_ids:
            try:
                sib_market = get_discogs_market_data(sib["discogs_id"])
                if sib_market:
                    discogs_market = sib_market
                    break
            except Exception:
                pass
        # Strategy 2: Try master release's main_release for market data
        if not discogs_market:
            try:
                master_data = await asyncio.to_thread(get_discogs_master, master_id)
                if master_data:
                    main_release_id = master_data.get("main_release")
                    if main_release_id and main_release_id != release_id:
                        main_market = get_discogs_market_data(main_release_id)
                        if main_market:
                            discogs_market = main_market
                    # Use master's lowest_price as last resort
                    if not discogs_market and master_data.get("lowest_price"):
                        lp = float(master_data["lowest_price"])
                        discogs_market = {
                            "median_value": round(lp * 1.3, 2),
                            "low_value": round(lp, 2),
                            "high_value": round(lp * 2.0, 2),
                        }
            except Exception as e:
                logger.warning(f"Master market fallback failed for {release_id}: {e}")

    artist = discogs_data.get("artist", "Unknown Artist")
    album = discogs_data.get("title", "Unknown Album")
    variant = discogs_data.get("color_variant") or derive_variant_tag(None, discogs_data.get("country"), discogs_data.get("format_descriptions", [])) or "Standard"
    year = discogs_data.get("year")
    country = discogs_data.get("country")

    # Resolve album art from releases collection (no Discogs image URLs — Restricted Data)
    release_doc = await db.releases.find_one({"discogsReleaseId": release_id})
    resolved_image = resolve_album_image({}, release_doc or {})

    label_raw = discogs_data.get("label")
    label = label_raw[0] if isinstance(label_raw, list) and label_raw else label_raw

    catno = discogs_data.get("catno")
    barcode = discogs_data.get("barcode")

    format_raw = discogs_data.get("format")
    fmt = format_raw[0] if isinstance(format_raw, list) and format_raw else (format_raw or "Vinyl")

    # Detect unofficial via Smart Flag (format, notes, keywords)
    is_unofficial = detect_unofficial(discogs_data)

    # Variant-specific community stats from Discogs
    discogs_have = discogs_data.get("community_have", 0)
    discogs_want = discogs_data.get("community_want", 0)
    discogs_for_sale = discogs_data.get("num_for_sale", 0)
    lowest_price = discogs_market.get("low_value")

    # BLOCK 413: Fallback to master release when variant stats are 0
    stats_source = "variant"
    if discogs_have == 0 and discogs_want == 0 and master_id:
        # Strategy 1: Aggregate from sibling releases in local DB
        pipeline = [
            {"$match": {"master_id": master_id, "community_have": {"$gt": 0}}},
            {"$group": {"_id": None, "total_have": {"$sum": "$community_have"}, "total_want": {"$sum": "$community_want"}, "total_for_sale": {"$sum": {"$ifNull": ["$num_for_sale", 0]}}}}
        ]
        agg = await db.discogs_releases.aggregate(pipeline).to_list(1)
        if agg and agg[0].get("total_have", 0) > 0:
            discogs_have = agg[0]["total_have"]
            discogs_want = agg[0].get("total_want", 0)
            discogs_for_sale = agg[0].get("total_for_sale", 0)
            stats_source = "master"
            logger.info(f"Variant {release_id}: using aggregated sibling stats (have={discogs_have}, want={discogs_want})")
        else:
            # Strategy 2: Fetch master release from Discogs API
            try:
                master_data = await asyncio.to_thread(get_discogs_master, master_id)
                if master_data:
                    # Master endpoint doesn't have community stats directly, try main release
                    main_id = master_data.get("main_release")
                    if main_id and main_id != release_id:
                        main_data = await asyncio.to_thread(get_discogs_release, main_id)
                        if main_data:
                            master_have = main_data.get("community_have", 0)
                            master_want = main_data.get("community_want", 0)
                            if master_have > 0 or master_want > 0:
                                discogs_have = master_have
                                discogs_want = master_want
                                discogs_for_sale = main_data.get("num_for_sale", discogs_for_sale)
                                stats_source = "master"
                                logger.info(f"Variant {release_id}: using main release {main_id} stats")
            except Exception as e:
                logger.warning(f"Master release fallback failed for {release_id}: {e}")

    rarity = calculate_rarity(discogs_have, discogs_want, discogs_for_sale)

    # Internal owners of this exact pressing
    records = await db.records.find(
        {"discogs_id": release_id},
        {"_id": 0, "id": 1, "user_id": 1, "is_unofficial": 1}
    ).to_list(200)

    # Smart Flag: also check internal records
    if not is_unofficial:
        is_unofficial = detect_unofficial({}, records)

    owner_ids = list(set(r.get("user_id") for r in records if r.get("user_id")))
    owners = []
    if owner_ids:
        owners = await db.users.find(
            {"id": {"$in": owner_ids[:20]}},
            {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
        ).to_list(20)

    # Internal Honeypot marketplace listings for this variant
    artist_re = re.compile(re.escape(artist), re.IGNORECASE)
    album_re = re.compile(re.escape(album), re.IGNORECASE)
    honeypot_query = {"artist": artist_re, "album": album_re, "status": "ACTIVE"}
    honeypot_listings = await db.listings.find(honeypot_query, {"_id": 0, "price": 1}).to_list(50)
    honeypot_count = len(honeypot_listings)
    honey_lowest = min((l.get("price", float("inf")) for l in honeypot_listings if l.get("price")), default=None)

    return {
        "release_id": release_id,
        "variant_overview": {
            "artist": artist,
            "album": album,
            "variant": variant,
            "year": year,
            "imageUrl": resolved_image.get("imageUrl"),
            "imageSmall": resolved_image.get("imageSmall"),
            "imageSource": resolved_image.get("imageSource"),
            "needsCoverPhoto": resolved_image.get("needsCoverPhoto", False),
            "format": fmt,
            "label": label,
            "catalog_number": catno,
            "barcode": barcode,
            "pressing_country": country,
            "discogs_id": release_id,
            "is_unofficial": is_unofficial,
        },
        "scarcity": {
            **rarity,
            "discogs_have": discogs_have,
            "discogs_want": discogs_want,
            "stats_source": stats_source,
            "master_id": master_id,
        },
        "honeypot": {
            "active_listings": honeypot_count,
            "honey_lowest": honey_lowest,
        },
        "value": {
            "discogs_median": discogs_market.get("median_value"),
            "discogs_low": discogs_market.get("low_value"),
            "discogs_high": discogs_market.get("high_value"),
        },
        "community": {
            "internal_owners_count": len(owner_ids),
            "owners": owners,
        },
    }


# ========== Variant Ownership & Actions ==========

@router.get("/ownership/{discogs_id}")
async def check_ownership(discogs_id: int, user=Depends(get_current_user)):
    """Check if the current user owns a variant, has it on ISO/wishlist."""
    if not user:
        return {"owned": False, "iso_status": None, "record_id": None, "iso_id": None}

    record = await db.records.find_one(
        {"user_id": user["id"], "discogs_id": discogs_id},
        {"_id": 0, "id": 1}
    )

    iso_item = await db.iso_items.find_one(
        {"user_id": user["id"], "discogs_id": discogs_id, "status": {"$in": ["OPEN", "WISHLIST"]}},
        {"_id": 0, "id": 1, "status": 1}
    )

    return {
        "owned": bool(record),
        "record_id": record["id"] if record else None,
        "iso_status": iso_item["status"] if iso_item else None,
        "iso_id": iso_item["id"] if iso_item else None,
    }


# ========== Variant Completion Tracker ==========

# Sleeve/packaging descriptors to strip when normalizing variant names
_STRIP_SUFFIXES = re.compile(
    r",?\s*(?:gatefold|tri-fold|die-cut|poster|insert|sticker|"
    r"pvc sleeve|inner sleeve|obi|hype sticker|download|booklet|"
    r"with (?:poster|booklet|insert|sticker)|stereo|mono|remaster(?:ed)?|"
    r"limited edition|special edition|deluxe edition|club edition|"
    r"reissue|repress|numbered)\s*$",
    re.IGNORECASE
)

_BRACKET_RE = re.compile(r"[\[\]()/]")
_MULTI_SPACE = re.compile(r"\s+")

# Filler words stripped during dedup key generation — not meaningful for variant identity
_FILLER_WORDS = {
    "vinyl", "colored", "coloured", "colour", "color", "pressed", "pressing",
    "edition", "version", "lp", "ep", "single", "record", "records",
    "gram", "heavyweight", "audiophile", "import", "standard",
    "w/", "with", "and", "the", "a", "an", "in", "on", "of",
}

# Weight descriptors (180g, 200g, etc.) — noise for variant identity
_WEIGHT_RE = re.compile(r"\b\d{2,3}\s*(?:g|gram|grams)\b", re.IGNORECASE)
# Format size descriptors (12", 7", 2xLP, etc.)
_FORMAT_SIZE_RE = re.compile(r'\b(?:\d+x?\s*(?:lp|ep)|\d+["″\']\s*)\b', re.IGNORECASE)


def _normalize_variant_name(text: str) -> str:
    """Normalize a format text string into a clean variant group name."""
    if not text:
        return "Standard Black Vinyl"
    cleaned = text.strip()
    for _ in range(3):
        cleaned = _STRIP_SUFFIXES.sub("", cleaned).strip().rstrip(",").strip()
    if not cleaned:
        return "Standard Black Vinyl"
    return cleaned.title()


def _dedup_key(name: str) -> str:
    """Create a lowercase dedup key: strip brackets, punctuation, filler words, weights."""
    s = _BRACKET_RE.sub(" ", name.lower())
    # Strip weight descriptors (180g, 200 gram, etc.)
    s = _WEIGHT_RE.sub(" ", s)
    # Strip format sizes (12", 7", 2xLP, etc.)
    s = _FORMAT_SIZE_RE.sub(" ", s)
    # Strip commas and other punctuation
    s = re.sub(r"[,;:.'\"]+", " ", s)
    s = _MULTI_SPACE.sub(" ", s).strip()
    # Remove filler words
    words = [w for w in s.split() if w not in _FILLER_WORDS and len(w) > 1]
    # Sort so "baby pink" == "pink baby"
    words = sorted(set(words))
    return " ".join(words)


def _merge_variant_groups(groups: dict) -> dict:
    """Merge groups whose dedup keys overlap, are subsets, or have high word similarity."""
    items = [(name, rids) for name, rids in groups.items()]
    keyed = [(_dedup_key(name), name, rids) for name, rids in items]

    merged = {}  # canonical_name -> set of release_ids
    used = set()

    # Sort by specificity: longer dedup key = more specific = better canonical name
    keyed.sort(key=lambda x: -len(x[0]))

    for i, (ki, ni, ri) in enumerate(keyed):
        if i in used:
            continue
        canon = ni
        combined_rids = list(ri)
        ki_words = set(ki.split())

        for j, (kj, nj, rj) in enumerate(keyed):
            if j <= i or j in used:
                continue
            kj_words = set(kj.split())

            should_merge = False
            if ki == kj:
                # Exact match — always merge
                should_merge = True
            elif kj_words and ki_words:
                smaller = kj_words if len(kj_words) <= len(ki_words) else ki_words
                larger = ki_words if len(kj_words) <= len(ki_words) else kj_words
                # Only merge via subset if the smaller has >= 50% of the larger's words
                # This prevents "black" from absorbing "gold splatter on black"
                if smaller <= larger and len(smaller) / len(larger) >= 0.5:
                    should_merge = True
                else:
                    # Jaccard similarity for fuzzy matching
                    intersection = ki_words & kj_words
                    union = ki_words | kj_words
                    jaccard = len(intersection) / len(union) if union else 0
                    if jaccard >= 0.6:
                        should_merge = True

            if should_merge:
                combined_rids.extend(rj)
                used.add(j)

        used.add(i)
        merged[canon] = combined_rids

    return merged


def _is_vinyl_version(version: dict) -> bool:
    major = version.get("major_formats", [])
    fmt = version.get("format", "")
    return "Vinyl" in major or "LP" in fmt or "12\"" in fmt


async def _fetch_release_color(release_id: int) -> str:
    """Get the color/variant text from a release, using cache."""
    cached = await db.discogs_releases.find_one(
        {"discogs_id": release_id}, {"_id": 0, "color_variant": 1}
    )
    if cached and cached.get("color_variant") is not None:
        return cached.get("color_variant") or ""

    # Fetch from API
    data = await asyncio.to_thread(get_discogs_release, release_id)
    if data:
        # Cache it
        cache_doc = {
            **data,
            "discogs_id": release_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.discogs_releases.update_one(
            {"discogs_id": release_id},
            {"$set": cache_doc},
            upsert=True,
        )
        return data.get("color_variant") or ""
    return ""


@router.get("/completion/{discogs_id}")
async def get_variant_completion(
    discogs_id: int,
    user=Depends(get_current_user),
):
    """Return variant completion data for an album, grouped by meaningful variant."""
    user_id = user["id"] if user else None

    # Check completion cache (valid for 10 minutes)
    cache_key = {"discogs_id": discogs_id, "user_id": user_id}
    cached = await db.completion_cache.find_one(cache_key, {"_id": 0})
    if cached:
        age = 0
        fetched_at = cached.get("fetched_at", "")
        if fetched_at:
            try:
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)).total_seconds()
            except (ValueError, TypeError):
                age = 999999
        if age < 600:  # 10 minute cache
            return cached.get("result", {})

    # Step 1: Get the release to find its master_id
    release = await _get_cached_discogs_release(discogs_id)
    if not release:
        return {"error": "Release not found", "variants": [], "completion": 0}

    master_id = release.get("master_id")
    if not master_id:
        # Fetch master_id directly from Discogs release API
        import requests as req
        try:
            headers = {"User-Agent": "WaxLog/1.0"}
            params = {"token": os.environ.get("DISCOGS_TOKEN", "")}
            r = req.get(f"https://api.discogs.com/releases/{discogs_id}", params=params, headers=headers, timeout=10)
            if r.status_code == 200:
                master_id = r.json().get("master_id")
                # Store master_id in cache for next time
                if master_id:
                    await db.discogs_releases.update_one(
                        {"discogs_id": discogs_id},
                        {"$set": {"master_id": master_id}},
                    )
        except Exception:
            pass

    if not master_id:
        # No master release — single release, 1 variant
        variant_name = _normalize_variant_name(release.get("color_variant"))
        owned = False
        if user:
            owned = bool(await db.records.find_one(
                {"user_id": user["id"], "discogs_id": discogs_id}, {"_id": 1}
            ))
        return {
            "album": release.get("title"),
            "artist": release.get("artist"),
            "master_id": None,
            "total_variants": 1,
            "owned_count": 1 if owned else 0,
            "completion_pct": 100 if owned else 0,
            "variants": [{
                "name": variant_name,
                "owned": owned,
                "release_ids": [discogs_id],
            }],
        }

    # Step 2: Fetch master versions (cached)
    cached_master = await db.master_versions.find_one(
        {"master_id": master_id}, {"_id": 0}
    )
    versions_data = None
    if cached_master:
        age = 0
        fetched_at = cached_master.get("fetched_at", "")
        if fetched_at:
            try:
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)).total_seconds()
            except (ValueError, TypeError):
                age = 999999
        if age < CACHE_TTL_HOURS * 3600:
            versions_data = cached_master.get("versions", [])

    if versions_data is None:
        raw_versions = await asyncio.to_thread(get_discogs_master_versions, master_id)
        if raw_versions:
            versions_data = raw_versions.get("versions", [])
            total_items = raw_versions.get("pagination", {}).get("items", 0)
            # Fetch additional pages if needed (up to 200 versions)
            if total_items > 100:
                page2 = await asyncio.to_thread(get_discogs_master_versions, master_id, 2, 100)
                if page2:
                    versions_data.extend(page2.get("versions", []))
            await db.master_versions.update_one(
                {"master_id": master_id},
                {"$set": {
                    "master_id": master_id,
                    "versions": versions_data,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True,
            )
        else:
            versions_data = []

    # Step 3: Filter to vinyl versions only
    vinyl_versions = [v for v in versions_data if _is_vinyl_version(v)]
    if not vinyl_versions:
        return {
            "album": release.get("title"),
            "artist": release.get("artist"),
            "master_id": master_id,
            "total_variants": 0,
            "owned_count": 0,
            "completion_pct": 0,
            "variants": [],
        }

    # Step 4: Fetch color data for each vinyl version (from cache or API, limited)
    release_ids = [v["id"] for v in vinyl_versions]

    # Check cache for all release IDs
    cached_releases = await db.discogs_releases.find(
        {"discogs_id": {"$in": release_ids}},
        {"_id": 0, "discogs_id": 1, "color_variant": 1}
    ).to_list(None)
    cached_map = {r["discogs_id"]: r.get("color_variant", "") for r in cached_releases}

    # Fetch uncached (limit to 20 to avoid timeout) — parallelized with rate-limiting semaphore
    uncached_ids = [rid for rid in release_ids if rid not in cached_map]
    fetch_limit = min(len(uncached_ids), 20)

    if uncached_ids[:fetch_limit]:
        sem = asyncio.Semaphore(5)  # Max 5 concurrent Discogs calls

        async def _fetch_one(rid):
            async with sem:
                color = await _fetch_release_color(rid)
                return rid, color

        tasks = [_fetch_one(rid) for rid in uncached_ids[:fetch_limit]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, tuple):
                rid, color = r
                cached_map[rid] = color

    # Step 5: Group by normalized variant name
    variant_groups = {}  # name -> list of release_ids
    for v in vinyl_versions:
        rid = v["id"]
        raw_color = cached_map.get(rid)
        fmt_str = v.get("format", "")
        # Use color from release data, or infer from format string
        if raw_color is None:
            # Infer from format descriptions
            if "Picture Disc" in fmt_str:
                raw_color = "Picture Disc"
            else:
                raw_color = ""
        name = _normalize_variant_name(raw_color)
        if name not in variant_groups:
            variant_groups[name] = []
        variant_groups[name].append(rid)

    # Step 5b: Deduplicate — merge groups like "Baby Pink", "Pink", "Pink [Baby Pink]"
    variant_groups = _merge_variant_groups(variant_groups)

    # Step 6: Check user ownership
    user_discogs_ids = set()
    if user:
        user_records = await db.records.find(
            {"user_id": user["id"], "discogs_id": {"$in": release_ids}},
            {"_id": 0, "discogs_id": 1}
        ).to_list(None)
        user_discogs_ids = set(r["discogs_id"] for r in user_records)

    # Build result
    variants = []
    owned_count = 0
    for name, rids in sorted(variant_groups.items()):
        owned = bool(user_discogs_ids & set(rids))
        if owned:
            owned_count += 1
        variants.append({
            "name": name,
            "owned": owned,
            "release_ids": rids,
        })

    # Sort: owned first, then alphabetical
    variants.sort(key=lambda v: (not v["owned"], v["name"]))

    total = len(variants)
    pct = round((owned_count / total) * 100) if total else 0

    result = {
        "album": release.get("title"),
        "artist": release.get("artist"),
        "master_id": master_id,
        "total_variants": total,
        "owned_count": owned_count,
        "completion_pct": pct,
        "variants": variants,
    }

    # Cache result
    await db.completion_cache.update_one(
        {"discogs_id": discogs_id, "user_id": user_id},
        {"$set": {
            "discogs_id": discogs_id,
            "user_id": user_id,
            "result": result,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    return result


# ========== SSR for bots ==========

@router.get("/ssr/{artist_slug}/{album_slug}/{variant_slug}", response_class=HTMLResponse)
async def ssr_variant_page(artist_slug: str, album_slug: str, variant_slug: str):
    """SSR HTML for social preview bots — metadata sourced from Discogs."""
    data = await get_variant_page(artist_slug, album_slug, variant_slug)
    overview = data["variant_overview"]
    value = data["value"]
    seo = data["seo"]

    artist = overview["artist"]
    album = overview["album"]
    variant = overview["variant"]
    year = overview.get("year", "")
    image = _e(seo["image"])
    url = f"{SITE_URL}{seo['canonical']}"

    extra_meta = f"""<meta name="vinyl:artist" content="{_e(artist)}"/>
<meta name="vinyl:album" content="{_e(album)}"/>
<meta name="vinyl:variant" content="{_e(variant)}"/>
<meta name="vinyl:format" content="{_e(overview.get('format', 'Vinyl'))}"/>"""
    if year:
        extra_meta += f'\n<meta name="vinyl:release_year" content="{_e(year)}"/>'
    if overview.get("label"):
        extra_meta += f'\n<meta name="vinyl:label" content="{_e(overview["label"])}"/>'
    if overview.get("catalog_number"):
        extra_meta += f'\n<meta name="vinyl:catalog_number" content="{_e(overview["catalog_number"])}"/>'
    if overview.get("pressing_country"):
        extra_meta += f'\n<meta name="vinyl:pressing_country" content="{_e(overview["pressing_country"])}"/>'
    if overview.get("discogs_id"):
        extra_meta += f'\n<meta name="vinyl:discogs_id" content="{overview["discogs_id"]}"/>'

    # Product meta from listings or Discogs market data
    listings = data["marketplace"]["active_listings"]
    if listings:
        listing_prices = [item["price"] for item in listings if item.get("price")]
        cheapest = min(listing_prices) if listing_prices else None
        if cheapest:
            extra_meta += f'\n<meta property="product:price:amount" content="{cheapest}"/>'
            extra_meta += '\n<meta property="product:price:currency" content="USD"/>'
            extra_meta += '\n<meta property="product:availability" content="in stock"/>'
    elif value.get("discogs_median"):
        extra_meta += f'\n<meta property="product:price:amount" content="{value["discogs_median"]}"/>'
        extra_meta += '\n<meta property="product:price:currency" content="USD"/>'

    # JSON-LD
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"{artist} — {album} ({variant})",
        "image": seo["image"],
        "category": "Vinyl Record",
        "url": url,
        "brand": {"@type": "MusicGroup", "name": artist},
        "description": seo["description"],
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Variant", "value": variant},
            {"@type": "PropertyValue", "name": "Format", "value": overview.get("format", "Vinyl")},
        ],
    }
    if year:
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Release Year", "value": str(year)})
    if overview.get("pressing_country"):
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Country", "value": overview["pressing_country"]})
    if overview.get("discogs_id"):
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Discogs Release ID", "value": str(overview["discogs_id"])})

    # Offers from internal data or Discogs
    if value.get("average_value"):
        json_ld["offers"] = {
            "@type": "AggregateOffer",
            "lowPrice": str(value["lowest_sale"] or value["average_value"]),
            "highPrice": str(value["highest_sale"] or value["average_value"]),
            "priceCurrency": "USD",
            "offerCount": str(value["recent_sales_count"]),
        }
    elif value.get("discogs_median"):
        json_ld["offers"] = {
            "@type": "AggregateOffer",
            "lowPrice": str(value.get("discogs_low", value["discogs_median"])),
            "highPrice": str(value.get("discogs_high", value["discogs_median"])),
            "priceCurrency": "USD",
        }
    elif listings:
        lp = [item["price"] for item in listings if item.get("price")]
        if lp:
            json_ld["offers"] = {
                "@type": "AggregateOffer",
                "lowPrice": str(min(lp)),
                "highPrice": str(max(lp)),
                "priceCurrency": "USD",
                "offerCount": str(len(lp)),
                "availability": "https://schema.org/InStock",
            }

    ld_script = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>'
    title = _e(seo["title"])
    desc = _e(seo["description"])

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title} | {_e(SITE_NAME)}</title>
<meta name="description" content="{desc}"/>
<link rel="canonical" href="{_e(url)}"/>
<meta property="og:site_name" content="{_e(SITE_NAME)}"/>
<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{desc}"/>
<meta property="og:image" content="{image}"/>
<meta property="og:url" content="{_e(url)}"/>
<meta property="og:type" content="product"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{title}"/>
<meta name="twitter:description" content="{desc}"/>
<meta name="twitter:image" content="{image}"/>
{extra_meta}
{ld_script}
</head>
<body>
<h1>{title}</h1>
<p>{desc}</p>
<a href="{_e(url)}">View on {_e(SITE_NAME)}</a>
</body>
</html>"""

    return HTMLResponse(html_out)
