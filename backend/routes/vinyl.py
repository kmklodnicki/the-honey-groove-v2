"""Vinyl Variant & Value Pages — SEO-optimized canonical pages per variant.

Each variant gets a dedicated page at /vinyl/{artist}/{album}/{variant}
combining variant details, marketplace listings, price data, demand, and activity.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from database import db
import re
import json
import html as html_mod

router = APIRouter(prefix="/vinyl")

SITE_NAME = "The Honey Groove"
SITE_URL = "https://thehoneygroove.com"
DEFAULT_IMAGE = f"{SITE_URL}/og-image.png"


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[''`]", "", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def unslugify(slug: str) -> str:
    """Convert slug back to approximate search term."""
    return slug.replace("-", " ").strip()


def _e(text):
    if text is None:
        return ""
    return html_mod.escape(str(text), quote=True)


async def _find_variant_records(artist_slug: str, album_slug: str, variant_slug: str):
    """Find all records matching an artist/album/variant slug combination."""
    artist_term = unslugify(artist_slug)
    album_term = unslugify(album_slug)
    variant_term = unslugify(variant_slug)

    # Build a regex-based query for flexible matching
    artist_re = re.compile(re.escape(artist_term), re.IGNORECASE)
    album_re = re.compile(re.escape(album_term), re.IGNORECASE)
    variant_re = re.compile(re.escape(variant_term), re.IGNORECASE)

    records = await db.records.find(
        {
            "artist": artist_re,
            "title": album_re,
            "color_variant": variant_re,
        },
        {"_id": 0}
    ).to_list(500)

    return records, artist_term, album_term, variant_term


@router.get("/{artist_slug}/{album_slug}/{variant_slug}")
async def get_variant_page(artist_slug: str, album_slug: str, variant_slug: str):
    """Return all data for a vinyl variant page."""
    records, artist_term, album_term, variant_term = await _find_variant_records(
        artist_slug, album_slug, variant_slug
    )

    # Use first record as canonical source for metadata
    canonical = records[0] if records else None
    artist = canonical.get("artist", artist_term.title()) if canonical else artist_term.title()
    album = canonical.get("title", album_term.title()) if canonical else album_term.title()
    variant = canonical.get("color_variant", variant_term.title()) if canonical else variant_term.title()
    year = canonical.get("year") if canonical else None
    cover_url = canonical.get("cover_url") if canonical else None
    fmt = canonical.get("format", "Vinyl") if canonical else "Vinyl"
    label = canonical.get("label") if canonical else None
    catno = canonical.get("catno") if canonical else None
    discogs_id = canonical.get("discogs_id") if canonical else None

    # Unique owners
    owner_ids = list(set(r.get("user_id") for r in records if r.get("user_id")))
    owners_count = len(owner_ids)

    # Fetch owner profiles (limit to 20 for display)
    owners = []
    if owner_ids:
        owners = await db.users.find(
            {"id": {"$in": owner_ids[:20]}},
            {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
        ).to_list(20)

    # Marketplace listings matching this variant
    listing_query = {
        "artist": re.compile(re.escape(artist_term), re.IGNORECASE),
        "album": re.compile(re.escape(album_term), re.IGNORECASE),
        "status": "ACTIVE",
    }
    active_listings = await db.listings.find(listing_query, {"_id": 0}).sort("created_at", -1).to_list(50)
    # Filter by variant if possible
    variant_listings = [
        listing for listing in active_listings
        if variant_re_match(listing, variant_term)
    ]
    # Fall back to all listings for this album if no variant-specific ones
    if not variant_listings:
        variant_listings = active_listings

    # Enrich listings with seller info
    for listing in variant_listings:
        seller = await db.users.find_one(
            {"id": listing.get("user_id")},
            {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
        )
        listing["seller"] = seller

    # Sold listings for price data
    sold_query = {
        "artist": re.compile(re.escape(artist_term), re.IGNORECASE),
        "album": re.compile(re.escape(album_term), re.IGNORECASE),
        "status": "SOLD",
    }
    sold_listings = await db.listings.find(sold_query, {"_id": 0, "price": 1, "created_at": 1}).to_list(200)
    prices = [s["price"] for s in sold_listings if s.get("price")]

    value_data = {
        "recent_sales_count": len(prices),
        "average_value": round(sum(prices) / len(prices), 2) if prices else None,
        "highest_sale": max(prices) if prices else None,
        "lowest_sale": min(prices) if prices else None,
    }

    # ISO demand — how many collectors are searching for this
    iso_query = {
        "artist": re.compile(re.escape(artist_term), re.IGNORECASE),
        "album": re.compile(re.escape(album_term), re.IGNORECASE),
        "status": {"$in": ["OPEN", "WISHLIST"]},
    }
    iso_count = await db.iso_items.count_documents(iso_query)

    # Hive posts mentioning this record
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
            "discogs_id": discogs_id,
        },
        "marketplace": {
            "active_listings": variant_listings,
            "listing_count": len(variant_listings),
        },
        "value": value_data,
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
            "description": build_seo_description(artist, album, variant, year, owners_count, iso_count, value_data),
            "canonical": f"/vinyl/{artist_slug}/{album_slug}/{variant_slug}",
            "image": cover_url or DEFAULT_IMAGE,
        },
    }


def variant_re_match(listing: dict, variant_term: str) -> bool:
    """Check if a listing matches a variant term."""
    vt = variant_term.lower()
    for field in ["pressing_notes", "color_variant", "description"]:
        val = listing.get(field, "")
        if val and vt in val.lower():
            return True
    return False


def build_seo_description(artist, album, variant, year, owners, iso_count, value):
    parts = [f"View the {variant} variant of {album} by {artist} on vinyl."]
    if year:
        parts.append(f"Released {year}.")
    if owners:
        parts.append(f"{owners} collector{'s' if owners != 1 else ''} own this pressing.")
    if iso_count:
        parts.append(f"{iso_count} collector{'s' if iso_count != 1 else ''} searching for it.")
    if value.get("average_value"):
        parts.append(f"Average market value: ${value['average_value']:.2f}.")
    return " ".join(parts)


# ========== SSR for bots ==========

@router.get("/ssr/{artist_slug}/{album_slug}/{variant_slug}", response_class=HTMLResponse)
async def ssr_variant_page(artist_slug: str, album_slug: str, variant_slug: str):
    """SSR HTML for social preview bots."""
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

    # Vinyl-specific meta
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

    # Product meta if listings exist
    listings = data["marketplace"]["active_listings"]
    if listings:
        listing_prices = [item["price"] for item in listings if item.get("price")]
        cheapest = min(listing_prices) if listing_prices else None
        if cheapest:
            extra_meta += f'\n<meta property="product:price:amount" content="{cheapest}"/>'
            extra_meta += '\n<meta property="product:price:currency" content="USD"/>'
            extra_meta += '\n<meta property="product:availability" content="in stock"/>'

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
    if value.get("average_value"):
        json_ld["offers"] = {
            "@type": "AggregateOffer",
            "lowPrice": str(value["lowest_sale"]) if value.get("lowest_sale") else str(value["average_value"]),
            "highPrice": str(value["highest_sale"]) if value.get("highest_sale") else str(value["average_value"]),
            "priceCurrency": "USD",
            "offerCount": str(value["recent_sales_count"]),
        }
    elif listings:
        listing_price_vals = [item["price"] for item in listings if item.get("price")]
        if listing_price_vals:
            json_ld["offers"] = {
                "@type": "AggregateOffer",
                "lowPrice": str(min(listing_price_vals)),
                "highPrice": str(max(listing_price_vals)),
                "priceCurrency": "USD",
                "offerCount": str(len(listing_price_vals)),
                "availability": "https://schema.org/InStock",
            }

    ld_script = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>'

    title = _e(seo["title"])
    desc = _e(seo["description"])

    html = f"""<!DOCTYPE html>
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

    return HTMLResponse(html)
