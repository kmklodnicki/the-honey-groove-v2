"""HoneyGroove API — main app entry point."""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import os
import logging

from database import db, client, init_storage, logger
from live_hive import sio

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
from routes.search import router as search_router
from routes.verification import router as verification_router
from routes.reports import router as reports_router
from routes.seo import router as seo_router
from routes.vinyl import router as vinyl_router
from routes.weekly_wax import router as weekly_wax_router, schedule_weekly_wax
from routes.image_proxy import router as image_proxy_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="HoneyGroove API")

# Register all route modules under /api prefix
for r in [auth_router, hive_router, collection_router, honeypot_router,
          trades_router, notifications_router, dms_router, explore_router,
          valuation_router, wax_reports_router, daily_prompts_router, newsletter_router,
          mood_boards_router, bingo_router, reports_router, admin_router, search_router,
          verification_router, reports_router, seo_router, vinyl_router,
          weekly_wax_router, image_proxy_router]:
    app.include_router(r, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


async def _backfill_color_variants():
    """Background task: backfill color_variant for records missing it."""
    from database import get_discogs_release
    await asyncio.sleep(15)  # Wait for server to settle
    try:
        records = await db.records.find(
            {"discogs_id": {"$ne": None}, "$or": [{"color_variant": None}, {"color_variant": {"$exists": False}}]},
            {"_id": 0, "id": 1, "discogs_id": 1, "title": 1}
        ).limit(500).to_list(500)
        if not records:
            logger.info("Variant backfill: no records need updating")
            return
        logger.info(f"Variant backfill: processing {len(records)} records")
        updated = 0
        for rec in records:
            try:
                release_data = await asyncio.to_thread(get_discogs_release, rec["discogs_id"])
                if release_data and release_data.get("color_variant"):
                    await db.records.update_one(
                        {"id": rec["id"]},
                        {"$set": {"color_variant": release_data["color_variant"]}}
                    )
                    updated += 1
                await asyncio.sleep(1.1)  # Respect Discogs rate limit
            except Exception as e:
                logger.debug(f"Variant backfill skip {rec.get('title')}: {e}")
        logger.info(f"Variant backfill complete: {updated}/{len(records)} updated")
    except Exception as e:
        logger.error(f"Variant backfill error: {e}")


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
    # Search indexes for global search performance
    await db.records.create_index([("artist", 1)])
    await db.records.create_index([("title", 1)])
    await db.posts.create_index([("caption", "text"), ("content", "text")])
    await db.listings.create_index([("artist", 1), ("album", 1)])

    # ── BLOCK 447: Warp Speed Indexes ──
    # Compound index for the filtered marketplace query (status + is_test_listing + sort)
    await db.listings.create_index([("status", 1), ("is_test_listing", 1), ("created_at", -1)])
    # Feed: post_type + created_at for filtered/sorted queries
    await db.posts.create_index([("post_type", 1), ("created_at", -1)])
    # Listing alerts: fast lookup by release/variant
    await db.listing_alerts.create_index([("release_id", 1), ("status", 1)])
    # Discogs ID on listings for ISO matching
    await db.listings.create_index("discogs_id")
    # Prompt responses: fast fetch by prompt_id sorted
    await db.prompt_responses.create_index([("prompt_id", 1), ("created_at", -1)])
    # Daily prompts indexes
    await db.prompts.create_index("scheduled_date")
    await db.prompts.create_index("id", unique=True)
    await db.prompt_responses.create_index([("user_id", 1), ("prompt_id", 1)], unique=True)
    await db.prompt_responses.create_index([("user_id", 1), ("created_at", -1)])
    await db.image_cache.create_index("release_id", unique=True)
    # Start weekly report scheduler
    asyncio.create_task(schedule_weekly_reports())
    # Start Weekly Wax email scheduler
    asyncio.create_task(schedule_weekly_wax())
    # Start streak nudge scheduler
    from routes.daily_prompts import schedule_streak_nudges
    asyncio.create_task(schedule_streak_nudges())
    # Start hold auto-reversal scheduler
    from routes.trades import auto_reverse_expired_holds
    asyncio.create_task(_schedule_hold_auto_reversal())
    # Start auto-payout scheduler
    asyncio.create_task(_schedule_auto_payouts())
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

    # BLOCK 511: Admin Override — ensure @katieintheafterglow is always Golden Hive Verified + admin
    await db.users.update_one(
        {"username": "katieintheafterglow"},
        {"$set": {
            "golden_hive_verified": True,
            "golden_hive": True,
            "golden_hive_status": "APPROVED",
            "is_admin": True,
        }}
    )
    logger.info("BLOCK 511: Admin override applied for @katieintheafterglow")

    # Verification + payout indexes
    await db.verification_requests.create_index("user_id")
    await db.verification_requests.create_index("status")
    await db.pulse_data.create_index("release_id", unique=True)
    await db.reports.create_index("reporter_user_id")
    await db.reports.create_index([("status", 1), ("target_type", 1)])

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
    # Start background variant backfill
    asyncio.create_task(_backfill_color_variants())


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


async def _schedule_auto_payouts():
    """Run auto-payout check every 30 minutes."""
    from routes.payout_cron import run_auto_payouts
    await asyncio.sleep(60)
    while True:
        try:
            await run_auto_payouts()
        except Exception as e:
            logger.error(f"Auto-payout cron error: {e}")
        await asyncio.sleep(1800)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# Wrap FastAPI with Socket.IO ASGI app for real-time support
combined_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="/api/ws/socket.io")
