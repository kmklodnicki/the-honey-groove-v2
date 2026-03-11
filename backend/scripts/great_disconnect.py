"""
BLOCK 473: THE "GREAT DISCONNECT" MIGRATION
One-time script to purge all manually-entered Discogs credentials
and reset migration flags so every user sees the security modal.

Run via: POST /api/admin/run-great-disconnect (admin-only)
Or directly: python scripts/great_disconnect.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


async def run_great_disconnect():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    now = datetime.now(timezone.utc).isoformat()
    results = {}

    # 1. Mass Disconnection: Nullify Discogs fields on all users
    user_result = await db.users.update_many(
        {},
        {"$set": {
            "discogs_username": None,
            "discogs_oauth_verified": False,
            "has_seen_security_migration": False,
            "discogs_migration_dismissed": False,
        }}
    )
    results["users_reset"] = user_result.modified_count

    # 2. Purge all discogs_tokens (access tokens and secrets)
    token_result = await db.discogs_tokens.delete_many({})
    results["tokens_deleted"] = token_result.deleted_count

    # 3. Purge any pending OAuth sessions
    pending_result = await db.discogs_oauth_pending.delete_many({})
    results["pending_cleared"] = pending_result.deleted_count

    # 4. Honeypot Cleanup: Hide listings from unverified accounts
    # Mark all active listings as HIDDEN_PENDING_VERIFICATION
    # They'll be restored when the user completes OAuth
    listing_result = await db.listings.update_many(
        {"status": "ACTIVE"},
        {"$set": {
            "status": "HIDDEN_PENDING_VERIFICATION",
            "hidden_at": now,
            "hidden_reason": "great_disconnect_migration",
        }}
    )
    results["listings_hidden"] = listing_result.modified_count

    # 5. Log the migration
    await db.migration_log.insert_one({
        "migration": "great_disconnect_v1",
        "executed_at": now,
        "results": results,
    })

    results["migration"] = "great_disconnect_v1"
    results["executed_at"] = now
    
    client.close()
    return results


if __name__ == "__main__":
    result = asyncio.run(run_great_disconnect())
    print(f"Great Disconnect complete: {result}")
