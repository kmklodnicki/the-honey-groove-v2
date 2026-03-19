"""Seed 18 Honeycomb Rooms. Idempotent — safe to re-run."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import db

ROOMS = [
    # Era rooms (10)
    {
        "slug": "50s-jazz",
        "name": "50s Jazz",
        "emoji": "🎷",
        "tagline": "Cool, hard bop, and west coast sounds",
        "type": "era",
        "filter": {"year": {"$gte": 1950, "$lte": 1959}},
        "theme": {
            "accentColor": "#B8860B",
            "bgGradient": "linear-gradient(135deg, #FFF8DC, #FAEBD7)",
            "hexColor": "#D4A017",
            "textColor": "#2A1A06",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "60s-rock",
        "name": "60s Rock",
        "emoji": "🎸",
        "tagline": "The decade that changed everything",
        "type": "era",
        "filter": {"year": {"$gte": 1960, "$lte": 1969}},
        "theme": {
            "accentColor": "#C0392B",
            "bgGradient": "linear-gradient(135deg, #FDEDEC, #FADBD8)",
            "hexColor": "#E74C3C",
            "textColor": "#2C0A08",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "70s-soul",
        "name": "70s Soul",
        "emoji": "🕺",
        "tagline": "Funk, soul, and everything between",
        "type": "era",
        "filter": {"year": {"$gte": 1970, "$lte": 1979}},
        "theme": {
            "accentColor": "#C8861A",
            "bgGradient": "linear-gradient(135deg, #FFF3E0, #FFE0B2)",
            "hexColor": "#E8A820",
            "textColor": "#2A1A06",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "80s-post-punk",
        "name": "80s Post-Punk",
        "emoji": "🖤",
        "tagline": "Dark, angular, and beautifully weird",
        "type": "era",
        "filter": {"year": {"$gte": 1980, "$lte": 1989}},
        "theme": {
            "accentColor": "#6C3483",
            "bgGradient": "linear-gradient(135deg, #F5EEF8, #EBD5F5)",
            "hexColor": "#9B59B6",
            "textColor": "#1A0A2A",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "80s-hip-hop",
        "name": "80s Hip-Hop",
        "emoji": "🎤",
        "tagline": "The birth of a culture",
        "type": "era",
        "filter": {"year": {"$gte": 1980, "$lte": 1989}},
        "theme": {
            "accentColor": "#1A5276",
            "bgGradient": "linear-gradient(135deg, #EBF5FB, #D6EAF8)",
            "hexColor": "#2E86C1",
            "textColor": "#0A1A26",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "90s-indie",
        "name": "90s Indie",
        "emoji": "📼",
        "tagline": "Lo-fi, loud, and unapologetically indie",
        "type": "era",
        "filter": {"year": {"$gte": 1990, "$lte": 1999}},
        "theme": {
            "accentColor": "#117A65",
            "bgGradient": "linear-gradient(135deg, #E8F8F5, #D1F2EB)",
            "hexColor": "#1ABC9C",
            "textColor": "#0A2A24",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "90s-electronic",
        "name": "90s Electronic",
        "emoji": "🎛️",
        "tagline": "Raves, drum machines, and synthesizers",
        "type": "era",
        "filter": {"year": {"$gte": 1990, "$lte": 1999}},
        "theme": {
            "accentColor": "#1F618D",
            "bgGradient": "linear-gradient(135deg, #EAF2FF, #D6E9FF)",
            "hexColor": "#2980B9",
            "textColor": "#0A1826",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "00s-rnb",
        "name": "00s R&B",
        "emoji": "💿",
        "tagline": "The glossy golden era of R&B",
        "type": "era",
        "filter": {"year": {"$gte": 2000, "$lte": 2009}},
        "theme": {
            "accentColor": "#7D3C98",
            "bgGradient": "linear-gradient(135deg, #F5EEF8, #E8DAEF)",
            "hexColor": "#AF7AC5",
            "textColor": "#1A0A2A",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "00s-metal",
        "name": "00s Metal",
        "emoji": "🤘",
        "tagline": "Heavy, loud, and relentless",
        "type": "era",
        "filter": {"year": {"$gte": 2000, "$lte": 2009}},
        "theme": {
            "accentColor": "#616A6B",
            "bgGradient": "linear-gradient(135deg, #F2F3F4, #E5E7E9)",
            "hexColor": "#85929E",
            "textColor": "#1A1A1A",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "10s-ambient",
        "name": "10s Ambient",
        "emoji": "🌊",
        "tagline": "Texture, space, and slow beauty",
        "type": "era",
        "filter": {"year": {"$gte": 2010, "$lte": 2019}},
        "theme": {
            "accentColor": "#1A5276",
            "bgGradient": "linear-gradient(135deg, #EBF5FB, #D6EAF8)",
            "hexColor": "#5DADE2",
            "textColor": "#0A1826",
        },
        "member_count": 0,
        "active": True,
    },
    # Genre rooms (4 — feed falls back to recent posts until genre enrichment is added)
    {
        "slug": "jazz-room",
        "name": "Jazz Room",
        "emoji": "🎺",
        "tagline": "All things jazz, all eras",
        "type": "genre",
        "filter": {"genre": "jazz"},
        "theme": {
            "accentColor": "#B7950B",
            "bgGradient": "linear-gradient(135deg, #FEF9E7, #FDEBD0)",
            "hexColor": "#F0B429",
            "textColor": "#2A1A06",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "hip-hop-room",
        "name": "Hip-Hop Room",
        "emoji": "🎧",
        "tagline": "Beats, bars, and culture",
        "type": "genre",
        "filter": {"genre": "hip-hop"},
        "theme": {
            "accentColor": "#1A5276",
            "bgGradient": "linear-gradient(135deg, #EBF5FB, #D6EAF8)",
            "hexColor": "#2E86C1",
            "textColor": "#0A1826",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "electronic-room",
        "name": "Electronic Room",
        "emoji": "⚡",
        "tagline": "Synthesizers and circuit boards",
        "type": "genre",
        "filter": {"genre": "electronic"},
        "theme": {
            "accentColor": "#117A65",
            "bgGradient": "linear-gradient(135deg, #E8F8F5, #D1F2EB)",
            "hexColor": "#1ABC9C",
            "textColor": "#0A2A24",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "classical-room",
        "name": "Classical Room",
        "emoji": "🎻",
        "tagline": "Timeless orchestral masterworks",
        "type": "genre",
        "filter": {"genre": "classical"},
        "theme": {
            "accentColor": "#784212",
            "bgGradient": "linear-gradient(135deg, #FDFEFE, #F5EEF8)",
            "hexColor": "#A04000",
            "textColor": "#2A0A06",
        },
        "member_count": 0,
        "active": True,
    },
    # Artist rooms (4)
    {
        "slug": "david-bowie",
        "name": "David Bowie",
        "emoji": "⚡",
        "tagline": "The chameleon lives on wax",
        "type": "artist",
        "filter": {"artist": {"$regex": "bowie", "$options": "i"}},
        "theme": {
            "accentColor": "#C0392B",
            "bgGradient": "linear-gradient(135deg, #FDEDEC, #FADBD8)",
            "hexColor": "#E74C3C",
            "textColor": "#2C0A08",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "coltrane-corner",
        "name": "Coltrane Corner",
        "emoji": "🎷",
        "tagline": "A love supreme, on vinyl",
        "type": "artist",
        "filter": {"artist": {"$regex": "coltrane", "$options": "i"}},
        "theme": {
            "accentColor": "#B7950B",
            "bgGradient": "linear-gradient(135deg, #FEF9E7, #FDEBD0)",
            "hexColor": "#F0B429",
            "textColor": "#2A1A06",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "fleetwood-mac",
        "name": "Fleetwood Mac",
        "emoji": "🌙",
        "tagline": "Rumours and beyond",
        "type": "artist",
        "filter": {"artist": {"$regex": "fleetwood", "$options": "i"}},
        "theme": {
            "accentColor": "#6C3483",
            "bgGradient": "linear-gradient(135deg, #F5EEF8, #EBD5F5)",
            "hexColor": "#9B59B6",
            "textColor": "#1A0A2A",
        },
        "member_count": 0,
        "active": True,
    },
    {
        "slug": "the-beatles",
        "name": "The Beatles",
        "emoji": "🍎",
        "tagline": "Original pressings and deep cuts",
        "type": "artist",
        "filter": {"artist": {"$regex": "beatles", "$options": "i"}},
        "theme": {
            "accentColor": "#C8861A",
            "bgGradient": "linear-gradient(135deg, #FFF3E0, #FFE0B2)",
            "hexColor": "#E8A820",
            "textColor": "#2A1A06",
        },
        "member_count": 0,
        "active": True,
    },
]


async def seed():
    # Create indexes
    await db.rooms.create_index("slug", unique=True)
    await db.room_members.create_index([("slug", 1), ("userId", 1)], unique=True)
    await db.room_members.create_index("userId")

    inserted = 0
    skipped = 0
    for room in ROOMS:
        result = await db.rooms.update_one(
            {"slug": room["slug"]},
            {"$setOnInsert": room},
            upsert=True
        )
        if result.upserted_id:
            inserted += 1
        else:
            skipped += 1

    print(f"Rooms seeded: {inserted} inserted, {skipped} already existed.")


if __name__ == "__main__":
    asyncio.run(seed())
