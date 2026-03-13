"""
HoneyGroove Data Migration Script
Exports all data from source DB and imports into target (production) DB.

Usage:
  # Export from current environment
  python scripts/migrate_to_production.py export

  # Import into production (provide PROD_MONGO_URL env var)
  PROD_MONGO_URL="mongodb+srv://..." PROD_DB_NAME="the_honey_groove" python scripts/migrate_to_production.py import

  # Full migration (export + import in one step)
  PROD_MONGO_URL="mongodb+srv://..." PROD_DB_NAME="the_honey_groove" python scripts/migrate_to_production.py migrate
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId

# Add parent dir
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from motor.motor_asyncio import AsyncIOMotorClient

EXPORT_DIR = Path(__file__).parent / "migration_data"

# Collections to migrate (order matters for references)
CRITICAL_COLLECTIONS = [
    "users",
    "posts",
    "records",
    "spins",
    "prompts",
    "prompt_responses",
    "followers",
    "likes",
    "comments",
    "notifications",
    "dm_conversations",
    "dm_messages",
    "iso_items",
    "listings",
    "trades",
    "trade_ratings",
    "invite_codes",
    "beta_signups",
    "hauls",
    "mood_boards",
    "bingo_cards",
    "bingo_squares",
    "bingo_marks",
    "wax_reports",
    "weekly_summaries",
    "discogs_tokens",
    "discogs_releases",
    "collection_values",
    "image_cache",
    "pulse_data",
    "verification_requests",
    "reports",
    "email_verifications",
    "newsletter_subscribers",
    "platform_settings",
    "recovery_runs",
    "payment_transactions",
    "files",
]


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return super().default(obj)


async def export_data():
    """Export all collections from source DB to JSON files."""
    source_url = os.environ["MONGO_URL"]
    source_db_name = os.environ["DB_NAME"]

    client = AsyncIOMotorClient(source_url)
    db = client[source_db_name]

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    total_docs = 0
    manifest = {}

    all_collections = await db.list_collection_names()
    collections_to_export = [c for c in CRITICAL_COLLECTIONS if c in all_collections]
    # Also grab any collections not in our list
    extras = [c for c in all_collections if c not in CRITICAL_COLLECTIONS and not c.startswith("system.")]
    collections_to_export.extend(extras)

    for coll_name in collections_to_export:
        docs = await db[coll_name].find({}).to_list(None)
        # Convert ObjectId fields
        clean_docs = []
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            clean_docs.append(doc)

        count = len(clean_docs)
        if count == 0:
            continue

        filepath = EXPORT_DIR / f"{coll_name}.json"
        with open(filepath, "w") as f:
            json.dump(clean_docs, f, cls=JSONEncoder, default=str)

        manifest[coll_name] = count
        total_docs += count
        print(f"  Exported {coll_name}: {count} docs")

    # Save manifest
    with open(EXPORT_DIR / "manifest.json", "w") as f:
        json.dump({
            "source_db": source_db_name,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "collections": manifest,
            "total_documents": total_docs,
        }, f, indent=2)

    print(f"\nExport complete: {total_docs} documents across {len(manifest)} collections")
    print(f"Files saved to: {EXPORT_DIR}")
    client.close()
    return manifest


async def import_data(prod_url=None, prod_db_name=None):
    """Import exported JSON data into production DB."""
    prod_url = prod_url or os.environ.get("PROD_MONGO_URL")
    prod_db_name = prod_db_name or os.environ.get("PROD_DB_NAME", "the_honey_groove")

    if not prod_url:
        print("ERROR: Set PROD_MONGO_URL environment variable")
        sys.exit(1)

    # Safety check
    print(f"\n{'='*60}")
    print(f"TARGET DATABASE: {prod_db_name}")
    print(f"TARGET CLUSTER: {prod_url.split('@')[1].split('/')[0] if '@' in prod_url else 'UNKNOWN'}")
    print(f"{'='*60}")

    client = AsyncIOMotorClient(prod_url)
    db = client[prod_db_name]

    # Test connection
    try:
        await db.command("ping")
        print("Connection OK")
    except Exception as e:
        print(f"Connection FAILED: {e}")
        sys.exit(1)

    manifest_path = EXPORT_DIR / "manifest.json"
    if not manifest_path.exists():
        print("ERROR: No export data found. Run 'export' first.")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    total_imported = 0

    for coll_name, expected_count in manifest["collections"].items():
        filepath = EXPORT_DIR / f"{coll_name}.json"
        if not filepath.exists():
            print(f"  SKIP {coll_name}: file not found")
            continue

        with open(filepath) as f:
            docs = json.load(f)

        if not docs:
            continue

        # Remove string _id fields (let MongoDB assign new ObjectIds)
        for doc in docs:
            if "_id" in doc:
                del doc["_id"]

        # Check existing count
        existing = await db[coll_name].count_documents({})

        if coll_name == "users":
            # For users, upsert by email to avoid duplicates
            imported = 0
            for doc in docs:
                email = doc.get("email")
                if email:
                    result = await db[coll_name].update_one(
                        {"email": email},
                        {"$setOnInsert": doc},
                        upsert=True
                    )
                    if result.upserted_id:
                        imported += 1
            print(f"  {coll_name}: {imported} new users imported (skipped {len(docs) - imported} existing)")
            total_imported += imported
        elif coll_name == "prompts":
            # For prompts, upsert by id
            imported = 0
            for doc in docs:
                pid = doc.get("id")
                if pid:
                    result = await db[coll_name].update_one(
                        {"id": pid},
                        {"$setOnInsert": doc},
                        upsert=True
                    )
                    if result.upserted_id:
                        imported += 1
            print(f"  {coll_name}: {imported} new prompts imported (skipped {len(docs) - imported} existing)")
            total_imported += imported
        else:
            # For other collections, check if any docs with 'id' field already exist
            if docs[0].get("id"):
                # Upsert by id
                imported = 0
                for doc in docs:
                    doc_id = doc.get("id")
                    if doc_id:
                        result = await db[coll_name].update_one(
                            {"id": doc_id},
                            {"$setOnInsert": doc},
                            upsert=True
                        )
                        if result.upserted_id:
                            imported += 1
                print(f"  {coll_name}: {imported} new docs imported (skipped {len(docs) - imported} existing)")
                total_imported += imported
            else:
                # Bulk insert if collection is empty, skip if has data
                if existing == 0:
                    await db[coll_name].insert_many(docs)
                    print(f"  {coll_name}: {len(docs)} docs inserted")
                    total_imported += len(docs)
                else:
                    print(f"  {coll_name}: SKIPPED ({existing} docs already exist)")

    print(f"\nImport complete: {total_imported} documents imported")

    # Verify
    print("\nVerification:")
    for coll_name in manifest["collections"]:
        count = await db[coll_name].count_documents({})
        print(f"  {coll_name}: {count} docs")

    client.close()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_production.py [export|import|migrate]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "export":
        await export_data()
    elif command == "import":
        await import_data()
    elif command == "migrate":
        await export_data()
        prod_url = os.environ.get("PROD_MONGO_URL")
        if not prod_url:
            print("\nExport done. Set PROD_MONGO_URL to continue with import.")
            sys.exit(0)
        await import_data()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
