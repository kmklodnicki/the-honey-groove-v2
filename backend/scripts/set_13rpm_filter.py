"""One-time migration: set Taylor Swift artist filter on the 13 RPM room."""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "honeygrovev2")


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    result = await db.rooms.update_one(
        {"slug": "13-rpm-swifties-who-spin"},
        {"$set": {
            "filter": {
                "artist": {"$regex": "Taylor Swift", "$options": "i"}
            }
        }}
    )
    print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")
    client.close()


asyncio.run(main())
