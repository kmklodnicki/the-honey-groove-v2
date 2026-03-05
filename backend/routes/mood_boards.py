"""Mood Board — 3x3 album art grid, auto-generated weekly + on-demand."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from typing import Dict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from io import BytesIO
import uuid
import requests

from database import db, require_auth, logger, create_notification

router = APIRouter()
FONTS_DIR = Path(__file__).parent.parent / "fonts"


async def _get_top_records(user_id: str, time_range: str = "week"):
    """Get top 9 most-spun records for a time range."""
    now = datetime.now(timezone.utc)
    if time_range == "week":
        since = (now - timedelta(days=7)).isoformat()
    elif time_range == "month":
        since = (now - timedelta(days=30)).isoformat()
    else:
        since = "2000-01-01T00:00:00"

    pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": since}}},
        {"$group": {"_id": "$record_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 9},
    ]
    top = await db.spins.aggregate(pipeline).to_list(9)

    records = []
    for t in top:
        rec = await db.records.find_one({"id": t["_id"]}, {"_id": 0})
        if rec:
            rec["spin_count"] = t["count"]
            records.append(rec)

    # Fill remaining from all-time if needed
    if len(records) < 9:
        existing_ids = {r["id"] for r in records}
        fill_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$record_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20},
        ]
        fill = await db.spins.aggregate(fill_pipeline).to_list(20)
        for t in fill:
            if len(records) >= 9:
                break
            if t["_id"] not in existing_ids:
                rec = await db.records.find_one({"id": t["_id"]}, {"_id": 0})
                if rec:
                    rec["spin_count"] = t["count"]
                    records.append(rec)
                    existing_ids.add(t["_id"])

    return records[:9]


async def _get_cover_url(record: dict) -> str:
    """Get best available cover URL with caching."""
    release_id = record.get("discogs_id")
    if release_id:
        cached = await db.image_cache.find_one({"release_id": release_id}, {"_id": 0})
        if cached:
            return cached["image_url"]
    return record.get("cover_url", "")


def _generate_mood_board_image(covers: list, username: str) -> bytes:
    """Generate 1080x1080 mood board PNG."""
    from PIL import Image, ImageDraw, ImageFont

    W = 1080
    GRID = 1000
    STRIP = 80
    H = GRID + STRIP
    BG = (250, 246, 238)
    AMBER = (200, 134, 26)

    img = Image.new("RGB", (W, H), BG)
    cell = GRID // 3

    for i, cover_url in enumerate(covers[:9]):
        row, col = divmod(i, 3)
        try:
            if cover_url:
                resp = requests.get(cover_url, timeout=10)
                if resp.status_code == 200:
                    art = Image.open(BytesIO(resp.content)).convert("RGB")
                    art = art.resize((cell, cell), Image.LANCZOS)
                    x = col * cell + (W - GRID) // 2
                    y = row * cell
                    img.paste(art, (x, y))
                    continue
        except Exception as e:
            logger.warning(f"Mood board cover fetch failed: {e}")
        # Fallback: amber placeholder
        x = col * cell + (W - GRID) // 2
        y = row * cell
        draw = ImageDraw.Draw(img)
        draw.rectangle([(x, y), (x + cell, y + cell)], fill=(232, 220, 200))

    draw = ImageDraw.Draw(img)
    strip_y = GRID

    try:
        cormorant_italic = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 30)
        playfair_italic = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Italic2.ttf"), 18)
    except Exception:
        cormorant_italic = ImageFont.load_default()
        playfair_italic = cormorant_italic

    # "my week in wax" left
    draw.text((40, strip_y + 22), "my week in wax", fill=AMBER, font=cormorant_italic)
    # Handle right
    handle = f"@{username}"
    bbox = draw.textbbox((0, 0), handle, font=cormorant_italic)
    draw.text((W - 40 - (bbox[2] - bbox[0]), strip_y + 22), handle, fill=AMBER, font=cormorant_italic)
    # "HoneyGroove" centered small below
    hg = "the Honey Groove"
    bbox = draw.textbbox((0, 0), hg, font=playfair_italic)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.text(((W - (bbox[2] - bbox[0])) / 2, strip_y + 56), hg, fill=(200, 134, 26, 102), font=playfair_italic)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    from io import BytesIO as BIO
    buf = BIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ─── Endpoints ───

@router.get("/mood-boards/latest/{username}")
async def get_latest_mood_board(username: str, user: Dict = Depends(require_auth)):
    target = await db.users.find_one({"username": username}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    board = await db.mood_boards.find_one(
        {"user_id": target["id"]}, {"_id": 0}, sort=[("created_at", -1)]
    )
    return board or {}


@router.get("/mood-boards/history/{username}")
async def get_mood_board_history(username: str, user: Dict = Depends(require_auth)):
    target = await db.users.find_one({"username": username}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    boards = await db.mood_boards.find(
        {"user_id": target["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(52)
    return boards


@router.post("/mood-boards/generate")
async def generate_mood_board_manual(data: dict, user: Dict = Depends(require_auth)):
    """Generate a mood board on demand."""
    time_range = data.get("time_range", "week")
    if time_range not in ("week", "month", "all_time"):
        raise HTTPException(status_code=400, detail="Invalid time range")

    records = await _get_top_records(user["id"], time_range)
    if not records:
        raise HTTPException(status_code=400, detail="No spins found for this period")

    covers = []
    record_data = []
    for r in records:
        url = await _get_cover_url(r)
        covers.append(url)
        record_data.append({"id": r["id"], "title": r.get("title"), "artist": r.get("artist"), "cover_url": url})

    image_bytes = _generate_mood_board_image(covers, user.get("username", ""))

    board_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    board_doc = {
        "id": board_id,
        "user_id": user["id"],
        "username": user.get("username", ""),
        "time_range": time_range,
        "records": record_data,
        "created_at": now,
    }
    await db.mood_boards.insert_one({k: v for k, v in board_doc.items()})
    return {"id": board_id, **board_doc}


@router.get("/mood-boards/{board_id}/image")
async def get_mood_board_image(board_id: str, user: Dict = Depends(require_auth)):
    board = await db.mood_boards.find_one({"id": board_id}, {"_id": 0})
    if not board:
        raise HTTPException(status_code=404, detail="Mood board not found")
    covers = [r.get("cover_url", "") for r in board.get("records", [])]
    image_bytes = _generate_mood_board_image(covers, board.get("username", ""))
    return Response(content=image_bytes, media_type="image/png")


async def generate_weekly_mood_boards():
    """Generate mood boards for all users (called from scheduler)."""
    users = await db.users.find({}, {"_id": 0, "id": 1, "username": 1}).to_list(10000)
    for u in users:
        try:
            records = await _get_top_records(u["id"], "week")
            if not records:
                continue
            covers = []
            record_data = []
            for r in records:
                url = await _get_cover_url(r)
                covers.append(url)
                record_data.append({"id": r["id"], "title": r.get("title"), "artist": r.get("artist"), "cover_url": url})

            board_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            await db.mood_boards.insert_one({
                "id": board_id, "user_id": u["id"], "username": u.get("username", ""),
                "time_range": "week", "records": record_data, "created_at": now,
            })
            await create_notification(u["id"], "MOOD_BOARD", "your mood board is ready", "your mood board is ready 🍯", {"board_id": board_id})
        except Exception as e:
            logger.error(f"Mood board gen failed for {u['id']}: {e}")
    logger.info("Mood board: weekly generation complete")
