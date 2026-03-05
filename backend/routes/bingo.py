"""Collector Bingo — weekly 5x5 bingo card, interactive marking, export."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from typing import Dict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from io import BytesIO
import uuid
import random
import textwrap

from database import db, require_auth, logger, create_notification

router = APIRouter()
FONTS_DIR = Path(__file__).parent.parent / "fonts"

SEED_SQUARES = [
    ("bought a record for the cover art", "🎨"),
    ("own multiple copies of the same album", "💿"),
    ("judged someone's collection silently", "👀"),
    ("have a record still in shrink wrap", "📦"),
    ("paid more than $100 for one record", "💸"),
    ("bought a record you already own on streaming", "🎵"),
    ("reorganized your collection twice this month", "📚"),
    ("have a record you've never played", "🤫"),
    ("own something your parents think is noise", "🔊"),
    ("found a gem at a thrift store", "💎"),
    ("cried to a record alone", "😢"),
    ("bought a record on a trip and had to carry it home", "✈️"),
    ("have a wantlist longer than your collection", "📝"),
    ("stayed up past midnight listening", "🌙"),
    ("bought a turntable upgrade this year", "🎛️"),
    ("own a colored or picture disc", "🌈"),
    ("have a record signed by the artist", "✍️"),
    ("recommended a record and they loved it", "❤️"),
    ("lied about how much a record cost", "🤥"),
    ("own something older than you are", "👴"),
    ("have a record with sentimental value you'd never sell", "💛"),
    ("bought something just because the label was cool", "🏷️"),
    ("discovered an artist through the Honey Groove", "🐝"),
    ("completed a trade on the Honey Groove", "🤝"),
    ("posted a Now Spinning this week", "🎶"),
]

FREE_SPACE = {"text": "sweet spot 🍯", "emoji": "🍯", "is_free": True}


async def seed_bingo_squares():
    count = await db.bingo_squares.count_documents({})
    if count > 0:
        return
    docs = []
    for text, emoji in SEED_SQUARES:
        docs.append({"id": str(uuid.uuid4()), "text": text, "emoji": emoji, "active": True, "created_at": datetime.now(timezone.utc).isoformat()})
    await db.bingo_squares.insert_many(docs)
    logger.info(f"Seeded {len(docs)} bingo squares")


def _get_current_week():
    """Get the Friday-to-Thursday week boundaries."""
    now = datetime.now(timezone.utc)
    days_since_friday = (now.weekday() - 4) % 7
    friday = (now - timedelta(days=days_since_friday)).replace(hour=9, minute=0, second=0, microsecond=0)
    if friday > now:
        friday -= timedelta(days=7)
    sunday = friday + timedelta(days=2, hours=15)  # Sunday midnight
    return friday, sunday


async def _get_or_create_weekly_card():
    """Get the current week's bingo card, or create one."""
    friday, sunday = _get_current_week()
    card = await db.bingo_cards.find_one({"week_start": friday.isoformat()}, {"_id": 0})
    if card:
        return card

    active_squares = await db.bingo_squares.find({"active": True}, {"_id": 0}).to_list(100)
    if len(active_squares) < 24:
        raise HTTPException(status_code=500, detail="Not enough active bingo squares")

    selected = random.sample(active_squares, 24)
    grid = []
    idx = 0
    for row in range(5):
        for col in range(5):
            if row == 2 and col == 2:
                grid.append({**FREE_SPACE, "row": row, "col": col, "index": row * 5 + col})
            else:
                sq = selected[idx]
                grid.append({"text": sq["text"], "emoji": sq["emoji"], "is_free": False, "row": row, "col": col, "index": row * 5 + col})
                idx += 1

    card_id = str(uuid.uuid4())
    card_doc = {
        "id": card_id,
        "week_start": friday.isoformat(),
        "week_end": sunday.isoformat(),
        "grid": grid,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.bingo_cards.insert_one({k: v for k, v in card_doc.items()})
    return card_doc


def _check_bingo(marks: list) -> bool:
    """Check if marks form a bingo (row, col, or diagonal)."""
    marked = set(marks)
    for r in range(5):
        if all((r * 5 + c) in marked for c in range(5)):
            return True
    for c in range(5):
        if all((r * 5 + c) in marked for r in range(5)):
            return True
    if all((i * 5 + i) in marked for i in range(5)):
        return True
    if all((i * 5 + (4 - i)) in marked for i in range(5)):
        return True
    return False


def _count_bingos(marks: list) -> int:
    """Count how many bingo lines (rows, cols, diagonals) are completed."""
    marked = set(marks)
    count = 0
    for r in range(5):
        if all((r * 5 + c) in marked for c in range(5)):
            count += 1
    for c in range(5):
        if all((r * 5 + c) in marked for r in range(5)):
            count += 1
    if all((i * 5 + i) in marked for i in range(5)):
        count += 1
    if all((i * 5 + (4 - i)) in marked for i in range(5)):
        count += 1
    return count


async def _get_community_stats(card_id: str) -> dict:
    """Compute percentage of players who marked each square."""
    all_marks = await db.bingo_marks.find({"card_id": card_id}, {"_id": 0, "marks": 1}).to_list(100000)
    total_players = len(all_marks)
    if total_players == 0:
        return {"total_players": 0, "percentages": {}}
    counts = {}
    for m in all_marks:
        for idx in m.get("marks", []):
            counts[idx] = counts.get(idx, 0) + 1
    percentages = {}
    for i in range(25):
        pct = round((counts.get(i, 0) / total_players) * 100)
        percentages[str(i)] = pct
    return {"total_players": total_players, "percentages": percentages}


# ─── Endpoints ───

@router.get("/bingo/current")
async def get_current_bingo(user: Dict = Depends(require_auth)):
    card = await _get_or_create_weekly_card()
    friday, sunday = _get_current_week()
    now = datetime.now(timezone.utc)
    is_locked = now > sunday

    user_marks = await db.bingo_marks.find_one(
        {"user_id": user["id"], "card_id": card["id"]}, {"_id": 0}
    )
    marks = user_marks.get("marks", [12]) if user_marks else [12]  # 12 = free space
    has_bingo = _check_bingo(marks)
    bingo_count = _count_bingos(marks)

    result = {
        "card": card,
        "marks": marks,
        "has_bingo": has_bingo,
        "bingo_count": bingo_count,
        "is_locked": is_locked,
        "week_start": card["week_start"],
        "week_end": card["week_end"],
    }

    if is_locked:
        result["community_stats"] = await _get_community_stats(card["id"])

    return result


@router.post("/bingo/mark")
async def toggle_mark(data: dict, user: Dict = Depends(require_auth)):
    index = data.get("index")
    if index is None or not (0 <= index < 25):
        raise HTTPException(status_code=400, detail="Invalid square index")
    if index == 12:
        raise HTTPException(status_code=400, detail="Cannot unmark the free space")

    card = await _get_or_create_weekly_card()
    _, sunday = _get_current_week()
    if datetime.now(timezone.utc) > sunday:
        raise HTTPException(status_code=400, detail="Card is locked")

    user_marks = await db.bingo_marks.find_one({"user_id": user["id"], "card_id": card["id"]}, {"_id": 0})
    marks = user_marks.get("marks", [12]) if user_marks else [12]

    if index in marks:
        marks.remove(index)
    else:
        marks.append(index)

    await db.bingo_marks.update_one(
        {"user_id": user["id"], "card_id": card["id"]},
        {"$set": {"marks": marks, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    has_bingo = _check_bingo(marks)
    bingo_count = _count_bingos(marks)
    return {"marks": marks, "has_bingo": has_bingo, "bingo_count": bingo_count}


@router.get("/bingo/export")
async def export_bingo_card(user: Dict = Depends(require_auth)):
    card = await _get_or_create_weekly_card()
    user_marks = await db.bingo_marks.find_one({"user_id": user["id"], "card_id": card["id"]}, {"_id": 0})
    marks = user_marks.get("marks", [12]) if user_marks else [12]
    has_bingo = _check_bingo(marks)
    username = user.get("username", "collector")

    friday, sunday = _get_current_week()
    is_locked = datetime.now(timezone.utc) > sunday
    community_stats = await _get_community_stats(card["id"]) if is_locked else None

    image_bytes = _generate_bingo_image(card, marks, has_bingo, username, community_stats)
    return Response(content=image_bytes, media_type="image/png")


def _generate_bingo_image(card: dict, marks: list, has_bingo: bool, username: str, community_stats: dict = None) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1080, 1920
    BG = (250, 246, 238)
    AMBER = (200, 134, 26)
    TEXT_DARK = (42, 26, 6)
    TEXT_MUTED = (138, 107, 74)

    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    try:
        playfair_bold = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 48)
        playfair_sm = ImageFont.truetype(str(FONTS_DIR / "PlayfairDisplay-Bold2.ttf"), 28)
        cormorant_italic = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 22)
        cormorant_sm = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Regular2.ttf"), 24)
        cormorant_xs = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Italic2.ttf"), 18)
        emoji_font = ImageFont.truetype(str(FONTS_DIR / "CormorantGaramond-Regular2.ttf"), 28)
    except Exception:
        playfair_bold = ImageFont.load_default()
        playfair_sm = cormorant_italic = cormorant_sm = cormorant_xs = emoji_font = playfair_bold

    # Header
    title = "collector bingo"
    bbox = draw.textbbox((0, 0), title, font=playfair_bold)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 100), title, fill=TEXT_DARK, font=playfair_bold)

    try:
        ws = datetime.fromisoformat(card["week_start"])
        we = datetime.fromisoformat(card["week_end"])
        date_range = f"{ws.strftime('%b %d')} — {we.strftime('%b %d')}"
    except Exception:
        date_range = ""
    bbox = draw.textbbox((0, 0), date_range, font=cormorant_sm)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, 165), date_range, fill=TEXT_MUTED, font=cormorant_sm)

    # Bingo badge
    if has_bingo:
        badge_text = "BINGO 🍯"
        bbox = draw.textbbox((0, 0), badge_text, font=cormorant_sm)
        bw = bbox[2] - bbox[0] + 40
        bx = (W - bw) / 2
        draw.rounded_rectangle([(bx, 210), (bx + bw, 250)], radius=20, fill=AMBER)
        draw.text((bx + 20, 216), badge_text, fill=(255, 255, 255), font=cormorant_sm)

    # Grid
    grid_top = 290
    grid_size = 980
    cell = grid_size // 5
    grid_left = (W - grid_size) // 2
    marked_set = set(marks)
    percentages = community_stats.get("percentages", {}) if community_stats else {}

    for row in range(5):
        for col in range(5):
            idx = row * 5 + col
            sq = card["grid"][idx]
            x = grid_left + col * cell
            y = grid_top + row * cell
            is_marked = idx in marked_set

            overlay = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)

            if is_marked:
                od.rectangle([(0, 0), (cell, cell)], fill=(232, 168, 32, 64))
                od.rectangle([(0, 0), (cell - 1, cell - 1)], outline=AMBER)
            else:
                od.rectangle([(0, 0), (cell, cell)], fill=(255, 255, 255))
                od.rectangle([(0, 0), (cell - 1, cell - 1)], outline=(200, 134, 26, 38))

            img.paste(Image.alpha_composite(Image.new("RGBA", (cell, cell), (0, 0, 0, 0)), overlay), (x, y), overlay)

            # Text
            text = sq["text"]
            emoji = sq.get("emoji", "")
            if sq.get("is_free"):
                draw.text((x + cell // 2 - 14, y + cell // 2 - 42), "🍯", fill=TEXT_DARK, font=emoji_font)
                lines = textwrap.wrap("sweet spot", width=12)
                ty = y + cell // 2 - 4
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=cormorant_italic)
                    tw = bbox[2] - bbox[0]
                    draw.text((x + (cell - tw) // 2, ty), line, fill=AMBER, font=cormorant_italic)
                    ty += 24
            else:
                ty = y + 14
                if emoji:
                    bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
                    draw.text((x + (cell - (bbox[2] - bbox[0])) // 2, ty), emoji, fill=TEXT_DARK, font=emoji_font)
                    ty += 32
                lines = textwrap.wrap(text, width=14)
                for line in lines[:4]:
                    bbox = draw.textbbox((0, 0), line, font=cormorant_italic)
                    tw = bbox[2] - bbox[0]
                    draw.text((x + (cell - tw) // 2, ty), line, fill=TEXT_DARK if is_marked else TEXT_MUTED, font=cormorant_italic)
                    ty += 24

            # Community stat percentage (only when locked)
            pct = percentages.get(str(idx))
            if pct is not None and not sq.get("is_free"):
                stat_text = f"{pct}% of the hive"
                bbox = draw.textbbox((0, 0), stat_text, font=cormorant_xs)
                tw = bbox[2] - bbox[0]
                stat_overlay = Image.new("RGBA", (tw + 4, 20), (0, 0, 0, 0))
                sd = ImageDraw.Draw(stat_overlay)
                sd.text((0, 0), stat_text, fill=(138, 107, 74, 153), font=cormorant_xs)
                sx = x + (cell - tw) // 2
                sy = y + cell - 22
                img.paste(stat_overlay, (sx, sy), stat_overlay)

    # Footer area
    fy = grid_top + grid_size + 40
    handle = f"@{username}"
    bbox = draw.textbbox((0, 0), handle, font=cormorant_sm)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, fy), handle, fill=AMBER, font=cormorant_sm)

    hg = "the Honey Groove"
    bbox = draw.textbbox((0, 0), hg, font=cormorant_italic)
    draw.text(((W - (bbox[2] - bbox[0])) / 2, fy + 36), hg, fill=TEXT_MUTED, font=cormorant_italic)

    buf = BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ─── Admin ───

@router.get("/bingo/admin/squares")
async def admin_get_squares(user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    return await db.bingo_squares.find({}, {"_id": 0}).sort("created_at", 1).to_list(200)


@router.post("/bingo/admin/squares")
async def admin_add_square(data: dict, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    doc = {"id": str(uuid.uuid4()), "text": data["text"], "emoji": data.get("emoji", ""), "active": True, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.bingo_squares.insert_one({k: v for k, v in doc.items()})
    return doc


@router.put("/bingo/admin/squares/{square_id}")
async def admin_toggle_square(square_id: str, data: dict, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    update = {}
    if "active" in data:
        update["active"] = data["active"]
    if "text" in data:
        update["text"] = data["text"]
    if update:
        await db.bingo_squares.update_one({"id": square_id}, {"$set": update})
    return await db.bingo_squares.find_one({"id": square_id}, {"_id": 0})


async def generate_weekly_bingo():
    """Create the weekly bingo card (called from scheduler on Friday 9am UTC)."""
    card = await _get_or_create_weekly_card()
    users = await db.users.find({}, {"_id": 0, "id": 1}).to_list(10000)
    for u in users:
        await create_notification(u["id"], "BINGO", "collector bingo", "this week's bingo card is ready 🐝 how many can you check off?", {"card_id": card["id"]})
    logger.info("Bingo: weekly card created and notifications sent")
