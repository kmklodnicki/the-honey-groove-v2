#!/usr/bin/env python3
"""Migration script: null out Discogs image URLs in records and discogs_releases collections.

Safe: only clears URLs containing 'discogs.com'. Cloudinary and Spotify URLs are untouched.

Usage:
    cd backend
    python scripts/migrate_cover_urls.py

Set MONGO_URL and DB_NAME in environment or .env file.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("=== THG Cover URL Migration — Discogs Image Cleanup ===\n")

    # 1. Null out cover_url on records containing discogs.com
    result = await db.records.update_many(
        {"cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
        {"$set": {"cover_url": None}}
    )
    print(f"records.cover_url cleared: {result.modified_count}")

    # 2. Null out cover_url on discogs_releases documents
    result2 = await db.discogs_releases.update_many(
        {"cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
        {"$set": {"cover_url": None}}
    )
    print(f"discogs_releases.cover_url cleared: {result2.modified_count}")

    # 3. Null out thumb_url on discogs_releases
    result3 = await db.discogs_releases.update_many(
        {"thumb_url": {"$regex": "discogs\\.com", "$options": "i"}},
        {"$set": {"thumb_url": None}}
    )
    print(f"discogs_releases.thumb_url cleared: {result3.modified_count}")

    # 4. Null out cover_url on posts containing discogs.com
    result4 = await db.posts.update_many(
        {"cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
        {"$set": {"cover_url": None}}
    )
    print(f"posts.cover_url cleared: {result4.modified_count}")

    # 5. Null out cover_url on haul items embedded in posts (items array)
    result5 = await db.posts.update_many(
        {"items.cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
        {"$set": {"items.$[elem].cover_url": None}},
        array_filters=[{"elem.cover_url": {"$regex": "discogs\\.com", "$options": "i"}}]
    )
    print(f"posts.items[].cover_url cleared: {result5.modified_count}")

    # 6. Null out cover_url on bundle_records embedded in haul posts
    result6 = await db.posts.update_many(
        {"bundle_records.cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
        {"$set": {"bundle_records.$[elem].cover_url": None}},
        array_filters=[{"elem.cover_url": {"$regex": "discogs\\.com", "$options": "i"}}]
    )
    print(f"posts.bundle_records[].cover_url cleared: {result6.modified_count}")

    # 7. Null out cover_url on haul items in hauls collection
    result7 = await db.hauls.update_many(
        {"items.cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
        {"$set": {"items.$[elem].cover_url": None}},
        array_filters=[{"elem.cover_url": {"$regex": "discogs\\.com", "$options": "i"}}]
    )
    print(f"hauls.items[].cover_url cleared: {result7.modified_count}")

    # 8. Clear iso_items, listing_alerts, listings, prompt_responses
    for coll_name in ["iso_items", "listing_alerts", "listings", "prompt_responses"]:
        r = await db[coll_name].update_many(
            {"cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
            {"$set": {"cover_url": None}}
        )
        print(f"{coll_name}.cover_url cleared: {r.modified_count}")

    # 9. Clear artist_images and image_cache
    await db.artist_images.update_many({"image_url": {"$regex": "discogs\\.com", "$options": "i"}}, {"$set": {"image_url": None}})
    await db.image_cache.update_many({"image_url": {"$regex": "discogs\\.com", "$options": "i"}}, {"$set": {"image_url": None}})
    await db.image_cache.update_many({"thumb_url": {"$regex": "discogs\\.com", "$options": "i"}}, {"$set": {"thumb_url": None}})
    print("artist_images and image_cache cleared")

    # 10. Clear explore cache entries with Discogs URLs
    r_cache = await db.cache.delete_many({"data.cover_url": {"$regex": "discogs\\.com", "$options": "i"}})
    print(f"cache entries deleted: {r_cache.deleted_count}")

    # 11. Verify: count remaining discogs.com URLs
    remaining_records = await db.records.count_documents(
        {"cover_url": {"$regex": "discogs\\.com", "$options": "i"}}
    )
    remaining_releases = await db.discogs_releases.count_documents(
        {"$or": [
            {"cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
            {"thumb_url": {"$regex": "discogs\\.com", "$options": "i"}},
        ]}
    )
    remaining_posts = await db.posts.count_documents(
        {"$or": [
            {"cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
            {"items.cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
            {"bundle_records.cover_url": {"$regex": "discogs\\.com", "$options": "i"}},
        ]}
    )

    print(f"\nVerification:")
    print(f"  records with Discogs URLs remaining: {remaining_records}")
    print(f"  discogs_releases with Discogs URLs remaining: {remaining_releases}")
    print(f"  posts with Discogs URLs remaining: {remaining_posts}")

    if remaining_records == 0 and remaining_releases == 0 and remaining_posts == 0:
        print("\n✓ Migration complete — no Discogs image URLs remain.")
    else:
        print("\n⚠ Some URLs remain — investigate manually.")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
