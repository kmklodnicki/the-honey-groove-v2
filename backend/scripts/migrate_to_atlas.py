"""
Migration script: Import backed-up JSON data into a target MongoDB (e.g., Atlas).

Usage:
  python3 migrate_to_atlas.py <ATLAS_MONGO_URL> [DB_NAME]

Example:
  python3 migrate_to_atlas.py "mongodb+srv://user:pass@cluster.mongodb.net" "test_database"

This will:
1. Connect to the target database
2. Import all JSON files from /app/backup/
3. Skip collections that already have data (safe to re-run)
4. Print a summary of imported documents
"""
import asyncio
import json
import sys
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

BACKUP_DIR = Path("/app/backup")

def restore_objectids(doc):
    """Convert string _id back to ObjectId if it looks like one."""
    if isinstance(doc, dict):
        for k, v in doc.items():
            if k == "_id" and isinstance(v, str) and len(v) == 24:
                try:
                    doc[k] = ObjectId(v)
                except:
                    pass
            elif isinstance(v, (dict, list)):
                restore_objectids(v)
    elif isinstance(doc, list):
        for item in doc:
            restore_objectids(item)
    return doc

async def migrate(target_url: str, db_name: str):
    print(f"Connecting to target: {target_url[:40]}...")
    client = AsyncIOMotorClient(target_url, serverSelectionTimeoutMS=10000)
    
    # Test connection
    try:
        await client.admin.command("ping")
        print("Connected successfully!\n")
    except Exception as e:
        print(f"FAILED to connect: {e}")
        sys.exit(1)
    
    db = client[db_name]
    
    json_files = sorted(BACKUP_DIR.glob("*.json"))
    if not json_files:
        print("No backup files found in /app/backup/")
        sys.exit(1)
    
    total_imported = 0
    total_skipped = 0
    
    for f in json_files:
        collection_name = f.stem
        with open(f) as fp:
            docs = json.load(fp)
        
        if not docs:
            continue
        
        # Check if target already has data
        existing = await db[collection_name].count_documents({})
        if existing > 0:
            print(f"  SKIP {collection_name}: already has {existing} docs (backup has {len(docs)})")
            total_skipped += len(docs)
            continue
        
        # Restore ObjectIds
        for doc in docs:
            restore_objectids(doc)
        
        # Insert
        try:
            result = await db[collection_name].insert_many(docs, ordered=False)
            count = len(result.inserted_ids)
            total_imported += count
            print(f"  OK   {collection_name}: {count} docs imported")
        except Exception as e:
            print(f"  ERR  {collection_name}: {e}")
    
    print(f"\n{'='*50}")
    print(f"MIGRATION COMPLETE")
    print(f"  Imported: {total_imported} documents")
    print(f"  Skipped:  {total_skipped} documents (already existed)")
    print(f"{'='*50}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 migrate_to_atlas.py <ATLAS_MONGO_URL> [DB_NAME]")
        sys.exit(1)
    
    target_url = sys.argv[1]
    db_name = sys.argv[2] if len(sys.argv) > 2 else "test_database"
    asyncio.run(migrate(target_url, db_name))
