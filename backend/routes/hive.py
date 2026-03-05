from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from database import db, require_auth, get_current_user, security, logger, create_notification
from database import hash_password, verify_password, create_token, search_discogs, get_discogs_release
from database import put_object, get_object, init_storage, storage_key
from database import STRIPE_API_KEY, PLATFORM_FEE_PERCENT, FRONTEND_URL
from database import DISCOGS_TOKEN, DISCOGS_USER_AGENT, DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET
from database import DISCOGS_REQUEST_TOKEN_URL, DISCOGS_AUTHORIZE_URL, DISCOGS_ACCESS_TOKEN_URL, DISCOGS_API_BASE
from database import oauth_request_tokens, import_progress, EMERGENT_KEY
from models import *
from io import BytesIO

router = APIRouter()

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



# ============== FEED/POSTS ROUTES ==============

def normalize_post_type(post_type: str) -> str:
    """Map legacy post types to new enum values"""
    return POST_TYPE_MAP.get(post_type, post_type)

async def build_post_response(post: Dict, current_user_id: Optional[str] = None) -> Dict:
    """Build a full post response with user, record, haul, iso data"""
    post_user = await db.users.find_one({"id": post["user_id"]}, {"_id": 0, "password_hash": 0})
    user_data = {"id": post_user["id"], "username": post_user["username"], "avatar_url": post_user.get("avatar_url"), "founding_member": post_user.get("founding_member", False)} if post_user else None
    
    record_data = None
    if post.get("record_id"):
        record = await db.records.find_one({"id": post["record_id"]}, {"_id": 0})
        record_data = record
    
    haul_data = None
    if post.get("haul_id"):
        haul = await db.hauls.find_one({"id": post["haul_id"]}, {"_id": 0})
        haul_data = haul
    
    iso_data = None
    if post.get("iso_id"):
        iso = await db.iso_items.find_one({"id": post["iso_id"]}, {"_id": 0})
        iso_data = iso
    
    likes_count = await db.likes.count_documents({"post_id": post["id"]})
    comments_count = await db.comments.count_documents({"post_id": post["id"]})
    
    is_liked = False
    if current_user_id:
        is_liked = await db.likes.find_one({"post_id": post["id"], "user_id": current_user_id}) is not None
    
    # Normalize post type
    pt = normalize_post_type(post.get("post_type", ""))
    
    return PostResponse(
        id=post["id"],
        user_id=post["user_id"],
        post_type=pt,
        caption=post.get("caption") or post.get("content"),
        image_url=post.get("image_url"),
        share_card_square_url=post.get("share_card_square_url"),
        share_card_story_url=post.get("share_card_story_url"),
        record_id=post.get("record_id"),
        haul_id=post.get("haul_id"),
        iso_id=post.get("iso_id"),
        weekly_wrap_id=post.get("weekly_wrap_id"),
        track=post.get("track"),
        mood=post.get("mood"),
        prompt_text=post.get("prompt_text"),
        record_title=post.get("record_title"),
        record_artist=post.get("record_artist"),
        cover_url=post.get("cover_url"),
        created_at=post["created_at"],
        likes_count=likes_count,
        comments_count=comments_count,
        user=user_data,
        record=record_data,
        haul=haul_data,
        iso=iso_data,
        is_liked=is_liked,
        content=post.get("content")
    )

@router.get("/feed", response_model=List[PostResponse])
async def get_feed(user: Dict = Depends(require_auth), limit: int = 50, skip: int = 0):
    # Get users I'm following
    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0}).to_list(1000)
    following_ids = [f["following_id"] for f in following]
    following_ids.append(user["id"])  # Include own posts
    
    posts = await db.posts.find(
        {"user_id": {"$in": following_ids}},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        resp = await build_post_response(post, user["id"])
        result.append(resp)
    
    return result

@router.get("/explore", response_model=List[PostResponse])
async def get_explore_feed(current_user: Optional[Dict] = Depends(get_current_user), limit: int = 50, skip: int = 0):
    posts = await db.posts.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        uid = current_user["id"] if current_user else None
        resp = await build_post_response(post, uid)
        result.append(resp)
    
    return result


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
        "created_at": now
    })
    
    # Create post
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "NOW_SPINNING",
        "caption": data.caption,
        "record_id": data.record_id,
        "track": data.track,
        "mood": data.mood,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    return await build_post_response(post_doc, user["id"])

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
            "format": "Vinyl",
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
    
    # Create post
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
    
    return await build_post_response(post_doc, user["id"])

@router.post("/composer/iso", response_model=PostResponse)
async def composer_iso(data: ISOPostCreate, user: Dict = Depends(require_auth)):
    """Create an ISO (In Search Of) post in one flow"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Create ISO item
    iso_id = str(uuid.uuid4())
    iso_doc = {
        "id": iso_id,
        "user_id": user["id"],
        "artist": data.artist,
        "album": data.album,
        "discogs_id": data.discogs_id,
        "cover_url": data.cover_url,
        "year": data.year,
        "pressing_notes": data.pressing_notes,
        "condition_pref": data.condition_pref,
        "tags": data.tags or [],
        "target_price_min": data.target_price_min,
        "target_price_max": data.target_price_max,
        "status": "OPEN",
        "created_at": now
    }
    await db.iso_items.insert_one(iso_doc)
    
    # Create post
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "ISO",
        "caption": data.caption,
        "iso_id": iso_id,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    return await build_post_response(post_doc, user["id"])

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
    
    return await build_post_response(post_doc, user["id"])


@router.post("/composer/note", response_model=PostResponse)
async def composer_note(data: NoteCreate, user: Dict = Depends(require_auth)):
    """Create a free-form text Note post"""
    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    if len(data.text) > 280:
        raise HTTPException(status_code=400, detail="Text must be 280 characters or less")

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
    return await build_post_response(post_doc, user["id"])


# ============== SEARCH ROUTES ==============

@router.get("/search/posts")
async def search_posts(q: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    """Search posts by keyword in caption/content"""
    regex = {"$regex": q, "$options": "i"}
    posts = await db.posts.find(
        {"$or": [{"caption": regex}, {"content": regex}]},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    results = []
    for p in posts:
        poster = await db.users.find_one({"id": p.get("user_id")}, {"_id": 0, "id": 1, "username": 1, "avatar_url": 1})
        results.append({
            "id": p.get("id"),
            "post_type": p.get("post_type"),
            "caption": (p.get("caption") or p.get("content") or "")[:120],
            "created_at": p.get("created_at"),
            "user": poster,
        })
    return results


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
        await create_notification(post["user_id"], "POST_LIKED", "Someone liked your post",
                                  f"@{u.get('username','?')} liked your post",
                                  {"post_id": post_id})

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
        "created_at": now
    }
    
    await db.comments.insert_one(comment_doc)
    
    if post.get("user_id") != user["id"]:
        await create_notification(post["user_id"], "NEW_COMMENT", "New comment on your post",
                                  f"@{user.get('username','?')} commented on your post",
                                  {"post_id": post_id})

    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")}
    
    return CommentResponse(**comment_doc, user=user_data)

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(post_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    comments = await db.comments.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(100)
    
    result = []
    for comment in comments:
        comment_user = await db.users.find_one({"id": comment["user_id"]}, {"_id": 0, "password_hash": 0})
        user_data = {"id": comment_user["id"], "username": comment_user["username"], "avatar_url": comment_user.get("avatar_url")} if comment_user else None
        result.append(CommentResponse(**comment, user=user_data))
    
    return result


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

