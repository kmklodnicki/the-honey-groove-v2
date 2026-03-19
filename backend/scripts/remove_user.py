"""One-time script to permanently remove a user and all their associated data.
Run: MONGO_URL=... DB_NAME=... python scripts/remove_user.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL")
if not MONGO_URL:
    raise RuntimeError("MONGO_URL environment variable is required")
DB_NAME = os.environ.get("DB_NAME", "honeygroove")

TARGET_USERNAME = "katie_test"


async def remove_user():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    target = await db.users.find_one({"username": TARGET_USERNAME}, {"_id": 0})
    if not target:
        print(f"User '{TARGET_USERNAME}' not found.")
        client.close()
        return

    user_id = target["id"]
    print(f"Found user: @{target['username']} (id={user_id}, email={target.get('email')})")
    confirm = input("Type 'yes' to permanently delete this user and all their data: ").strip()
    if confirm != "yes":
        print("Aborted.")
        client.close()
        return

    results = {}
    results["posts"]         = (await db.posts.delete_many({"user_id": user_id})).deleted_count
    results["comments"]      = (await db.comments.delete_many({"user_id": user_id})).deleted_count
    results["likes"]         = (await db.likes.delete_many({"user_id": user_id})).deleted_count
    results["followers"]     = (await db.followers.delete_many({"$or": [{"follower_id": user_id}, {"following_id": user_id}]})).deleted_count
    results["records"]       = (await db.records.delete_many({"user_id": user_id})).deleted_count
    results["spins"]         = (await db.spins.delete_many({"user_id": user_id})).deleted_count
    results["iso_items"]     = (await db.iso_items.delete_many({"user_id": user_id})).deleted_count
    results["notifications"] = (await db.notifications.delete_many({"$or": [{"user_id": user_id}, {"from_user_id": user_id}]})).deleted_count
    results["reports"]       = (await db.reports.delete_many({"reporter_user_id": user_id})).deleted_count
    results["listings"]      = (await db.listings.delete_many({"user_id": user_id})).deleted_count
    results["room_members"]  = (await db.room_members.delete_many({"userId": user_id})).deleted_count
    results["milestones"]    = (await db.milestones.delete_many({"userId": user_id})).deleted_count
    results["user"]          = (await db.users.delete_one({"id": user_id})).deleted_count

    print("\nDeleted:")
    for collection, count in results.items():
        if count:
            print(f"  {collection}: {count}")
    print(f"\n✓ @{TARGET_USERNAME} removed.")
    client.close()


asyncio.run(remove_user())
