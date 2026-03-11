"""Daily Prompts — daily prompt card, buzz-in, streak tracking, export cards."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from pathlib import Path
from io import BytesIO
import uuid
import asyncio
import random
import requests

from database import db, require_auth, get_current_user, logger, create_notification
from database import get_discogs_release, DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_API_BASE
from services.email_service import send_email_fire_and_forget
import templates.emails as email_tpl

router = APIRouter()
FONTS_DIR = Path(__file__).parent.parent / "fonts"

# ─────────── Seed Prompts ───────────
SEED_PROMPTS = [
    "the record you'd save in a fire",
    "last record you bought without listening first",
    "the album that got you into vinyl",
    "a record everyone sleeps on",
    "what's on right now, no context",
    "the record that defined a specific year of your life",
    "a record you own but never play",
    "the one that started it all",
    "something you'd trade everything for",
    "the record you know every word to",
    "a find that still doesn't feel real",
    "what you put on when you need to feel something",
    "a record you bought for the cover art",
    "the one that broke your heart",
    "your most played record of all time",
    "a record that reminds you of someone",
    "something you'd never trade, no matter what",
    "the record that made you a collector",
    "your most valuable record right now",
    "a pressing you're still hunting",
    "the record that sounds best on a rainy day",
    "a record you discovered through a friend",
    "the album you play when you want to dance alone",
    "a record that takes you back to high school",
    "the one that made you cry in public",
    "a record you bought twice",
    "the album you'd play for someone who doesn't get vinyl",
    "a record that changed how you listen to music",
    "the one you spin to clear your head",
    "a record that deserves more love than it gets",
]


async def seed_prompts():
    """Seed the prompts collection if empty."""
    count = await db.prompts.count_documents({})
    if count > 0:
        return
    today = datetime.now(ET).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    docs = []
    for i, text in enumerate(SEED_PROMPTS):
        docs.append({
            "id": str(uuid.uuid4()),
            "text": text,
            "scheduled_date": (today + timedelta(days=i)).isoformat(),
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    await db.prompts.insert_many(docs)
    logger.info(f"Seeded {len(docs)} daily prompts")


# ─────────── Image Cache ───────────

async def get_cached_image(release_id: int) -> Optional[str]:
    """Get cached high-res image URL for a release."""
    cached = await db.image_cache.find_one({"release_id": release_id}, {"_id": 0})
    if cached:
        cached_at = datetime.fromisoformat(cached["cached_at"])
        if datetime.now(timezone.utc) - cached_at < timedelta(days=30):
            return cached["image_url"]
    return None


async def cache_discogs_image(release_id: int) -> Optional[str]:
    """Fetch and cache high-res Discogs image for a release."""
    existing = await get_cached_image(release_id)
    if existing:
        return existing
    release = get_discogs_release(release_id)
    if not release or not release.get("cover_url"):
        return None
    image_url = release["cover_url"]
    await db.image_cache.update_one(
        {"release_id": release_id},
        {"$set": {
            "release_id": release_id,
            "image_url": image_url,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "resolution": "high",
        }},
        upsert=True,
    )
    return image_url


# ─────────── Today's Prompt ───────────

from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

def _get_today_range():
    """Return (start, end) of today in Eastern Time, as UTC datetimes."""
    now_et = datetime.now(ET)
    start_et = now_et.replace(hour=0, minute=0, second=0, microsecond=0)
    end_et = start_et + timedelta(days=1)
    start_utc = start_et.astimezone(timezone.utc)
    end_utc = end_et.astimezone(timezone.utc)
    return start_utc, end_utc


@router.get("/prompts/today")
async def get_todays_prompt(user: Dict = Depends(require_auth)):
    today_start, today_end = _get_today_range()
    prompt = await db.prompts.find_one(
        {"scheduled_date": {"$gte": today_start.isoformat(), "$lt": today_end.isoformat()}, "active": True},
        {"_id": 0},
    )
    if not prompt:
        # Fallback: pick the prompt for today based on day-of-year cycling
        all_prompts = await db.prompts.find({"active": True}, {"_id": 0}).sort("scheduled_date", 1).to_list(1000)
        if not all_prompts:
            return {"prompt": None}
        day_index = (datetime.now(ET).replace(hour=0, minute=0, second=0, microsecond=0) - datetime.fromisoformat(all_prompts[0]["scheduled_date"].replace("Z", "+00:00") if "Z" in all_prompts[0]["scheduled_date"] else all_prompts[0]["scheduled_date"]).astimezone(ET).replace(hour=0, minute=0, second=0, microsecond=0)).days % len(all_prompts)
        prompt = all_prompts[day_index]

    # Check if user already buzzed in today
    response = await db.prompt_responses.find_one(
        {"user_id": user["id"], "prompt_id": prompt["id"]},
        {"_id": 0},
    )
    # Get user streak
    streak = await _calculate_streak(user["id"])
    # Count how many buzzed in today
    buzz_count = await db.prompt_responses.count_documents({"prompt_id": prompt["id"]})
    return {
        "prompt": prompt,
        "has_buzzed_in": response is not None,
        "response": response,
        "streak": streak,
        "buzz_count": buzz_count,
    }


async def _calculate_streak(user_id: str) -> int:
    """Calculate consecutive days the user has buzzed in."""
    today_start, _ = _get_today_range()
    streak = 0
    for i in range(365):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)
        has_response = await db.prompt_responses.find_one({
            "user_id": user_id,
            "created_at": {"$gte": day.isoformat(), "$lt": day_end.isoformat()},
        })
        if has_response:
            streak += 1
        elif i == 0:
            continue  # Today might not be answered yet
        else:
            break
    return streak


# ─────────── Buzz In ───────────

@router.post("/prompts/buzz-in")
async def buzz_in(data: dict, user: Dict = Depends(require_auth)):
    prompt_id = data.get("prompt_id")
    record_id = data.get("record_id")
    caption = data.get("caption", "")
    post_to_hive = data.get("post_to_hive", False)

    if not prompt_id or not record_id:
        raise HTTPException(status_code=400, detail="prompt_id and record_id required")

    prompt = await db.prompts.find_one({"id": prompt_id}, {"_id": 0})
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Check not already responded
    existing = await db.prompt_responses.find_one({"user_id": user["id"], "prompt_id": prompt_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already buzzed in today")

    # Get record
    record = await db.records.find_one({"id": record_id, "user_id": user["id"]}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found in your collection")

    # Fetch high-res Discogs data
    discogs_data = None
    if record.get("discogs_id"):
        discogs_data = get_discogs_release(record["discogs_id"])
        await cache_discogs_image(record["discogs_id"])

    response_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    response_doc = {
        "id": response_id,
        "user_id": user["id"],
        "prompt_id": prompt_id,
        "record_id": record_id,
        "caption": caption,
        "record_title": discogs_data.get("title") if discogs_data else record.get("title"),
        "record_artist": discogs_data.get("artist") if discogs_data else record.get("artist"),
        "cover_url": discogs_data.get("cover_url") if discogs_data else record.get("cover_url"),
        "label": (discogs_data.get("label", [None])[0] if discogs_data and discogs_data.get("label") else None),
        "year": discogs_data.get("year") if discogs_data else record.get("year"),
        "format": (discogs_data.get("format", [None])[0] if discogs_data and discogs_data.get("format") else None),
        "prompt_text": prompt["text"],
        "created_at": now,
    }
    insert_doc = {k: v for k, v in response_doc.items()}
    await db.prompt_responses.insert_one(insert_doc)

    # Post to hive if requested
    post_id = None
    if post_to_hive:
        post_id = str(uuid.uuid4())
        post_doc = {
            "id": post_id,
            "user_id": user["id"],
            "username": user.get("username", ""),
            "post_type": "DAILY_PROMPT",
            "prompt_text": prompt["text"],
            "record_id": record_id,
            "record_title": response_doc["record_title"],
            "record_artist": response_doc["record_artist"],
            "cover_url": response_doc["cover_url"],
            "caption": caption,
            "created_at": now,
        }
        await db.posts.insert_one({k: v for k, v in post_doc.items()})

    streak = await _calculate_streak(user["id"])
    return {
        "id": response_id,
        "streak": streak,
        "post_id": post_id,
        **{k: v for k, v in response_doc.items() if k not in ("_id",)},
    }


@router.get("/prompts/{prompt_id}/responses")
async def get_prompt_responses(prompt_id: str, user: Dict = Depends(require_auth)):
    """Get all responses for a prompt (for the carousel). Only available after buzzing in."""
    my_response = await db.prompt_responses.find_one({"user_id": user["id"], "prompt_id": prompt_id})
    if not my_response:
        raise HTTPException(status_code=403, detail="Buzz in first to see other responses")

    responses = await db.prompt_responses.find(
        {"prompt_id": prompt_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    # Enrich with user data and linked post_id
    for r in responses:
        u = await db.users.find_one({"id": r["user_id"]}, {"_id": 0, "username": 1, "display_name": 1, "avatar_url": 1, "founding_member": 1})
        if u:
            r["username"] = u.get("username")
            r["display_name"] = u.get("display_name")
            r["avatar_url"] = u.get("avatar_url")
            r["founding_member"] = u.get("founding_member", False)
        # Get the record's color_variant if available
        if r.get("record_id"):
            rec = await db.records.find_one({"id": r["record_id"]}, {"_id": 0, "color_variant": 1})
            r["color_variant"] = rec.get("color_variant") if rec else None
        else:
            r["color_variant"] = None
        # Find the linked Hive post for deep-linking
        if not r.get("post_id"):
            linked_post = await db.posts.find_one(
                {"user_id": r["user_id"], "post_type": "DAILY_PROMPT", "prompt_text": r.get("prompt_text")},
                {"_id": 0, "id": 1}
            )
            r["post_id"] = linked_post["id"] if linked_post else None

    return responses

@router.post("/prompts/export-card")
async def generate_export_card(data: dict, user: Dict = Depends(require_auth)):
    """Generate a 1080x1080 daily prompt export card."""
    response_id = data.get("response_id")
    if not response_id:
        raise HTTPException(status_code=400, detail="response_id required")

    resp = await db.prompt_responses.find_one({"id": response_id, "user_id": user["id"]}, {"_id": 0})
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")

    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        W, H = 1080, 1080
        BG = (250, 246, 238)  # #FAF6EE
        AMBER = (200, 134, 26)  # #C8861A
        DARK = (42, 26, 6)

        img = Image.new("RGBA", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Load fonts
        playfair_bold = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 36)
        playfair_italic = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Italic2.ttf"), 22)
        cormorant_italic = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 30)
        cormorant_italic_sm = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 24)
        cormorant_italic_xs = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 20)
        cormorant_reg = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Regular2.ttf"), 22)

        y = 40

        # Prompt text — italic centered at top in amber
        prompt_text = resp.get("prompt_text", "")
        lines = textwrap.wrap(prompt_text, width=40)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=cormorant_italic)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, y), line, fill=AMBER, font=cormorant_italic)
            y += 42
        y += 30

        # Album art — 600x600 centered, rounded corners
        cover_url = resp.get("cover_url")
        art_size = 600
        art_x = (W - art_size) // 2
        if cover_url:
            try:
                art_resp = requests.get(cover_url, timeout=15)
                if art_resp.status_code == 200:
                    art_img = Image.open(BytesIO(art_resp.content)).convert("RGBA")
                    art_img = art_img.resize((art_size, art_size), Image.LANCZOS)
                    # Round corners
                    mask = Image.new("L", (art_size, art_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.rounded_rectangle([(0, 0), (art_size, art_size)], radius=20, fill=255)
                    art_img.putalpha(mask)
                    img.paste(art_img, (art_x, y), art_img)
            except Exception as e:
                logger.warning(f"Failed to fetch cover art: {e}")
                draw.rounded_rectangle([(art_x, y), (art_x + art_size, y + art_size)], radius=20, fill=(230, 220, 200))
        else:
            draw.rounded_rectangle([(art_x, y), (art_x + art_size, y + art_size)], radius=20, fill=(230, 220, 200))

        y += art_size + 24

        # Artist and album — Playfair Display bold
        title = resp.get("record_title", "Unknown")
        artist = resp.get("record_artist", "Unknown")
        title_lines = textwrap.wrap(title, width=35)
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=playfair_bold)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, y), line, fill=DARK, font=playfair_bold)
            y += 44
        y += 4
        bbox = draw.textbbox((0, 0), artist, font=cormorant_reg)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, y), artist, fill=DARK, font=cormorant_reg)
        y += 32

        # Label and year — Cormorant Garamond italic muted
        label = resp.get("label", "")
        year = resp.get("year", "")
        meta = f"{label} · {year}" if label and year else (label or str(year) if year else "")
        if meta:
            bbox = draw.textbbox((0, 0), meta, font=cormorant_italic_sm)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) / 2, y), meta, fill=AMBER, font=cormorant_italic_sm)
            y += 32

        # Caption
        caption = resp.get("caption", "")
        if caption:
            y += 8
            cap_lines = textwrap.wrap(caption, width=50)
            for line in cap_lines:
                bbox = draw.textbbox((0, 0), line, font=cormorant_italic_sm)
                tw = bbox[2] - bbox[0]
                draw.text(((W - tw) / 2, y), line, fill=DARK, font=cormorant_italic_sm)
                y += 30

        # Date — small text bottom right
        date_str = datetime.fromisoformat(resp["created_at"]).strftime("%B %d, %Y")
        bbox = draw.textbbox((0, 0), date_str, font=cormorant_italic_xs)
        tw = bbox[2] - bbox[0]
        draw.text((W - tw - 40, H - 100), date_str, fill=AMBER, font=cormorant_italic_xs)

        # "buzzed in on the honey groove" line
        buzz_text = "buzzed in on the honey groove"
        bbox = draw.textbbox((0, 0), buzz_text, font=cormorant_italic_xs)
        tw = bbox[2] - bbox[0]
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.text(((W - tw) / 2, H - 70), buzz_text, fill=(200, 134, 26, 128), font=cormorant_italic_xs)
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        # Footer: handle left, HoneyGroove right
        handle = f"@{user.get('username', 'user')}"
        draw.text((40, H - 44), handle, fill=DARK, font=cormorant_reg)
        hg_text = "the Honey Groove"
        bbox = draw.textbbox((0, 0), hg_text, font=playfair_italic)
        tw = bbox[2] - bbox[0]
        draw.text((W - tw - 40, H - 44), hg_text, fill=AMBER, font=playfair_italic)

        # Convert to PNG bytes
        final = img.convert("RGB")
        buf = BytesIO()
        final.save(buf, format="PNG", quality=95)
        buf.seek(0)
        return Response(content=buf.read(), media_type="image/png")

    except Exception as e:
        logger.error(f"Export card generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate export card")


# ─────────── Streak for Profile ───────────

@router.get("/prompts/streak/{username}")
async def get_user_streak(username: str):
    user = await db.users.find_one({"username": username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    streak = await _calculate_streak(user["id"])
    longest = await _calculate_longest_streak(user["id"])
    return {"streak": streak, "longest_streak": longest, "username": username}


async def _calculate_longest_streak(user_id: str) -> int:
    """Calculate the longest ever buzz-in streak for a user."""
    responses = await db.prompt_responses.find(
        {"user_id": user_id}, {"_id": 0, "created_at": 1}
    ).sort("created_at", 1).to_list(5000)
    if not responses:
        return 0

    dates = set()
    for r in responses:
        try:
            dt = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00") if "Z" in r["created_at"] else r["created_at"])
            dates.add(dt.date())
        except Exception:
            continue

    if not dates:
        return 0

    sorted_dates = sorted(dates)
    longest = 1
    current = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


# ─────────── Streak Nudge Notifications Scheduler ───────────

async def send_streak_nudge_notifications():
    """
    Send nudge notifications to users with active streaks:
    - 7pm: Users with streak >= 3 who haven't buzzed in today
    - 10pm: Users with streak >= 7 who haven't buzzed in today (urgent)
    """
    now = datetime.now(timezone.utc)
    today_start, today_end = _get_today_range()

    # Find all users who have buzzed in within the last 30 days
    recent_responders = await db.prompt_responses.distinct(
        "user_id",
        {"created_at": {"$gte": (now - timedelta(days=30)).isoformat()}}
    )

    for user_id in recent_responders:
        streak = await _calculate_streak(user_id)
        if streak < 3:
            continue

        # Check if they've already buzzed in today
        today_response = await db.prompt_responses.find_one({
            "user_id": user_id,
            "created_at": {"$gte": today_start.isoformat(), "$lt": today_end.isoformat()},
        })
        if today_response:
            continue  # Already buzzed in today

        # Check if we've already sent a nudge today
        existing_nudge = await db.notifications.find_one({
            "user_id": user_id,
            "type": "streak_nudge",
            "created_at": {"$gte": today_start.isoformat()},
        })

        if not existing_nudge and streak >= 3:
            # First nudge (7pm style)
            await create_notification(
                user_id, "streak_nudge",
                f"don't break your {streak}-day streak!",
                f"you've buzzed in {streak} days in a row. today's prompt is waiting for you.",
                {"streak": streak}
            )
            # Send email
            nudge_user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if nudge_user and nudge_user.get("email"):
                today_prompt = await db.daily_prompts.find_one(
                    {"active_date": {"$gte": today_start.isoformat(), "$lt": today_end.isoformat()}},
                    {"_id": 0}
                )
                prompt_text = today_prompt.get("prompt_text", "check the hive") if today_prompt else "check the hive"
                tpl = email_tpl.streak_nudge(nudge_user.get("username", ""), streak, prompt_text)
                await send_email_fire_and_forget(nudge_user["email"], tpl["subject"], tpl["html"])

        if existing_nudge and not await db.notifications.find_one({
            "user_id": user_id,
            "type": "streak_nudge_urgent",
            "created_at": {"$gte": today_start.isoformat()},
        }) and streak >= 7:
            # Second urgent nudge (10pm style)
            await create_notification(
                user_id, "streak_nudge_urgent",
                f"your {streak}-day streak is about to break!",
                f"last chance — buzz in before midnight to keep your {streak}-day streak alive.",
                {"streak": streak, "urgent": True}
            )


async def schedule_streak_nudges():
    """Run streak nudge checks every hour."""
    while True:
        try:
            now = datetime.now(timezone.utc)
            hour = now.hour
            # Run at approximately 19:00 and 22:00 UTC (adjustable)
            if hour in (19, 22):
                logger.info(f"Running streak nudge notifications (hour={hour})")
                await send_streak_nudge_notifications()
        except Exception as e:
            logger.error(f"Streak nudge error: {e}")
        await asyncio.sleep(3600)  # Check every hour


# ─────────── Admin: Prompt Manager ───────────

@router.get("/prompts/admin/all")
async def admin_get_all_prompts(user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    prompts = await db.prompts.find({}, {"_id": 0}).sort("scheduled_date", 1).to_list(1000)
    # Add response count for each prompt
    for p in prompts:
        p["response_count"] = await db.prompt_responses.count_documents({"prompt_id": p["id"]})
    return prompts


@router.post("/prompts/admin/create")
async def admin_create_prompt(data: dict, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    prompt_id = str(uuid.uuid4())
    doc = {
        "id": prompt_id,
        "text": data["text"],
        "scheduled_date": data["scheduled_date"],
        "active": data.get("active", True),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.prompts.insert_one({k: v for k, v in doc.items()})
    return doc


@router.put("/prompts/admin/{prompt_id}")
async def admin_update_prompt(prompt_id: str, data: dict, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    update = {}
    if "text" in data:
        update["text"] = data["text"]
    if "scheduled_date" in data:
        update["scheduled_date"] = data["scheduled_date"]
    if "active" in data:
        update["active"] = data["active"]
    if update:
        await db.prompts.update_one({"id": prompt_id}, {"$set": update})
    prompt = await db.prompts.find_one({"id": prompt_id}, {"_id": 0})
    return prompt


@router.post("/prompts/admin/reorder")
async def admin_reorder_prompts(data: dict, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    ordered_ids = data.get("prompt_ids", [])
    base_date = datetime.fromisoformat(data.get("start_date", datetime.now(timezone.utc).isoformat()))
    for i, pid in enumerate(ordered_ids):
        new_date = (base_date + timedelta(days=i)).isoformat()
        await db.prompts.update_one({"id": pid}, {"$set": {"scheduled_date": new_date}})
    return {"reordered": len(ordered_ids)}


# ─────────── Discogs High-Res Fetch ───────────

@router.get("/prompts/discogs-hires/{release_id}")
async def get_discogs_hires(release_id: int, user: Dict = Depends(require_auth)):
    """Get high-res Discogs data for a record (with caching)."""
    cached_url = await get_cached_image(release_id)
    release_data = get_discogs_release(release_id)
    if not release_data:
        raise HTTPException(status_code=404, detail="Release not found on Discogs")
    if not cached_url and release_data.get("cover_url"):
        await cache_discogs_image(release_id)
    return release_data
