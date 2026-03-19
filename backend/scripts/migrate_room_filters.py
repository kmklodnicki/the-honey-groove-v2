"""
Migration: update room filters to use correct Discogs genre/style taxonomy.

Genre values (Discogs): "Hip Hop", "Jazz", "Electronic", "Classical",
                         "Rock", "Pop", "Funk / Soul"
Style values (Discogs sub-genre): "Post-Punk", "Indie Rock", "Heavy Metal",
                                   "Ambient", "R&B"
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import db

FILTER_UPDATES = [
    # Era rooms — add genre/style sub-filter so each room is distinct
    ("50s-jazz",       {"year": {"$gte": 1950, "$lte": 1959}, "genre": "Jazz"}),
    ("60s-rock",       {"year": {"$gte": 1960, "$lte": 1969}, "genre": "Rock"}),
    ("70s-soul",       {"year": {"$gte": 1970, "$lte": 1979}, "genre": "Funk / Soul"}),
    ("80s-post-punk",  {"year": {"$gte": 1980, "$lte": 1989}, "style": "Post-Punk"}),
    ("80s-hip-hop",    {"year": {"$gte": 1980, "$lte": 1989}, "genre": "Hip Hop"}),
    ("90s-indie",      {"year": {"$gte": 1990, "$lte": 1999}, "style": "Indie Rock"}),
    ("90s-electronic", {"year": {"$gte": 1990, "$lte": 1999}, "genre": "Electronic"}),
    ("00s-rnb",        {"year": {"$gte": 2000, "$lte": 2009}, "style": "R&B"}),
    ("00s-metal",      {"year": {"$gte": 2000, "$lte": 2009}, "style": "Heavy Metal"}),
    ("10s-ambient",    {"year": {"$gte": 2010, "$lte": 2019}, "style": "Ambient"}),
    # Genre rooms — proper Discogs capitalization (was lowercase)
    ("jazz-room",       {"genre": "Jazz"}),
    ("hip-hop-room",    {"genre": "Hip Hop"}),
    ("electronic-room", {"genre": "Electronic"}),
    ("classical-room",  {"genre": "Classical"}),
]


async def main():
    total_matched = 0
    total_modified = 0
    for slug, new_filter in FILTER_UPDATES:
        result = await db.rooms.update_one(
            {"slug": slug},
            {"$set": {"filter": new_filter}}
        )
        total_matched += result.matched_count
        total_modified += result.modified_count
        status = "updated" if result.modified_count else ("not found" if not result.matched_count else "unchanged")
        print(f"  {slug}: {status}")

    print(f"\nDone — {total_matched} matched, {total_modified} modified.")


asyncio.run(main())
