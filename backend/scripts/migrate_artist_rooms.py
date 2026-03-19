"""
Migration: add matchCriteria to existing artist rooms + create dedup index.

matchCriteria: { type: "artist", value: "<canonical artist name>" }
Unique sparse index on (matchCriteria.type, matchCriteria.value) for artist rooms.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import db

ARTIST_MATCH_CRITERIA = [
    ("david-bowie",    "David Bowie"),
    ("coltrane-corner","John Coltrane"),
    ("fleetwood-mac",  "Fleetwood Mac"),
    ("the-beatles",    "The Beatles"),
    # 13 RPM is a vibe room, not an artist room — skip
]


async def main():
    # 1. Add matchCriteria to known artist rooms
    for slug, artist_value in ARTIST_MATCH_CRITERIA:
        result = await db.rooms.update_one(
            {"slug": slug, "type": "artist"},
            {"$set": {"matchCriteria": {"type": "artist", "value": artist_value}}}
        )
        status = "updated" if result.modified_count else ("not found" if not result.matched_count else "unchanged")
        print(f"  {slug}: {status}")

    # 2. Create unique sparse index on matchCriteria for artist rooms
    # partialFilterExpression limits the unique constraint to artist-type rooms only
    await db.rooms.create_index(
        [("matchCriteria.type", 1), ("matchCriteria.value", 1)],
        unique=True,
        partialFilterExpression={"type": "artist"},
        name="artist_room_match_criteria_unique",
    )
    print("\nUnique index 'artist_room_match_criteria_unique' created (or already exists).")


asyncio.run(main())
