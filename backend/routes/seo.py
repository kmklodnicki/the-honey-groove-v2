"""SEO & SSR metadata routes for bot/crawler preview rendering.

Serves pre-rendered HTML with OG tags, Twitter Cards, JSON-LD, and
vinyl-specific metadata for social preview bots (iMessage, Discord,
Slack, Twitter/X, Facebook) and search engine crawlers.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from database import db, logger
import json
import html as html_mod
import os

router = APIRouter()

SITE_NAME = "The Honey Groove"
SITE_URL = os.environ.get("FRONTEND_URL", "https://thehoneygroove.com")
DEFAULT_IMAGE = f"{SITE_URL}/og-image.png"
DEFAULT_DESC = "The vinyl social club, finally. Track your collection, discover pressings, and connect with collectors worldwide."

# Known bot user agents
BOT_USER_AGENTS = [
    "twitterbot", "facebookexternalhit", "linkedinbot", "slackbot",
    "discordbot", "telegrambot", "whatsapp", "googlebot", "bingbot",
    "yandexbot", "baiduspider", "duckduckbot", "applebot",
    "imessagebot", "pinterestbot", "redditbot", "tumblr",
    "embedly", "showyoubot", "outbrain", "quora link preview",
    "rogerbot", "ahrefsbot", "semrushbot", "preview",
]


def _e(text):
    """HTML-escape a string, handling None."""
    if text is None:
        return ""
    return html_mod.escape(str(text), quote=True)


def _build_html(
    title: str,
    description: str,
    url: str,
    image: str = DEFAULT_IMAGE,
    og_type: str = "website",
    extra_meta: str = "",
    json_ld: dict = None,
    canonical: str = None,
):
    """Build a minimal HTML page with full metadata for crawlers."""
    canon = canonical or url
    ld_script = ""
    if json_ld:
        ld_script = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_e(title)}</title>
<meta name="description" content="{_e(description)}"/>
<link rel="canonical" href="{_e(canon)}"/>

<!-- Open Graph -->
<meta property="og:site_name" content="{_e(SITE_NAME)}"/>
<meta property="og:title" content="{_e(title)}"/>
<meta property="og:description" content="{_e(description)}"/>
<meta property="og:image" content="{_e(image)}"/>
<meta property="og:url" content="{_e(url)}"/>
<meta property="og:type" content="{_e(og_type)}"/>

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{_e(title)}"/>
<meta name="twitter:description" content="{_e(description)}"/>
<meta name="twitter:image" content="{_e(image)}"/>

{extra_meta}
{ld_script}
</head>
<body>
<h1>{_e(title)}</h1>
<p>{_e(description)}</p>
<a href="{_e(url)}">View on The Honey Groove</a>
</body>
</html>"""


def _resolve_image(url: str) -> str:
    """Resolve a relative image URL to an absolute one."""
    if not url:
        return DEFAULT_IMAGE
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        return f"{SITE_URL}{url}"
    return f"{SITE_URL}/{url}"


def _vinyl_meta(data: dict) -> str:
    """Build vinyl-specific meta tags from a data dict."""
    tags = []
    field_map = {
        "artist": "vinyl:artist",
        "album": "vinyl:album",
        "title": "vinyl:album",
        "variant": "vinyl:variant",
        "color_variant": "vinyl:variant",
        "color": "vinyl:color",
        "year": "vinyl:release_year",
        "label": "vinyl:label",
        "catno": "vinyl:catalog_number",
        "format": "vinyl:format",
        "rpm": "vinyl:speed",
        "disc_count": "vinyl:disc_count",
        "pressing_country": "vinyl:pressing_country",
        "condition": "vinyl:media_condition",
        "sleeve_condition": "vinyl:sleeve_condition",
    }
    seen_names = set()
    for key, meta_name in field_map.items():
        val = data.get(key)
        if val and meta_name not in seen_names:
            tags.append(f'<meta name="{_e(meta_name)}" content="{_e(val)}"/>')
            seen_names.add(meta_name)

    # Default format tag
    if "vinyl:format" not in seen_names and data.get("format", "Vinyl"):
        tags.append('<meta name="vinyl:format" content="Vinyl"/>')

    return "\n".join(tags)


def _condition_meta(data: dict) -> str:
    """Build condition metadata tags."""
    tags = []
    if data.get("condition"):
        tags.append(f'<meta name="vinyl:media_condition" content="{_e(data["condition"])}"/>')
    if data.get("sleeve_condition"):
        tags.append(f'<meta name="vinyl:sleeve_condition" content="{_e(data["sleeve_condition"])}"/>')
    graded = "true" if data.get("condition") else "false"
    tags.append(f'<meta name="vinyl:graded" content="{graded}"/>')
    return "\n".join(tags)


def _product_meta(data: dict) -> str:
    """Build marketplace product meta tags."""
    tags = []
    if data.get("price"):
        tags.append(f'<meta property="product:price:amount" content="{data["price"]}"/>')
        tags.append('<meta property="product:price:currency" content="USD"/>')
    avail = "in stock" if data.get("status") == "ACTIVE" else "out of stock"
    tags.append(f'<meta property="product:availability" content="{avail}"/>')
    if data.get("condition"):
        tags.append(f'<meta property="product:condition" content="{_e(data["condition"])}"/>')
    return "\n".join(tags)


def _trade_meta(data: dict) -> str:
    """Build trade metadata tags."""
    tags = []
    listing_type = data.get("listing_type", "")
    if listing_type == "TRADE" or listing_type == "MAKE_OFFER":
        tags.append('<meta name="trade:available" content="true"/>')
        tags.append('<meta name="trade:trade_type" content="swap"/>')
        tags.append('<meta name="trade:negotiable" content="true"/>')
        if data.get("pressing_notes"):
            tags.append(f'<meta name="trade:iso" content="{_e(data["pressing_notes"])}"/>')
    return "\n".join(tags)


def _post_meta(data: dict) -> str:
    """Build Hive post metadata tags."""
    tags = ['<meta name="post:type" content="vinyl"/>']
    if data.get("record_artist") or data.get("artist"):
        tags.append(f'<meta name="post:artist" content="{_e(data.get("record_artist") or data.get("artist"))}"/>')
    if data.get("record_title") or data.get("album") or data.get("title"):
        tags.append(f'<meta name="post:album" content="{_e(data.get("record_title") or data.get("album") or data.get("title"))}"/>')
    if data.get("color_variant"):
        tags.append(f'<meta name="post:variant" content="{_e(data["color_variant"])}"/>')
    return "\n".join(tags)


def _collector_meta(data: dict) -> str:
    """Build user/collector metadata tags."""
    tags = []
    if data.get("username"):
        tags.append(f'<meta name="collector:username" content="{_e(data["username"])}"/>')
    if data.get("collection_count") is not None:
        tags.append(f'<meta name="collector:collection_size" content="{data["collection_count"]}"/>')
    if data.get("iso_count") is not None:
        tags.append(f'<meta name="collector:iso_count" content="{data["iso_count"]}"/>')
    return "\n".join(tags)


# ========== LISTING SSR ==========

@router.get("/ssr/listing/{listing_id}", response_class=HTMLResponse)
async def ssr_listing(listing_id: str):
    """SSR metadata page for marketplace listings."""
    listing = await db.listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        return HTMLResponse(_build_html(
            f"Listing Not Found | {SITE_NAME}",
            DEFAULT_DESC,
            f"{SITE_URL}/honeypot",
        ), status_code=404)

    artist = listing.get("artist", "Unknown Artist")
    album = listing.get("album", "Unknown Album")
    variant = listing.get("pressing_notes") or listing.get("color_variant") or ""
    condition = listing.get("condition", "")
    price = listing.get("price")
    listing_type = listing.get("listing_type", "BUY_NOW")
    year = listing.get("year", "")

    # Build SEO-optimized title for variant-specific searches
    title_parts = [f"{artist} - {album}"]
    if variant:
        title_parts.append(f"({variant})")
    if listing_type == "TRADE":
        title_parts.append("For Trade")
    elif price:
        title_parts.append(f"${price:.2f}")
    title_parts.append(f"| {SITE_NAME}")
    title = " ".join(title_parts)

    # Build description for search intent
    desc_parts = []
    if listing_type == "TRADE":
        desc_parts.append(f"{artist} - {album} available for trade on {SITE_NAME}.")
    elif price:
        desc_parts.append(f"Buy {artist} - {album} for ${price:.2f} on {SITE_NAME}.")
    else:
        desc_parts.append(f"{artist} - {album} for sale on {SITE_NAME}.")
    if variant:
        desc_parts.append(f"Pressing: {variant}.")
    if condition:
        desc_parts.append(f"Condition: {condition}.")
    if year:
        desc_parts.append(f"Year: {year}.")
    description = " ".join(desc_parts)

    url = f"{SITE_URL}/honeypot/listing/{listing_id}"
    photos = listing.get("photo_urls", [])
    image = _resolve_image(photos[0] if photos else listing.get("cover_url"))

    # Fetch seller info
    seller = await db.users.find_one({"id": listing.get("user_id")}, {"_id": 0, "username": 1})
    seller_name = seller.get("username", "Unknown") if seller else "Unknown"

    # Additional Discogs data if available
    discogs_data = {}
    if listing.get("discogs_id"):
        record = await db.records.find_one({"discogs_id": listing["discogs_id"]}, {"_id": 0})
        if record:
            discogs_data = record

    # Build all metadata
    all_meta_data = {**listing, **discogs_data}
    extra_meta = "\n".join(filter(None, [
        _vinyl_meta(all_meta_data),
        _condition_meta(listing),
        _product_meta(listing),
        _trade_meta(listing),
    ]))

    # JSON-LD Product schema
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"{artist} - {album}" + (f" ({variant})" if variant else ""),
        "image": image,
        "description": description,
        "category": "Vinyl Record",
        "brand": {
            "@type": "MusicGroup",
            "name": artist,
        },
        "url": url,
        "additionalProperty": [],
    }

    if variant:
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Variant", "value": variant})
    if listing.get("color_variant"):
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Color", "value": listing["color_variant"]})
    if year:
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Release Year", "value": str(year)})
    if condition:
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Condition", "value": condition})

    if listing_type == "TRADE":
        json_ld["offers"] = {
            "@type": "Offer",
            "availability": "https://schema.org/InStock" if listing.get("status") == "ACTIVE" else "https://schema.org/SoldOut",
            "description": "Available for trade",
            "seller": {"@type": "Person", "name": seller_name},
        }
    elif price:
        json_ld["offers"] = {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock" if listing.get("status") == "ACTIVE" else "https://schema.org/SoldOut",
            "itemCondition": "https://schema.org/UsedCondition",
            "seller": {"@type": "Person", "name": seller_name},
        }

    return HTMLResponse(_build_html(title, description, url, image, "product", extra_meta, json_ld))


# ========== RECORD DETAIL SSR ==========

@router.get("/ssr/record/{record_id}", response_class=HTMLResponse)
async def ssr_record(record_id: str):
    """SSR metadata page for record detail/variant pages."""
    record = await db.records.find_one({"id": record_id}, {"_id": 0})
    if not record:
        return HTMLResponse(_build_html(
            f"Record Not Found | {SITE_NAME}",
            DEFAULT_DESC,
            f"{SITE_URL}/collection",
        ), status_code=404)

    artist = record.get("artist", "Unknown Artist")
    album = record.get("title", "Unknown Album")
    variant = record.get("color_variant", "")
    year = record.get("year", "")
    fmt = record.get("format", "Vinyl")

    title_parts = [f"{artist} - {album}"]
    if variant:
        title_parts.append(f"({variant})")
    if year:
        title_parts.append(f"[{year}]")
    title_parts.append(f"| {SITE_NAME}")
    title = " ".join(title_parts)

    desc_parts = [f"{artist} - {album}"]
    if variant:
        desc_parts.append(f"- {variant} pressing")
    if year:
        desc_parts.append(f"({year})")
    desc_parts.append(f"in a collector's vinyl library on {SITE_NAME}.")
    description = " ".join(desc_parts)

    url = f"{SITE_URL}/record/{record_id}"
    image = _resolve_image(record.get("cover_url"))

    extra_meta = _vinyl_meta({**record, "album": album})

    # JSON-LD MusicRecording
    json_ld = {
        "@context": "https://schema.org",
        "@type": "MusicRecording",
        "name": album,
        "byArtist": {"@type": "MusicGroup", "name": artist},
        "image": image,
        "url": url,
        "datePublished": str(year) if year else None,
        "recordingOf": {"@type": "MusicComposition", "name": album},
        "additionalProperty": [],
    }
    if variant:
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Variant", "value": variant})
    if fmt:
        json_ld["additionalProperty"].append({"@type": "PropertyValue", "name": "Format", "value": fmt})
    # Clean None values
    json_ld = {k: v for k, v in json_ld.items() if v is not None}

    return HTMLResponse(_build_html(title, description, url, image, "music.song", extra_meta, json_ld))


# ========== PROFILE SSR ==========

@router.get("/ssr/profile/{username}", response_class=HTMLResponse)
async def ssr_profile(username: str):
    """SSR metadata page for user profiles."""
    user = await db.users.find_one(
        {"username": username.lower()},
        {"_id": 0, "password_hash": 0}
    )
    if not user:
        return HTMLResponse(_build_html(
            f"Collector Not Found | {SITE_NAME}",
            DEFAULT_DESC,
            f"{SITE_URL}/profile/{username}",
        ), status_code=404)

    uname = user.get("username", username)
    bio = user.get("bio", "")
    location = user.get("location") or user.get("city") or ""
    avatar = _resolve_image(user.get("avatar_url"))

    # Fetch stats
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    iso_count = await db.iso_items.count_documents({"user_id": user["id"], "status": {"$in": ["OPEN", "WISHLIST"]}})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})

    title_parts = [f"@{uname}"]
    if user.get("title_label"):
        title_parts.append(f"- {user['title_label']}")
    title_parts.append(f"| {collection_count} Records")
    title_parts.append(f"| {SITE_NAME}")
    title = " ".join(title_parts)

    desc_parts = [f"@{uname}'s vinyl collection on {SITE_NAME}."]
    if bio:
        desc_parts.append(bio[:160])
    desc_parts.append(f"{collection_count} records collected.")
    if location:
        desc_parts.append(f"Based in {location}.")
    description = " ".join(desc_parts)

    url = f"{SITE_URL}/profile/{uname}"

    extra_meta = _collector_meta({
        "username": uname,
        "collection_count": collection_count,
        "iso_count": iso_count,
    })

    # JSON-LD ProfilePage
    json_ld = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "name": f"@{uname}",
        "url": url,
        "image": avatar,
        "description": description,
        "mainEntity": {
            "@type": "Person",
            "name": uname,
            "url": url,
            "image": avatar,
            "interactionStatistic": [
                {
                    "@type": "InteractionCounter",
                    "interactionType": "https://schema.org/FollowAction",
                    "userInteractionCount": followers_count,
                },
            ],
        },
    }

    return HTMLResponse(_build_html(title, description, url, avatar, "profile", extra_meta, json_ld))


# ========== HIVE POST SSR ==========

@router.get("/ssr/post/{post_id}", response_class=HTMLResponse)
async def ssr_post(post_id: str):
    """SSR metadata page for Hive posts."""
    post = await db.posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        return HTMLResponse(_build_html(
            f"Post Not Found | {SITE_NAME}",
            DEFAULT_DESC,
            f"{SITE_URL}/hive",
        ), status_code=404)

    # Get post author
    author = await db.users.find_one({"id": post.get("user_id")}, {"_id": 0, "username": 1, "avatar_url": 1})
    author_name = author.get("username", "Unknown") if author else "Unknown"

    post_type = post.get("post_type", "")
    caption = post.get("caption") or post.get("content") or ""
    record_title = post.get("record_title") or ""
    record_artist = post.get("record_artist") or ""
    variant = post.get("color_variant") or ""
    image = _resolve_image(post.get("image_url") or post.get("cover_url"))

    # Enrich with record data if available
    if post.get("record_id") and not record_title:
        record = await db.records.find_one({"id": post["record_id"]}, {"_id": 0})
        if record:
            record_title = record.get("title", "")
            record_artist = record.get("artist", "")
            variant = variant or record.get("color_variant", "")
            if not post.get("cover_url"):
                image = _resolve_image(record.get("cover_url"))

    # Build title based on post type
    type_labels = {
        "NOW_SPINNING": "Now Spinning",
        "ADDED_TO_COLLECTION": "Added to Collection",
        "NEW_HAUL": "New Haul",
        "ISO": "ISO",
        "A_NOTE": "A Note",
        "DAILY_PROMPT": "Daily Prompt",
        "VINYL_MOOD": "Vinyl Mood",
    }
    type_label = type_labels.get(post_type, "Post")

    if record_title and record_artist:
        title = f"@{author_name}: {type_label} — {record_artist} - {record_title}"
        if variant:
            title += f" ({variant})"
    else:
        title = f"@{author_name}: {type_label}"
    title += f" | {SITE_NAME}"

    desc_parts = [f"@{author_name}"]
    if post_type == "NOW_SPINNING" and record_title:
        desc_parts.append(f"is spinning {record_artist} - {record_title}")
        if variant:
            desc_parts.append(f"({variant})")
    elif post_type == "ADDED_TO_COLLECTION" and record_title:
        desc_parts.append(f"added {record_artist} - {record_title} to their collection")
    elif caption:
        desc_parts.append(f"says: {caption[:200]}")
    desc_parts.append(f"on {SITE_NAME}")
    description = " ".join(desc_parts)

    url = f"{SITE_URL}/hive?post={post_id}"

    extra_meta = _post_meta({
        "record_artist": record_artist,
        "record_title": record_title,
        "color_variant": variant,
    })

    # JSON-LD SocialMediaPosting
    json_ld = {
        "@context": "https://schema.org",
        "@type": "SocialMediaPosting",
        "headline": title,
        "author": {"@type": "Person", "name": author_name},
        "datePublished": post.get("created_at", ""),
        "image": image,
        "url": url,
        "description": description,
    }

    return HTMLResponse(_build_html(title, description, url, image, "article", extra_meta, json_ld))


# ========== COLLECTION SSR ==========

@router.get("/ssr/collection/{username}", response_class=HTMLResponse)
async def ssr_collection(username: str):
    """SSR metadata page for a user's collection."""
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0, "id": 1, "username": 1, "avatar_url": 1})
    if not user:
        return HTMLResponse(_build_html(
            f"Collection Not Found | {SITE_NAME}",
            DEFAULT_DESC,
            f"{SITE_URL}/collection",
        ), status_code=404)

    uname = user.get("username", username)
    collection_count = await db.records.count_documents({"user_id": user["id"]})

    # Get top artists
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$group": {"_id": "$artist", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    top_artists_raw = await db.records.aggregate(pipeline).to_list(5)
    top_artists = [a["_id"] for a in top_artists_raw if a.get("_id")]

    title = f"@{uname}'s Vinyl Collection — {collection_count} Records | {SITE_NAME}"
    desc_parts = [f"Explore @{uname}'s collection of {collection_count} vinyl records on {SITE_NAME}."]
    if top_artists:
        desc_parts.append(f"Top artists: {', '.join(top_artists[:3])}.")
    description = " ".join(desc_parts)

    url = f"{SITE_URL}/profile/{uname}"
    image = _resolve_image(user.get("avatar_url"))

    extra_meta = _collector_meta({"username": uname, "collection_count": collection_count})

    json_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"@{uname}'s Vinyl Collection",
        "url": url,
        "description": description,
        "numberOfItems": collection_count,
    }

    return HTMLResponse(_build_html(title, description, url, image, "website", extra_meta, json_ld))


# ========== ISO LIST SSR ==========

@router.get("/ssr/iso/{username}", response_class=HTMLResponse)
async def ssr_iso(username: str):
    """SSR metadata page for a user's ISO / wantlist."""
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0, "id": 1, "username": 1, "avatar_url": 1})
    if not user:
        return HTMLResponse(_build_html(
            f"ISO List Not Found | {SITE_NAME}",
            DEFAULT_DESC,
            f"{SITE_URL}/honeypot",
        ), status_code=404)

    uname = user.get("username", username)
    iso_count = await db.iso_items.count_documents({"user_id": user["id"], "status": {"$in": ["OPEN", "WISHLIST"]}})

    # Get top ISO artists
    isos = await db.iso_items.find(
        {"user_id": user["id"], "status": {"$in": ["OPEN", "WISHLIST"]}},
        {"_id": 0, "artist": 1, "album": 1}
    ).limit(10).to_list(10)
    iso_titles = [f"{i.get('artist', '')} - {i.get('album', '')}" for i in isos[:5]]

    title = f"@{uname}'s ISO List — {iso_count} Records Wanted | {SITE_NAME}"
    desc_parts = [f"@{uname} is searching for {iso_count} vinyl records on {SITE_NAME}."]
    if iso_titles:
        desc_parts.append(f"Looking for: {', '.join(iso_titles[:3])}.")
    description = " ".join(desc_parts)

    url = f"{SITE_URL}/profile/{uname}"
    image = _resolve_image(user.get("avatar_url"))

    extra_meta = _collector_meta({"username": uname, "iso_count": iso_count})

    json_ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"@{uname}'s Vinyl ISO List",
        "url": url,
        "description": description,
        "numberOfItems": iso_count,
    }

    return HTMLResponse(_build_html(title, description, url, image, "website", extra_meta, json_ld))


# ========== MARKETPLACE SSR ==========

@router.get("/ssr/honeypot", response_class=HTMLResponse)
async def ssr_marketplace():
    """SSR metadata page for the marketplace."""
    active_count = await db.listings.count_documents({"status": "ACTIVE"})

    title = f"Vinyl Marketplace — {active_count} Records For Sale & Trade | {SITE_NAME}"
    description = f"Browse {active_count} vinyl records for sale and trade on {SITE_NAME}. Find rare pressings, colored vinyl, and connect directly with collectors."
    url = f"{SITE_URL}/honeypot"

    json_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "The Honeypot — Vinyl Marketplace",
        "url": url,
        "description": description,
        "numberOfItems": active_count,
    }

    return HTMLResponse(_build_html(title, description, url, DEFAULT_IMAGE, "website", "", json_ld))


# ========== CATCH-ALL SSR ==========

@router.get("/ssr/{path:path}", response_class=HTMLResponse)
async def ssr_catchall(path: str):
    """Fallback SSR page for any unmatched path."""
    url = f"{SITE_URL}/{path}"
    title = f"{SITE_NAME} — The Vinyl Social Club"
    return HTMLResponse(_build_html(title, DEFAULT_DESC, url))


@router.get("/ssr", response_class=HTMLResponse)
async def ssr_root():
    """SSR for the root/landing page."""
    title = f"{SITE_NAME} — The Vinyl Social Club, Finally."
    description = "Track your vinyl collection, discover rare pressings, buy, sell, and trade records with collectors worldwide. Join the hive."
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": description,
        "applicationCategory": "SocialNetworkingApplication",
        "operatingSystem": "Web",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }
    return HTMLResponse(_build_html(title, description, SITE_URL, DEFAULT_IMAGE, "website", "", json_ld))
