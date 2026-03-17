"""BLOCK 476: Value Recovery Engine — OAuth-aware collection valuation pipeline.

Uses user's Discogs OAuth tokens for higher rate limits and more accurate pricing.
Falls back to the platform's personal token when OAuth is unavailable.
Tracks per-user recovery progress so the frontend can show a progress bar.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

from database import (
    db, get_discogs_market_data,
    DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET,
    DISCOGS_API_BASE, DISCOGS_USER_AGENT,
)

logger = logging.getLogger("value_recovery")

# In-memory progress tracker  {user_id: {status, total, valued, ...}}
recovery_progress: Dict[str, Dict] = {}

CACHE_TTL_HOURS = 24
BATCH_PAUSE_SECS = 1.2  # Discogs rate limit: ~60 req/min


# ──────────────────── OAuth-Aware Fetch ────────────────────

def _get_market_data_with_oauth(release_id: int, oauth_token: str, oauth_token_secret: str) -> Optional[Dict]:
    """Fetch Discogs market data using OAuth 1.0a tokens. Forces USD via curr_abbr."""
    from requests_oauthlib import OAuth1Session

    session = OAuth1Session(
        client_key=DISCOGS_CONSUMER_KEY,
        client_secret=DISCOGS_CONSUMER_SECRET,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
        signature_method="HMAC-SHA1",
    )
    session.headers.update({"User-Agent": DISCOGS_USER_AGENT})

    try:
        resp = session.get(
            f"{DISCOGS_API_BASE}/marketplace/price_suggestions/{release_id}",
            params={"curr_abbr": "USD"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            vinyl_price = data.get("Very Good Plus (VG+)", {})
            mint_price = data.get("Mint (M)", {})
            good_price = data.get("Good Plus (G+)", {})
            median = vinyl_price.get("value") or mint_price.get("value")
            low = good_price.get("value") or vinyl_price.get("value")
            high = mint_price.get("value") or vinyl_price.get("value")
            if median is not None and float(median) > 0.5:
                return {
                    "median_value": round(float(median), 2),
                    "low_value": round(float(low), 2) if low else round(float(median) * 0.6, 2),
                    "high_value": round(float(high), 2) if high else round(float(median) * 1.5, 2),
                }

        resp2 = session.get(
            f"{DISCOGS_API_BASE}/releases/{release_id}",
            params={"curr_abbr": "USD"},
            timeout=10,
        )
        if resp2.status_code == 200:
            data2 = resp2.json()
            lowest = data2.get("lowest_price")
            if lowest is not None and float(lowest) > 0.5:
                lp = float(lowest)
                return {
                    "median_value": round(lp * 2.0, 2),
                    "low_value": round(lp, 2),
                    "high_value": round(lp * 3.5, 2),
                }
    except Exception as e:
        logger.warning(f"OAuth market data fetch failed for {release_id}: {e}")
    return None


async def _fetch_market_value(release_id: int, oauth_token: str = None, oauth_token_secret: str = None) -> Optional[Dict]:
    """Fetch market data: prefer OAuth tokens, fallback to platform token."""
    if oauth_token and oauth_token_secret:
        data = await asyncio.to_thread(
            _get_market_data_with_oauth, release_id, oauth_token, oauth_token_secret
        )
        if data:
            return data
    # Fallback to platform token
    return await asyncio.to_thread(get_discogs_market_data, release_id)


# ──────────────────── Core Recovery Pipeline ────────────────────

async def run_value_recovery(user_id: str):
    """Main recovery pipeline: fetch values for all unvalued records in a user's collection."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Get user's OAuth tokens (if available)
    token_doc = await db.discogs_tokens.find_one({"user_id": user_id}, {"_id": 0})
    oauth_token = token_doc.get("oauth_token") if token_doc else None
    oauth_token_secret = token_doc.get("oauth_token_secret") if token_doc else None
    has_oauth = bool(oauth_token and oauth_token_secret)

    # 2. Get all records with discogs_id
    records = await db.records.find(
        {"user_id": user_id, "discogs_id": {"$ne": None}},
        {"_id": 0, "id": 1, "discogs_id": 1},
    ).to_list(10000)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})

    if not discogs_ids:
        recovery_progress[user_id] = {
            "status": "completed",
            "total": 0, "valued": 0, "recovered": 0, "failed": 0,
            "using_oauth": has_oauth,
            "started_at": now_iso, "completed_at": now_iso,
        }
        return

    # 3. Find which are already cached and fresh (sub-$1 values are treated as stale — likely wrong currency data)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)).isoformat()
    fresh_docs = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}, "last_updated": {"$gte": cutoff}, "median_value": {"$gte": 1}},
        {"_id": 0, "release_id": 1},
    ).to_list(10000)
    fresh_ids = {d["release_id"] for d in fresh_docs}
    stale_ids = [did for did in discogs_ids if did not in fresh_ids]

    total = len(discogs_ids)
    already_valued = len(fresh_ids)

    recovery_progress[user_id] = {
        "status": "in_progress",
        "total": total,
        "valued": already_valued,
        "recovered": 0,
        "failed": 0,
        "using_oauth": has_oauth,
        "started_at": now_iso,
        "completed_at": None,
    }

    if not stale_ids:
        recovery_progress[user_id]["status"] = "completed"
        recovery_progress[user_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Value Recovery [{user_id}]: all {total} records already valued")
        return

    logger.info(f"Value Recovery [{user_id}]: {len(stale_ids)} of {total} records need valuation (oauth={has_oauth})")

    recovered = 0
    failed = 0
    recovered_details = []  # Track per-record recovery for interactive toast

    for did in stale_ids:
        try:
            # Get old value before recovery
            old_doc = await db.collection_values.find_one({"release_id": did}, {"_id": 0, "median_value": 1})
            old_value = old_doc.get("median_value", 0) if old_doc else 0
            price_source = "Discogs"
            rec_doc = None

            data = await _fetch_market_value(did, oauth_token, oauth_token_secret)

            # Advanced Price Hunting: if Discogs returns no data, try eBay/Google scraper
            if not data or data.get("median_value", 0) == 0:
                rec_doc = await db.records.find_one(
                    {"discogs_id": did, "user_id": user_id},
                    {"_id": 0, "title": 1, "artist": 1, "id": 1, "catno": 1}
                )
                if rec_doc:
                    from services.price_scraper import hunt_external_price
                    ext = await hunt_external_price(
                        rec_doc.get("artist", ""),
                        rec_doc.get("title", ""),
                        rec_doc.get("catno", ""),
                        db=db,
                    )
                    if ext:
                        data = ext
                        price_source = ext["source"]  # "eBay Sold" or "Google Market"

            if data and data.get("median_value", 0) > 0:
                await db.collection_values.update_one(
                    {"release_id": did},
                    {"$set": {
                        "release_id": did,
                        "median_value": data["median_value"],
                        "low_value": data.get("low_value", 0),
                        "high_value": data.get("high_value", 0),
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "source": price_source,
                    }},
                    upsert=True,
                )
                recovered += 1

                # Get record title/artist for the detail
                if not rec_doc:
                    rec_doc = await db.records.find_one(
                        {"discogs_id": did, "user_id": user_id},
                        {"_id": 0, "title": 1, "artist": 1, "id": 1}
                    )
                if rec_doc:
                    recovered_details.append({
                        "record_id": rec_doc.get("id"),
                        "title": rec_doc.get("title", "Unknown"),
                        "artist": rec_doc.get("artist", "Unknown"),
                        "old_value": round(old_value, 2),
                        "new_value": data["median_value"],
                        "increase": round(data["median_value"] - old_value, 2),
                        "source": price_source,
                    })
            else:
                failed += 1
        except Exception as e:
            logger.warning(f"Value Recovery [{user_id}]: failed for {did}: {e}")
            failed += 1

        # Update progress
        recovery_progress[user_id]["valued"] = already_valued + recovered
        recovery_progress[user_id]["recovered"] = recovered
        recovery_progress[user_id]["failed"] = failed

        await asyncio.sleep(BATCH_PAUSE_SECS)

    total_increase = round(sum(d["increase"] for d in recovered_details), 2)

    recovery_progress[user_id]["status"] = "completed"
    recovery_progress[user_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    recovery_progress[user_id]["recovered_details"] = recovered_details[:50]  # Cap at 50 for payload size
    recovery_progress[user_id]["total_increase"] = total_increase
    logger.info(f"Value Recovery [{user_id}]: complete — {recovered} recovered, {failed} failed, {already_valued} already fresh, +${total_increase}")

    # Persist summary to DB for historical tracking
    await db.recovery_runs.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "total": total,
            "valued": already_valued + recovered,
            "recovered": recovered,
            "failed": failed,
            "using_oauth": has_oauth,
            "last_run_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )


async def get_recovery_status(user_id: str) -> Dict:
    """Return current or last recovery status for a user."""
    # Check in-memory first (active run)
    if user_id in recovery_progress:
        return recovery_progress[user_id]

    # Check DB for last run
    doc = await db.recovery_runs.find_one({"user_id": user_id}, {"_id": 0})
    if doc:
        return {
            "status": "completed",
            "total": doc.get("total", 0),
            "valued": doc.get("valued", 0),
            "recovered": doc.get("recovered", 0),
            "failed": doc.get("failed", 0),
            "using_oauth": doc.get("using_oauth", False),
            "started_at": None,
            "completed_at": doc.get("last_run_at"),
        }

    return {"status": "idle", "total": 0, "valued": 0, "recovered": 0, "failed": 0}


# ──────────────────── Scheduler: Nightly Recovery ────────────────────

async def schedule_nightly_recovery():
    """Run value recovery for all users with OAuth tokens once per day at 3 AM UTC."""
    await asyncio.sleep(120)  # Wait for server to settle
    while True:
        now = datetime.now(timezone.utc)
        # Calculate seconds until next 3 AM UTC
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        wait_secs = (target - now).total_seconds()
        logger.info(f"Value Recovery scheduler: next run in {wait_secs/3600:.1f}h at {target.isoformat()}")
        await asyncio.sleep(wait_secs)

        try:
            # Get all users with OAuth tokens
            users = await db.discogs_tokens.find(
                {"oauth_token": {"$exists": True, "$ne": None}},
                {"_id": 0, "user_id": 1},
            ).to_list(10000)

            logger.info(f"Value Recovery scheduler: running for {len(users)} OAuth users")
            for u in users:
                try:
                    await run_value_recovery(u["user_id"])
                except Exception as e:
                    logger.error(f"Nightly recovery failed for {u['user_id']}: {e}")
                await asyncio.sleep(5)  # Pause between users
        except Exception as e:
            logger.error(f"Value Recovery scheduler error: {e}")

        await asyncio.sleep(60)  # Prevent double-run
