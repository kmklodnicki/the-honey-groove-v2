"""Wax Report — Weekly vinyl summary generated every Sunday midnight UTC."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter
import asyncio
import io
import uuid
import random
import textwrap
import math

from database import db, require_auth, logger, create_notification

router = APIRouter()
FONTS_DIR = Path(__file__).parent.parent / "fonts"

# ─────────────────── Personality Labels ───────────────────
PERSONALITY_LABELS = {
    "crate_digger": [
        "You're a true crate digger — always hunting, never settling.",
        "Deep cuts only. You don't follow trends, you start them.",
        "Your collection tells a story most people can't read yet.",
    ],
    "mood_curator": [
        "You spin with intention — every record matches the moment.",
        "Your turntable is a mood ring. This week proved it.",
        "Vibes over volume. You curate feelings, not just records.",
    ],
    "night_owl": [
        "The best records hit different after midnight.",
        "Late night sessions are your love language.",
        "While the world sleeps, your turntable keeps spinning.",
    ],
    "golden_hour": [
        "You live for that golden hour glow on vinyl.",
        "Sunset and side B — your favorite combination.",
        "Warm tones, warm light, warm wax.",
    ],
    "vinyl_hoarder": [
        "Your shelves are full but your wantlist is fuller.",
        "You don't have a problem, you have a collection.",
        "More records than days in the year — and proud of it.",
    ],
    "genre_explorer": [
        "One week it's jazz, the next it's punk. You can't be boxed in.",
        "Your collection is a world tour in wax.",
        "Genre loyalty? Never heard of it.",
    ],
    "nostalgia_seeker": [
        "You keep going back to the decades that shaped you.",
        "Old records, new memories. That's your thing.",
        "If it's from the era that raised you, it's on your shelf.",
    ],
    "social_spinner": [
        "You don't just spin records — you share the experience.",
        "Your feed is a playlist the whole hive follows.",
        "Spinning is better when the hive is watching.",
    ],
    "value_hunter": [
        "Your collection isn't just art — it's an investment.",
        "You know the market price of every record you own.",
        "Hidden gems are your specialty.",
    ],
    "completionist": [
        "One record from an artist? You need the whole discography.",
        "Gaps in a discography keep you up at night.",
        "Your top artists list doesn't change — it deepens.",
    ],
}


def _assign_personality(stats: dict) -> dict:
    """Assign a personality label based on weekly activity."""
    scores = Counter()

    # Genre-based
    top_genres = stats.get("top_genres", [])
    if len(top_genres) >= 4:
        scores["genre_explorer"] += 3
    elif len(top_genres) <= 2 and top_genres:
        scores["completionist"] += 2

    # Time of day
    active_time = stats.get("most_active_time", "")
    if "night" in active_time.lower() or "12am" in active_time.lower() or "1am" in active_time.lower():
        scores["night_owl"] += 3
    elif "evening" in active_time.lower() or "5pm" in active_time.lower() or "6pm" in active_time.lower():
        scores["golden_hour"] += 3

    # Mood
    top_moods = stats.get("mood_breakdown", [])
    if top_moods:
        scores["mood_curator"] += 2
        top_mood = top_moods[0].get("mood", "").lower() if top_moods else ""
        if "late night" in top_mood or "melancholy" in top_mood:
            scores["night_owl"] += 1
        if "golden hour" in top_mood or "sunday morning" in top_mood:
            scores["golden_hour"] += 1

    # Era
    era_breakdown = stats.get("era_breakdown", [])
    for era in era_breakdown:
        if era.get("pct", 0) > 40:
            decade = era.get("decade", "")
            if decade in ["1960s", "1970s", "1980s"]:
                scores["nostalgia_seeker"] += 3
            break

    # Collection size + value
    total_records = stats.get("collection_value", {}).get("total_count", 0)
    if total_records > 100:
        scores["vinyl_hoarder"] += 2
    if stats.get("collection_value", {}).get("total_value", 0) > 5000:
        scores["value_hunter"] += 2

    # Social
    social = stats.get("social_stats", {})
    if social.get("total_posts", 0) > 5:
        scores["social_spinner"] += 2

    # Spins
    if stats.get("total_spins", 0) > 20:
        scores["crate_digger"] += 2

    if not scores:
        scores["crate_digger"] = 1

    label_key = scores.most_common(1)[0][0]
    label_text = _generate_personality_label_v2(stats)
    return {"key": label_key, "label": label_text}


def _generate_personality_label_v2(stats: dict) -> str:
    """Generate a specific, personal personality label from real user data."""
    top_artist = stats.get("top_artists", [{}])[0].get("artist", "") if stats.get("top_artists") else ""
    era_breakdown = stats.get("era_breakdown", [])
    dominant_era = era_breakdown[0].get("decade", "") if era_breakdown else ""
    top_mood = stats.get("mood_breakdown", [{}])[0].get("mood", "").lower() if stats.get("mood_breakdown") else ""
    active_time = stats.get("most_active_time", "").lower()
    unique_artists_count = len(set(a.get("artist", "") for a in stats.get("top_artists", [])))
    total_spins = stats.get("total_spins", 0)
    top_genres = stats.get("top_genres", [])
    top_genre = top_genres[0].get("genre", "").lower() if top_genres else ""

    templates = []

    # Templates that use real data combinations
    if top_artist and dominant_era:
        templates.append(f"a {dominant_era} devotee with a soft spot for {top_artist}")
        if active_time in ("late night",):
            templates.append(f"a {dominant_era} maximalist with a soft spot for {top_artist} and late night listening")
        if active_time in ("morning",):
            templates.append(f"early mornings, {top_artist}, and the sound of the {dominant_era}")
        if active_time in ("evening",):
            templates.append(f"golden hour, {top_artist}, and a deep love for the {dominant_era}")

    if top_artist and top_mood:
        templates.append(f"{top_mood} nights and {top_artist} on repeat")
        templates.append(f"the kind of week where {top_artist} and {top_mood} vibes say it all")

    if top_artist and top_genre:
        templates.append(f"a {top_genre} heart beating to the rhythm of {top_artist}")

    if dominant_era and top_mood:
        templates.append(f"{dominant_era} records and {top_mood} energy all week long")

    if total_spins > 15 and top_artist:
        templates.append(f"{total_spins} spins deep and still reaching for {top_artist}")

    if unique_artists_count >= 4:
        templates.append(f"a genre-hopper who always comes back to {top_artist}" if top_artist else "a genre-hopper with impeccable taste")

    if not templates:
        if top_artist:
            templates.append(f"this week belonged to {top_artist} and the turntable")
        else:
            templates.append("another week lost in the grooves")

    return random.choice(templates)


def _generate_closing_line(stats: dict) -> str:
    """Generate a poetic, personal, artist-specific closing line."""
    import random

    top_artist = stats.get("top_artists", [{}])[0].get("artist", "") if stats.get("top_artists") else ""
    top_record = stats.get("top_records", [{}])[0] if stats.get("top_records") else {}
    top_record_title = top_record.get("title", "")
    era_breakdown = stats.get("era_breakdown", [])
    dominant_era = era_breakdown[0].get("decade", "") if era_breakdown else ""
    top_mood = stats.get("mood_breakdown", [{}])[0].get("mood", "").lower() if stats.get("mood_breakdown") else ""
    top_genres = stats.get("top_genres", [])
    top_genre = top_genres[0].get("genre", "").lower() if top_genres else ""

    # ── Opening phrases (rotate randomly) ──
    openers = [
        "this week's vibe was",
        "something about this week called for",
        "this was a week defined by",
        "the needle kept finding its way back to",
        "this week belonged to",
        "a week that only made sense with",
        "everything this week pointed back to",
    ]

    # ── Mood-specific openers ──
    mood_openers = {
        "chill": "pure chill energy, courtesy of",
        "nostalgic": "pure nostalgia, courtesy of",
        "energized": "pure adrenaline, courtesy of",
        "melancholy": "pure ache, courtesy of",
        "euphoric": "pure dopamine, courtesy of",
        "focused": "pure focus energy, courtesy of",
        "rebellious": "pure rebellion, courtesy of",
        "romantic": "pure heartbreak, courtesy of",
        "peaceful": "pure stillness, courtesy of",
        "dark": "pure shadow energy, courtesy of",
        "uplifting": "pure sunlight, courtesy of",
        "groovy": "pure groove, courtesy of",
    }

    # ── Genre-based artist descriptors ──
    genre_descriptors = {
        "pop": [
            "the pink-pony energy of",
            "the sugary maximalism of",
            "the glossy heartbreak of",
        ],
        "indie": [
            "the quiet devastation of",
            "the bedroom melancholy of",
            "the soft chaos of",
        ],
        "rock": [
            "the raw voltage of",
            "the chest-open fury of",
            "the amp-worship of",
        ],
        "folk": [
            "the candlelit warmth of",
            "the front-porch storytelling of",
            "the earthen calm of",
        ],
        "r&b": [
            "the silk and ache of",
            "the slow burn of",
            "the velvet gravity of",
        ],
        "soul": [
            "the silk and ache of",
            "the slow burn of",
            "the deep warmth of",
        ],
        "classical": [
            "the unhurried grace of",
            "the late-night sophistication of",
            "the quiet architecture of",
        ],
        "jazz": [
            "the unhurried grace of",
            "the late-night sophistication of",
            "the smoky elegance of",
        ],
        "hip hop": [
            "the low-end theory of",
            "the concrete poetry of",
            "the bass-heavy gravity of",
        ],
        "electronic": [
            "the neon pulse of",
            "the synthetic dreamscape of",
            "the fluorescent drift of",
        ],
        "punk": [
            "the three-chord gospel of",
            "the safety-pin elegance of",
            "the raw nerve of",
        ],
        "country": [
            "the dusty-road heart of",
            "the steel-and-twang honesty of",
            "the wide-open longing of",
        ],
        "metal": [
            "the chest-open fury of",
            "the seismic weight of",
            "the molten roar of",
        ],
    }

    # Fallback descriptors when genre is unknown
    fallback_descriptors = [
        "the unmistakable pull of",
        "the deep grooves of",
        "the singular magnetism of",
        "the undeniable gravity of",
    ]

    if not top_artist:
        return "another week in the grooves. the needle knows."

    # ── Pick descriptor for artist ──
    descriptor = None
    for genre_key, descs in genre_descriptors.items():
        if genre_key in top_genre:
            descriptor = random.choice(descs)
            break
    if not descriptor:
        descriptor = random.choice(fallback_descriptors)

    # ── Build the closing line ──
    # Decide between mood-specific opener or general opener
    if top_mood and top_mood in mood_openers and random.random() < 0.4:
        opener = mood_openers[top_mood]
        line = f"{opener} {descriptor} {top_artist}."
    else:
        opener = random.choice(openers)
        line = f"{opener} {descriptor} {top_artist}."

    # Optionally append era or evocative record reference
    if dominant_era and random.random() < 0.35:
        line = line.rstrip(".")
        line += f", straight out of the {dominant_era}."
    elif top_record_title and len(top_record_title) < 30 and random.random() < 0.3:
        line = line.rstrip(".")
        line += f" — {top_record_title} on repeat."

    # Add perfect weekly streak mention
    weekly_prompts = stats.get("weekly_prompt_streak", 0)
    if weekly_prompts >= 7:
        line = line.rstrip(".")
        line += " — and a perfect prompt streak to prove it."

    return line


# ─────────────────── Report Generation ───────────────────

async def generate_wax_report(user_id: str, week_start: datetime, week_end: datetime) -> dict:
    """Generate a full Wax Report for a user for the given week."""
    ws = week_start.isoformat()
    we = week_end.isoformat()

    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        return {}

    # ── Listening Stats ──
    spins = await db.spins.find(
        {"user_id": user_id, "created_at": {"$gte": ws, "$lt": we}}, {"_id": 0}
    ).to_list(10000)

    total_spins = len(spins)
    record_ids_spun = [s["record_id"] for s in spins]
    unique_records = len(set(record_ids_spun))
    avg_spins = round(total_spins / unique_records, 1) if unique_records else 0

    # Group by day
    day_counts = Counter()
    hour_counts = Counter()
    for s in spins:
        try:
            dt = datetime.fromisoformat(s["created_at"])
            day_counts[dt.strftime("%A")] += 1
            hour_counts[dt.hour] += 1
        except Exception:
            pass

    most_active_day = day_counts.most_common(1)[0][0] if day_counts else "N/A"
    longest_listening_day = day_counts.most_common(1)[0] if day_counts else ("N/A", 0)

    # Time of day bucket
    peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else 12
    if peak_hour < 6:
        active_time = "Late Night"
    elif peak_hour < 12:
        active_time = "Morning"
    elif peak_hour < 17:
        active_time = "Afternoon"
    elif peak_hour < 21:
        active_time = "Evening"
    else:
        active_time = "Late Night"

    listening_stats = {
        "total_spins": total_spins,
        "unique_records": unique_records,
        "avg_spins_per_record": avg_spins,
        "longest_listening_day": {"day": longest_listening_day[0], "spins": longest_listening_day[1]} if isinstance(longest_listening_day, tuple) else {"day": "N/A", "spins": 0},
        "most_active_day": most_active_day,
        "most_active_time": active_time,
    }

    # ── Top 5 Artists, Records, Genres ──
    records_map = {}
    if record_ids_spun:
        recs = await db.records.find({"id": {"$in": list(set(record_ids_spun))}}, {"_id": 0}).to_list(5000)
        records_map = {r["id"]: r for r in recs}

    artist_counts = Counter()
    record_counts = Counter()
    genre_counts = Counter()
    era_counts = Counter()
    for rid in record_ids_spun:
        rec = records_map.get(rid, {})
        artist = rec.get("artist", "Unknown")
        title = rec.get("title", "Unknown")
        artist_counts[artist] += 1
        record_counts[(title, artist, rec.get("cover_url", ""))] += 1
        for g in (rec.get("genre") or []):
            genre_counts[g] += 1
        year = rec.get("year")
        if year:
            try:
                decade = f"{(int(year) // 10) * 10}s"
                era_counts[decade] += 1
            except (ValueError, TypeError):
                pass

    top_artists = [{"artist": a, "spins": c} for a, c in artist_counts.most_common(5)]
    top_records = [{"title": t, "artist": a, "cover_url": cu, "spins": c} for (t, a, cu), c in record_counts.most_common(5)]
    top_genres = [{"genre": g, "spins": c} for g, c in genre_counts.most_common(5)]
    unique_artists_count = len(artist_counts)

    # Era breakdown
    total_era = sum(era_counts.values()) or 1
    era_breakdown = sorted(
        [{"decade": d, "spins": c, "pct": round(c / total_era * 100)} for d, c in era_counts.items()],
        key=lambda x: x["pct"], reverse=True
    )

    # ── Mood Breakdown ──
    mood_posts = await db.posts.find(
        {"user_id": user_id, "post_type": "vinyl_mood", "created_at": {"$gte": ws, "$lt": we}},
        {"_id": 0}
    ).to_list(1000)
    mood_counts = Counter()
    for p in mood_posts:
        mood = p.get("mood") or p.get("content", "")
        if mood:
            mood_counts[mood] += 1
    mood_breakdown = [{"mood": m, "count": c} for m, c in mood_counts.most_common()]

    # ── Collection Value ──
    all_records = await db.records.find(
        {"user_id": user_id, "discogs_id": {"$ne": None}}, {"_id": 0, "discogs_id": 1, "id": 1}
    ).to_list(5000)
    discogs_ids = list({r["discogs_id"] for r in all_records if r.get("discogs_id")})
    values = await db.collection_values.find(
        {"release_id": {"$in": discogs_ids}}, {"_id": 0}
    ).to_list(5000) if discogs_ids else []
    val_map = {v["release_id"]: v for v in values}

    total_value = 0.0
    over_50 = over_100 = over_200 = 0
    most_valuable = None
    mv_val = 0
    hidden_gem = None

    all_recs_full = await db.records.find({"user_id": user_id}, {"_id": 0}).to_list(5000)
    valued_records = []
    for r in all_recs_full:
        v = val_map.get(r.get("discogs_id"))
        if v and v.get("median_value"):
            mv = v["median_value"]
            total_value += mv
            if mv > 50: over_50 += 1
            if mv > 100: over_100 += 1
            if mv > 200: over_200 += 1
            valued_records.append({"title": r.get("title"), "artist": r.get("artist"), "cover_url": r.get("cover_url"), "value": mv})
            if mv > mv_val:
                mv_val = mv
                most_valuable = {"title": r.get("title"), "artist": r.get("artist"), "cover_url": r.get("cover_url"), "value": mv}

    # Hidden gem = mid-range value record not in top 3
    valued_records.sort(key=lambda x: x["value"], reverse=True)
    if len(valued_records) > 5:
        mid = valued_records[len(valued_records) // 2]
        hidden_gem = {"title": mid["title"], "artist": mid["artist"], "value": mid["value"]}

    # Previous week value
    prev_start = week_start - timedelta(days=7)
    prev_report = await db.wax_reports.find_one(
        {"user_id": user_id, "week_start": prev_start.isoformat()}, {"_id": 0, "collection_value.total_value": 1}
    )
    prev_value = prev_report.get("collection_value", {}).get("total_value", 0) if prev_report else 0
    value_change = round(total_value - prev_value, 2) if prev_value else 0

    collection_value = {
        "total_value": round(total_value, 2),
        "value_change": value_change,
        "most_valuable": most_valuable,
        "over_50": over_50, "over_100": over_100, "over_200": over_200,
        "hidden_gem": hidden_gem,
        "total_count": len(all_recs_full),
    }

    # ── Wantlist Pulse ──
    iso_items = await db.iso_items.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    total_wantlist = len(iso_items)
    found_this_week = sum(1 for i in iso_items if i.get("status") == "FOUND" and i.get("found_at", i.get("created_at", "")) >= ws)
    longest_hunt = 0
    for i in iso_items:
        if i.get("status") == "OPEN" and i.get("created_at"):
            try:
                created = datetime.fromisoformat(i["created_at"])
                days = (week_end - created).days
                longest_hunt = max(longest_hunt, days)
            except Exception:
                pass

    # Trending wantlist = most-wanted across all users this week
    trending_iso = None
    pipeline = [
        {"$match": {"status": "OPEN"}},
        {"$group": {"_id": {"artist": "$artist", "album": "$album"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    trending = await db.iso_items.aggregate(pipeline).to_list(1)
    if trending:
        t = trending[0]
        trending_iso = {"artist": t["_id"]["artist"], "album": t["_id"]["album"], "want_count": t["count"]}

    wantlist_pulse = {
        "total": total_wantlist,
        "matches_found": found_this_week,
        "longest_hunt_days": longest_hunt,
        "trending": trending_iso,
    }

    # ── Social Stats ──
    all_posts_week = await db.posts.find(
        {"user_id": user_id, "created_at": {"$gte": ws, "$lt": we}}, {"_id": 0}
    ).to_list(1000)
    post_type_counts = Counter(p.get("post_type", "other") for p in all_posts_week)

    new_followers = await db.followers.count_documents(
        {"following_id": user_id, "created_at": {"$gte": ws, "$lt": we}}
    )
    trades_completed = await db.trades.count_documents(
        {"$or": [{"proposer_id": user_id}, {"receiver_id": user_id}],
         "status": "COMPLETED", "updated_at": {"$gte": ws, "$lt": we}}
    )

    # Most liked post
    most_liked = None
    if all_posts_week:
        post_ids = [p["id"] for p in all_posts_week]
        like_pipeline = [
            {"$match": {"post_id": {"$in": post_ids}}},
            {"$group": {"_id": "$post_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        top_liked = await db.likes.aggregate(like_pipeline).to_list(1)
        if top_liked:
            liked_post = next((p for p in all_posts_week if p["id"] == top_liked[0]["_id"]), None)
            if liked_post:
                most_liked = {
                    "id": liked_post["id"],
                    "post_type": liked_post.get("post_type"),
                    "content": (liked_post.get("content") or "")[:80],
                    "likes": top_liked[0]["count"],
                }

    social_stats = {
        "new_followers": new_followers,
        "total_posts": len(all_posts_week),
        "post_types": dict(post_type_counts),
        "trades_completed": trades_completed,
        "most_liked_post": most_liked,
    }

    # ── Build Report ──
    report_data = {
        "total_spins": total_spins,
        "listening_stats": listening_stats,
        "top_artists": top_artists,
        "top_records": top_records,
        "top_genres": top_genres,
        "unique_artists_count": unique_artists_count,
        "era_breakdown": era_breakdown,
        "mood_breakdown": mood_breakdown,
        "collection_value": collection_value,
        "wantlist_pulse": wantlist_pulse,
        "social_stats": social_stats,
        "most_active_time": active_time,
    }

    # Personality
    personality = _assign_personality(report_data)
    report_data["personality"] = personality

    # Check for perfect weekly prompt streak (7/7 days)
    prompt_responses_this_week = await db.prompt_responses.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": week_start.isoformat(), "$lt": week_end.isoformat()},
    })
    report_data["weekly_prompt_streak"] = prompt_responses_this_week

    # Closing line
    closing = _generate_closing_line(report_data)
    report_data["closing_line"] = closing

    # ── Store report ──
    report_id = str(uuid.uuid4())
    doc = {
        "id": report_id,
        "user_id": user_id,
        "username": user.get("username", ""),
        "avatar_url": user.get("avatar_url"),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "label_regenerated": False,
        **report_data,
    }
    await db.wax_reports.update_one(
        {"user_id": user_id, "week_start": week_start.isoformat()},
        {"$set": doc}, upsert=True
    )
    return doc


# ─────────────────── API Endpoints ───────────────────

@router.get("/wax-reports/latest")
async def get_latest_wax_report(user: Dict = Depends(require_auth)):
    """Get the most recent Wax Report for the authenticated user."""
    report = await db.wax_reports.find_one(
        {"user_id": user["id"]}, {"_id": 0}, sort=[("week_end", -1)]
    )
    if not report:
        raise HTTPException(status_code=404, detail="No reports yet")
    return report


@router.get("/wax-reports/latest/{username}")
async def get_latest_wax_report_public(username: str):
    """Get the most recent Wax Report for any user (public)."""
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    report = await db.wax_reports.find_one(
        {"user_id": target["id"]}, {"_id": 0}, sort=[("week_end", -1)]
    )
    if not report:
        raise HTTPException(status_code=404, detail="No reports yet")
    return report


@router.get("/wax-reports/history")
async def get_wax_report_history(user: Dict = Depends(require_auth), limit: int = 52):
    """Get all past Wax Reports for the authenticated user."""
    reports = await db.wax_reports.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("week_end", -1).limit(limit).to_list(limit)
    return reports


@router.get("/wax-reports/{report_id}")
async def get_wax_report(report_id: str, user: Dict = Depends(require_auth)):
    """Get a specific Wax Report."""
    report = await db.wax_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/wax-reports/regenerate-label/{report_id}")
async def regenerate_label(report_id: str, user: Dict = Depends(require_auth)):
    """Regenerate the personality label (once per week)."""
    report = await db.wax_reports.find_one({"id": report_id, "user_id": user["id"]}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.get("label_regenerated"):
        raise HTTPException(status_code=400, detail="Already regenerated this week")

    new_personality = _assign_personality(report)
    closing = _generate_closing_line({**report, "personality": new_personality})

    await db.wax_reports.update_one(
        {"id": report_id},
        {"$set": {"personality": new_personality, "closing_line": closing, "label_regenerated": True}}
    )
    return {"personality": new_personality, "closing_line": closing}


@router.post("/wax-reports/generate")
async def trigger_generate(user: Dict = Depends(require_auth)):
    """Manually trigger generation of the current week's report."""
    now = datetime.now(timezone.utc)
    # Current week: Monday to Sunday
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    report = await generate_wax_report(user["id"], week_start, week_end)
    return report


# ─────────────────── Share Card (1080x1080) ───────────────────

def _download_cover(url: str, size: int = 300):
    """Download a cover image and resize it."""
    from PIL import Image
    try:
        import requests as http_req
        resp = http_req.get(url, timeout=8, headers={"User-Agent": "HoneyGrooveApp/1.0"})
        if resp.status_code == 200 and len(resp.content) > 100:
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            img = img.resize((size, size), Image.LANCZOS)
            return img
    except Exception:
        pass
    return None


def _round_corners(img, radius: int):
    from PIL import Image, ImageDraw
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    result = img.copy()
    result.putalpha(mask)
    return result


def _generate_share_card(report: dict) -> bytes:
    """Generate a redesigned 1080x1920 Instagram Story share card PNG."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1080, 1920
    BG = (250, 246, 238)         # #FAF6EE warm cream
    CARD_WHITE = (255, 255, 255)
    TEXT_DARK = (42, 26, 6)      # #2A1A06
    TEXT_MUTED = (138, 107, 74)  # #8A6B4A
    AMBER = (153, 96, 18)       # #996012
    AMBER_ACCENT = (200, 134, 26)  # #C8861A

    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Subtle radial glows
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r in range(700, 0, -2):
        alpha = max(0, int(15 * (1 - r / 700)))
        glow_draw.ellipse([(W - 200 - r, -100 - r), (W - 200 + r, -100 + r)], fill=(200, 134, 26, alpha))
    for r in range(500, 0, -2):
        alpha = max(0, int(10 * (1 - r / 500)))
        glow_draw.ellipse([(-100 - r, H - 200 - r), (-100 + r, H - 200 + r)], fill=(200, 134, 26, alpha))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        playfair_bold_72 = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 72)
        playfair_bold_56 = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 56)
        playfair_bold_48 = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 48)
        playfair_bold_42 = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 42)
        playfair_bold_38 = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 38)
        playfair_italic_28 = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Italic2.ttf"), 28)
        cormorant_italic_52 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 52)
        cormorant_italic_46 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 46)
        cormorant_italic_40 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 40)
        cormorant_italic_32 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 32)
        cormorant_italic_26 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 26)
        cormorant_italic_24 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 24)
        cormorant_reg_36 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Regular2.ttf"), 36)
        cormorant_reg_28 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Regular2.ttf"), 28)
        cormorant_reg_26 = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Regular2.ttf"), 26)
        stat_num_font = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 64)
        eyebrow_font = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Regular2.ttf"), 26)
        footer_font = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 26)
    except Exception:
        f = ImageFont.load_default()
        playfair_bold_72 = playfair_bold_56 = playfair_bold_48 = f
        playfair_bold_42 = playfair_bold_38 = playfair_italic_28 = f
        cormorant_italic_52 = cormorant_italic_46 = cormorant_italic_40 = f
        cormorant_italic_32 = cormorant_italic_26 = cormorant_italic_24 = f
        cormorant_reg_36 = cormorant_reg_28 = cormorant_reg_26 = f
        stat_num_font = eyebrow_font = footer_font = f

    pad = 60

    def draw_divider(y_pos):
        overlay = Image.new("RGBA", (W - 2 * pad, 4), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        mid = (W - 2 * pad) // 2
        for x in range(W - 2 * pad):
            alpha = int(45 * (1 - abs(x - mid) / mid))
            od.point((x, 1), fill=(200, 134, 26, max(0, alpha)))
        img.paste(overlay, (pad, y_pos), overlay)
        return y_pos + 8

    def text_width(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def text_height(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    # ════════════════════════════════════════════════════════
    # HEADER — 130px
    # ════════════════════════════════════════════════════════
    y = 50
    draw.text((pad, y), "the Honey Groove", fill=AMBER_ACCENT, font=playfair_italic_28)
    username = report.get("username", "collector")
    draw.text((pad, y + 34), f"@{username}", fill=TEXT_MUTED, font=cormorant_reg_26)
    ws = report.get("week_start", "")
    we = report.get("week_end", "")
    try:
        ws_dt = datetime.fromisoformat(ws)
        we_dt = datetime.fromisoformat(we) - timedelta(days=1)
        date_range = f"{ws_dt.strftime('%b %d')} — {we_dt.strftime('%b %d, %Y')}"
    except Exception:
        date_range = ""
    draw.text((W - pad - text_width(date_range, cormorant_reg_26), y + 6), date_range, fill=TEXT_MUTED, font=cormorant_reg_26)
    y = 130
    y = draw_divider(y)

    # ════════════════════════════════════════════════════════
    # PERSONALITY LABEL — ~150px (no quotes!)
    # ════════════════════════════════════════════════════════
    personality = report.get("personality", {})
    label = personality.get("label", "")
    if label:
        # Strip any existing quote marks
        label = label.strip('"\'')
        y += 40
        lines = textwrap.wrap(label, width=30)
        for line in lines[:3]:
            tw = text_width(line, cormorant_italic_46)
            draw.text(((W - tw) / 2, y), line, fill=AMBER_ACCENT, font=cormorant_italic_46)
            y += 54
        y += 36
    else:
        y += 20
    y = draw_divider(y)

    # ════════════════════════════════════════════════════════
    # TOP ARTISTS — ~420px with visual hierarchy
    # ════════════════════════════════════════════════════════
    y += 12
    draw.text((pad, y), "TOP ARTISTS", fill=TEXT_MUTED, font=eyebrow_font)
    y += 36
    top_artists = report.get("top_artists", [])[:5]
    max_spins = max((a.get("spins", 0) for a in top_artists), default=1)

    # Font sizes: rank 1=72, 2=56, 3=48, 4=42, 5=38
    artist_fonts = [playfair_bold_72, playfair_bold_56, playfair_bold_48, playfair_bold_42, playfair_bold_38]
    # Spin count fonts (italic)
    spin_fonts = [cormorant_italic_32, cormorant_italic_32, cormorant_italic_26, cormorant_italic_26, cormorant_italic_24]
    # Row heights scale with font
    row_heights = [86, 72, 64, 56, 52]

    for i, a in enumerate(top_artists):
        font_idx = min(i, 4)
        name_font = artist_fonts[font_idx]
        spin_font = spin_fonts[font_idx]
        row_h = row_heights[font_idx]

        # Proportional amber bar behind — 35% opacity for rank 1, scaling down
        bar_opacity = max(10, int(35 - i * 5))
        spins = a.get("spins", 0)
        bar_ratio = spins / max(max_spins, 1)
        bar_w = int(bar_ratio * (W - 2 * pad))
        bar_w = max(bar_w, 120)

        # Draw bar background
        bar_overlay = Image.new("RGBA", (bar_w, row_h), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar_overlay)
        bar_draw.rounded_rectangle([(0, 0), (bar_w, row_h)], radius=10,
                                    fill=(200, 134, 26, bar_opacity))
        img.paste(bar_overlay, (pad, y), bar_overlay)
        draw = ImageDraw.Draw(img)  # refresh draw after paste

        # Artist name — dark text, left aligned with padding
        artist_name = a.get("artist", "")[:24]
        name_y = y + (row_h - text_height(artist_name, name_font)) // 2 - 4
        draw.text((pad + 16, name_y), artist_name, fill=TEXT_DARK, font=name_font)

        # Spin count — right-aligned, amber italic
        spins_text = str(spins)
        spin_tw = text_width(spins_text, spin_font)
        spin_y = y + (row_h - text_height(spins_text, spin_font)) // 2 - 2
        draw.text((W - pad - spin_tw, spin_y), spins_text, fill=AMBER_ACCENT, font=spin_font)

        y += row_h + 4

    y += 10
    y = draw_divider(y)

    # ════════════════════════════════════════════════════════
    # STATS ROW — 3 tiles: spins, unique records, unique artists
    # ════════════════════════════════════════════════════════
    y += 12
    draw.text((pad, y), "THIS WEEK", fill=TEXT_MUTED, font=eyebrow_font)
    y += 34
    tile_w = (W - 2 * pad - 20) // 3
    tile_h = 130

    # Determine 3rd stat: unique artists (always has data if any spins)
    unique_artists_val = report.get("unique_artists_count", 0)
    # Fallback: count distinct artists from top_artists list
    if not unique_artists_val and top_artists:
        unique_artists_val = len(top_artists)

    stats_data = [
        (str(report.get("total_spins", 0)), "spins"),
        (str(report.get("listening_stats", {}).get("unique_records", 0)), "unique records"),
        (str(unique_artists_val), "unique artists"),
    ]

    for i, (val, lbl) in enumerate(stats_data):
        tx = pad + i * (tile_w + 10)
        # White card with subtle amber border
        draw.rounded_rectangle([(tx, y), (tx + tile_w, y + tile_h)], radius=16,
                                fill=CARD_WHITE, outline=(200, 134, 26, 38))
        # Stat number centered
        val_tw = text_width(val, stat_num_font)
        draw.text((tx + (tile_w - val_tw) // 2, y + 14), val, fill=AMBER, font=stat_num_font)
        # Label centered
        lbl_tw = text_width(lbl, cormorant_italic_24)
        draw.text((tx + (tile_w - lbl_tw) // 2, y + 88), lbl, fill=TEXT_MUTED, font=cormorant_italic_24)

    y += tile_h + 12
    y = draw_divider(y)

    # ════════════════════════════════════════════════════════
    # ERAS — pills, slightly larger
    # ════════════════════════════════════════════════════════
    era = report.get("era_breakdown", [])
    if era:
        y += 10
        draw.text((pad, y), "ERAS", fill=TEXT_MUTED, font=eyebrow_font)
        y += 34
        pill_x = pad
        for e in era[:6]:
            text = f'{e["decade"]} ({e["pct"]}%)'
            pw = text_width(text, cormorant_reg_36) + 32
            ph = 48
            if pill_x + pw > W - pad:
                pill_x = pad
                y += ph + 12
            draw.rounded_rectangle([(pill_x, y), (pill_x + pw, y + ph)], radius=24,
                                    fill=CARD_WHITE, outline=(200, 134, 26, 51))
            draw.text((pill_x + 16, y + 4), text, fill=TEXT_MUTED, font=cormorant_reg_36)
            pill_x += pw + 12
        y += 56
    else:
        y += 6
    y = draw_divider(y)

    # ════════════════════════════════════════════════════════
    # TOP RECORD — most spun this week with album art hero
    # ════════════════════════════════════════════════════════
    top_records = report.get("top_records", [])
    top_record = top_records[0] if top_records else None

    if top_record:
        y += 10
        # Eyebrow label
        eyebrow_text = "MOST SPUN THIS WEEK"
        etw = text_width(eyebrow_text, eyebrow_font)
        draw.text(((W - etw) / 2, y), eyebrow_text, fill=TEXT_MUTED, font=eyebrow_font)
        y += 32

        # Album art — 440px wide centered with shadow effect
        art_size = 440
        art_x = (W - art_size) // 2
        cover_url = top_record.get("cover_url", "")
        cover_img = _download_cover(cover_url, art_size) if cover_url else None

        if cover_img:
            # Drop shadow
            shadow = Image.new("RGBA", (art_size + 40, art_size + 40), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle([(0, 8), (art_size + 40, art_size + 48)],
                                           radius=24, fill=(0, 0, 0, 30))
            img.paste(shadow, (art_x - 20, y - 4), shadow)
            draw = ImageDraw.Draw(img)

            # Round corners on album art
            cover_rounded = _round_corners(cover_img, 20)
            img.paste(cover_rounded, (art_x, y), cover_rounded)
            draw = ImageDraw.Draw(img)
            y += art_size + 16
        else:
            # Placeholder rectangle
            draw.rounded_rectangle([(art_x, y), (art_x + art_size, y + art_size)],
                                    radius=20, fill=(230, 222, 210), outline=(200, 134, 26, 40))
            placeholder = "no cover"
            ptw = text_width(placeholder, cormorant_reg_28)
            draw.text(((W - ptw) / 2, y + art_size // 2 - 14), placeholder, fill=TEXT_MUTED, font=cormorant_reg_28)
            y += art_size + 16

        # Artist name centered
        rec_artist = top_record.get("artist", "")[:40]
        ratw = text_width(rec_artist, playfair_bold_42)
        draw.text(((W - ratw) / 2, y), rec_artist, fill=TEXT_DARK, font=playfair_bold_42)
        y += 46

        # Album name centered
        rec_title = top_record.get("title", "")[:45]
        rttw = text_width(rec_title, cormorant_italic_32)
        draw.text(((W - rttw) / 2, y), rec_title, fill=AMBER_ACCENT, font=cormorant_italic_32)
        y += 38
    else:
        y += 20

    y = draw_divider(y)

    # ════════════════════════════════════════════════════════
    # CLOSING LINE — poetic, data-driven, fits within canvas
    # ════════════════════════════════════════════════════════
    closing = report.get("closing_line", "")
    if closing:
        # Calculate remaining space: footer needs ~80px from bottom
        footer_zone = H - 80
        available = footer_zone - y - 10

        y += 20
        available -= 20

        # Try font sizes from large to small until it fits
        for closing_font_size, closing_font, wrap_w in [
            (52, cormorant_italic_52, 30),
            (46, cormorant_italic_46, 34),
            (40, cormorant_italic_40, 40),
            (32, cormorant_italic_32, 48),
        ]:
            lines = textwrap.wrap(closing, width=wrap_w)
            total_text_h = len(lines) * (closing_font_size + 8)
            if total_text_h <= available:
                break

        for line in lines:
            tw = text_width(line, closing_font)
            draw.text(((W - tw) / 2, y), line, fill=TEXT_DARK, font=closing_font)
            y += closing_font_size + 8

    # ════════════════════════════════════════════════════════
    # FOOTER — pinned to bottom
    # ════════════════════════════════════════════════════════
    fy = H - 60
    draw_divider(fy - 14)

    # Left: thehoneygroove.com
    draw.text((pad, fy), "thehoneygroove.com", fill=TEXT_MUTED, font=footer_font)
    # Center: bee emoji
    bee = "\U0001F41D"
    bee_tw = text_width(bee, footer_font)
    draw.text(((W - bee_tw) / 2, fy), bee, fill=TEXT_DARK, font=footer_font)
    # Right: your week in wax
    yw_text = "your week in wax"
    yw_tw = text_width(yw_text, footer_font)
    draw.text((W - pad - yw_tw, fy), yw_text, fill=TEXT_MUTED, font=footer_font)

    buf = io.BytesIO()
    final = img.convert("RGB")
    final.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@router.get("/wax-reports/{report_id}/share-card")
async def get_share_card(report_id: str, user: Dict = Depends(require_auth)):
    """Generate a 1080x1920 shareable story card PNG."""
    report = await db.wax_reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    png = _generate_share_card(report)
    return Response(content=png, media_type="image/png")


# ─────────────────── Background Job ───────────────────

async def run_weekly_generation():
    """Background task: generate reports for all users."""
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday() + 7)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)

    users = await db.users.find({}, {"_id": 0, "id": 1, "username": 1}).to_list(10000)
    logger.info(f"Wax Report: generating for {len(users)} users, week {week_start.date()} to {week_end.date()}")

    for u in users:
        try:
            existing = await db.wax_reports.find_one(
                {"user_id": u["id"], "week_start": week_start.isoformat()}, {"_id": 0, "id": 1}
            )
            if existing:
                continue
            await generate_wax_report(u["id"], week_start, week_end)
            await create_notification(
                u["id"], "WAX_REPORT", "your week in wax is ready",
                "your week in wax is ready 🍯",
                {"week_start": week_start.isoformat()}
            )
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Wax Report gen failed for {u['id']}: {e}")

    logger.info("Wax Report: weekly generation complete")
    # Also generate mood boards
    try:
        from routes.mood_boards import generate_weekly_mood_boards
        await generate_weekly_mood_boards()
    except Exception as e:
        logger.error(f"Mood board weekly gen failed: {e}")


async def schedule_weekly_reports():
    """Scheduler loop — runs weekly generation every Sunday at midnight UTC."""
    while True:
        now = datetime.now(timezone.utc)
        # Next Sunday midnight
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0 and now.hour >= 0 and now.minute > 5:
            days_until_sunday = 7
        next_sunday = (now + timedelta(days=days_until_sunday)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = (next_sunday - now).total_seconds()
        if wait_seconds < 0:
            wait_seconds = 0

        logger.info(f"Wax Report scheduler: next run in {wait_seconds/3600:.1f}h at {next_sunday}")
        await asyncio.sleep(wait_seconds)
        await run_weekly_generation()
        await asyncio.sleep(60)  # prevent double-run
