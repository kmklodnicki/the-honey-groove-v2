"""Remove 13 RPM vibe room, insert Taylor Swift artist room."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import db

TAYLOR_SWIFT_ROOM = {
    "slug": "taylor-swift",
    "name": "Taylor Swift",
    "emoji": "🩷",
    "tagline": "13 RPM. The hunt, the hauls, and the holy grail pressings.",
    "type": "artist",
    "filter": {"artist": {"$regex": "Taylor Swift", "$options": "i"}},
    "matchCriteria": {"type": "artist", "value": "Taylor Swift"},
    "theme": {
        "accentColor": "#D98FA1",
        "bgGradient": "linear-gradient(135deg, #F8D7DA, #F1AEB5)",
        "hexColor": "#D98FA1",
        "textColor": "#3D1520",
    },
    "theme_preset": "rose",
    "member_count": 0,
    "active": True,
    "nickname": None,
}

async def main():
    # Remove 13 RPM room and its members
    r1 = await db.rooms.delete_one({"slug": "13-rpm-swifties-who-spin"})
    r2 = await db.room_members.delete_many({"slug": "13-rpm-swifties-who-spin"})
    print(f"Deleted 13 RPM room: {r1.deleted_count}, members: {r2.deleted_count}")

    # Insert Taylor Swift artist room (upsert so safe to re-run)
    result = await db.rooms.update_one(
        {"slug": "taylor-swift"},
        {"$setOnInsert": TAYLOR_SWIFT_ROOM},
        upsert=True,
    )
    if result.upserted_id:
        print("Taylor Swift room inserted.")
    else:
        print("Taylor Swift room already exists — skipped.")

asyncio.run(main())
