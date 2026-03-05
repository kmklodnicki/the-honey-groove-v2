from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import requests
from requests_oauthlib import OAuth1Session
from io import BytesIO
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 168))

# Discogs Configuration
DISCOGS_TOKEN = os.environ.get('DISCOGS_TOKEN', '')
DISCOGS_USER_AGENT = os.environ.get('DISCOGS_USER_AGENT', 'HoneyGroove/1.0')
DISCOGS_CONSUMER_KEY = os.environ.get('DISCOGS_CONSUMER_KEY', '')
DISCOGS_CONSUMER_SECRET = os.environ.get('DISCOGS_CONSUMER_SECRET', '')
DISCOGS_REQUEST_TOKEN_URL = "https://api.discogs.com/oauth/request_token"
DISCOGS_AUTHORIZE_URL = "https://www.discogs.com/oauth/authorize"
DISCOGS_ACCESS_TOKEN_URL = "https://api.discogs.com/oauth/access_token"
DISCOGS_API_BASE = "https://api.discogs.com"

# In-memory store for OAuth request tokens (keyed by oauth_token)
oauth_request_tokens: Dict[str, str] = {}

# In-memory store for import progress (keyed by user_id)
import_progress: Dict[str, Dict] = {}

# Storage Configuration
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
APP_NAME = "honeygroove"
storage_key = None

# Create the main app
app = FastAPI(title="HoneyGroove API", version="1.0.0")

# Create routers
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== PYDANTIC MODELS ==============

# Auth Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: str = Field(min_length=3, max_length=30)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: str
    collection_count: int = 0
    spin_count: int = 0
    followers_count: int = 0
    following_count: int = 0

class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Record Models
class RecordCreate(BaseModel):
    discogs_id: Optional[int] = None
    title: str
    artist: str
    cover_url: Optional[str] = None
    year: Optional[int] = None
    format: Optional[str] = "Vinyl"
    notes: Optional[str] = None

class RecordResponse(BaseModel):
    id: str
    discogs_id: Optional[int] = None
    title: str
    artist: str
    cover_url: Optional[str] = None
    year: Optional[int] = None
    format: Optional[str] = None
    notes: Optional[str] = None
    user_id: str
    created_at: str
    spin_count: int = 0

class DiscogsSearchResult(BaseModel):
    discogs_id: int
    title: str
    artist: str
    cover_url: Optional[str] = None
    year: Optional[int] = None
    format: Optional[str] = None
    country: Optional[str] = None

# Spin Models
class SpinCreate(BaseModel):
    record_id: str
    notes: Optional[str] = None

class SpinResponse(BaseModel):
    id: str
    record_id: str
    user_id: str
    notes: Optional[str] = None
    created_at: str
    record: Optional[RecordResponse] = None

# Haul Models
class HaulItemCreate(BaseModel):
    discogs_id: Optional[int] = None
    title: str
    artist: str
    cover_url: Optional[str] = None
    year: Optional[int] = None
    notes: Optional[str] = None

class HaulCreate(BaseModel):
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    items: List[HaulItemCreate]

class HaulResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    items: List[Dict[str, Any]]
    created_at: str
    user: Optional[Dict[str, Any]] = None

# Follow Models
class FollowResponse(BaseModel):
    id: str
    follower_id: str
    following_id: str
    created_at: str

# Post/Activity Models
POST_TYPES = ["NOW_SPINNING", "NEW_HAUL", "ISO", "ADDED_TO_COLLECTION", "WEEKLY_WRAP", "VINYL_MOOD"]
# Mapping from old post types to new ones
POST_TYPE_MAP = {
    "spin": "NOW_SPINNING",
    "haul": "NEW_HAUL",
    "record_added": "ADDED_TO_COLLECTION",
    "weekly_summary": "WEEKLY_WRAP",
}

class PostCreate(BaseModel):
    post_type: str  # NOW_SPINNING, NEW_HAUL, ISO, ADDED_TO_COLLECTION, WEEKLY_WRAP, VINYL_MOOD
    caption: Optional[str] = None
    image_url: Optional[str] = None
    record_id: Optional[str] = None
    haul_id: Optional[str] = None
    iso_id: Optional[str] = None
    weekly_wrap_id: Optional[str] = None
    # For NOW_SPINNING inline creation
    track: Optional[str] = None
    # For VINYL_MOOD inline creation
    mood: Optional[str] = None

class PostResponse(BaseModel):
    id: str
    user_id: str
    post_type: str
    caption: Optional[str] = None
    image_url: Optional[str] = None
    share_card_square_url: Optional[str] = None
    share_card_story_url: Optional[str] = None
    record_id: Optional[str] = None
    haul_id: Optional[str] = None
    iso_id: Optional[str] = None
    weekly_wrap_id: Optional[str] = None
    track: Optional[str] = None
    mood: Optional[str] = None
    created_at: str
    likes_count: int = 0
    comments_count: int = 0
    user: Optional[Dict[str, Any]] = None
    record: Optional[Dict[str, Any]] = None
    haul: Optional[Dict[str, Any]] = None
    iso: Optional[Dict[str, Any]] = None
    is_liked: bool = False
    # Legacy compat
    content: Optional[str] = None

# Comment Models
class CommentCreate(BaseModel):
    post_id: str
    content: str

class CommentResponse(BaseModel):
    id: str
    post_id: str
    user_id: str
    content: str
    created_at: str
    user: Optional[Dict[str, Any]] = None

# ISO Models
class ISOCreate(BaseModel):
    artist: str
    album: str
    record_id: Optional[str] = None
    priority: str = "MED"  # HIGH, MED, LOW
    pressing_notes: Optional[str] = None
    condition_pref: Optional[str] = None
    tags: Optional[List[str]] = None  # OG Press, Factory Sealed, Any, Promo
    target_price_min: Optional[float] = None
    target_price_max: Optional[float] = None

class ISOResponse(BaseModel):
    id: str
    user_id: str
    artist: str
    album: str
    record_id: Optional[str] = None
    priority: str = "MED"
    pressing_notes: Optional[str] = None
    condition_pref: Optional[str] = None
    tags: Optional[List[str]] = None
    target_price_min: Optional[float] = None
    target_price_max: Optional[float] = None
    status: str = "OPEN"
    created_at: str
    found_at: Optional[str] = None
    record: Optional[Dict[str, Any]] = None

# Composer Models (one-shot post creation)
class NowSpinningCreate(BaseModel):
    record_id: str
    track: Optional[str] = None
    caption: Optional[str] = None

class NewHaulCreate(BaseModel):
    store_name: Optional[str] = None
    caption: Optional[str] = None
    image_url: Optional[str] = None
    items: List[HaulItemCreate]

class ISOPostCreate(BaseModel):
    artist: str
    album: str
    pressing_notes: Optional[str] = None
    condition_pref: Optional[str] = None
    tags: Optional[List[str]] = None
    target_price_min: Optional[float] = None
    target_price_max: Optional[float] = None
    caption: Optional[str] = None

class VinylMoodCreate(BaseModel):
    mood: str  # Late Night, Sunday Morning, Rainy Day, etc.
    caption: Optional[str] = None
    record_id: Optional[str] = None

# Weekly Summary Models
class WeeklySummaryResponse(BaseModel):
    id: str
    user_id: str
    week_start: str
    week_end: str
    total_spins: int
    top_artist: Optional[str] = None
    top_album: Optional[str] = None
    listening_mood: Optional[str] = None
    records_added: int = 0
    created_at: str

# Share Graphic Models
class ShareGraphicRequest(BaseModel):
    graphic_type: str  # now_spinning, new_haul, weekly_summary
    format: str = "square"  # square (1080x1080) or story (1080x1920)
    record_id: Optional[str] = None
    haul_id: Optional[str] = None
    summary_id: Optional[str] = None

# Discogs Import Models
class DiscogsImportStatus(BaseModel):
    status: str  # idle, in_progress, completed, error
    total: int = 0
    imported: int = 0
    skipped: int = 0
    error_message: Optional[str] = None
    discogs_username: Optional[str] = None
    last_synced: Optional[str] = None

# ============== UTILITY FUNCTIONS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "exp": expiration,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        return user
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

# Storage Functions
def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    if not EMERGENT_KEY:
        logger.warning("EMERGENT_LLM_KEY not set, storage disabled")
        return None
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        return storage_key
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
        return None

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple:
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# Discogs API Functions
def search_discogs(query: str, search_type: str = "release") -> List[Dict]:
    if not DISCOGS_TOKEN:
        logger.warning("Discogs token not configured")
        return []
    
    headers = {
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": DISCOGS_USER_AGENT
    }
    
    try:
        response = requests.get(
            "https://api.discogs.com/database/search",
            params={"q": query, "type": search_type, "per_page": 20},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            # Parse title - Discogs format is "Artist - Title"
            title_parts = item.get("title", "").split(" - ", 1)
            artist = title_parts[0] if title_parts else "Unknown Artist"
            title = title_parts[1] if len(title_parts) > 1 else title_parts[0]
            
            results.append({
                "discogs_id": item.get("id"),
                "title": title,
                "artist": artist,
                "cover_url": item.get("cover_image"),
                "year": item.get("year"),
                "format": item.get("format", ["Vinyl"])[0] if item.get("format") else "Vinyl",
                "country": item.get("country")
            })
        
        return results
    except Exception as e:
        logger.error(f"Discogs search error: {e}")
        return []

def get_discogs_release(release_id: int) -> Optional[Dict]:
    if not DISCOGS_TOKEN:
        return None
    
    headers = {
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": DISCOGS_USER_AGENT
    }
    
    try:
        response = requests.get(
            f"https://api.discogs.com/releases/{release_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        artists = data.get("artists", [])
        artist_name = artists[0].get("name", "Unknown Artist") if artists else "Unknown Artist"
        
        images = data.get("images", [])
        cover_url = images[0].get("uri") if images else None
        
        return {
            "discogs_id": data.get("id"),
            "title": data.get("title"),
            "artist": artist_name,
            "cover_url": cover_url,
            "year": data.get("year"),
            "format": data.get("formats", [{}])[0].get("name", "Vinyl") if data.get("formats") else "Vinyl",
            "country": data.get("country")
        }
    except Exception as e:
        logger.error(f"Discogs release fetch error: {e}")
        return None

# Image Generation Functions - HoneyGroove themed
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

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    existing_username = await db.users.find_one({"username": user_data.username.lower()})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username.lower(),
        "password_hash": hash_password(user_data.password),
        "avatar_url": f"https://api.dicebear.com/7.x/miniavs/svg?seed={user_data.username}",
        "bio": None,
        "created_at": now
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            username=user_data.username.lower(),
            avatar_url=user_doc["avatar_url"],
            bio=None,
            created_at=now,
            collection_count=0,
            spin_count=0,
            followers_count=0,
            following_count=0
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"])
    
    # Get counts
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    spin_count = await db.spins.count_documents({"user_id": user["id"]})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})
    following_count = await db.followers.count_documents({"follower_id": user["id"]})
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            avatar_url=user.get("avatar_url"),
            bio=user.get("bio"),
            created_at=user["created_at"],
            collection_count=collection_count,
            spin_count=spin_count,
            followers_count=followers_count,
            following_count=following_count
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: Dict = Depends(require_auth)):
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    spin_count = await db.spins.count_documents({"user_id": user["id"]})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})
    following_count = await db.followers.count_documents({"follower_id": user["id"]})
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        avatar_url=user.get("avatar_url"),
        bio=user.get("bio"),
        created_at=user["created_at"],
        collection_count=collection_count,
        spin_count=spin_count,
        followers_count=followers_count,
        following_count=following_count
    )

@api_router.put("/auth/me", response_model=UserResponse)
async def update_me(update_data: UserUpdate, user: Dict = Depends(require_auth)):
    update_fields = {}
    if update_data.username:
        existing = await db.users.find_one({"username": update_data.username.lower(), "id": {"$ne": user["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_fields["username"] = update_data.username.lower()
    if update_data.bio is not None:
        update_fields["bio"] = update_data.bio
    if update_data.avatar_url is not None:
        update_fields["avatar_url"] = update_data.avatar_url
    
    if update_fields:
        await db.users.update_one({"id": user["id"]}, {"$set": update_fields})
    
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    spin_count = await db.spins.count_documents({"user_id": user["id"]})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})
    following_count = await db.followers.count_documents({"follower_id": user["id"]})
    
    return UserResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        username=updated_user["username"],
        avatar_url=updated_user.get("avatar_url"),
        bio=updated_user.get("bio"),
        created_at=updated_user["created_at"],
        collection_count=collection_count,
        spin_count=spin_count,
        followers_count=followers_count,
        following_count=following_count
    )

# ============== USER ROUTES ==============

@api_router.get("/users/discover/suggestions")
async def get_suggested_users(user: Dict = Depends(require_auth)):
    """Get suggested users to follow (users not already followed)"""
    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0}).to_list(1000)
    following_ids = [f["following_id"] for f in following]
    following_ids.append(user["id"])
    
    all_users = await db.users.find(
        {"id": {"$nin": following_ids}},
        {"_id": 0, "password_hash": 0}
    ).to_list(50)
    
    suggestions = []
    for u in all_users:
        record_count = await db.records.count_documents({"user_id": u["id"]})
        suggestions.append({
            "id": u["id"],
            "username": u["username"],
            "avatar_url": u.get("avatar_url"),
            "bio": u.get("bio"),
            "record_count": record_count,
            "is_following": False
        })
    
    suggestions.sort(key=lambda x: x["record_count"], reverse=True)
    return suggestions[:20]

@api_router.get("/users/search")
async def search_users_q(query: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    users = await db.users.find(
        {"username": {"$regex": query, "$options": "i"}},
        {"_id": 0, "password_hash": 0}
    ).limit(20).to_list(20)
    result = []
    for u in users:
        is_following = await db.followers.find_one({"follower_id": user["id"], "following_id": u["id"]}) is not None
        result.append({
            "id": u["id"],
            "username": u["username"],
            "avatar_url": u.get("avatar_url"),
            "bio": u.get("bio"),
            "is_following": is_following
        })
    return result

@api_router.get("/users/{username}", response_model=UserResponse)
async def get_user_profile(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    collection_count = await db.records.count_documents({"user_id": user["id"]})
    spin_count = await db.spins.count_documents({"user_id": user["id"]})
    followers_count = await db.followers.count_documents({"following_id": user["id"]})
    following_count = await db.followers.count_documents({"follower_id": user["id"]})
    
    return UserResponse(
        id=user["id"],
        email=user["email"] if current_user and current_user["id"] == user["id"] else "",
        username=user["username"],
        avatar_url=user.get("avatar_url"),
        bio=user.get("bio"),
        created_at=user["created_at"],
        collection_count=collection_count,
        spin_count=spin_count,
        followers_count=followers_count,
        following_count=following_count
    )

# ============== DISCOGS ROUTES ==============

@api_router.get("/discogs/search", response_model=List[DiscogsSearchResult])
async def search_records_discogs(q: str = Query(..., min_length=2), user: Dict = Depends(require_auth)):
    results = search_discogs(q)
    return [DiscogsSearchResult(**r) for r in results]

@api_router.get("/discogs/release/{release_id}")
async def get_discogs_release_info(release_id: int, user: Dict = Depends(require_auth)):
    result = get_discogs_release(release_id)
    if not result:
        raise HTTPException(status_code=404, detail="Release not found")
    return result

# ============== COLLECTION/RECORDS ROUTES ==============

@api_router.post("/records", response_model=RecordResponse)
async def add_record(record_data: RecordCreate, user: Dict = Depends(require_auth)):
    record_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    record_doc = {
        "id": record_id,
        "user_id": user["id"],
        "discogs_id": record_data.discogs_id,
        "title": record_data.title,
        "artist": record_data.artist,
        "cover_url": record_data.cover_url,
        "year": record_data.year,
        "format": record_data.format,
        "notes": record_data.notes,
        "created_at": now
    }
    
    await db.records.insert_one(record_doc)
    
    # Create activity post
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "ADDED_TO_COLLECTION",
        "caption": f"Added {record_data.title} by {record_data.artist} to their collection",
        "record_id": record_id,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    return RecordResponse(
        id=record_id,
        discogs_id=record_data.discogs_id,
        title=record_data.title,
        artist=record_data.artist,
        cover_url=record_data.cover_url,
        year=record_data.year,
        format=record_data.format,
        notes=record_data.notes,
        user_id=user["id"],
        created_at=now,
        spin_count=0
    )

@api_router.get("/records", response_model=List[RecordResponse])
async def get_my_records(user: Dict = Depends(require_auth)):
    records = await db.records.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    result = []
    for record in records:
        spin_count = await db.spins.count_documents({"record_id": record["id"]})
        result.append(RecordResponse(
            **record,
            spin_count=spin_count
        ))
    
    return result

@api_router.get("/records/{record_id}", response_model=RecordResponse)
async def get_record(record_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    record = await db.records.find_one({"id": record_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    spin_count = await db.spins.count_documents({"record_id": record_id})
    
    return RecordResponse(**record, spin_count=spin_count)

@api_router.get("/users/{username}/records", response_model=List[RecordResponse])
async def get_user_records(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    records = await db.records.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    result = []
    for record in records:
        spin_count = await db.spins.count_documents({"record_id": record["id"]})
        result.append(RecordResponse(**record, spin_count=spin_count))
    
    return result

@api_router.delete("/records/{record_id}")
async def delete_record(record_id: str, user: Dict = Depends(require_auth)):
    record = await db.records.find_one({"id": record_id, "user_id": user["id"]})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    await db.records.delete_one({"id": record_id})
    await db.spins.delete_many({"record_id": record_id})
    await db.posts.delete_many({"record_id": record_id})
    
    return {"message": "Record deleted"}

# ============== SPIN ROUTES ==============

@api_router.post("/spins", response_model=SpinResponse)
async def log_spin(spin_data: SpinCreate, user: Dict = Depends(require_auth)):
    record = await db.records.find_one({"id": spin_data.record_id, "user_id": user["id"]}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found in your collection")
    
    spin_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    spin_doc = {
        "id": spin_id,
        "user_id": user["id"],
        "record_id": spin_data.record_id,
        "notes": spin_data.notes,
        "created_at": now
    }
    
    await db.spins.insert_one(spin_doc)
    
    # Create activity post
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "NOW_SPINNING",
        "caption": f"Spinning {record['title']} by {record['artist']}",
        "record_id": spin_data.record_id,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    return SpinResponse(
        id=spin_id,
        record_id=spin_data.record_id,
        user_id=user["id"],
        notes=spin_data.notes,
        created_at=now,
        record=RecordResponse(**record, spin_count=0)
    )

@api_router.get("/spins", response_model=List[SpinResponse])
async def get_my_spins(user: Dict = Depends(require_auth), limit: int = 50):
    spins = await db.spins.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for spin in spins:
        record = await db.records.find_one({"id": spin["record_id"]}, {"_id": 0})
        result.append(SpinResponse(
            **spin,
            record=RecordResponse(**record, spin_count=0) if record else None
        ))
    
    return result

# ============== HAUL ROUTES ==============

@api_router.post("/hauls", response_model=HaulResponse)
async def create_haul(haul_data: HaulCreate, user: Dict = Depends(require_auth)):
    haul_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Add each record to collection
    items_with_ids = []
    for item in haul_data.items:
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
            "created_at": now
        }
        await db.records.insert_one(record_doc)
        items_with_ids.append({**item.model_dump(), "record_id": record_id})
    
    haul_doc = {
        "id": haul_id,
        "user_id": user["id"],
        "title": haul_data.title,
        "description": haul_data.description,
        "image_url": haul_data.image_url,
        "items": items_with_ids,
        "created_at": now
    }
    
    await db.hauls.insert_one(haul_doc)
    
    # Create activity post
    post_id = str(uuid.uuid4())
    post_doc = {
        "id": post_id,
        "user_id": user["id"],
        "post_type": "NEW_HAUL",
        "caption": f"Added {len(haul_data.items)} new records: {haul_data.title}",
        "haul_id": haul_id,
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")}
    
    return HaulResponse(
        id=haul_id,
        user_id=user["id"],
        title=haul_data.title,
        description=haul_data.description,
        image_url=haul_data.image_url,
        items=items_with_ids,
        created_at=now,
        user=user_data
    )

@api_router.get("/hauls", response_model=List[HaulResponse])
async def get_my_hauls(user: Dict = Depends(require_auth)):
    hauls = await db.hauls.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")}
    
    return [HaulResponse(**haul, user=user_data) for haul in hauls]

@api_router.get("/hauls/{haul_id}", response_model=HaulResponse)
async def get_haul(haul_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    haul = await db.hauls.find_one({"id": haul_id}, {"_id": 0})
    if not haul:
        raise HTTPException(status_code=404, detail="Haul not found")
    
    user = await db.users.find_one({"id": haul["user_id"]}, {"_id": 0, "password_hash": 0})
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")} if user else None
    
    return HaulResponse(**haul, user=user_data)

# ============== FOLLOW ROUTES ==============

@api_router.post("/follow/{username}")
async def follow_user(username: str, user: Dict = Depends(require_auth)):
    target_user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    existing = await db.followers.find_one({
        "follower_id": user["id"],
        "following_id": target_user["id"]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already following this user")
    
    follow_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    follow_doc = {
        "id": follow_id,
        "follower_id": user["id"],
        "following_id": target_user["id"],
        "created_at": now
    }
    
    await db.followers.insert_one(follow_doc)
    
    return {"message": f"Now following {username}"}

@api_router.delete("/follow/{username}")
async def unfollow_user(username: str, user: Dict = Depends(require_auth)):
    target_user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.followers.delete_one({
        "follower_id": user["id"],
        "following_id": target_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Not following this user")
    
    return {"message": f"Unfollowed {username}"}

@api_router.get("/follow/check/{username}")
async def check_following(username: str, user: Dict = Depends(require_auth)):
    target_user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = await db.followers.find_one({
        "follower_id": user["id"],
        "following_id": target_user["id"]
    })
    
    return {"is_following": existing is not None}

@api_router.get("/users/{username}/followers")
async def get_followers(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    followers = await db.followers.find({"following_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    result = []
    for f in followers:
        follower_user = await db.users.find_one({"id": f["follower_id"]}, {"_id": 0, "password_hash": 0})
        if follower_user:
            is_following = False
            if current_user:
                is_following = await db.followers.find_one({
                    "follower_id": current_user["id"],
                    "following_id": follower_user["id"]
                }) is not None
            result.append({
                "id": follower_user["id"],
                "username": follower_user["username"],
                "avatar_url": follower_user.get("avatar_url"),
                "bio": follower_user.get("bio"),
                "is_following": is_following
            })
    
    return result

@api_router.get("/users/{username}/following")
async def get_following(username: str, current_user: Optional[Dict] = Depends(get_current_user)):
    user = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    following = await db.followers.find({"follower_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    result = []
    for f in following:
        following_user = await db.users.find_one({"id": f["following_id"]}, {"_id": 0, "password_hash": 0})
        if following_user:
            is_following = False
            if current_user:
                is_following = await db.followers.find_one({
                    "follower_id": current_user["id"],
                    "following_id": following_user["id"]
                }) is not None
            result.append({
                "id": following_user["id"],
                "username": following_user["username"],
                "avatar_url": following_user.get("avatar_url"),
                "bio": following_user.get("bio"),
                "is_following": is_following
            })
    
    return result

# ============== FEED/POSTS ROUTES ==============

def normalize_post_type(post_type: str) -> str:
    """Map legacy post types to new enum values"""
    return POST_TYPE_MAP.get(post_type, post_type)

async def build_post_response(post: Dict, current_user_id: Optional[str] = None) -> Dict:
    """Build a full post response with user, record, haul, iso data"""
    post_user = await db.users.find_one({"id": post["user_id"]}, {"_id": 0, "password_hash": 0})
    user_data = {"id": post_user["id"], "username": post_user["username"], "avatar_url": post_user.get("avatar_url")} if post_user else None
    
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

@api_router.get("/feed", response_model=List[PostResponse])
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

@api_router.get("/explore", response_model=List[PostResponse])
async def get_explore_feed(current_user: Optional[Dict] = Depends(get_current_user), limit: int = 50, skip: int = 0):
    posts = await db.posts.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        uid = current_user["id"] if current_user else None
        resp = await build_post_response(post, uid)
        result.append(resp)
    
    return result

# ============== COMPOSER ENDPOINTS (one-shot post creation) ==============

@api_router.post("/composer/now-spinning", response_model=PostResponse)
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
        "created_at": now
    }
    await db.posts.insert_one(post_doc)
    
    return await build_post_response(post_doc, user["id"])

@api_router.post("/composer/new-haul", response_model=PostResponse)
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

@api_router.post("/composer/iso", response_model=PostResponse)
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

@api_router.post("/composer/vinyl-mood", response_model=PostResponse)
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

# ============== ISO ROUTES ==============

@api_router.get("/iso", response_model=List[ISOResponse])
async def get_my_isos(user: Dict = Depends(require_auth)):
    isos = await db.iso_items.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    result = []
    for iso in isos:
        record_data = None
        if iso.get("record_id"):
            record_data = await db.records.find_one({"id": iso["record_id"]}, {"_id": 0})
        result.append(ISOResponse(**iso, record=record_data))
    return result

@api_router.put("/iso/{iso_id}/found")
async def mark_iso_found(iso_id: str, user: Dict = Depends(require_auth)):
    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]})
    if not iso:
        raise HTTPException(status_code=404, detail="ISO not found")
    
    now = datetime.now(timezone.utc).isoformat()
    await db.iso_items.update_one({"id": iso_id}, {"$set": {"status": "FOUND", "found_at": now}})
    return {"message": "ISO marked as found"}

@api_router.delete("/iso/{iso_id}")
async def delete_iso(iso_id: str, user: Dict = Depends(require_auth)):
    iso = await db.iso_items.find_one({"id": iso_id, "user_id": user["id"]})
    if not iso:
        raise HTTPException(status_code=404, detail="ISO not found")
    await db.iso_items.delete_one({"id": iso_id})
    return {"message": "ISO deleted"}

# ============== PROFILE DATA ROUTES ==============

@api_router.get("/users/{username}/spins")
async def get_user_spins(username: str, limit: int = 50):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    spins = await db.spins.find({"user_id": target["id"]}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    result = []
    for spin in spins:
        record = await db.records.find_one({"id": spin["record_id"]}, {"_id": 0})
        if record:
            result.append({**spin, "record": record})
    return result

@api_router.get("/users/{username}/iso")
async def get_user_isos(username: str):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    isos = await db.iso_items.find({"user_id": target["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return isos

@api_router.get("/users/{username}/posts")
async def get_user_posts(username: str, current_user: Optional[Dict] = Depends(get_current_user), limit: int = 50):
    target = await db.users.find_one({"username": username.lower()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    posts = await db.posts.find({"user_id": target["id"]}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    result = []
    uid = current_user["id"] if current_user else None
    for post in posts:
        resp = await build_post_response(post, uid)
        result.append(resp)
    return result

# ============== BUZZING NOW (Trending) ROUTES ==============

@api_router.get("/buzzing")
async def get_buzzing_records(current_user: Optional[Dict] = Depends(get_current_user), limit: int = 10):
    """Get trending/buzzing records based on recent spins"""
    # Get spins from last 7 days
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    pipeline = [
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {"_id": "$record_id", "spin_count": {"$sum": 1}}},
        {"$sort": {"spin_count": -1}},
        {"$limit": limit}
    ]
    
    trending = await db.spins.aggregate(pipeline).to_list(limit)
    
    result = []
    for item in trending:
        record = await db.records.find_one({"id": item["_id"]}, {"_id": 0})
        if record:
            result.append({
                **record,
                "buzz_count": item["spin_count"]
            })
    
    return result

# ============== LIKES ROUTES ==============

@api_router.post("/posts/{post_id}/like")
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
    
    return {"message": "Post liked"}

@api_router.delete("/posts/{post_id}/like")
async def unlike_post(post_id: str, user: Dict = Depends(require_auth)):
    result = await db.likes.delete_one({"post_id": post_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Not liked")
    
    return {"message": "Post unliked"}

# ============== COMMENTS ROUTES ==============

@api_router.post("/posts/{post_id}/comments", response_model=CommentResponse)
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
    
    user_data = {"id": user["id"], "username": user["username"], "avatar_url": user.get("avatar_url")}
    
    return CommentResponse(**comment_doc, user=user_data)

@api_router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(post_id: str, current_user: Optional[Dict] = Depends(get_current_user)):
    comments = await db.comments.find({"post_id": post_id}, {"_id": 0}).sort("created_at", 1).to_list(100)
    
    result = []
    for comment in comments:
        comment_user = await db.users.find_one({"id": comment["user_id"]}, {"_id": 0, "password_hash": 0})
        user_data = {"id": comment_user["id"], "username": comment_user["username"], "avatar_url": comment_user.get("avatar_url")} if comment_user else None
        result.append(CommentResponse(**comment, user=user_data))
    
    return result

# ============== WEEKLY SUMMARY ROUTES ==============

@api_router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(user: Dict = Depends(require_auth)):
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).isoformat()
    week_end = now.isoformat()
    
    # Get spins from last week
    spins = await db.spins.find({
        "user_id": user["id"],
        "created_at": {"$gte": week_start}
    }, {"_id": 0}).to_list(1000)
    
    total_spins = len(spins)
    
    # Calculate top artist and album
    artist_counts = {}
    album_counts = {}
    
    for spin in spins:
        record = await db.records.find_one({"id": spin["record_id"]}, {"_id": 0})
        if record:
            artist = record.get("artist", "Unknown")
            album = record.get("title", "Unknown")
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
            album_key = f"{artist} - {album}"
            album_counts[album_key] = album_counts.get(album_key, 0) + 1
    
    top_artist = max(artist_counts, key=artist_counts.get) if artist_counts else None
    top_album_key = max(album_counts, key=album_counts.get) if album_counts else None
    top_album = top_album_key.split(" - ", 1)[1] if top_album_key and " - " in top_album_key else top_album_key
    
    # Determine listening mood (honey themed)
    moods = ["Buzzing", "Mellow", "Golden", "Sweet", "Warm", "Groovy"]
    listening_mood = moods[total_spins % len(moods)] if total_spins > 0 else "Quiet week"
    
    # Count records added
    records_added = await db.records.count_documents({
        "user_id": user["id"],
        "created_at": {"$gte": week_start}
    })
    
    summary_id = str(uuid.uuid4())
    
    # Check if summary already exists for this week
    existing = await db.weekly_summaries.find_one({
        "user_id": user["id"],
        "week_start": {"$gte": week_start}
    }, {"_id": 0})
    
    if existing:
        return WeeklySummaryResponse(**existing)
    
    summary_doc = {
        "id": summary_id,
        "user_id": user["id"],
        "week_start": week_start,
        "week_end": week_end,
        "total_spins": total_spins,
        "top_artist": top_artist,
        "top_album": top_album,
        "listening_mood": listening_mood,
        "records_added": records_added,
        "created_at": now.isoformat()
    }
    
    await db.weekly_summaries.insert_one(summary_doc)
    
    # Create activity post for weekly summary
    if total_spins > 0:
        post_id = str(uuid.uuid4())
        post_doc = {
            "id": post_id,
            "user_id": user["id"],
            "post_type": "WEEKLY_WRAP",
            "caption": f"HoneyGroove Weekly: {total_spins} spins this week. Top artist: {top_artist or 'N/A'}",
            "weekly_wrap_id": summary_id,
            "created_at": now.isoformat()
        }
        await db.posts.insert_one(post_doc)
    
    return WeeklySummaryResponse(**summary_doc)

# ============== SHARE GRAPHICS ROUTES ==============

@api_router.post("/share/generate")
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

# ============== DISCOGS OAUTH & IMPORT ROUTES ==============

@api_router.get("/discogs/oauth/start")
async def discogs_oauth_start(user: Dict = Depends(require_auth)):
    """Step 1: Get request token and return authorization URL"""
    if not DISCOGS_CONSUMER_KEY or not DISCOGS_CONSUMER_SECRET:
        raise HTTPException(status_code=400, detail="Discogs OAuth not configured. Please add Consumer Key and Secret in settings.")
    
    frontend_url = os.environ.get('FRONTEND_URL', '')
    callback_url = f"{frontend_url}/api/discogs/oauth/callback"
    
    try:
        oauth = OAuth1Session(
            client_key=DISCOGS_CONSUMER_KEY,
            client_secret=DISCOGS_CONSUMER_SECRET,
            callback_uri=callback_url
        )
        
        response = oauth.fetch_request_token(
            DISCOGS_REQUEST_TOKEN_URL,
            headers={"User-Agent": DISCOGS_USER_AGENT}
        )
        
        oauth_token = response.get('oauth_token')
        oauth_token_secret = response.get('oauth_token_secret')
        
        # Store the request token secret (keyed by oauth_token)
        oauth_request_tokens[oauth_token] = oauth_token_secret
        
        # Also store user_id mapping so we know who initiated this
        await db.discogs_oauth_pending.update_one(
            {"oauth_token": oauth_token},
            {"$set": {
                "oauth_token": oauth_token,
                "oauth_token_secret": oauth_token_secret,
                "user_id": user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        authorization_url = f"{DISCOGS_AUTHORIZE_URL}?oauth_token={oauth_token}"
        
        return {"authorization_url": authorization_url}
    
    except Exception as e:
        logger.error(f"Discogs OAuth start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start Discogs OAuth: {str(e)}")


@api_router.get("/discogs/oauth/callback")
async def discogs_oauth_callback(oauth_token: str = Query(...), oauth_verifier: str = Query(...)):
    """Step 2: Handle callback from Discogs, exchange for access token"""
    try:
        # Look up the stored request token secret
        pending = await db.discogs_oauth_pending.find_one({"oauth_token": oauth_token}, {"_id": 0})
        if not pending:
            # Try in-memory fallback
            oauth_token_secret = oauth_request_tokens.get(oauth_token)
            if not oauth_token_secret:
                raise HTTPException(status_code=400, detail="Invalid or expired OAuth token")
            user_id = None
        else:
            oauth_token_secret = pending["oauth_token_secret"]
            user_id = pending["user_id"]
        
        # Exchange for access token
        oauth = OAuth1Session(
            client_key=DISCOGS_CONSUMER_KEY,
            client_secret=DISCOGS_CONSUMER_SECRET,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
            verifier=oauth_verifier
        )
        
        access_tokens = oauth.fetch_access_token(
            DISCOGS_ACCESS_TOKEN_URL,
            headers={"User-Agent": DISCOGS_USER_AGENT}
        )
        
        access_token = access_tokens.get('oauth_token')
        access_token_secret = access_tokens.get('oauth_token_secret')
        
        # Get user identity from Discogs
        identity_oauth = OAuth1Session(
            client_key=DISCOGS_CONSUMER_KEY,
            client_secret=DISCOGS_CONSUMER_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )
        
        identity_resp = identity_oauth.get(
            f"{DISCOGS_API_BASE}/oauth/identity",
            headers={"User-Agent": DISCOGS_USER_AGENT}
        )
        identity_resp.raise_for_status()
        identity = identity_resp.json()
        discogs_username = identity.get("username", "")
        
        # Store the access tokens for this user
        if user_id:
            await db.discogs_tokens.update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "oauth_token": access_token,
                    "oauth_token_secret": access_token_secret,
                    "discogs_username": discogs_username,
                    "connected_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
            
            # Clean up pending
            await db.discogs_oauth_pending.delete_one({"oauth_token": oauth_token})
            oauth_request_tokens.pop(oauth_token, None)
        
        # Redirect to frontend import page with success
        from fastapi.responses import RedirectResponse
        frontend_base = os.environ.get('FRONTEND_URL', '')
        return RedirectResponse(url=f"{frontend_base}/collection?discogs=connected&username={discogs_username}")
    
    except Exception as e:
        logger.error(f"Discogs OAuth callback failed: {e}")
        frontend_base = os.environ.get('FRONTEND_URL', '')
        return RedirectResponse(url=f"{frontend_base}/collection?discogs=error&message={str(e)}")


@api_router.get("/discogs/status")
async def discogs_connection_status(user: Dict = Depends(require_auth)):
    """Check if user has connected their Discogs account"""
    token_doc = await db.discogs_tokens.find_one({"user_id": user["id"]}, {"_id": 0})
    
    if not token_doc:
        return {
            "connected": False,
            "discogs_username": None,
            "last_synced": None
        }
    
    # Check import progress
    progress = import_progress.get(user["id"])
    
    # Get last sync time
    last_import = await db.discogs_imports.find_one(
        {"user_id": user["id"]},
        {"_id": 0},
    )
    
    return {
        "connected": True,
        "discogs_username": token_doc.get("discogs_username"),
        "connected_at": token_doc.get("connected_at"),
        "last_synced": last_import.get("completed_at") if last_import else None,
        "import_status": progress if progress else None
    }


@api_router.post("/discogs/import")
async def start_discogs_import(user: Dict = Depends(require_auth)):
    """Start importing the user's Discogs collection"""
    token_doc = await db.discogs_tokens.find_one({"user_id": user["id"]}, {"_id": 0})
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Discogs account not connected. Please authorize first.")
    
    # Check if import is already in progress
    current = import_progress.get(user["id"])
    if current and current.get("status") == "in_progress":
        return current
    
    # Initialize progress
    import_progress[user["id"]] = {
        "status": "in_progress",
        "total": 0,
        "imported": 0,
        "skipped": 0,
        "error_message": None,
        "discogs_username": token_doc.get("discogs_username"),
        "started_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Run import in background
    auth_type = token_doc.get("auth_type", "oauth")
    asyncio.create_task(_run_discogs_import(
        user["id"],
        token_doc.get("oauth_token"),
        token_doc.get("oauth_token_secret"),
        token_doc["discogs_username"],
        auth_type
    ))
    
    return import_progress[user["id"]]


@api_router.get("/discogs/import/progress")
async def get_import_progress(user: Dict = Depends(require_auth)):
    """Get current import progress"""
    progress = import_progress.get(user["id"])
    if not progress:
        # Check if there was a past import
        last_import = await db.discogs_imports.find_one(
            {"user_id": user["id"]},
            {"_id": 0},
        )
        if last_import:
            return {
                "status": "completed",
                "total": last_import.get("total", 0),
                "imported": last_import.get("imported", 0),
                "skipped": last_import.get("skipped", 0),
                "error_message": None,
                "discogs_username": last_import.get("discogs_username"),
                "last_synced": last_import.get("completed_at")
            }
        return {"status": "idle", "total": 0, "imported": 0, "skipped": 0}
    return progress


async def _run_discogs_import(user_id: str, oauth_token: str, oauth_token_secret: str, discogs_username: str, auth_type: str = "oauth"):
    """Background task to import Discogs collection"""
    try:
        # Set up the appropriate session based on auth type
        if auth_type == "personal_token":
            # Use personal token auth
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Discogs token={DISCOGS_TOKEN}",
                "User-Agent": DISCOGS_USER_AGENT
            })
        else:
            # Use OAuth session
            session = OAuth1Session(
                client_key=DISCOGS_CONSUMER_KEY,
                client_secret=DISCOGS_CONSUMER_SECRET,
                resource_owner_key=oauth_token,
                resource_owner_secret=oauth_token_secret
            )
            session.headers.update({"User-Agent": DISCOGS_USER_AGENT})
        
        # First, get the total count from folder 0 (All)
        first_page_url = f"{DISCOGS_API_BASE}/users/{discogs_username}/collection/folders/0/releases"
        first_resp = session.get(first_page_url, params={"page": 1, "per_page": 100})
        
        if first_resp.status_code != 200:
            import_progress[user_id]["status"] = "error"
            import_progress[user_id]["error_message"] = f"Failed to fetch collection: {first_resp.status_code}"
            return
        
        first_data = first_resp.json()
        pagination = first_data.get("pagination", {})
        total_items = pagination.get("items", 0)
        total_pages = pagination.get("pages", 1)
        
        import_progress[user_id]["total"] = total_items
        
        if total_items == 0:
            import_progress[user_id]["status"] = "completed"
            import_progress[user_id]["error_message"] = "No releases found in your Discogs collection."
            return
        
        # Process all pages
        all_releases = first_data.get("releases", [])
        
        for page in range(2, total_pages + 1):
            # Rate limit: respect Discogs 60 req/min
            remaining = int(first_resp.headers.get('X-Discogs-Ratelimit-Remaining', 60))
            if remaining < 5:
                await asyncio.sleep(30)
            else:
                await asyncio.sleep(1.1)  # ~55 req/min to be safe
            
            page_resp = session.get(
                first_page_url,
                params={"page": page, "per_page": 100}
            )
            
            if page_resp.status_code == 429:
                # Rate limited - wait and retry
                await asyncio.sleep(60)
                page_resp = session.get(
                    first_page_url,
                    params={"page": page, "per_page": 100}
                )
            
            if page_resp.status_code == 200:
                page_data = page_resp.json()
                all_releases.extend(page_data.get("releases", []))
                first_resp = page_resp  # update for rate limit headers
            else:
                logger.warning(f"Failed to fetch page {page}: {page_resp.status_code}")
        
        # Now import each release into the user's collection
        imported = 0
        skipped = 0
        now = datetime.now(timezone.utc).isoformat()
        
        for release in all_releases:
            try:
                basic_info = release.get("basic_information", {})
                discogs_id = basic_info.get("id")
                
                if not discogs_id:
                    skipped += 1
                    import_progress[user_id]["skipped"] = skipped
                    continue
                
                # Check if already exists in user's collection
                existing = await db.records.find_one({
                    "user_id": user_id,
                    "discogs_id": discogs_id
                })
                
                if existing:
                    skipped += 1
                    import_progress[user_id]["skipped"] = skipped
                    import_progress[user_id]["imported"] = imported
                    continue
                
                # Parse artist(s)
                artists = basic_info.get("artists", [])
                artist_name = ", ".join(a.get("name", "") for a in artists) if artists else "Unknown Artist"
                
                # Get cover image
                cover_url = basic_info.get("cover_image") or basic_info.get("thumb")
                
                # Get format
                formats = basic_info.get("formats", [])
                format_name = formats[0].get("name", "Vinyl") if formats else "Vinyl"
                
                record_id = str(uuid.uuid4())
                record_doc = {
                    "id": record_id,
                    "user_id": user_id,
                    "discogs_id": discogs_id,
                    "title": basic_info.get("title", "Unknown Title"),
                    "artist": artist_name,
                    "cover_url": cover_url,
                    "year": basic_info.get("year"),
                    "format": format_name,
                    "notes": f"Imported from Discogs",
                    "source": "discogs_import",
                    "created_at": now
                }
                
                await db.records.insert_one(record_doc)
                imported += 1
                import_progress[user_id]["imported"] = imported
                
            except Exception as e:
                logger.error(f"Failed to import release: {e}")
                skipped += 1
                import_progress[user_id]["skipped"] = skipped
        
        # Mark complete
        import_progress[user_id]["status"] = "completed"
        import_progress[user_id]["imported"] = imported
        import_progress[user_id]["skipped"] = skipped
        
        # Store import record
        await db.discogs_imports.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "discogs_username": discogs_username,
                "total": total_items,
                "imported": imported,
                "skipped": skipped,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        # Create activity post for the import
        if imported > 0:
            post_id = str(uuid.uuid4())
            post_doc = {
                "id": post_id,
                "user_id": user_id,
                "post_type": "record_added",
                "content": f"Imported {imported} records from Discogs",
                "record_id": None,
                "haul_id": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.posts.insert_one(post_doc)
        
        logger.info(f"Discogs import complete for {user_id}: {imported} imported, {skipped} skipped out of {total_items}")
        
    except Exception as e:
        logger.error(f"Discogs import failed for {user_id}: {e}")
        import_progress[user_id]["status"] = "error"
        import_progress[user_id]["error_message"] = str(e)


@api_router.delete("/discogs/disconnect")
async def disconnect_discogs(user: Dict = Depends(require_auth)):
    """Disconnect Discogs account"""
    await db.discogs_tokens.delete_one({"user_id": user["id"]})
    await db.discogs_oauth_pending.delete_many({"user_id": user["id"]})
    import_progress.pop(user["id"], None)
    return {"message": "Discogs account disconnected"}


class DiscogsTokenConnect(BaseModel):
    discogs_username: str

@api_router.post("/discogs/connect-token")
async def connect_discogs_with_token(data: DiscogsTokenConnect, user: Dict = Depends(require_auth)):
    """Connect Discogs using the app's personal access token (no OAuth needed)"""
    if not DISCOGS_TOKEN:
        raise HTTPException(status_code=400, detail="Discogs token not configured")
    
    # Verify the username exists on Discogs
    headers = {
        "Authorization": f"Discogs token={DISCOGS_TOKEN}",
        "User-Agent": DISCOGS_USER_AGENT
    }
    try:
        resp = requests.get(
            f"{DISCOGS_API_BASE}/users/{data.discogs_username}",
            headers=headers, timeout=10
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Discogs user '{data.discogs_username}' not found")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify Discogs user: {str(e)}")
    
    # Store as token-based connection
    await db.discogs_tokens.update_one(
        {"user_id": user["id"]},
        {"$set": {
            "user_id": user["id"],
            "auth_type": "personal_token",
            "discogs_username": data.discogs_username,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": f"Connected as {data.discogs_username}", "discogs_username": data.discogs_username}

# ============== FILE UPLOAD ROUTES ==============

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: Dict = Depends(require_auth)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    path = f"{APP_NAME}/uploads/{user['id']}/{uuid.uuid4()}.{ext}"
    
    data = await file.read()
    
    try:
        result = put_object(path, data, file.content_type or "image/jpeg")
        
        # Store file reference
        file_id = str(uuid.uuid4())
        await db.files.insert_one({
            "id": file_id,
            "user_id": user["id"],
            "storage_path": result["path"],
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": result.get("size", len(data)),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"file_id": file_id, "path": result["path"]}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

@api_router.get("/files/{file_id}")
async def get_file(file_id: str, user: Dict = Depends(require_auth)):
    file_record = await db.files.find_one({"id": file_id}, {"_id": 0})
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        data, content_type = get_object(file_record["storage_path"])
        return Response(content=data, media_type=content_type)
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

# ============== STATS ROUTES ==============

@api_router.get("/stats")
async def get_global_stats():
    users_count = await db.users.count_documents({})
    records_count = await db.records.count_documents({})
    spins_count = await db.spins.count_documents({})
    hauls_count = await db.hauls.count_documents({})
    
    return {
        "users": users_count,
        "records": records_count,
        "spins": spins_count,
        "hauls": hauls_count
    }

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Welcome to HoneyGroove API", "version": "1.0.0"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Create indexes
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
    
    # Initialize storage
    try:
        init_storage()
        logger.info("Storage initialized")
    except Exception as e:
        logger.warning(f"Storage initialization skipped: {e}")
    
    logger.info("HoneyGroove API started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
