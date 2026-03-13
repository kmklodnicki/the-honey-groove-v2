"""Export users, records, posts, profiles from production Atlas to JSON files."""
import json
import os
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient

ATLAS_URI = os.environ.get("MONGO_URL", "mongodb+srv://katie:Swiftie420!@cluster0.abcipnu.mongodb.net/the_honey_groove")
DB_NAME = "groove-social-beta-test_database"
OUT_DIR = "/app/export"

COLLECTIONS = ["users", "records", "posts", "followers", "likes", "spins", "hauls",
               "mood_boards", "iso_items", "dm_conversations", "dm_messages",
               "invite_codes", "discogs_tokens", "discogs_releases", "discogs_imports",
               "collection_values", "bingo_cards", "bingo_squares", "daily_prompts",
               "prompt_responses", "listings", "trade_ratings", "wax_reports"]


class MongoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def main():
    client = MongoClient(ATLAS_URI)
    db = client[DB_NAME]

    for coll_name in COLLECTIONS:
        docs = list(db[coll_name].find({}))
        # Convert _id to string id field
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        path = os.path.join(OUT_DIR, f"{coll_name}.json")
        with open(path, "w") as f:
            json.dump(docs, f, cls=MongoEncoder, indent=2)
        print(f"✓ {coll_name}: {len(docs)} docs → {path}")

    # Verify ashsvinyl
    user = db["users"].find_one({"email": "contact.ashsvinyl@gmail.com"}, {"password_hash": 0})
    if user:
        user["_id"] = str(user["_id"])
        user_id = user["_id"]
        recs = db["records"].count_documents({"user_id": user_id})
        posts = db["posts"].count_documents({"user_id": user_id})
        print(f"\n=== VERIFICATION: contact.ashsvinyl@gmail.com ===")
        print(f"User ID: {user_id}")
        print(f"Username: {user.get('username')}")
        print(f"Records: {recs}")
        print(f"Posts: {posts}")
        print(json.dumps(user, cls=MongoEncoder, indent=2))
    else:
        print("\n⚠ contact.ashsvinyl@gmail.com NOT FOUND in users collection")

    client.close()


if __name__ == "__main__":
    main()
