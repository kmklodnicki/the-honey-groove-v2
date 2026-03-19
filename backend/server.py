"""HoneyGroove API — main app entry point."""
import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import socketio
import os
import logging

from database import db, client, init_storage, logger, hash_password, verify_db_connection
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
from routes.spotify import router as spotify_router
from routes.payments import router as payments_router
from routes.ebay import router as ebay_router
from routes.rooms import router as rooms_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="HoneyGroove API")

# Register all route modules under /api prefix
for r in [auth_router, hive_router, collection_router, honeypot_router,
          trades_router, notifications_router, dms_router, explore_router,
          valuation_router, wax_reports_router, daily_prompts_router, newsletter_router,
          mood_boards_router, bingo_router, reports_router, admin_router, search_router,
          verification_router, reports_router, seo_router, vinyl_router,
          weekly_wax_router, image_proxy_router, spotify_router, payments_router,
          ebay_router, rooms_router]:
    app.include_router(r, prefix="/api")

# --- Data export download endpoints ---
import glob as _glob

@app.get("/api/export/list")
async def list_exports():
    files = _glob.glob("/app/export/*.json")
    return [{"name": os.path.basename(f), "size_kb": round(os.path.getsize(f)/1024, 1)} for f in sorted(files)]

@app.get("/api/export/{filename}")
async def download_export(filename: str):
    path = f"/app/export/{filename}"
    if not os.path.exists(path) or ".." in filename:
        return {"error": "not found"}
    return FileResponse(path, media_type="application/json", filename=filename)

@app.get("/api/export/archive/all")
async def download_archive():
    path = "/app/export/honeygroove_export.tar.gz"
    if not os.path.exists(path):
        return {"error": "archive not found"}
    return FileResponse(path, media_type="application/gzip", filename="honeygroove_export.tar.gz")


cors_origins = [
    "https://thehoneygroove.com",
    "https://www.thehoneygroove.com",
    "https://honey-groove-backend.vercel.app",
]
# Also include FRONTEND_URL if it's a real URL and not already listed
_frontend = os.environ.get("FRONTEND_URL", "")
if _frontend and _frontend.startswith("http") and _frontend.rstrip("/") not in cors_origins:
    cors_origins.append(_frontend.rstrip("/"))
cors_env = os.environ.get("CORS_ORIGINS", "")
if cors_env and cors_env != "*":
    cors_origins += [o.strip().rstrip("/") for o in cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)


# ── Global OPTIONS preflight handler ──
# Intercepts ALL OPTIONS requests and returns 200 immediately with CORS headers.
# This sits OUTSIDE CORSMiddleware so it fires first, even behind reverse proxies.
@app.middleware("http")
async def handle_preflight(request: Request, call_next):
    if request.method == "OPTIONS":
        origin = request.headers.get("origin", "")
        resp = Response(status_code=200)
        if origin in cors_origins:
            resp.headers["Access-Control-Allow-Origin"] = origin
        else:
            resp.headers["Access-Control-Allow-Origin"] = cors_origins[0]
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Max-Age"] = "86400"
        return resp
    response = await call_next(request)
    return response


# ── Image proxy middleware: rewrite cover_url in JSON responses ──
from urllib.parse import quote as _url_quote
import json as _json

def _rewrite_cover_urls(obj):
    """Recursively rewrite cover_url values to route through image proxy."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key == "cover_url" and isinstance(val, str) and val.startswith("http") and "/api/image-proxy" not in val:
                obj[key] = f"/api/image-proxy?url={_url_quote(val, safe='')}"
            elif isinstance(val, (dict, list)):
                _rewrite_cover_urls(val)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                _rewrite_cover_urls(item)

@app.middleware("http")
async def proxy_cover_urls_middleware(request: Request, call_next):
    response = await call_next(request)
    # Only process JSON API responses (skip image-proxy, files, websocket, etc.)
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response
    path = request.url.path
    # Skip endpoints that don't return cover_url data
    if path.startswith("/api/image-proxy") or path.startswith("/api/health") or path.startswith("/api/ws"):
        return response
    # Read and rewrite the response body
    body_bytes = b""
    async for chunk in response.body_iterator:
        if isinstance(chunk, bytes):
            body_bytes += chunk
        else:
            body_bytes += chunk.encode("utf-8")
    try:
        data = _json.loads(body_bytes)
        _rewrite_cover_urls(data)
        new_body = _json.dumps(data).encode("utf-8")
        # Build new headers, updating content-length
        headers = dict(response.headers)
        headers["content-length"] = str(len(new_body))
        return Response(
            content=new_body,
            status_code=response.status_code,
            headers=headers,
            media_type="application/json",
        )
    except (ValueError, UnicodeDecodeError):
        # Not valid JSON, return as-is
        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


# ── Health check ──
@app.get("/health")
@app.get("/api/health")
async def health_check():
    pool_info = {}
    try:
        server_info = client.topology_description.server_descriptions()
        for addr, desc in server_info.items():
            pool_info[f"{addr[0]}:{addr[1]}"] = str(desc.server_type)
        # Ping to verify connection
        await client.admin.command('ping')
        pool_info["db_status"] = "connected"
    except Exception as e:
        pool_info["db_status"] = f"error: {str(e)}"
    pool_info["maxPoolSize"] = client.options.pool_options.max_pool_size
    pool_info["minPoolSize"] = client.options.pool_options.min_pool_size
    return {"status": "ok", "service": "honeygroove-api", "pool": pool_info}


async def _backfill_color_variants():
    """Background task: backfill color_variant for records missing it (connection-safe)."""
    from database import get_discogs_release
    await asyncio.sleep(30)  # Wait for server to settle
    try:
        records = await db.records.find(
            {"discogs_id": {"$ne": None}, "$or": [{"color_variant": None}, {"color_variant": {"$exists": False}}]},
            {"_id": 0, "id": 1, "discogs_id": 1, "title": 1}
        ).limit(100).to_list(100)  # Reduced batch size to limit connection pressure
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
                await asyncio.sleep(2)  # Increased sleep to reduce connection contention
            except Exception as e:
                logger.debug(f"Variant backfill skip {rec.get('title')}: {e}")
        logger.info(f"Variant backfill complete: {updated}/{len(records)} updated")
    except Exception as e:
        logger.error(f"Variant backfill error: {e}")


async def _backfill_iso_color_variants():
    """Background task: backfill color_variant for ISO items missing it (connection-safe)."""
    from database import get_discogs_release
    await asyncio.sleep(60)  # Stagger well after records backfill
    try:
        isos = await db.iso_items.find(
            {"discogs_id": {"$ne": None}, "$or": [{"color_variant": None}, {"color_variant": {"$exists": False}}]},
            {"_id": 0, "id": 1, "discogs_id": 1, "album": 1}
        ).limit(50).to_list(50)  # Reduced batch size
        if not isos:
            logger.info("ISO variant backfill: no items need updating")
            return
        logger.info(f"ISO variant backfill: processing {len(isos)} items")
        updated = 0
        for iso in isos:
            try:
                release_data = await asyncio.to_thread(get_discogs_release, iso["discogs_id"])
                if release_data and release_data.get("color_variant"):
                    await db.iso_items.update_one(
                        {"id": iso["id"]},
                        {"$set": {"color_variant": release_data["color_variant"]}}
                    )
                    updated += 1
                await asyncio.sleep(2)  # Increased sleep to reduce connection contention
            except Exception as e:
                logger.debug(f"ISO variant backfill skip {iso.get('album')}: {e}")
        logger.info(f"ISO variant backfill complete: {updated}/{len(isos)} updated")
    except Exception as e:
        logger.error(f"ISO variant backfill error: {e}")


@app.on_event("startup")
async def startup_event():
    # Verify database connection first
    db_ok = await verify_db_connection()
    if not db_ok:
        logger.error("STARTUP WARNING: Database connection failed — some features may not work")
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
    # Honeycomb Rooms indexes
    await db.rooms.create_index("slug", unique=True)
    await db.room_members.create_index([("slug", 1), ("userId", 1)], unique=True)
    await db.room_members.create_index("userId")
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

    # BLOCK 569/571: Admin Override — tied to user identity (email + user ID), not username
    ADMIN_USER_ID = "4072aaa7-1171-4cd2-9c8f-20dfca8fdc58"
    ADMIN_EMAIL = "kmklodnicki@gmail.com"
    ADMIN_USERNAME = "katie"
    admin_set = {"golden_hive_verified": True, "golden_hive": True, "golden_hive_status": "APPROVED", "is_admin": True}

    # Check if admin exists at all
    admin_user = await db.users.find_one({"$or": [{"id": ADMIN_USER_ID}, {"email": ADMIN_EMAIL}]})
    if not admin_user:
        # Fresh database — seed the master admin
        logger.info("Fresh database detected — seeding master admin account")
        admin_hash = hash_password("HoneyGroove2026!")
        now = datetime.now(timezone.utc).isoformat()
        await db.users.insert_one({
            "id": ADMIN_USER_ID,
            "email": ADMIN_EMAIL,
            "username": ADMIN_USERNAME,
            "password_hash": admin_hash,
            "avatar_url": "https://api.dicebear.com/7.x/miniavs/svg?seed=katie",
            "bio": None, "setup": None, "location": None, "favorite_genre": None,
            "onboarding_completed": False,
            "founding_member": True,
            "is_admin": True,
            "golden_hive_verified": True, "golden_hive": True, "golden_hive_status": "APPROVED",
            "created_at": now,
        })
        logger.info(f"Master admin seeded: {ADMIN_EMAIL} / username: {ADMIN_USERNAME}")
    else:
        # Ensure admin flags + correct username
        await db.users.update_one(
            {"$or": [{"id": ADMIN_USER_ID}, {"email": ADMIN_EMAIL}]},
            {"$set": {**admin_set, "username": ADMIN_USERNAME}}
        )
        logger.info(f"Admin override applied for {ADMIN_EMAIL} / username: {ADMIN_USERNAME}")

    # Verification + payout indexes
    await db.verification_requests.create_index("user_id")
    await db.verification_requests.create_index("status")
    await db.pulse_data.create_index("release_id", unique=True)
    await db.recovery_runs.create_index("user_id", unique=True)
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

    # OAuth Configuration Verification Log
    from database import DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
    oauth_key_ok = bool(DISCOGS_CONSUMER_KEY)
    oauth_secret_ok = bool(DISCOGS_CONSUMER_SECRET)
    if oauth_key_ok and oauth_secret_ok:
        logger.info(f"Discogs OAuth configured: KEY={DISCOGS_CONSUMER_KEY[:4]}... SECRET=****")
    else:
        logger.error(f"Discogs OAuth MISSING: KEY_present={oauth_key_ok}, SECRET_present={oauth_secret_ok}")

    logger.info(f"HoneyGroove API started | DB: {db.name} | Users: {await db.users.count_documents({})} | CORS origins: {cors_origins}")
    logger.info(f"Routes: {[r.path for r in app.routes if hasattr(r, 'path')]}")
    # Start background variant backfill
    asyncio.create_task(_backfill_color_variants())
    asyncio.create_task(_backfill_iso_color_variants())
    # BLOCK 476: Start nightly value recovery scheduler
    from services.value_recovery import schedule_nightly_recovery
    asyncio.create_task(schedule_nightly_recovery())


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
