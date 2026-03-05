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
    label_text = random.choice(PERSONALITY_LABELS[label_key])
    return {"key": label_key, "label": label_text}


def _generate_closing_line(stats: dict) -> str:
    """Generate a closing sentence from the week's data."""
    parts = []
    top_artist = stats.get("top_artists", [{}])[0].get("artist", "") if stats.get("top_artists") else ""
    top_record = stats.get("top_records", [{}])[0].get("title", "") if stats.get("top_records") else ""
    top_mood = stats.get("mood_breakdown", [{}])[0].get("mood", "") if stats.get("mood_breakdown") else ""
    total_spins = stats.get("total_spins", 0)
    personality = stats.get("personality", {}).get("label", "")

    if top_artist and top_record:
        parts.append(f"This week was all about {top_artist}")
    elif top_artist:
        parts.append(f"{top_artist} dominated your turntable this week")

    if total_spins > 0:
        parts.append(f"with {total_spins} spins across the week")

    if top_mood:
        parts.append(f"in a {top_mood.lower()} kind of mood")

    if not parts:
        return "Another week of great vinyl. Keep spinning."

    line = ", ".join(parts) + "."
    return line[0].upper() + line[1:]


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
    """Generate a 1080x1080 condensed share card PNG."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1080, 1080
    # Brand colors from spec
    BG = (250, 237, 199)         # #FAEDC7
    CARD = (255, 255, 255)       # white card
    TEXT_DARK = (42, 26, 6)      # #2A1A06
    TEXT_MUTED = (138, 107, 74)  # #8A6B4A
    AMBER = (153, 96, 18)       # #996012
    AMBER_ACCENT = (200, 134, 26)  # #C8861A
    AMBER_LIGHT = (232, 168, 32)   # #E8A820
    GREEN = (51, 145, 71)        # #339147

    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    try:
        heading_lg = ImageFont.truetype(str(FONTS_DIR / "DMSerifDisplay-Regular.ttf"), 56)
        heading_md = ImageFont.truetype(str(FONTS_DIR / "DMSerifDisplay-Regular.ttf"), 40)
        heading_sm = ImageFont.truetype(str(FONTS_DIR / "DMSerifDisplay-Regular.ttf"), 32)
        body_lg = ImageFont.truetype(str(FONTS_DIR / "Inter.ttf"), 28)
        body_md = ImageFont.truetype(str(FONTS_DIR / "Inter.ttf"), 22)
        body_sm = ImageFont.truetype(str(FONTS_DIR / "Inter.ttf"), 18)
        body_xs = ImageFont.truetype(str(FONTS_DIR / "Inter.ttf"), 15)
    except Exception:
        heading_lg = ImageFont.load_default()
        heading_md = heading_sm = body_lg = body_md = body_sm = body_xs = heading_lg

    pad = 60
    y = pad

    # ── Brand header ──
    draw.text((pad, y), "HoneyGroove", fill=AMBER, font=heading_md)
    y += 50
    username = report.get("username", "collector")
    ws = report.get("week_start", "")
    we = report.get("week_end", "")
    try:
        ws_dt = datetime.fromisoformat(ws)
        we_dt = datetime.fromisoformat(we) - timedelta(days=1)
        date_range = f"{ws_dt.strftime('%b %d')} — {we_dt.strftime('%b %d')}"
    except Exception:
        date_range = ""
    draw.text((pad, y), f"@{username}  ·  {date_range}", fill=TEXT_MUTED, font=body_sm)
    y += 40

    # ── Personality label ──
    personality = report.get("personality", {})
    label = personality.get("label", "")
    if label:
        # Card background
        draw.rounded_rectangle([(pad, y), (W - pad, y + 70)], radius=16, fill=CARD, outline=(*AMBER_ACCENT, 38))
        draw.text((pad + 20, y + 18), f'"{label}"', fill=AMBER_ACCENT, font=body_md)
        y += 90

    # ── Top 3 Artists ──
    draw.text((pad, y), "top artists", fill=TEXT_MUTED, font=body_sm)
    y += 30
    top_artists = report.get("top_artists", [])[:3]
    for i, a in enumerate(top_artists):
        draw.text((pad, y), f"{i+1}.", fill=AMBER, font=heading_sm)
        draw.text((pad + 40, y + 2), a.get("artist", ""), fill=TEXT_DARK, font=body_lg)
        draw.text((W - pad - 80, y + 4), f'{a.get("spins", 0)} spins', fill=AMBER_ACCENT, font=body_sm)
        y += 42
    y += 15

    # ── Stats row ──
    draw.rounded_rectangle([(pad, y), (W - pad, y + 90)], radius=16, fill=CARD, outline=(*AMBER_ACCENT, 38))
    col_w = (W - 2 * pad) // 3
    stats_data = [
        (str(report.get("total_spins", 0)), "spins this week"),
        (f'${report.get("collection_value", {}).get("total_value", 0):,.0f}', "collection value"),
    ]
    top_mood = report.get("mood_breakdown", [{}])
    mood_label = top_mood[0].get("mood", "—") if top_mood else "—"
    stats_data.append((mood_label[:15], "top mood"))

    for i, (val, label) in enumerate(stats_data):
        sx = pad + 20 + i * col_w
        draw.text((sx, y + 15), val, fill=AMBER, font=heading_sm)
        draw.text((sx, y + 55), label, fill=TEXT_MUTED, font=body_xs)
    y += 110

    # ── Closing line ──
    closing = report.get("closing_line", "")
    if closing:
        draw.text((pad, y), closing[:70], fill=TEXT_DARK, font=body_md)
        if len(closing) > 70:
            draw.text((pad, y + 28), closing[70:140], fill=TEXT_DARK, font=body_md)
        y += 65

    # ── Footer ──
    y = H - 60
    draw.text((pad, y), "thehoneygroove.com", fill=AMBER, font=body_md)
    draw.text((W - pad - 180, y), "your week in wax", fill=TEXT_MUTED, font=body_sm)

    # Top + bottom accent lines
    draw.rectangle([(0, 0), (W, 5)], fill=AMBER_ACCENT)
    draw.rectangle([(0, H - 5), (W, H)], fill=AMBER_ACCENT)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@router.get("/wax-reports/{report_id}/share-card")
async def get_share_card(report_id: str, user: Dict = Depends(require_auth)):
    """Generate a 1080x1080 shareable card PNG."""
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
