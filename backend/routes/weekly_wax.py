"""Weekly Wax Email — personalized weekly email sent every Sunday at 12:00 PM ET."""

from fastapi import APIRouter, Depends
from typing import Dict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import asyncio
import logging

from database import db, require_auth
from services.email_service import send_email

logger = logging.getLogger("weekly_wax")
router = APIRouter()

ET = ZoneInfo("America/New_York")
BATCH_SIZE = 50


# ─────────────────── Personal Stats ───────────────────

async def _get_user_weekly_stats(user_id: str, week_start: str, week_end: str) -> dict:
    """Compute personal stats for a user's week."""
    stats = {
        "weekly_spins_count": 0,
        "records_added_this_week": 0,
        "new_taste_matches": 0,
        "last_now_spinning_record": None,
    }

    # Count Now Spinning posts this week
    stats["weekly_spins_count"] = await db.posts.count_documents({
        "user_id": user_id,
        "post_type": "NOW_SPINNING",
        "created_at": {"$gte": week_start, "$lte": week_end},
    })

    # Count records added to collection this week
    stats["records_added_this_week"] = await db.records.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": week_start, "$lte": week_end},
    })

    # Most recent Now Spinning post — join with records to get artist/album
    pipeline = [
        {"$match": {"user_id": user_id, "post_type": "NOW_SPINNING"}},
        {"$sort": {"created_at": -1}},
        {"$limit": 1},
        {"$lookup": {
            "from": "records",
            "localField": "record_id",
            "foreignField": "id",
            "as": "record",
        }},
        {"$unwind": {"path": "$record", "preserveNullAndEmptyArrays": True}},
    ]
    async for doc in db.posts.aggregate(pipeline):
        rec = doc.get("record", {})
        artist = rec.get("artist", "")
        title = rec.get("title", "")
        variant = rec.get("color_variant", "")
        if artist or title:
            text = f"{artist} — {title}" if artist and title else (artist or title)
            if variant:
                text += f" ({variant})"
            stats["last_now_spinning_record"] = text

    # New taste matches: top 3 not-yet-followed users with collection overlap
    user_discogs = set()
    async for rec in db.records.find({"user_id": user_id, "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}):
        user_discogs.add(rec["discogs_id"])

    if user_discogs:
        # Get users this person follows
        following_ids = set()
        async for f in db.followers.find({"follower_id": user_id}, {"_id": 0, "following_id": 1}):
            following_ids.add(f["following_id"])
        following_ids.add(user_id)

        # Get blocked user ids
        blocked_ids = set()
        async for b in db.blocks.find({"$or": [{"blocker_id": user_id}, {"blocked_id": user_id}]}, {"_id": 0, "blocker_id": 1, "blocked_id": 1}):
            blocked_ids.add(b["blocker_id"])
            blocked_ids.add(b["blocked_id"])

        exclude_ids = following_ids | blocked_ids

        # Find other users with overlapping discogs_ids
        pipeline = [
            {"$match": {"discogs_id": {"$in": list(user_discogs)}, "user_id": {"$nin": list(exclude_ids)}}},
            {"$group": {"_id": "$user_id", "common": {"$sum": 1}}},
            {"$sort": {"common": -1}},
            {"$limit": 3},
        ]
        matches = []
        async for doc in db.records.aggregate(pipeline):
            matches.append(doc)
        stats["new_taste_matches"] = len(matches)

    return stats


# ─────────────────── Community Stats (precomputed once) ───────────────────

async def _get_community_stats(week_start: str, week_end: str) -> dict:
    """Compute platform-wide community stats for the week."""
    stats = {
        "most_spun_record": None,
        "rising_variant": None,
        "most_wanted_variant": None,
    }

    # Most spun record: record_id with most Now Spinning posts this week, then lookup record
    async def _most_spun(date_filter: dict) -> str | None:
        pipeline = [
            {"$match": {"post_type": "NOW_SPINNING", **date_filter}},
            {"$group": {"_id": "$record_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
            {"$lookup": {
                "from": "records",
                "localField": "_id",
                "foreignField": "id",
                "as": "record",
            }},
            {"$unwind": {"path": "$record", "preserveNullAndEmptyArrays": True}},
        ]
        async for doc in db.posts.aggregate(pipeline):
            rec = doc.get("record", {})
            a = rec.get("artist", "")
            t = rec.get("title", "")
            v = rec.get("color_variant", "")
            if a or t:
                return f"{a} — {t}" + (f" ({v})" if v else "")
        return None

    # Try weekly, fallback to all-time
    stats["most_spun_record"] = await _most_spun({"created_at": {"$gte": week_start, "$lte": week_end}})
    if not stats["most_spun_record"]:
        stats["most_spun_record"] = await _most_spun({})

    # Rising variant: variant with most ISO adds this week
    async def _rising(date_filter: dict) -> str | None:
        pipeline = [
            {"$match": {"status": {"$in": ["OPEN", "WISHLIST"]}, **date_filter}},
            {"$group": {
                "_id": {"artist": "$artist", "album": "$album"},
                "count": {"$sum": 1},
                "variant": {"$first": "$color_variant"},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]
        async for doc in db.iso_items.aggregate(pipeline):
            a = doc["_id"].get("artist", "")
            t = doc["_id"].get("album", "")
            v = doc.get("variant", "")
            if a or t:
                return f"{a} — {t}" + (f" ({v})" if v else "")
        return None

    stats["rising_variant"] = await _rising({"created_at": {"$gte": week_start, "$lte": week_end}})
    if not stats["rising_variant"]:
        stats["rising_variant"] = await _rising({})

    # Most wanted variant: variant added to Actively Seeking most this week
    async def _most_wanted(date_filter: dict) -> str | None:
        pipeline = [
            {"$match": {"status": "OPEN", **date_filter}},
            {"$group": {
                "_id": {"artist": "$artist", "album": "$album"},
                "count": {"$sum": 1},
                "variant": {"$first": "$color_variant"},
            }},
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]
        async for doc in db.iso_items.aggregate(pipeline):
            a = doc["_id"].get("artist", "")
            t = doc["_id"].get("album", "")
            v = doc.get("variant", "")
            if a or t:
                return f"{a} — {t}" + (f" ({v})" if v else "")
        return None

    stats["most_wanted_variant"] = await _most_wanted({"created_at": {"$gte": week_start, "$lte": week_end}})
    if not stats["most_wanted_variant"]:
        stats["most_wanted_variant"] = await _most_wanted({})

    return stats


# ─────────────────── Collector Recommendations ───────────────────

async def _get_collector_recommendations(user_id: str) -> list[dict]:
    """Get top 3 collector recommendations the user doesn't follow."""
    user_discogs = set()
    async for rec in db.records.find({"user_id": user_id, "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1}):
        user_discogs.add(rec["discogs_id"])

    if not user_discogs:
        return []

    # Get excluded user ids (self, following, blocked)
    following_ids = set()
    async for f in db.followers.find({"follower_id": user_id}, {"_id": 0, "following_id": 1}):
        following_ids.add(f["following_id"])

    blocked_ids = set()
    async for b in db.blocks.find({"$or": [{"blocker_id": user_id}, {"blocked_id": user_id}]}, {"_id": 0, "blocker_id": 1, "blocked_id": 1}):
        blocked_ids.add(b["blocker_id"])
        blocked_ids.add(b["blocked_id"])

    exclude_ids = list(following_ids | blocked_ids | {user_id})

    # Find users with most records in common
    pipeline = [
        {"$match": {"discogs_id": {"$in": list(user_discogs)}, "user_id": {"$nin": exclude_ids}}},
        {"$group": {"_id": "$user_id", "records_in_common": {"$sum": 1}}},
        {"$sort": {"records_in_common": -1}},
        {"$limit": 10},
    ]
    candidates = []
    async for doc in db.records.aggregate(pipeline):
        candidates.append(doc)

    if not candidates:
        return []

    # Fetch usernames, filter out private users
    candidate_ids = [c["_id"] for c in candidates]
    users_map = {}
    async for u in db.users.find(
        {"id": {"$in": candidate_ids}, "is_private": {"$ne": True}},
        {"_id": 0, "id": 1, "username": 1}
    ):
        users_map[u["id"]] = u["username"]

    results = []
    for c in candidates:
        username = users_map.get(c["_id"])
        if username:
            results.append({
                "name": username,
                "records_in_common": c["records_in_common"],
            })
        if len(results) >= 3:
            break

    return results


# ─────────────────── Email Template ───────────────────

def _build_weekly_wax_html(data: dict) -> str:
    """Build the full Weekly Wax HTML email body."""
    from templates.base import wrap_email
    import os
    FRONTEND = os.environ.get("FRONTEND_URL", "https://thehoneygroove.com")

    AMBER = "color:#C8861A;"
    MUTED = "color:#8A6B4A;font-size:13px;"
    GREETING = "color:#2A1A06;font-size:15px;"
    SEC_HEAD = "font-family:'Playfair Display',Georgia,serif;font-weight:700;color:#2A1A06;font-size:18px;margin:0 0 12px 0;"
    STAT = "color:#2A1A06;font-size:14px;line-height:1.8;"
    STRONG = "font-weight:700;color:#2A1A06;"
    DIVIDER = '<div style="height:1px;background:#C8861A;opacity:0.2;margin:28px 0;"></div>'

    first_name = data.get("first_name", "collector")
    spins = data.get("weekly_spins_count", 0)
    added = data.get("records_added_this_week", 0)
    taste = data.get("new_taste_matches", 0)
    last_spin = data.get("last_now_spinning_record") or "nothing logged yet — drop your first spin."
    most_spun = data.get("most_spun_record") or "the Hive is just getting warmed up"
    rising = data.get("rising_variant") or "new favorites are bubbling up"
    most_wanted = data.get("most_wanted_variant") or "collectors are building their Dream Lists now"
    collectors = data.get("collectors", [])

    # BLOCK 476: Collection value data
    collection_value = data.get("collection_value", {})
    total_value = collection_value.get("total_value", 0)
    valued_count = collection_value.get("valued_count", 0)
    total_count = collection_value.get("total_count", 0)
    top_gem = data.get("top_gem")

    # Collector recommendations section
    collector_html = ""
    if collectors:
        for c in collectors:
            collector_html += f'<p style="{STAT}"><strong style="{STRONG}">{c["name"]}</strong> — {c["records_in_common"]} records in common</p>\n'
        collector_html += f'\n<p style="{STAT}">Follow them and see what they\'re spinning.</p>'
    else:
        collector_html = f'<p style="{STAT}">More collector recommendations are coming as the Hive grows.</p>'

    body = f"""
    <p style="{GREETING}">Hey <strong>{first_name}</strong>,</p>

    <p style="{GREETING}">Welcome to the hive.</p>

    <p style="{GREETING}">This is your <strong>Weekly Wax</strong> — a Sunday ritual we're starting together. Every week you'll get a recap of what the community has been spinning, what's trending across collectors, and what dropped on <strong>New Music Friday</strong> worth paying attention to.</p>

    <p style="{GREETING}">This is week one. You're part of something that's just getting started. Your spins, your taste, and your collection help shape what this community becomes.</p>

    <p style="{GREETING}">That's not nothing.</p>

    {DIVIDER}

    <h2 style="{SEC_HEAD}">your week on wax</h2>

    <p style="{STAT}">Here's how your groove looked this week:</p>

    <p style="{STAT}">
    &bull; records spun: <strong style="{STRONG}">{spins}</strong><br>
    &bull; records added to your collection: <strong style="{STRONG}">{added}</strong><br>
    &bull; collectors with similar taste discovered: <strong style="{STRONG}">{taste}</strong>
    </p>

    <p style="{STAT}">Your most recent spin:<br>
    <strong style="{STRONG}">{last_spin}</strong></p>

    <p style="{STAT}">Keep the wax spinning.</p>
"""

    # BLOCK 476: Insert collection value section if user has valued records
    if total_value > 0:
        value_section = f"""
    {DIVIDER}

    <h2 style="{SEC_HEAD}">your collection value</h2>

    <p style="{STAT}">Your collection is currently valued at:</p>

    <p style="font-family:'Playfair Display',Georgia,serif;font-weight:700;color:#C8861A;font-size:28px;margin:8px 0 16px 0;">${total_value:,.0f}</p>

    <p style="{STAT}">
    &bull; records valued: <strong style="{STRONG}">{valued_count}</strong> of {total_count}<br>"""

        if top_gem:
            value_section += f"""    &bull; most valuable: <strong style="{STRONG}">{top_gem.get('artist', '')} — {top_gem.get('title', '')}</strong> (${top_gem.get('median_value', 0):,.0f})<br>"""

        unvalued = total_count - valued_count
        if unvalued > 0:
            value_section += f"""    &bull; <span style="{AMBER}">{unvalued} record{'s' if unvalued != 1 else ''} pending valuation</span>"""

        value_section += f"""
    </p>

    <p style="{STAT}">Connect your Discogs to recover more value automatically.</p>
"""
        body += value_section

    body += f"""
    {DIVIDER}

    <h2 style="{SEC_HEAD}">the hive is buzzing</h2>

    <p style="{STAT}">Here's what collectors across the Hive were talking about this week:</p>

    <p style="{STAT}">
    <span style="{AMBER}font-weight:700;">most spun record</span><br>
    {most_spun}
    </p>

    <p style="{STAT}">
    <span style="{AMBER}font-weight:700;">rising variant</span><br>
    {rising}
    </p>

    <p style="{STAT}">
    <span style="{AMBER}font-weight:700;">most wanted vinyl</span><br>
    {most_wanted}
    </p>

    {DIVIDER}

    <h2 style="{SEC_HEAD}">collectors you might like</h2>

    <p style="{STAT}">You share taste with these collectors:</p>

    {collector_html}

    {DIVIDER}

    <h2 style="{SEC_HEAD}">getting started in the hive</h2>

    <p style="{STAT}"><strong style="{STRONG}">Add your collection first</strong><br>
    Connect your Discogs under Collection to import everything automatically.</p>

    <p style="{STAT}"><strong style="{STRONG}">Drop a Now Spinning</strong><br>
    Tap the composer in the Hive and log what's on your turntable. It's the heartbeat of this place.</p>

    <p style="{STAT}"><strong style="{STRONG}">Build your Dream List</strong><br>
    Add your ISO list. We'll notify you the moment a match surfaces.</p>

    <p style="{STAT}"><strong style="{STRONG}">Buzz in on the daily prompt</strong><br>
    Answer the prompt, see what others are spinning, and find your people.</p>

    {DIVIDER}

    <h2 style="{SEC_HEAD}">a note on trades</h2>

    <p style="{STAT}">Trading here is taken seriously.</p>

    <p style="{STAT}">Every trade requires a <strong style="{STRONG}">Mutual Hold</strong> — both collectors place a hold equal to the value of the exchange. This hold is fully reversed within 24 hours of confirmed delivery.</p>

    <p style="{STAT}">No one walks away ahead by scamming.</p>

    <p style="{STAT}">Trade with confidence.</p>

    {DIVIDER}

    <h2 style="{SEC_HEAD}">this week on new music friday</h2>

    <p style="{STAT}"><strong style="{STRONG}">Harry Styles</strong> dropped <em>Kiss All the Time, Disco Occasionally</em> and the internet definitely has feelings.</p>

    <p style="{STAT}">I've been playing it on repeat — lush, cinematic, and made for vinyl.</p>

    <p style="{STAT}">Are you on it or not?</p>

    <p style="{STAT}">Buzz in on the daily prompt and let us know.</p>

    {DIVIDER}

    <h2 style="{SEC_HEAD}">help us build the honey</h2>

    <p style="{STAT}">Since we're in beta, things might get sticky.</p>

    <p style="{STAT}">We just added a <strong style="{STRONG}">Bug Alert</strong> icon to the top navigation. If something breaks, or if you just have feedback (good or bad), tap that button and tell us.</p>

    <p style="{STAT}">I read everything.</p>

    {DIVIDER}

    <p style="{GREETING}">Welcome to the groove.</p>

    <p style="{MUTED}">— Katie<br>Founder, The Honey Groove</p>
    """

    unsub_url = f"{FRONTEND}/settings"
    return wrap_email(body, unsub_url)


# ─────────────────── Send Pipeline ───────────────────

async def send_weekly_wax():
    """Main send pipeline: query eligible users, build data, send in batches."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Window: last 7 days
    week_start = (now - timedelta(days=7)).isoformat()
    week_end = now_iso

    # Precompute community stats once
    logger.info("Weekly Wax: precomputing community stats...")
    community = await _get_community_stats(week_start, week_end)
    logger.info(f"Weekly Wax: community stats ready — most_spun={community.get('most_spun_record', 'none')}")

    # Query eligible users
    send_window_start = (now - timedelta(days=6)).isoformat()
    eligible_filter = {
        "email": {"$exists": True, "$ne": None},
        "$or": [
            {"sent_weekly_wax_at": None},
            {"sent_weekly_wax_at": {"$exists": False}},
            {"sent_weekly_wax_at": {"$lt": send_window_start}},
        ],
    }
    users = await db.users.find(
        eligible_filter,
        {"_id": 0, "id": 1, "username": 1, "email": 1, "first_name": 1, "display_name": 1}
    ).to_list(10000)

    logger.info(f"Weekly Wax: {len(users)} eligible users found")

    sent_count = 0
    fail_count = 0

    for i in range(0, len(users), BATCH_SIZE):
        batch = users[i:i + BATCH_SIZE]
        for u in batch:
            try:
                # Build personalized data
                user_stats = await _get_user_weekly_stats(u["id"], week_start, week_end)
                collectors = await _get_collector_recommendations(u["id"])

                # Determine first name
                first_name = (
                    u.get("first_name")
                    or u.get("display_name")
                    or u.get("username", "collector")
                )

                data = {
                    "first_name": first_name,
                    **user_stats,
                    "most_spun_record": community.get("most_spun_record"),
                    "rising_variant": community.get("rising_variant"),
                    "most_wanted_variant": community.get("most_wanted_variant"),
                    "collectors": collectors,
                }

                # BLOCK 476: Fetch collection value for email
                try:
                    records = await db.records.find(
                        {"user_id": u["id"], "discogs_id": {"$ne": None}},
                        {"_id": 0, "discogs_id": 1},
                    ).to_list(5000)
                    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
                    total_records = await db.records.count_documents({"user_id": u["id"]})
                    if discogs_ids:
                        values = await db.collection_values.find(
                            {"release_id": {"$in": discogs_ids}}, {"_id": 0}
                        ).to_list(5000)
                        val_total = sum(v["median_value"] for v in values if v.get("median_value"))
                        val_count = len([v for v in values if v.get("median_value")])
                        data["collection_value"] = {
                            "total_value": round(val_total, 2),
                            "valued_count": val_count,
                            "total_count": total_records,
                        }
                        # Top gem
                        val_map = {v["release_id"]: v for v in values}
                        best = None
                        best_val = 0
                        for r in records:
                            v = val_map.get(r.get("discogs_id"))
                            if v and v.get("median_value", 0) > best_val:
                                best_val = v["median_value"]
                                rec = await db.records.find_one({"user_id": u["id"], "discogs_id": r["discogs_id"]}, {"_id": 0, "title": 1, "artist": 1})
                                if rec:
                                    best = {"title": rec.get("title", ""), "artist": rec.get("artist", ""), "median_value": best_val}
                        if best:
                            data["top_gem"] = best
                except Exception as e:
                    logger.warning(f"Weekly Wax: collection value fetch failed for {u['id']}: {e}")

                html = _build_weekly_wax_html(data)
                subject = "your first weekly wax is here."

                success = await send_email(u["email"], subject, html)

                if success:
                    await db.users.update_one(
                        {"id": u["id"]},
                        {"$set": {"sent_weekly_wax_at": now_iso}}
                    )
                    sent_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                logger.error(f"Weekly Wax: failed for user {u.get('username', u['id'])}: {e}")
                fail_count += 1

            await asyncio.sleep(0.05)  # Rate limit between sends

        # Brief pause between batches
        if i + BATCH_SIZE < len(users):
            await asyncio.sleep(1)

    logger.info(f"Weekly Wax: complete — {sent_count} sent, {fail_count} failed")


# ─────────────────── Scheduler ───────────────────

async def schedule_weekly_wax():
    """Scheduler loop — sends Weekly Wax every Sunday at 12:00 PM ET."""
    while True:
        now_utc = datetime.now(timezone.utc)
        now_et = now_utc.astimezone(ET)
        # Find next Sunday at 12:00 PM ET
        days_until_sunday = (6 - now_et.weekday()) % 7
        next_sunday_noon = now_et.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=days_until_sunday)
        if next_sunday_noon <= now_et:
            next_sunday_noon += timedelta(days=7)
        wait_seconds = (next_sunday_noon - now_et).total_seconds()

        logger.info(f"Weekly Wax scheduler: next run in {wait_seconds/3600:.1f}h at {next_sunday_noon.strftime('%Y-%m-%d %I:%M %p %Z')}")
        await asyncio.sleep(wait_seconds)
        await send_weekly_wax()
        await asyncio.sleep(60)  # prevent double-run


# ─────────────────── Admin / Test Endpoints ───────────────────

@router.post("/admin/weekly-wax/send-test")
async def send_test_weekly_wax(user: Dict = Depends(require_auth)):
    """Admin endpoint to send a test Weekly Wax to the requesting user."""
    if not user.get("is_admin"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin only")

    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).isoformat()
    week_end = now.isoformat()

    community = await _get_community_stats(week_start, week_end)
    user_stats = await _get_user_weekly_stats(user["id"], week_start, week_end)
    collectors = await _get_collector_recommendations(user["id"])

    first_name = user.get("first_name") or user.get("display_name") or user.get("username", "collector")

    data = {
        "first_name": first_name,
        **user_stats,
        "most_spun_record": community.get("most_spun_record"),
        "rising_variant": community.get("rising_variant"),
        "most_wanted_variant": community.get("most_wanted_variant"),
        "collectors": collectors,
    }

    # BLOCK 476: Include collection value in test email
    records = await db.records.find(
        {"user_id": user["id"], "discogs_id": {"$ne": None}},
        {"_id": 0, "discogs_id": 1},
    ).to_list(5000)
    discogs_ids = list({r["discogs_id"] for r in records if r.get("discogs_id")})
    total_records = await db.records.count_documents({"user_id": user["id"]})
    if discogs_ids:
        values = await db.collection_values.find(
            {"release_id": {"$in": discogs_ids}}, {"_id": 0}
        ).to_list(5000)
        val_total = sum(v["median_value"] for v in values if v.get("median_value"))
        val_count = len([v for v in values if v.get("median_value")])
        data["collection_value"] = {
            "total_value": round(val_total, 2),
            "valued_count": val_count,
            "total_count": total_records,
        }

    html = _build_weekly_wax_html(data)
    success = await send_email(user["email"], "your first weekly wax is here.", html)

    return {"sent": success, "to": user["email"], "data": data}


@router.get("/admin/weekly-wax/preview")
async def preview_weekly_wax(user: Dict = Depends(require_auth)):
    """Admin endpoint to preview Weekly Wax data without sending."""
    if not user.get("is_admin"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin only")

    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).isoformat()
    week_end = now.isoformat()

    community = await _get_community_stats(week_start, week_end)
    user_stats = await _get_user_weekly_stats(user["id"], week_start, week_end)
    collectors = await _get_collector_recommendations(user["id"])

    first_name = user.get("first_name") or user.get("display_name") or user.get("username", "collector")

    return {
        "first_name": first_name,
        **user_stats,
        "community": community,
        "collectors": collectors,
        "eligible_users": await db.users.count_documents({
            "email": {"$exists": True, "$ne": None},
        }),
    }
