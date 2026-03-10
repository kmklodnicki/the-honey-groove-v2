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
from database import db, get_discogs_release, get_discogs_market_data, get_discogs_master_versions, logger, get_current_user
from datetime import datetime, timezone
import asyncio
import os
import re
import json
import html as html_mod

router = APIRouter(prefix="/vinyl")

SITE_NAME = "The Honey Groove"
SITE_URL = "https://thehoneygroove.com"
DEFAULT_IMAGE = f"{SITE_URL}/og-image.png"
CACHE_TTL_HOURS = 24

# ── Rarity Score System (Discogs-sourced) ──
RARITY_TIERS = [
    (13, "Ultra Rare"),
    (10, "Very Rare"),
    (7, "Rare"),
    (4, "Uncommon"),
    (0, "Common"),
]


def _owner_score(have: int) -> int:
    """Fewer Discogs owners = rarer."""
    if have <= 50:
        return 5
    if have <= 200:
        return 4
    if have <= 1000:
        return 3
    if have <= 5000:
        return 2
    return 1


def _demand_score(want: int, have: int) -> int:
    """Higher want-to-have ratio on Discogs = rarer."""
    ratio = want / max(have, 1)
    if ratio > 10:
        return 5
    if ratio > 5:
        return 4
    if ratio > 2:
        return 3
    if ratio > 0.5:
        return 2
    return 1


def _supply_score(num_for_sale: int) -> int:
    """Fewer Discogs marketplace listings = rarer."""
    if num_for_sale == 0:
        return 5
    if num_for_sale <= 5:
        return 4
    if num_for_sale <= 20:
        return 3
    if num_for_sale <= 50:
        return 2
    return 1


def calculate_rarity(have: int, want: int, num_for_sale: int) -> dict:
    total = _owner_score(have) + _demand_score(want, have) + _supply_score(num_for_sale)
    tier = "Common"
    for threshold, label in RARITY_TIERS:
        if total >= threshold:
            tier = label
            break
    return {
        "score": total,
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


async def _resolve_discogs_id(artist_slug: str, album_slug: str, variant_slug: str):
    """Find a Discogs release ID from URL slugs by matching records in the DB."""
    artist_term = unslugify(artist_slug)
    album_term = unslugify(album_slug)
    variant_term = unslugify(variant_slug)

    artist_re = re.compile(re.escape(artist_term), re.IGNORECASE)
    album_re = re.compile(re.escape(album_term), re.IGNORECASE)
    variant_re = re.compile(re.escape(variant_term), re.IGNORECASE)

    # Search records collection for matching discogs_id
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
    variant = discogs_data.get("color_variant") or canonical_record.get("color_variant") or variant_term.title()
    year = discogs_data.get("year") or canonical_record.get("year")
    country = discogs_data.get("country") or canonical_record.get("country")
    notes = discogs_data.get("notes")

    # Cover image: Discogs authoritative, fall back to internal
    cover_url = discogs_data.get("cover_url") or canonical_record.get("cover_url")

    # Label & catno from Discogs
    label_raw = discogs_data.get("label")
    if isinstance(label_raw, list):
        label = label_raw[0] if label_raw else None
    else:
        label = label_raw or canonical_record.get("label")

    catno = discogs_data.get("catno") or canonical_record.get("catno")

    # Format from Discogs
    format_raw = discogs_data.get("format")
    if isinstance(format_raw, list):
        fmt = format_raw[0] if format_raw else "Vinyl"
    else:
        fmt = format_raw or canonical_record.get("format") or "Vinyl"

    # Unique owners
    owner_ids = list(set(r.get("user_id") for r in records if r.get("user_id")))
    owners_count = len(owner_ids)

    owners = []
    if owner_ids:
        owners = await db.users.find(
            {"id": {"$in": owner_ids[:20]}},
            {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
        ).to_list(20)

    # Marketplace listings
    artist_re = re.compile(re.escape(artist_term), re.IGNORECASE)
    album_re = re.compile(re.escape(album_term), re.IGNORECASE)

    listing_query = {"artist": artist_re, "album": album_re, "status": "ACTIVE"}
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
    sold_query = {"artist": artist_re, "album": album_re, "status": "SOLD"}
    sold_listings = await db.listings.find(sold_query, {"_id": 0, "price": 1, "created_at": 1}).to_list(200)
    prices = [s["price"] for s in sold_listings if s.get("price")]

    internal_value = {
        "recent_sales_count": len(prices),
        "average_value": round(sum(prices) / len(prices), 2) if prices else None,
        "highest_sale": max(prices) if prices else None,
        "lowest_sale": min(prices) if prices else None,
    }

    # ISO demand
    iso_query = {"artist": artist_re, "album": album_re, "status": {"$in": ["OPEN", "WISHLIST"]}}
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
            "pressing_country": country,
            "discogs_id": discogs_id,
            "notes": notes[:300] if notes else None,
        },
        "rarity": rarity,
        "marketplace": {
            "active_listings": variant_listings,
            "listing_count": len(variant_listings),
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


def _normalize_variant_name(text: str) -> str:
    """Normalize a format text string into a clean variant group name."""
    if not text:
        return "Standard Black Vinyl"
    # Strip sleeve/packaging suffixes iteratively
    cleaned = text.strip()
    for _ in range(3):
        cleaned = _STRIP_SUFFIXES.sub("", cleaned).strip().rstrip(",").strip()
    if not cleaned:
        return "Standard Black Vinyl"
    # Title-case
    return cleaned.title()


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

    # Fetch uncached (limit to 20 to avoid timeout)
    uncached_ids = [rid for rid in release_ids if rid not in cached_map]
    fetch_limit = min(len(uncached_ids), 20)
    for rid in uncached_ids[:fetch_limit]:
        color = await _fetch_release_color(rid)
        cached_map[rid] = color
        await asyncio.sleep(0.3)  # Rate limit

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

    return {
        "album": release.get("title"),
        "artist": release.get("artist"),
        "master_id": master_id,
        "total_variants": total,
        "owned_count": owned_count,
        "completion_pct": pct,
        "variants": variants,
    }


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
