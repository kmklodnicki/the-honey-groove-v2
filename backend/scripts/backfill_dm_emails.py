"""One-time script: send DM notification emails to recipients of first messages
from the past 90 minutes who never got an email (because the feature didn't exist yet).
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from database import db, should_send_notification_email, FRONTEND_URL
from services.email_service import send_email_fire_and_forget
import templates.emails as email_tpl


async def main():
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()
    print(f"[backfill] Looking for conversations created since {cutoff}")

    # Find conversations created in the last 90 minutes
    convs = await db.dm_conversations.find(
        {"created_at": {"$gte": cutoff}},
        {"_id": 0}
    ).to_list(500)

    print(f"[backfill] Found {len(convs)} conversations in window")

    sent_count = 0
    skipped_count = 0

    for conv in convs:
        # Get the first message in this conversation
        first_msg = await db.dm_messages.find_one(
            {"conversation_id": conv["id"]},
            {"_id": 0},
            sort=[("created_at", 1)]
        )
        if not first_msg:
            continue

        sender_id = first_msg["sender_id"]
        # Recipient is the other participant
        recipient_id = [pid for pid in conv["participant_ids"] if pid != sender_id]
        if not recipient_id:
            continue
        recipient_id = recipient_id[0]

        # Look up both users
        sender = await db.users.find_one({"id": sender_id}, {"_id": 0, "username": 1})
        recipient = await db.users.find_one({"id": recipient_id}, {"_id": 0, "username": 1, "email": 1})

        if not sender or not recipient or not recipient.get("email"):
            skipped_count += 1
            continue

        # Check email preferences
        if not await should_send_notification_email(recipient_id, sender_id=sender_id):
            print(f"  [skip] @{recipient.get('username')} opted out of emails")
            skipped_count += 1
            continue

        # Send the email
        context = ""
        if conv.get("context"):
            context = conv["context"].get("record_name", "")

        tpl = email_tpl.new_dm(
            recipient.get("username", ""),
            sender.get("username", ""),
            context,
            f"{FRONTEND_URL}/messages"
        )
        print(f"  [send] Email to @{recipient.get('username')} ({recipient['email']}) — DM from @{sender.get('username')}")
        await send_email_fire_and_forget(recipient["email"], tpl["subject"], tpl["html"])
        sent_count += 1

    print(f"\n[backfill] Done. Sent: {sent_count}, Skipped: {skipped_count}")


if __name__ == "__main__":
    asyncio.run(main())
