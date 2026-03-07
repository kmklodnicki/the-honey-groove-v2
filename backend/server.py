"""HoneyGroove API — main app entry point."""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from database import db, client, init_storage, logger

from routes.auth import router as auth_router
from routes.hive import router as hive_router
from routes.collection import router as collection_router
from routes.honeypot import router as honeypot_router
from routes.trades import router as trades_router
from routes.notifications import router as notifications_router
from routes.dms import router as dms_router
from routes.explore import router as explore_router
from routes.valuation import router as valuation_router
from routes.wax_reports import router as wax_reports_router, schedule_weekly_reports
from routes.mood_boards import generate_weekly_mood_boards as gen_mood_boards
from routes.daily_prompts import router as daily_prompts_router, seed_prompts
from routes.newsletter import router as newsletter_router
from routes.mood_boards import router as mood_boards_router, generate_weekly_mood_boards
from routes.bingo import router as bingo_router, seed_bingo_squares
from routes.reports import router as reports_router
from routes.admin import router as admin_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="HoneyGroove API")

# Register all route modules under /api prefix
for r in [auth_router, hive_router, collection_router, honeypot_router,
          trades_router, notifications_router, dms_router, explore_router,
          valuation_router, wax_reports_router, daily_prompts_router, newsletter_router,
          mood_boards_router, bingo_router, reports_router, admin_router]:
    app.include_router(r, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.users.create_index("id", unique=True)
    await db.records.create_index("user_id")
    await db.records.create_index("id", unique=True)
    await db.spins.create_index("user_id")
    await db.spins.create_index("record_id")
    await db.posts.create_index("user_id")
    await db.posts.create_index("created_at")
    await db.followers.create_index([("follower_id", 1), ("following_id", 1)], unique=True)
    await db.likes.create_index([("post_id", 1), ("user_id", 1)], unique=True)
    await db.records.create_index([("user_id", 1), ("discogs_id", 1)])
    await db.discogs_tokens.create_index("user_id", unique=True)
    await db.iso_items.create_index("user_id")
    await db.iso_items.create_index("status")
    await db.listings.create_index([("status", 1), ("created_at", -1)])
    await db.listings.create_index("user_id")
    await db.trades.create_index([("initiator_id", 1)])
    await db.trades.create_index([("responder_id", 1)])
    await db.trades.create_index("status")
    await db.trade_ratings.create_index("rated_user_id")
    await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
    await db.notifications.create_index([("user_id", 1), ("read", 1)])
    await db.payment_transactions.create_index("session_id")
    await db.dm_conversations.create_index("participant_ids")
    await db.dm_conversations.create_index([("last_message_at", -1)])
    await db.dm_messages.create_index("conversation_id")
    await db.dm_messages.create_index([("sender_id", 1), ("read", 1)])
    await db.collection_values.create_index("release_id", unique=True)
    await db.collection_values.create_index("last_updated")
    await db.wax_reports.create_index([("user_id", 1), ("week_start", 1)], unique=True)
    await db.wax_reports.create_index([("user_id", 1), ("week_end", -1)])
    # Daily prompts indexes
    await db.prompts.create_index("scheduled_date")
    await db.prompts.create_index("id", unique=True)
    await db.prompt_responses.create_index([("user_id", 1), ("prompt_id", 1)], unique=True)
    await db.prompt_responses.create_index([("user_id", 1), ("created_at", -1)])
    await db.image_cache.create_index("release_id", unique=True)
    # Start weekly report scheduler
    asyncio.create_task(schedule_weekly_reports())
    # Start streak nudge scheduler
    from routes.daily_prompts import schedule_streak_nudges
    asyncio.create_task(schedule_streak_nudges())
    # Start hold auto-reversal scheduler
    from routes.trades import auto_reverse_expired_holds
    asyncio.create_task(_schedule_hold_auto_reversal())
    # Seed prompts
    await seed_prompts()
    # Seed bingo squares
    await seed_bingo_squares()
    # Mood board indexes
    await db.mood_boards.create_index([("user_id", 1), ("created_at", -1)])
    # Bingo indexes
    await db.bingo_cards.create_index("week_start", unique=True)
    await db.bingo_marks.create_index([("user_id", 1), ("card_id", 1)], unique=True)
    await db.bingo_squares.create_index("id", unique=True)

    # Beta & invite code indexes
    await db.beta_signups.create_index("email", unique=True)
    await db.beta_signups.create_index([("submitted_at", -1)])
    await db.invite_codes.create_index("code", unique=True)
    await db.invite_codes.create_index([("created_at", -1)])

    await db.users.update_one({"email": "demo@example.com"}, {"$set": {"is_admin": True}})

    try:
        init_storage()
        logger.info("Storage initialized")
    except Exception as e:
        logger.warning(f"Storage initialization skipped: {e}")

    logger.info("HoneyGroove API started")


async def _schedule_hold_auto_reversal():
    """Run hold auto-reversal check every 10 minutes."""
    from routes.trades import auto_reverse_expired_holds
    await asyncio.sleep(30)
    while True:
        try:
            await auto_reverse_expired_holds()
        except Exception as e:
            logger.error(f"Hold auto-reversal error: {e}")
        await asyncio.sleep(600)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
