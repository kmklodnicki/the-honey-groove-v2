"""
Merge master_migration_data.json into Production Atlas DB.
Strategy: Match by EMAIL, re-parent user_ids on records/posts/spins.
"""
import json
import os
from datetime import datetime, timezone
from pymongo import MongoClient

ATLAS_URI = os.environ.get("MONGO_URL", "mongodb+srv://katie:Swiftie420!@cluster0.abcipnu.mongodb.net/the_honey_groove")
DB_NAME = "groove-social-beta-test_database"
DATA_PATH = "/app/scripts/master_migration_data.json"


def main():
    with open(DATA_PATH) as f:
        data = json.load(f)

    client = MongoClient(ATLAS_URI)
    db = client[DB_NAME]

    migration_users = data.get("users", [])
    migration_records = data.get("records", [])
    migration_posts = data.get("posts", [])
    migration_spins = data.get("spins", [])

    print(f"Migration source: {len(migration_users)} users, {len(migration_records)} records, {len(migration_posts)} posts, {len(migration_spins)} spins")

    # Step 1: Build old_user_id -> email mapping from migration data
    old_id_to_email = {}
    for u in migration_users:
        if u.get("email") and u.get("id"):
            old_id_to_email[u["id"]] = u["email"]
    print(f"\nOld ID->email mappings: {len(old_id_to_email)}")

    # Step 2: Build email -> new_user_id mapping from production Atlas
    email_to_new_id = {}
    for u in db["users"].find({}, {"_id": 0, "id": 1, "email": 1}):
        if u.get("email") and u.get("id"):
            email_to_new_id[u["email"]] = u["id"]
    print(f"Production email->id mappings: {len(email_to_new_id)}")

    # Step 3: Build the re-parenting map: old_user_id -> new_user_id
    reparent_map = {}
    for old_id, email in old_id_to_email.items():
        new_id = email_to_new_id.get(email)
        if new_id:
            reparent_map[old_id] = new_id
            if old_id != new_id:
                print(f"  REMAP: {email}: {old_id[:12]}... -> {new_id[:12]}...")
        else:
            print(f"  WARNING: No prod user for {email} (old_id={old_id[:12]}...)")
    
    # Also handle orphan user_ids not in the user list (e.g. 54c4f7dc...)
    orphan_ids = set()
    for r in migration_records + migration_posts + migration_spins:
        uid = r.get("user_id", "")
        if uid and uid not in reparent_map and uid not in old_id_to_email:
            orphan_ids.add(uid)
    if orphan_ids:
        print(f"\n  ORPHAN user_ids (not in migration users): {orphan_ids}")

    # Step 4: Migrate records
    print(f"\n=== MIGRATING RECORDS ({len(migration_records)}) ===")
    rec_inserted = rec_skipped = rec_reparented = 0
    for rec in migration_records:
        old_uid = rec.get("user_id", "")
        new_uid = reparent_map.get(old_uid, old_uid)
        
        # Check if this exact record already exists in prod (by 'id' field)
        rec_id = rec.get("id")
        if rec_id and db["records"].find_one({"id": rec_id}):
            rec_skipped += 1
            continue

        # Re-parent
        rec["user_id"] = new_uid
        if old_uid != new_uid:
            rec_reparented += 1
        
        # Remove MongoDB _id if present (let Atlas generate a new one)
        rec.pop("_id", None)
        rec["migrated_at"] = datetime.now(timezone.utc).isoformat()
        rec["migration_source"] = "master_migration_data"
        
        db["records"].insert_one(rec)
        rec_inserted += 1

    print(f"  Records: {rec_inserted} inserted, {rec_skipped} skipped (already exist), {rec_reparented} re-parented")

    # Step 5: Migrate posts
    print(f"\n=== MIGRATING POSTS ({len(migration_posts)}) ===")
    post_inserted = post_skipped = post_reparented = 0
    for post in migration_posts:
        old_uid = post.get("user_id", "")
        new_uid = reparent_map.get(old_uid, old_uid)

        post_id = post.get("id")
        if post_id and db["posts"].find_one({"id": post_id}):
            post_skipped += 1
            continue

        post["user_id"] = new_uid
        if old_uid != new_uid:
            post_reparented += 1
        
        post.pop("_id", None)
        post["migrated_at"] = datetime.now(timezone.utc).isoformat()
        post["migration_source"] = "master_migration_data"
        
        db["posts"].insert_one(post)
        post_inserted += 1

    print(f"  Posts: {post_inserted} inserted, {post_skipped} skipped, {post_reparented} re-parented")

    # Step 6: Migrate spins
    print(f"\n=== MIGRATING SPINS ({len(migration_spins)}) ===")
    spin_inserted = spin_skipped = 0
    for spin in migration_spins:
        old_uid = spin.get("user_id", "")
        new_uid = reparent_map.get(old_uid, old_uid)

        spin_id = spin.get("id")
        if spin_id and db["spins"].find_one({"id": spin_id}):
            spin_skipped += 1
            continue

        spin["user_id"] = new_uid
        spin.pop("_id", None)
        spin["migrated_at"] = datetime.now(timezone.utc).isoformat()
        
        db["spins"].insert_one(spin)
        spin_inserted += 1

    print(f"  Spins: {spin_inserted} inserted, {spin_skipped} skipped")

    # Step 7: Verify Ash's data
    print(f"\n=== VERIFICATION: contact.ashsvinyl@gmail.com ===")
    ash = db["users"].find_one({"email": "contact.ashsvinyl@gmail.com"}, {"_id": 0, "id": 1, "username": 1, "email": 1})
    if ash:
        ash_id = ash["id"]
        ash_recs = db["records"].count_documents({"user_id": ash_id})
        ash_posts = db["posts"].count_documents({"user_id": ash_id})
        print(f"  User: {ash['username']} (id={ash_id})")
        print(f"  Records: {ash_recs}")
        print(f"  Posts: {ash_posts}")
    else:
        print("  User NOT FOUND in production")

    # Step 8: Final counts
    print(f"\n=== FINAL PRODUCTION COUNTS ===")
    print(f"  users:   {db['users'].count_documents({})}")
    print(f"  records: {db['records'].count_documents({})}")
    print(f"  posts:   {db['posts'].count_documents({})}")
    print(f"  spins:   {db['spins'].count_documents({})}")

    # Admin check
    admin = db["users"].find_one({"email": "kmklodnicki@gmail.com"}, {"_id": 0, "email": 1, "is_admin": 1})
    print(f"\n  Admin check: {admin}")

    client.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
