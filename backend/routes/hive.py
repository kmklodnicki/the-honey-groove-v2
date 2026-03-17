from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import re

from database import db, require_auth, get_current_user, security, logger, create_notification, get_hidden_user_ids, get_all_blocked_ids
from services.email_service import send_email_fire_and_forget
import templates.emails as email_tpl
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, PLATFORM_FEE_PERCENT, FRONTEND_URL
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from live_hive import emit_new_post
from database import oauth_request_tokens, import_progress, EMERGENT_KEY
from models import *
from io import BytesIO
from util.content_filter import detect_offplatform_payment, detect_profanity

router = APIRouter()


async def _shadow_flag_post(post_doc: dict, user: dict):
    """Check a post for off-platform payment or profanity content.
    If detected, auto-create an admin report with 'Reviewing' status."""
    text = (post_doc.get("caption") or post_doc.get("text") or "").strip()
    if not text:
        return

    payment_flagged, payment_kws = detect_offplatform_payment(text)
    profanity_flagged, profanity_kws = detect_profanity(text)

    if not payment_flagged and not profanity_flagged:
        return

    reasons = []
    if payment_flagged:
        reasons.append(f"Off-platform payment detected: {', '.join(payment_kws)}")
    if profanity_flagged:
        reasons.append(f"Profanity detected: {', '.join(profanity_kws)}")

    now = datetime.now(timezone.utc).isoformat()
    report_doc = {
        "id": str(uuid.uuid4()),
        "type": "auto_moderation",
        "reporter_id": "system",
        "reported_user_id": user.get("id"),
        "post_id": post_doc.get("id"),
        "reason": "; ".join(reasons),
        "details": f"Auto-flagged by content filter. Post text: {text[:300]}",
        "status": "Reviewing",
        "created_at": now,
    }
    await db.reports.insert_one(report_doc)

    # Also flag the post itself
    await db.posts.update_one(
        {"id": post_doc["id"]},
        {"$set": {"shadow_flagged": True, "flag_reasons": reasons}}
    )

def generate_share_graphic(graphic_type: str, data: Dict, format_type: str = "square") -> bytes:
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Set dimensions based on format
        if format_type == "story":
            width, height = 1080, 1920
        else:
            width, height = 1080, 1080
        
        # HoneyGroove Colors
        bg_cream = (255, 246, 230)  # Cream background
        honey = (244, 185, 66)  # Primary honey gold
        honey_soft = (249, 215, 118)  # Soft honey
        amber = (217, 140, 47)  # Warm amber
        black = (31, 31, 31)  # Vinyl black text
        white = (255, 255, 255)
        
        img = Image.new('RGB', (width, height), bg_cream)
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts, fallback to default
        try:
            if format_type == "story":
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 72)
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
                body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
            else:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 56)
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
                body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = title_font
            body_font = title_font
            small_font = title_font
        
        # Draw honeycomb pattern in background (subtle hexagons)
        def draw_hexagon(draw, x, y, size, color):
            import math
            points = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                px = x + size * math.cos(angle)
                py = y + size * math.sin(angle)
                points.append((px, py))
            draw.polygon(points, outline=color)
        
        # Draw subtle honeycomb pattern
        for row in range(0, height + 60, 60):
            offset = 35 if (row // 60) % 2 else 0
            for col in range(-30 + offset, width + 60, 70):
                draw_hexagon(draw, col, row, 20, (*honey, 40))
        
        # Draw header bar
        header_height = 220 if format_type == "story" else 180
        draw.rectangle([0, 0, width, header_height], fill=honey)
        
        # Draw footer bar
        footer_height = 100 if format_type == "story" else 80
        draw.rectangle([0, height-footer_height, width, height], fill=honey)
        
        if graphic_type == "now_spinning":
            # Header
            header_y = 110 if format_type == "story" else 90
            draw.text((width//2, header_y), "NOW SPINNING", font=title_font, fill=black, anchor="mm")
            
            # Album info
            artist = data.get("artist", "Unknown Artist")
            album = data.get("title", "Unknown Album")
            
            if format_type == "story":
                # Story format - larger vinyl, more space
                center_y = 850
                vinyl_size = 350
                
                # Outer vinyl
                draw.ellipse([width//2-vinyl_size, center_y-vinyl_size, width//2+vinyl_size, center_y+vinyl_size], fill=(18, 18, 18))
                # Grooves
                for r in range(300, 80, -40):
                    draw.ellipse([width//2-r, center_y-r, width//2+r, center_y+r], outline=(40, 40, 40), width=1)
                # Label (honey colored)
                draw.ellipse([width//2-80, center_y-80, width//2+80, center_y+80], fill=honey)
                draw.ellipse([width//2-55, center_y-55, width//2+55, center_y+55], fill=amber)
                draw.ellipse([width//2-20, center_y-20, width//2+20, center_y+20], fill=black)
                
                # Artist and album text
                draw.text((width//2, 1400), artist, font=subtitle_font, fill=black, anchor="mm")
                draw.text((width//2, 1500), album, font=body_font, fill=amber, anchor="mm")
                
                # Decorative bees
                bee_positions = [(150, 400), (930, 400), (150, 1650), (930, 1650)]
                for bx, by in bee_positions:
                    draw.ellipse([bx-12, by-8, bx+12, by+8], fill=black)
                    draw.ellipse([bx-6, by-4, bx+6, by+4], fill=honey_soft)
            else:
                # Square format
                center_y = 520
                draw.ellipse([290, center_y-250, 790, center_y+250], fill=(18, 18, 18))
                for r in range(200, 50, -30):
                    draw.ellipse([540-r, center_y-r, 540+r, center_y+r], outline=(40, 40, 40), width=1)
                draw.ellipse([480, center_y-60, 600, center_y+60], fill=honey)
                draw.ellipse([500, center_y-40, 580, center_y+40], fill=amber)
                draw.ellipse([525, center_y-15, 555, center_y+15], fill=black)
                
                draw.text((width//2, 830), artist, font=subtitle_font, fill=black, anchor="mm")
                draw.text((width//2, 890), album, font=body_font, fill=amber, anchor="mm")
            
        elif graphic_type == "new_haul":
            header_y = 110 if format_type == "story" else 90
            draw.text((width//2, header_y), "NEW HAUL", font=title_font, fill=black, anchor="mm")
            
            title = data.get("title", "My Vinyl Haul")
            items = data.get("items", [])
            count = len(items)
            
            if format_type == "story":
                # Decorative hexagon with count
                draw.regular_polygon(((540, 500), 120), 6, fill=honey_soft, outline=amber)
                draw.text((540, 480), str(count), font=title_font, fill=black, anchor="mm")
                draw.text((540, 560), "RECORDS", font=small_font, fill=amber, anchor="mm")
                
                draw.text((width//2, 720), title, font=subtitle_font, fill=black, anchor="mm")
                
                # List items with more space
                y_pos = 850
                for i, item in enumerate(items[:8]):
                    text = f"{item.get('artist', '')} - {item.get('title', '')}"
                    if len(text) > 40:
                        text = text[:37] + "..."
                    draw.text((width//2, y_pos), text, font=body_font, fill=black, anchor="mm")
                    y_pos += 70
                
                if count > 8:
                    draw.text((width//2, y_pos), f"+ {count - 8} more...", font=body_font, fill=amber, anchor="mm")
            else:
                draw.regular_polygon(((540, 350), 80), 6, fill=honey_soft, outline=amber)
                draw.text((540, 350), str(count), font=title_font, fill=black, anchor="mm")
                
                draw.text((width//2, 480), title, font=subtitle_font, fill=black, anchor="mm")
                draw.text((width//2, 540), "records added", font=body_font, fill=amber, anchor="mm")
                
                y_pos = 620
                for i, item in enumerate(items[:4]):
                    text = f"{item.get('artist', '')} - {item.get('title', '')}"
                    if len(text) > 42:
                        text = text[:39] + "..."
                    draw.text((width//2, y_pos), text, font=small_font, fill=black, anchor="mm")
                    y_pos += 45
                
                if count > 4:
                    draw.text((width//2, y_pos), f"+ {count - 4} more...", font=small_font, fill=amber, anchor="mm")
                
        elif graphic_type == "weekly_summary":
            header_y = 110 if format_type == "story" else 90
            draw.text((width//2, header_y), "HONEY GROOVE WEEKLY", font=title_font, fill=black, anchor="mm")
            
            spins = data.get("total_spins", 0)
            top_artist = data.get("top_artist", "No data")
            top_album = data.get("top_album", "No data")
            mood = data.get("listening_mood", "Eclectic")
            
            if format_type == "story":
                # Big spin count with hexagon background
                draw.regular_polygon(((540, 480), 140), 6, fill=honey_soft, outline=amber)
                draw.text((540, 450), str(spins), font=title_font, fill=black, anchor="mm")
                draw.text((540, 530), "SPINS", font=body_font, fill=amber, anchor="mm")
                
                # Stats cards - stacked vertically
                card_width = 800
                card_x = (width - card_width) // 2
                
                # Top Artist card
                draw.rounded_rectangle([card_x, 700, card_x+card_width, 850], radius=25, fill=white, outline=honey)
                draw.text((width//2, 740), "TOP ARTIST", font=small_font, fill=amber, anchor="mm")
                artist_text = top_artist if len(str(top_artist)) < 30 else str(top_artist)[:27] + "..."
                draw.text((width//2, 800), artist_text, font=subtitle_font, fill=black, anchor="mm")
                
                # Top Album card
                draw.rounded_rectangle([card_x, 900, card_x+card_width, 1050], radius=25, fill=white, outline=honey)
                draw.text((width//2, 940), "TOP ALBUM", font=small_font, fill=amber, anchor="mm")
                album_text = top_album if top_album and len(str(top_album)) < 30 else (str(top_album)[:27] + "..." if top_album else "N/A")
                draw.text((width//2, 1000), album_text, font=subtitle_font, fill=black, anchor="mm")
                
                # Mood card
                draw.rounded_rectangle([card_x, 1100, card_x+card_width, 1280], radius=25, fill=honey_soft, outline=amber)
                draw.text((width//2, 1150), "LISTENING MOOD", font=small_font, fill=amber, anchor="mm")
                draw.text((width//2, 1220), mood, font=subtitle_font, fill=black, anchor="mm")
                
                # Decorative bees
                bee_positions = [(150, 350), (930, 350), (150, 1500), (930, 1500)]
                for bx, by in bee_positions:
                    draw.ellipse([bx-12, by-8, bx+12, by+8], fill=black)
                    draw.ellipse([bx-6, by-4, bx+6, by+4], fill=honey_soft)
            else:
                draw.regular_polygon(((540, 320), 100), 6, fill=honey_soft, outline=amber)
                draw.text((540, 300), str(spins), font=title_font, fill=black, anchor="mm")
                draw.text((540, 360), "SPINS", font=small_font, fill=amber, anchor="mm")
                
                card_y = 520
                draw.rounded_rectangle([100, card_y, 500, card_y+120], radius=20, fill=white, outline=honey)
                draw.text((300, card_y+30), "TOP ARTIST", font=small_font, fill=amber, anchor="mm")
                artist_text = top_artist if len(str(top_artist)) < 25 else str(top_artist)[:22] + "..."
                draw.text((300, card_y+75), artist_text, font=body_font, fill=black, anchor="mm")
                
                draw.rounded_rectangle([580, card_y, 980, card_y+120], radius=20, fill=white, outline=honey)
                draw.text((780, card_y+30), "TOP ALBUM", font=small_font, fill=amber, anchor="mm")
                album_text = top_album if top_album and len(str(top_album)) < 25 else (str(top_album)[:22] + "..." if top_album else "N/A")
                draw.text((780, card_y+75), album_text, font=body_font, fill=black, anchor="mm")
                
                draw.rounded_rectangle([250, 700, 830, 800], radius=20, fill=honey_soft, outline=amber)
                draw.text((540, 730), "LISTENING MOOD", font=small_font, fill=amber, anchor="mm")
                draw.text((540, 770), mood, font=subtitle_font, fill=black, anchor="mm")
        
        # HoneyGroove branding
        footer_y = height - 50 if format_type == "story" else height - 40
        draw.text((width//2, footer_y), "the honey groove", font=body_font, fill=black, anchor="mm")
        
        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', quality=95)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate image")


async def _emit_and_return(post_response, user_id: str):
    """Emit NEW_POST via Socket.IO and return the PostResponse."""
    if post_response:
        try:
            await emit_new_post(post_response.dict(), user_id)
        except Exception as e:
            logger.warning(f"Socket emit failed (non-blocking): {e}")
    return post_response




# ============== FEED/POSTS ROUTES ==============

def normalize_post_type(post_type: str) -> str:
    """Map legacy post types to new enum values"""
    return POST_TYPE_MAP.get(post_type, post_type)

async def build_post_response(post: Dict, current_user_id: Optional[str] = None):
    """Build a full post response with user, record, haul, iso data. Returns None for blank/invalid posts."""
    # Skip blank ISO posts (no iso data, no caption, no content)
    pt = post.get("post_type", "")
    if pt == "ISO" and not post.get("caption") and not post.get("content"):
        iso = await db.iso_items.find_one({"id": post.get("iso_id", "")}, {"_id": 0})
        if not iso or (not iso.get("artist", "").strip() and not iso.get("album", "").strip()):
            return None
    # Skip blank listing posts with no album info
    if pt in ("listing_sale", "listing_trade") and not post.get("record_title") and not post.get("content"):
        return None

    post_user = await db.users.find_one({"id": post["user_id"]}, {"_id": 0, "password_hash": 0})
    user_data = {"id": post_user["id"], "username": post_user["username"], "avatar_url": post_user.get("avatar_url"), "founding_member": post_user.get("founding_member", False), "title_label": post_user.get("title_label"), "golden_hive_verified": post_user.get("golden_hive_verified", False)} if post_user else None
    
    record_data = None
    record_color_variant = None
    if post.get("record_id"):
        record = await db.records.find_one({"id": post["record_id"]}, {"_id": 0})
        if record:
            record_color_variant = record.get("color_variant")
            record_data = record
            # Hydrate missing post-level record fields from the actual record
            if not post.get("record_title") and record.get("title"):
                post["record_title"] = record["title"]
            if not post.get("record_artist") and record.get("artist"):
                post["record_artist"] = record["artist"]
            if not post.get("cover_url") and record.get("cover_url"):
                post["cover_url"] = record["cover_url"]
        else:
            # Record was deleted — skip ghost post if it has no usable data
            if not post.get("record_title"):
                return None
    
    haul_data = None
    if post.get("haul_id"):
        haul = await db.hauls.find_one({"id": post["haul_id"]}, {"_id": 0})
        if haul:
            # Hydrate missing cover_url for haul items from records collection
            items = haul.get("items", [])
            for item in items:
                if not item.get("cover_url") and item.get("discogs_id"):
                    rec = await db.records.find_one({"discogs_id": item["discogs_id"]}, {"_id": 0, "cover_url": 1})
                    if rec and rec.get("cover_url"):
                        item["cover_url"] = rec["cover_url"]
        haul_data = haul

    # Hydrate cover_url for auto-bundle records
    bundle = post.get("bundle_records")
    if bundle:
        # First pass: try records collection
        for item in bundle:
            if not item.get("cover_url"):
                if item.get("record_id"):
                    rec = await db.records.find_one({"id": item["record_id"]}, {"_id": 0, "cover_url": 1})
                    if rec and rec.get("cover_url"):
                        item["cover_url"] = rec["cover_url"]
                elif item.get("discogs_id"):
                    rec = await db.records.find_one({"discogs_id": item["discogs_id"]}, {"_id": 0, "cover_url": 1})
                    if rec and rec.get("cover_url"):
                        item["cover_url"] = rec["cover_url"]
        # Second pass: Discogs API fallback for still-missing covers
        for item in bundle:
            if not item.get("cover_url") and item.get("discogs_id"):
                try:
                    from routes.vinyl import _get_cached_discogs_release
                    discogs = await _get_cached_discogs_release(item["discogs_id"])
                    if discogs and discogs.get("cover_url"):
                        item["cover_url"] = discogs["cover_url"]
                        # Persist to records collection so future loads are instant
                        await db.records.update_many(
                            {"discogs_id": item["discogs_id"], "$or": [{"cover_url": None}, {"cover_url": ""}]},
                            {"$set": {"cover_url": discogs["cover_url"]}}
                        )
                except Exception as e:
                    logger.warning(f"Bundle cover hydration failed for discogs_id {item.get('discogs_id')}: {e}")
        # Third pass: fallback to any sibling cover in the same bundle (same album)
        fallback_cover = next((i.get("cover_url") for i in bundle if i.get("cover_url")), None)
        if fallback_cover:
            for item in bundle:
                if not item.get("cover_url"):
                    item["cover_url"] = fallback_cover
    
    iso_data = None
    iso_color_variant = None
    if post.get("iso_id"):
        iso = await db.iso_items.find_one({"id": post["iso_id"]}, {"_id": 0})
        iso_data = iso
        if iso:
            iso_color_variant = iso.get("color_variant")
            # Hydrate missing cover_url from Discogs or records collection
            if not iso.get("cover_url") and iso.get("discogs_id"):
                try:
                    from routes.vinyl import _get_cached_discogs_release
                    discogs = await _get_cached_discogs_release(iso["discogs_id"])
                    if discogs and discogs.get("cover_url"):
                        iso["cover_url"] = discogs["cover_url"]
                        # Persist so we don't re-fetch next time
                        await db.iso_items.update_one(
                            {"id": iso["id"]},
                            {"$set": {"cover_url": discogs["cover_url"]}}
                        )
                except Exception as e:
                    logger.warning(f"ISO cover_url hydration failed for {iso.get('id')}: {e}")
            if not iso.get("cover_url"):
                # Fallback: check records collection
                rec = await db.records.find_one({"discogs_id": iso.get("discogs_id")}, {"_id": 0, "cover_url": 1})
                if rec and rec.get("cover_url"):
                    iso["cover_url"] = rec["cover_url"]
            if not iso.get("cover_url") and iso.get("artist") and iso.get("album"):
                # Fallback: check discogs_releases for any sibling with same artist+title
                import re as _re
                sibling_dr = await db.discogs_releases.find_one(
                    {"artist": {"$regex": f"^{_re.escape(iso['artist'])}$", "$options": "i"},
                     "title": {"$regex": f"^{_re.escape(iso['album'])}$", "$options": "i"},
                     "cover_url": {"$nin": [None, ""]}},
                    {"_id": 0, "cover_url": 1}
                )
                if sibling_dr and sibling_dr.get("cover_url"):
                    iso["cover_url"] = sibling_dr["cover_url"]
            iso_data = iso
    
    # Resolve color_variant: post-level > record-level > iso-level
    resolved_color_variant = post.get("color_variant") or record_color_variant or iso_color_variant
    
    likes_count = await db.likes.count_documents({"post_id": post["id"]})
    comments_count = await db.comments.count_documents({"post_id": post["id"]})
    
    is_liked = False
    if current_user_id:
        is_liked = await db.likes.find_one({"post_id": post["id"], "user_id": current_user_id}) is not None
    
    # Normalize post type
    pt = normalize_post_type(post.get("post_type", ""))

    # Poll vote data
    poll_total = 0
    poll_user_vote = None
    poll_results = None
    if pt == "POLL":
        poll_total = await db.poll_votes.count_documents({"post_id": post["id"]})
        if current_user_id:
            my_vote = await db.poll_votes.find_one({"post_id": post["id"], "user_id": current_user_id}, {"_id": 0, "option_index": 1})
            if my_vote:
                poll_user_vote = my_vote["option_index"]
                # Include per-option results for voters
                pipeline = [
                    {"$match": {"post_id": post["id"]}},
                    {"$group": {"_id": "$option_index", "count": {"$sum": 1}}},
                ]
                agg = await db.poll_votes.aggregate(pipeline).to_list(20)
                vote_map = {r["_id"]: r["count"] for r in agg}
                poll_results = []
                for i, opt in enumerate(post.get("poll_options", [])):
                    c = vote_map.get(i, 0)
                    poll_results.append({"option": opt, "count": c, "percentage": round(c / poll_total * 100) if poll_total else 0})

    return PostResponse(
        id=post["id"],
        user_id=post["user_id"],
        post_type=pt,
        caption=post.get("caption") or post.get("content"),
        image_url=post.get("image_url"),
        photo_url=post.get("photo_url") or post.get("image_url"),
        share_card_square_url=post.get("share_card_square_url"),
        share_card_story_url=post.get("share_card_story_url"),
        record_id=post.get("record_id"),
        haul_id=post.get("haul_id"),
        listing_id=post.get("listing_id"),
        iso_id=post.get("iso_id"),
        weekly_wrap_id=post.get("weekly_wrap_id"),
        track=post.get("track"),
        mood=post.get("mood"),
        prompt_text=post.get("prompt_text"),
        record_title=post.get("record_title"),
        record_artist=post.get("record_artist"),
        cover_url=post.get("cover_url"),
        color_variant=resolved_color_variant,
        pressing_notes=post.get("pressing_notes"),
        created_at=post["created_at"],
        likes_count=likes_count,
        comments_count=comments_count,
        user=user_data,
        record=record_data,
        haul=haul_data,
        iso=iso_data,
        is_liked=is_liked,
        is_pinned=post.get("is_pinned", False),
        is_new_feature=post.get("is_new_feature", False),
        is_release_note=post.get("is_release_note", False),
        content=post.get("content"),
        intent=post.get("intent"),
        bundle_records=post.get("bundle_records"),
        poll_question=post.get("poll_question"),
        poll_options=post.get("poll_options"),
        poll_total_votes=poll_total,
        poll_user_vote=poll_user_vote,
        poll_results=poll_results,
        record_format=record_data.get("format") if record_data else post.get("record_format"),
    )

@router.get("/feed")
async def get_feed(user: Dict = Depends(require_auth), limit: int = 20, skip: int = 0, before: Optional[str] = None, after: Optional[str] = None, post_type: Optional[str] = None):
    try:
        hidden_ids = await get_hidden_user_ids()
        blocked_ids = await get_all_blocked_ids(user["id"])
        exclude_ids = list(set(hidden_ids + blocked_ids))

        # Fetch pinned post first (if any) — only include if it matches the filter
        pinned_post = await db.posts.find_one({"is_pinned": True}, {"_id": 0})
        pinned_resp = None
        if pinned_post and pinned_post.get("user_id") not in exclude_ids:
            if not post_type:
                pinned_resp = await build_post_response(pinned_post, user["id"])
            else:
                pt_upper = post_type.upper()
                pinned_pt = (pinned_post.get("post_type") or "").upper()
                if pt_upper == "NOW_SPINNING" and pinned_pt in ("NOW_SPINNING", "RANDOMIZER"):
                    pinned_resp = await build_post_response(pinned_post, user["id"])
                elif pt_upper == "LISTING" and pinned_pt in ("listing_sale", "listing_trade"):
                    pinned_resp = await build_post_response(pinned_post, user["id"])
                elif pt_upper == "RELEASE_NOTE" and pinned_post.get("is_release_note"):
                    pinned_resp = await build_post_response(pinned_post, user["id"])
                elif pinned_pt == pt_upper:
                    pinned_resp = await build_post_response(pinned_post, user["id"])

        query = {"is_pinned": {"$ne": True}, "source": {"$ne": "discogs_import"}}
        if exclude_ids:
            query["user_id"] = {"$nin": exclude_ids}
        if before:
            query["created_at"] = {"$lt": before}
        if after:
            query.setdefault("created_at", {})
            query["created_at"]["$gt"] = after

        # Server-side post_type filtering
        if post_type:
            pt_upper = post_type.upper()
            if pt_upper == "NOW_SPINNING":
                query["post_type"] = {"$in": ["NOW_SPINNING", "RANDOMIZER"]}
            elif pt_upper == "LISTING":
                query["post_type"] = {"$in": ["listing_sale", "listing_trade"]}
            elif pt_upper == "RELEASE_NOTE":
                query["is_release_note"] = True
            else:
                query["post_type"] = pt_upper

        # Allowed post types in the Hive feed
        ALLOWED_TYPES = {"NOW_SPINNING", "NEW_HAUL", "ISO", "RANDOMIZER", "DAILY_PROMPT", "NOTE", "POLL"}

        # Over-fetch to compensate for Python-side filtering, then trim to limit
        result = []
        if pinned_resp and not before and skip == 0:
            result.append(pinned_resp)

        batch_size = limit * 4
        current_skip = skip
        max_iterations = 5
        for _ in range(max_iterations):
            if len(result) >= limit:
                break
            posts = await db.posts.find(
                query, {"_id": 0}
            ).sort("created_at", -1).skip(current_skip).limit(batch_size).to_list(batch_size)
            if not posts:
                break
            for post in posts:
                if len(result) >= limit + 1:
                    break
                try:
                    pt = (post.get("post_type") or "").upper()
                    caption = (post.get("caption") or post.get("content") or "").strip()
                    if pt and pt not in ALLOWED_TYPES:
                        continue
                    if pt in ("NOW_SPINNING", "NEW_HAUL", "RANDOMIZER") and not caption:
                        continue
                    resp = await build_post_response(post, user["id"])
                    if resp:
                        result.append(resp)
                except Exception as e:
                    logger.error(f"build_post_response failed for post {post.get('id', '?')}: {e}")
            current_skip += batch_size
            if len(posts) < batch_size:
                break

        # If we collected more than limit, there are more posts available
        # Trim to exactly limit
        if len(result) > limit:
            result = result[:limit]

        return result
    except Exception as e:
        logger.error(f"GET /feed FATAL: {type(e).__name__}: {e}")
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"error": "DB_CONNECTION_LOST", "detail": str(e)[:200]})

@router.get("/explore", response_model=List[PostResponse])
async def get_explore_feed(current_user: Optional[Dict] = Depends(get_current_user), limit: int = 50, skip: int = 0):
    hidden_ids = await get_hidden_user_ids()
    blocked_ids = await get_all_blocked_ids(current_user["id"]) if current_user else []
    exclude_ids = list(set(hidden_ids + blocked_ids))
    query = {"user_id": {"$nin": exclude_ids}, "source": {"$ne": "discogs_import"}} if exclude_ids else {"source": {"$ne": "discogs_import"}}
    posts = await db.posts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    ALLOWED_TYPES = {"NOW_SPINNING", "NEW_HAUL", "ISO", "RANDOMIZER", "DAILY_PROMPT", "NOTE", "POLL"}
    
    result = []
    for post in posts:
        uid = current_user["id"] if current_user else None
        pt = (post.get("post_type") or "").upper()
        caption = (post.get("caption") or post.get("content") or "").strip()
        if pt and pt not in ALLOWED_TYPES:
            continue
        if pt in ("NOW_SPINNING", "NEW_HAUL", "RANDOMIZER") and not caption:
            continue
        resp = await build_post_response(post, uid)
        if resp:
            result.append(resp)
    
    return result



@router.get("/collection/random")
async def get_random_record(user: Dict = Depends(require_auth)):
    """Return a random record from the user's owned collection (excludes wishlists/ISOs)."""
    pipeline = [
        {"$match": {"user_id": user["id"], "source": {"$nin": ["wantlist", "dreamlist", "iso"]}}},
        {"$sample": {"size": 1}},
        {"$project": {"_id": 0}},
    ]
    results = await db.records.aggregate(pipeline).to_list(1)
    if not results:
        raise HTTPException(status_code=404, detail="No records in your collection")
    return results[0]


# ============== COMPOSER ENDPOINTS (one-shot post creation) ==============

@router.post("/composer/now-spinning", response_model=PostResponse)
async def composer_now_spinning(data: NowSpinningCreate, user: Dict = Depends(require_auth)):
    """Create a Now Spinning post + log a spin in one flow"""
    record = await db.records.find_one({"id": data.record_id, "user_id": user["id"]}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found in your collection")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Log the spin
    spin_id = str(uuid.uuid4())
    await db.spins.insert_one({
        "id": spin_id,
        "user_id": user["id"],
        "record_id": data.record_id,
        "notes": data.track,
        "caption": data.caption,
        "mood": data.mood,
        "created_at": now
    })
    
    # Create post only if user wants to post to Hive
    post_doc = None
    if data.post_to_hive:
        post_id = str(uuid.uuid4())
        post_doc = {
            "id": post_id,
            "user_id": user["id"],
            "post_type": "NOW_SPINNING",
            "caption": data.caption,
            "record_id": data.record_id,
            "track": data.track,
            "mood": data.mood,
            "image_url": data.photo_url,
            "photo_url": data.photo_url,
            "spin_id": spin_id,
            "color_variant": record.get("color_variant") or record.get("pressing_notes"),
            "created_at": now
        }
        await db.posts.insert_one(post_doc)
        await parse_and_notify_mentions(post_doc.get("caption", ""), post_doc["id"], user["id"])
        await _shadow_flag_post(post_doc, user)
    
    if post_doc:
        return await _emit_and_return(await build_post_response(post_doc, user["id"]), user["id"])
    else:
        # Return a minimal response for silent spins
        return await build_post_response({
            "id": spin_id,
            "user_id": user["id"],
            "post_type": "NOW_SPINNING",
            "caption": data.caption or f"Spinning {record['title']} by {record['artist']}",
            "record_id": data.record_id,
            "spin_id": spin_id,
            "color_variant": record.get("color_variant") or record.get("pressing_notes"),
            "created_at": now,
            "_silent": True,
        }, user["id"])

@router.post("/composer/randomizer", response_model=PostResponse)
async def composer_randomizer(data: NowSpinningCreate, user: Dict = Depends(require_auth)):
    """Create a Randomizer post – a playful, spontaneous discovery post."""
    record = await db.records.find_one({"id": data.record_id, "user_id": user["id"]}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found in your collection")
    now = datetime.now(timezone.utc).isoformat()
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "RANDOMIZER",
        "caption": data.caption,
        "record_id": data.record_id,
        "color_variant": record.get("color_variant") or record.get("pressing_notes"),
        "created_at": now,
    }
    await db.posts.insert_one(post_doc)
    await parse_and_notify_mentions(post_doc.get("caption", ""), post_doc["id"], user["id"])
    await _shadow_flag_post(post_doc, user)
    return await _emit_and_return(await build_post_response(post_doc, user["id"]), user["id"])



@router.post("/composer/new-haul", response_model=PostResponse)
async def composer_new_haul(data: NewHaulCreate, user: Dict = Depends(require_auth)):
    """Create a New Haul post + add records to collection in one flow"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Add each record to collection and build haul items
    items_with_ids = []
    for item in data.items:
        record_id = str(uuid.uuid4())
        record_doc = {
            "id": record_id,
            "user_id": user["id"],
            "discogs_id": item.discogs_id,
            "title": item.title,
            "artist": item.artist,
            "cover_url": item.cover_url,
            "year": item.year,
            "format": getattr(item, 'format', None) or "Vinyl",
            "notes": item.notes,
            "source": "haul",
            "created_at": now
        }
        await db.records.insert_one(record_doc)
        items_with_ids.append({**item.model_dump(), "record_id": record_id})
    
    # Create haul
    haul_id = str(uuid.uuid4())
    haul_doc = {
        "id": haul_id,
        "user_id": user["id"],
        "store_name": data.store_name,
        "title": data.store_name or "New Haul",
        "description": data.caption,
        "image_url": data.image_url,
        "items": items_with_ids,
        "purchased_at": now,
        "created_at": now
    }
    await db.hauls.insert_one(haul_doc)
    
    # Only create a Hive post if user wants to share
    if data.post_to_hive:
        post_id = str(uuid.uuid4())
        post_doc = {
            "id": post_id,
            "user_id": user["id"],
            "post_type": "NEW_HAUL",
            "caption": data.caption,
            "image_url": data.image_url,
            "haul_id": haul_id,
            "created_at": now
        }
        await db.posts.insert_one(post_doc)
        await parse_and_notify_mentions(post_doc.get("caption", ""), post_doc["id"], user["id"])
        await _shadow_flag_post(post_doc, user)
        return await _emit_and_return(await build_post_response(post_doc, user["id"]), user["id"])
    
    # Silent haul — return a minimal response (records added to vault, no post)
    return {
        "id": haul_id, "user_id": user["id"], "post_type": "NEW_HAUL",
        "caption": data.caption or "", "created_at": now,
        "user": {"id": user["id"], "username": user.get("username", "")},
        "likes_count": 0, "comments_count": 0, "is_liked": False,
    }

@router.post("/composer/iso", response_model=PostResponse)
async def composer_iso(data: ISOPostCreate, user: Dict = Depends(require_auth)):
    """Create an ISO (In Search Of) post in one flow"""
    if not data.artist.strip() or not data.album.strip():
        raise HTTPException(status_code=400, detail="Artist and album are required for ISO posts")
    now = datetime.now(timezone.utc).isoformat()
    
    # Create ISO item — route status based on intent
    is_dreaming = data.intent == "dreaming"
    iso_id = str(uuid.uuid4())

    # Auto-populate cover_url and discogs_id if missing but artist+album given
    resolved_cover_url = data.cover_url
    resolved_discogs_id = data.discogs_id
    if not resolved_discogs_id and data.artist and data.album:
        try:
            import asyncio
            results = await asyncio.to_thread(search_discogs, f"{data.artist} {data.album}")
            if results:
                best = results[0]
                resolved_discogs_id = best.get("discogs_id")
                if not resolved_cover_url:
                    resolved_cover_url = best.get("cover_url")
                if not data.color_variant and best.get("color_variant"):
                    data.color_variant = best["color_variant"]
        except Exception as e:
            logger.warning(f"Discogs auto-lookup for ISO failed: {e}")

    # BLOCK 592: Check Discogs for "Unofficial Release" format
    is_unofficial = False
    discogs_color_variant = None
    if resolved_discogs_id:
        release_info = get_discogs_release(resolved_discogs_id)
        if release_info:
            is_unofficial = "Unofficial Release" in release_info.get("format_descriptions", [])
            discogs_color_variant = release_info.get("color_variant")
            if not resolved_cover_url and release_info.get("cover_url"):
                resolved_cover_url = release_info["cover_url"]

    # Resolve color_variant: explicit from user > Discogs > None
    resolved_color_variant = data.color_variant or discogs_color_variant

    iso_doc = {
        "id": iso_id,
        "user_id": user["id"],
        "artist": data.artist,
        "album": data.album,
        "discogs_id": resolved_discogs_id,
        "cover_url": resolved_cover_url,
        "year": data.year,
        "color_variant": resolved_color_variant,
        "pressing_notes": data.pressing_notes,
        "condition_pref": data.condition_pref,
        "tags": data.tags or [],
        "target_price_min": data.target_price_min,
        "target_price_max": data.target_price_max,
        "is_unofficial": is_unofficial,
        "status": "WISHLIST" if is_dreaming else "OPEN",
        "priority": "LOW" if is_dreaming else "MED",
        "created_at": now
    }
    await db.iso_items.insert_one(iso_doc)
    
    # Only create a Hive post if user wants to share
    if data.post_to_hive:
        post_id = str(uuid.uuid4())
        post_doc = {
            "id": post_id,
            "user_id": user["id"],
            "post_type": "ISO",
            "caption": data.caption,
            "iso_id": iso_id,
            "intent": data.intent or "seeking",
            "created_at": now
        }
        await db.posts.insert_one(post_doc)
        await parse_and_notify_mentions(post_doc.get("caption", ""), post_doc["id"], user["id"])
        await _shadow_flag_post(post_doc, user)
        return await _emit_and_return(await build_post_response(post_doc, user["id"]), user["id"])
    
    # Silent ISO — return minimal response
    return {
        "id": iso_id, "user_id": user["id"], "post_type": "ISO",
        "caption": data.caption or "", "created_at": now,
        "user": {"id": user["id"], "username": user.get("username", "")},
        "likes_count": 0, "comments_count": 0, "is_liked": False,
    }

@router.post("/composer/vinyl-mood", response_model=PostResponse)
async def composer_vinyl_mood(data: VinylMoodCreate, user: Dict = Depends(require_auth)):
    """Create a Vinyl Mood post"""
    now = datetime.now(timezone.utc).isoformat()
    
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "VINYL_MOOD",
        "caption": data.caption,
        "mood": data.mood,
        "record_id": data.record_id,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    await parse_and_notify_mentions(post_doc.get("caption", ""), post_doc["id"], user["id"])
    await _shadow_flag_post(post_doc, user)
    
    return await _emit_and_return(await build_post_response(post_doc, user["id"]), user["id"])


@router.post("/composer/note", response_model=PostResponse)
async def composer_note(data: NoteCreate, user: Dict = Depends(require_auth)):
    """Create a free-form text Note post"""
    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    # Admin users have no character limit (for Change Logs)
    if len(data.text) > 1500 and not user.get("is_admin"):
        raise HTTPException(status_code=400, detail="Text must be 1500 characters or less")

    now = datetime.now(timezone.utc).isoformat()

    # Validate record if tagged
    if data.record_id:
        record = await db.records.find_one({"id": data.record_id, "user_id": user["id"]}, {"_id": 0})
        if not record:
            raise HTTPException(status_code=404, detail="Record not found in your collection")

    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "NOTE",
        "caption": data.text.strip(),
        "record_id": data.record_id,
        "image_url": data.image_url,
        "created_at": now,
    }
    await db.posts.insert_one(post_doc)
    await parse_and_notify_mentions(post_doc.get("caption", "") or post_doc.get("text", ""), post_doc["id"], user["id"])
    await _shadow_flag_post(post_doc, user)
    return await _emit_and_return(await build_post_response(post_doc, user["id"]), user["id"])


# ============== POLL ROUTES ==============

@router.post("/composer/poll", response_model=PostResponse)
async def composer_poll(data: PollCreate, user: Dict = Depends(require_auth)):
    """Create a Poll post"""
    question = data.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question must be 500 characters or less")
    options = [o.strip() for o in data.options if o.strip()]
    if len(options) < 2:
        raise HTTPException(status_code=400, detail="At least 2 options are required")
    if len(options) > 6:
        raise HTTPException(status_code=400, detail="Maximum 6 options allowed")

    now = datetime.now(timezone.utc).isoformat()
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "POLL",
        "caption": question,
        "poll_question": question,
        "poll_options": options,
        "created_at": now,
    }
    await db.posts.insert_one(post_doc)
    await _shadow_flag_post(post_doc, user)
    return await _emit_and_return(await build_post_response(post_doc, user["id"]), user["id"])


@router.post("/polls/{post_id}/vote")
async def vote_on_poll(post_id: str, body: dict, user: Dict = Depends(require_auth)):
    """Cast a vote on a poll. Body: { option_index: int }"""
    option_index = body.get("option_index")
    if option_index is None or not isinstance(option_index, int):
        raise HTTPException(status_code=400, detail="option_index is required")

    post = await db.posts.find_one({"id": post_id, "post_type": "POLL"}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Poll not found")
    if option_index < 0 or option_index >= len(post.get("poll_options", [])):
        raise HTTPException(status_code=400, detail="Invalid option index")

    existing = await db.poll_votes.find_one({"post_id": post_id, "user_id": user["id"]}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="Already voted")

    await db.poll_votes.insert_one({
        "id": str(uuid.uuid4()),
        "post_id": post_id,
        "user_id": user["id"],
        "option_index": option_index,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Build results to return
    pipeline = [
        {"$match": {"post_id": post_id}},
        {"$group": {"_id": "$option_index", "count": {"$sum": 1}}},
    ]
    agg = await db.poll_votes.aggregate(pipeline).to_list(20)
    vote_map = {r["_id"]: r["count"] for r in agg}
    total = sum(vote_map.values())
    results = []
    for i, opt in enumerate(post.get("poll_options", [])):
        c = vote_map.get(i, 0)
        results.append({"option": opt, "count": c, "percentage": round(c / total * 100) if total else 0})

    return {"total_votes": total, "user_vote": option_index, "results": results}


@router.get("/polls/{post_id}/results")
async def get_poll_results(post_id: str, user: Dict = Depends(require_auth)):
    """Get poll results without voting (creator view)."""
    post = await db.posts.find_one({"id": post_id, "post_type": "POLL"}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Poll not found")
    pipeline = [
        {"$match": {"post_id": post_id}},
        {"$group": {"_id": "$option_index", "count": {"$sum": 1}}},
    ]
    agg = await db.poll_votes.aggregate(pipeline).to_list(20)
    vote_map = {r["_id"]: r["count"] for r in agg}
    total = sum(vote_map.values())
    results = []
    for i, opt in enumerate(post.get("poll_options", [])):
        c = vote_map.get(i, 0)
        results.append({"option": opt, "count": c, "percentage": round(c / total * 100) if total else 0})
    return {"total_votes": total, "results": results}



@router.get("/search/posts")
async def search_posts(q: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    """Search posts by keyword in caption/content"""
    hidden_ids = await get_hidden_user_ids()
    regex = {"$regex": q, "$options": "i"}
    match_filter = {"$or": [{"caption": regex}, {"content": regex}]}
    if hidden_ids:
        match_filter["user_id"] = {"$nin": hidden_ids}
    posts = await db.posts.find(
        match_filter,
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    results = []
    for p in posts:
        poster = await db.users.find_one({"id": p.get("user_id")}, {"_id": 0, "id": 1, "username": 1, "avatar_url": 1, "title_label": 1})
        results.append({
            "id": p.get("id"),
            "post_type": p.get("post_type"),
            "caption": (p.get("caption") or p.get("content") or "")[:120],
            "created_at": p.get("created_at"),
            "user": poster,
        })
    return results


# ============== GET SINGLE POST ==============

@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, user: Dict = Depends(require_auth)):
    post = await db.posts.find_one({"id": post_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return await build_post_response(post, user["id"])


# ============== DELETE POST ==============

@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, user: Dict = Depends(require_auth)):
    """Delete a post owned by the current user, along with its likes and comments. Spin history in the Vault is preserved."""
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")

    # Unlink the spin from the post (keep spin in Vault, just clear the post reference)
    if post.get("spin_id"):
        await db.spins.update_one({"id": post["spin_id"]}, {"$unset": {"post_id": ""}})

    await db.likes.delete_many({"post_id": post_id})
    await db.comments.delete_many({"post_id": post_id})
    await db.posts.delete_one({"id": post_id})
    return {"message": "Post deleted"}

@router.delete("/spins/{spin_id}")
async def delete_spin(spin_id: str, user: Dict = Depends(require_auth)):
    """Delete a spin and its linked feed post (bidirectional)."""
    spin = await db.spins.find_one({"id": spin_id})
    if not spin:
        raise HTTPException(status_code=404, detail="Spin not found")
    if spin["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own spins")

    # Delete the corresponding post
    post = await db.posts.find_one({"spin_id": spin_id})
    if not post:
        post = await db.posts.find_one({
            "user_id": user["id"], "record_id": spin.get("record_id"),
            "post_type": "NOW_SPINNING", "created_at": spin.get("created_at")
        })
    if post:
        await db.likes.delete_many({"post_id": post["id"]})
        await db.comments.delete_many({"post_id": post["id"]})
        await db.posts.delete_one({"id": post["id"]})

    await db.spins.delete_one({"id": spin_id})
    return {"message": "Spin and linked post deleted"}



# ============== LIKES ROUTES ==============

@router.post("/posts/{post_id}/like")
async def like_post(post_id: str, user: Dict = Depends(require_auth)):
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    existing = await db.likes.find_one({"post_id": post_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")
    
    like_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    await db.likes.insert_one({
        "id": like_id,
        "post_id": post_id,
        "user_id": user["id"],
        "created_at": now
    })
    
    if post.get("user_id") != user["id"]:
        u = await db.users.find_one({"id": user["id"]}, {"_id": 0})
        # Only email on first like for this post
        like_count = await db.likes.count_documents({"post_id": post_id})
        if like_count == 1:
            post_owner = await db.users.find_one({"id": post["user_id"]}, {"_id": 0})
            if post_owner and post_owner.get("email"):
                post_type = post.get("post_type", "post").replace("_", " ").title()
                preview = post.get("content", post.get("caption", ""))[:80] or post_type
                tpl = email_tpl.new_like(u.get("username", "?"), post_type, preview, f"{FRONTEND_URL}/hive")
                await send_email_fire_and_forget(post_owner["email"], tpl["subject"], tpl["html"])
        await create_notification(post["user_id"], "POST_LIKED", "Someone liked your post",
                                  f"@{u.get('username','?')} liked your post",
                                  {"post_id": post_id}, sender_id=u["id"])

    return {"message": "Post liked"}

@router.delete("/posts/{post_id}/like")
async def unlike_post(post_id: str, user: Dict = Depends(require_auth)):
    result = await db.likes.delete_one({"post_id": post_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Not liked")
    
    return {"message": "Post unliked"}


# ============== COMMENTS ROUTES ==============

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def add_comment(post_id: str, comment_data: CommentCreate, user: Dict = Depends(require_auth)):
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    comment_doc = {
        "id": comment_id,
        "post_id": post_id,
        "user_id": user["id"],
        "content": comment_data.content,
        "parent_id": comment_data.parent_id,
        "image_url": comment_data.image_url,
        "created_at": now
    }
    
    await db.comments.insert_one(comment_doc)
    
    # Notify post owner about comment (if not self)
    if post.get("user_id") != user["id"]:
        await create_notification(post["user_id"], "NEW_COMMENT", "New comment on your post",
                                  f"@{user.get('username','?')} commented on your post",
                                  {"post_id": post_id}, sender_id=user["id"])
        post_owner = await db.users.find_one({"id": post["user_id"]}, {"_id": 0})
        if post_owner and post_owner.get("email"):
            post_type = post.get("post_type", "post").replace("_", " ").title()
            tpl = email_tpl.new_comment(user.get("username", "?"), post_type, comment_data.content[:200], f"{FRONTEND_URL}/hive")
            await send_email_fire_and_forget(post_owner["email"], tpl["subject"], tpl["html"])

    # If replying, notify the parent comment author (if not self)
    if comment_data.parent_id:
        parent = await db.comments.find_one({"id": comment_data.parent_id}, {"_id": 0})
        if parent and parent.get("user_id") != user["id"]:
            await create_notification(parent["user_id"], "COMMENT_REPLY", "Someone replied to your comment",
                                      f"@{user.get('username','?')} replied to your comment",
                                      {"post_id": post_id, "comment_id": comment_id}, sender_id=user["id"])
        # Smart threading: if parent is itself a reply, also notify the thread owner (top-level comment author)
        if parent and parent.get("parent_id"):
            thread_owner = await db.comments.find_one({"id": parent["parent_id"]}, {"_id": 0})
            if thread_owner and thread_owner.get("user_id") != user["id"] and thread_owner.get("user_id") != parent.get("user_id"):
                await create_notification(thread_owner["user_id"], "COMMENT_REPLY", "New reply in your thread",
                                          f"@{user.get('username','?')} replied in your comment thread",
                                          {"post_id": post_id, "comment_id": comment_id}, sender_id=user["id"])

    # Parse @mentions and notify mentioned users (if not self or already notified)
    mentions = set(re.findall(r'@(\w+)', comment_data.content))
    notified_ids = set()
    if post.get("user_id") != user["id"]:
        notified_ids.add(post["user_id"])
    if comment_data.parent_id and parent and parent.get("user_id") != user["id"]:
        notified_ids.add(parent["user_id"])
    # Include thread owner in already-notified set
    if comment_data.parent_id and parent and parent.get("parent_id"):
        thread_owner_comment = await db.comments.find_one({"id": parent["parent_id"]}, {"_id": 0, "user_id": 1})
        if thread_owner_comment:
            notified_ids.add(thread_owner_comment["user_id"])
    for username in mentions:
        mentioned_user = await db.users.find_one({"username": username.lower()}, {"_id": 0, "id": 1, "username": 1})
        if mentioned_user and mentioned_user["id"] != user["id"] and mentioned_user["id"] not in notified_ids:
            await create_notification(mentioned_user["id"], "MENTION", "You were mentioned in a comment",
                                      f"@{user.get('username','?')} mentioned you in a comment",
                                      {"post_id": post_id, "comment_id": comment_id}, sender_id=user["id"])
            notified_ids.add(mentioned_user["id"])

    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url"), "title_label": user.get("title_label")}
    
    return CommentResponse(**comment_doc, user=user_data, likes_count=0, is_liked=False)

@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    comments = await db.comments.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    
    current_user_id = current_user["id"] if current_user else None
    blocked_ids = await get_all_blocked_ids(current_user_id) if current_user_id else []
    
    # Build response for all comments with like info
    comment_map = {}
    for comment in comments:
        if comment.get("user_id") in blocked_ids:
            continue
        comment_user = await db.users.find_one({"id": comment["user_id"]}, {"_id": 0, "password_hash": 0})
        user_data = {"id": comment_user["id"], "username": comment_user["username"], "avatar_url": comment_user.get("avatar_url"), "title_label": comment_user.get("title_label")} if comment_user else None
        likes_count = await db.comment_likes.count_documents({"comment_id": comment["id"]})
        is_liked = False
        if current_user_id:
            is_liked = await db.comment_likes.find_one({"comment_id": comment["id"], "user_id": current_user_id}) is not None
        resp = {
            **comment,
            "user": user_data,
            "likes_count": likes_count,
            "is_liked": is_liked,
            "is_deleted": comment.get("is_deleted", False),
            "replies": [],
        }
        comment_map[comment["id"]] = resp

    # Build nested structure: top-level comments with replies
    top_level = []
    for cid, c in comment_map.items():
        pid = c.get("parent_id")
        if pid and pid in comment_map:
            comment_map[pid]["replies"].append(c)
        else:
            top_level.append(c)
    
    # Filter: remove top-level deleted comments with no replies; keep deleted parents that have replies
    top_level = [c for c in top_level if not c.get("is_deleted") or len(c.get("replies", [])) > 0]
    
    return top_level



# ============== COMMENT DELETION (SOFT-DELETE) ==============

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user: Dict = Depends(require_auth)):
    comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    # Only author or admin can delete
    if comment.get("user_id") != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    # Soft-delete: mark as deleted, preserve for threading
    await db.comments.update_one(
        {"id": comment_id},
        {"$set": {"is_deleted": True, "content": "[deleted]", "deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    # Decrement comment count on the post
    await db.posts.update_one({"id": comment.get("post_id")}, {"$inc": {"comments_count": -1}})
    return {"message": "Comment deleted"}


# ============== COMMENT LIKES ==============

@router.post("/comments/{comment_id}/like")
async def like_comment(comment_id: str, user: Dict = Depends(require_auth)):
    comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    existing = await db.comment_likes.find_one({"comment_id": comment_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")
    now = datetime.now(timezone.utc).isoformat()
    await db.comment_likes.insert_one({
        "id": str(uuid.uuid4()),
        "comment_id": comment_id,
        "user_id": user["id"],
        "created_at": now,
    })
    # Notify comment author
    if comment.get("user_id") != user["id"]:
        await create_notification(comment["user_id"], "COMMENT_LIKED", "Someone liked your comment",
                                  f"@{user.get('username','?')} liked your comment",
                                  {"post_id": comment.get("post_id"), "comment_id": comment_id}, sender_id=user["id"])
    return {"message": "Comment liked"}

@router.delete("/comments/{comment_id}/like")
async def unlike_comment(comment_id: str, user: Dict = Depends(require_auth)):
    result = await db.comment_likes.delete_one({"comment_id": comment_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Not liked")
    return {"message": "Comment unliked"}


# ============== @MENTION USER SEARCH ==============

MENTION_RE = re.compile(r'@(\w+)')

async def parse_and_notify_mentions(text: str, post_id: str, author_id: str):
    """Extract @mentions from text, store on post, and notify mentioned users."""
    if not text:
        return []
    matches = MENTION_RE.findall(text)
    if not matches:
        return []
    unique_usernames = list(dict.fromkeys(u.lower() for u in matches))
    mentioned_ids = []
    author = await db.users.find_one({"id": author_id}, {"_id": 0, "username": 1})
    author_name = author.get("username", "?") if author else "?"
    for uname in unique_usernames[:10]:  # cap at 10 mentions
        u = await db.users.find_one({"username": uname}, {"_id": 0, "id": 1})
        if u and u["id"] != author_id:
            mentioned_ids.append(u["id"])
            await create_notification(u["id"], "MENTION", "You were mentioned",
                                      f"@{author_name} mentioned you in a post",
                                      {"post_id": post_id, "from_username": author_name}, sender_id=author_id)
    if mentioned_ids:
        await db.posts.update_one({"id": post_id}, {"$set": {"mentions": unique_usernames}})
    return unique_usernames


@router.get("/mention-search")
async def search_users_mention(q: str = "", user: Dict = Depends(require_auth)):
    """Search users for @mention autocomplete."""
    if not q or len(q) < 1:
        return []
    hidden_ids = await get_hidden_user_ids()
    regex = {"$regex": f"^{q}", "$options": "i"}
    users = await db.users.find(
        {"username": regex, "id": {"$nin": hidden_ids}},
        {"_id": 0, "id": 1, "username": 1, "avatar_url": 1}
    ).limit(8).to_list(8)
    return users


# ============== ADMIN PIN POST ==============

@router.post("/posts/{post_id}/pin")
async def pin_post(post_id: str, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    # Unpin any currently pinned post
    await db.posts.update_many({"is_pinned": True}, {"$set": {"is_pinned": False}})
    # Pin this post
    await db.posts.update_one({"id": post_id}, {"$set": {"is_pinned": True}})
    return {"message": "Post pinned"}

@router.delete("/posts/{post_id}/pin")
async def unpin_post(post_id: str, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.posts.update_one({"id": post_id}, {"$set": {"is_pinned": False}})
    return {"message": "Post unpinned"}


# ============== ADMIN NEW FEATURE TAG ==============

@router.post("/posts/{post_id}/new-feature")
async def toggle_new_feature(post_id: str, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    new_val = not post.get("is_new_feature", False)
    await db.posts.update_one({"id": post_id}, {"$set": {"is_new_feature": new_val}})
    return {"is_new_feature": new_val, "message": f"New Feature tag {'added' if new_val else 'removed'}"}


# ============== ADMIN RELEASE NOTE ==============

@router.post("/posts/{post_id}/release-note")
async def toggle_release_note(post_id: str, user: Dict = Depends(require_auth)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    new_val = not post.get("is_release_note", False)
    await db.posts.update_one({"id": post_id}, {"$set": {"is_release_note": new_val}})
    return {"is_release_note": new_val, "message": f"Release Note {'promoted' if new_val else 'demoted'}"}



# ============== SHARE GRAPHICS ROUTES ==============

@router.post("/share/generate")
async def generate_share_graphic_endpoint(request: ShareGraphicRequest, user: Dict = Depends(require_auth)):
    data = {}
    
    if request.graphic_type == "now_spinning" and request.record_id:
        record = await db.records.find_one({"id": request.record_id}, {"_id": 0})
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        data = record
        
    elif request.graphic_type == "new_haul" and request.haul_id:
        haul = await db.hauls.find_one({"id": request.haul_id}, {"_id": 0})
        if not haul:
            raise HTTPException(status_code=404, detail="Haul not found")
        data = haul
        
    elif request.graphic_type == "weekly_summary":
        summary = await get_weekly_summary(user)
        data = summary.model_dump()
    
    format_type = request.format if request.format in ["square", "story"] else "square"
    image_bytes = generate_share_graphic(request.graphic_type, data, format_type)
    
    format_suffix = "_story" if format_type == "story" else ""
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={request.graphic_type}{format_suffix}_{datetime.now().strftime('%Y%m%d')}.png"}
    )

