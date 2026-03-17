"""Shared database, config, auth, storage, and notification helpers."""
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, List
from pathlib import Path
from dotenv import load_dotenv
import os
import bcrypt
import jwt
import uuid
import logging
import requests
import time as _time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv()

# MongoDB — connect with pool limits for M0 Atlas (500 connection cap)
import asyncio as _asyncio

mongo_url = os.environ['MONGO_URL']
_db_name = os.environ['DB_NAME']
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    maxPoolSize=10,          # Max 10 connections per process (M0 = 500 cap shared across all clients)
    minPoolSize=1,           # Keep 1 warm connection
    maxIdleTimeMS=45000,     # Close idle connections after 45s
    maxConnecting=2,         # Limit concurrent connection establishment
    socketTimeoutMS=30000,   # Kill stuck operations after 30s
    retryWrites=True,
    retryReads=True,
)
db = client[_db_name]

logger = logging.getLogger("database")

async def verify_db_connection():
    """Called at startup — retries 3 times with backoff before giving up."""
    for attempt in range(1, 4):
        try:
            await client.admin.command('ping')
            count = await db.users.estimated_document_count()
            logger.info(f"DATABASE CONNECTED (attempt {attempt}) — cluster: {mongo_url.split('@')[1].split('/')[0]}, db: {_db_name}, users: {count}")
            return True
        except Exception as e:
            logger.error(f"DATABASE CONNECTION ATTEMPT {attempt}/3 FAILED — {type(e).__name__}: {e}")
            if attempt < 3:
                wait = attempt * 3
                logger.info(f"Retrying in {wait}s...")
                await _asyncio.sleep(wait)
    logger.error("DATABASE CONNECTION FAILED after 3 attempts — app may not function correctly")
    return False

# JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 720))

# Discogs
DISCOGS_TOKEN = os.environ.get('DISCOGS_TOKEN', '')
DISCOGS_USER_AGENT = os.environ.get('DISCOGS_USER_AGENT', 'HoneyGroove/1.0')
DISCOGS_CONSUMER_KEY = os.environ.get('DISCOGS_CONSUMER_KEY', '')
DISCOGS_CONSUMER_SECRET = os.environ.get('DISCOGS_CONSUMER_SECRET', '')
DISCOGS_REQUEST_TOKEN_URL = "https://api.discogs.com/oauth/request_token"
DISCOGS_AUTHORIZE_URL = "https://www.discogs.com/oauth/authorize"
DISCOGS_ACCESS_TOKEN_URL = "https://api.discogs.com/oauth/access_token"
DISCOGS_API_BASE = "https://api.discogs.com"

# Country-to-adjective mapping for international pressing tags
_COUNTRY_ADJECTIVE = {
    "Japan": "Japanese", "Germany": "German", "France": "French", "Italy": "Italian",
    "UK": "UK", "Canada": "Canadian", "Australia": "Australian", "Brazil": "Brazilian",
    "Netherlands": "Dutch", "Spain": "Spanish", "Mexico": "Mexican", "Argentina": "Argentine",
    "South Korea": "Korean", "Taiwan": "Taiwanese", "India": "Indian", "Greece": "Greek",
    "Portugal": "Portuguese", "Turkey": "Turkish", "South Africa": "South African",
    "New Zealand": "New Zealand", "Europe": "European", "Sweden": "Swedish",
    "Norway": "Norwegian", "Denmark": "Danish", "Finland": "Finnish",
    "Philippines": "Philippine", "Colombia": "Colombian", "Chile": "Chilean",
    "Venezuela": "Venezuelan", "Peru": "Peruvian", "Uruguay": "Uruguayan",
    "Yugoslavia": "Yugoslavian", "Czechoslovakia": "Czechoslovak", "USSR": "Soviet",
    "Poland": "Polish", "Hungary": "Hungarian", "Romania": "Romanian",
}

def derive_variant_tag(color_variant: str, country: str, descriptions: list = None) -> str:
    """Generate a variant tag when color_variant is null.
    Priority: format descriptions (Club Edition, Limited Edition, etc.) > country pressing > None."""
    if color_variant:
        return color_variant
    descriptions = descriptions or []
    # Check format descriptions for meaningful edition tags
    edition_keywords = ["Club Edition", "Limited Edition", "Remastered", "Promo", "DJ Copy",
                        "Test Pressing", "Mono", "Quadraphonic", "Half-Speed Mastered",
                        "Deluxe Edition", "Special Edition", "Anniversary", "Numbered"]
    for d in descriptions:
        for kw in edition_keywords:
            if kw.lower() in d.lower():
                return d
    # Fall back to country pressing tag (skip US as it's the default)
    if country and country != "US":
        adj = _COUNTRY_ADJECTIVE.get(country, country)
        return f"{adj} Pressing"
    return None

def _discogs_session() -> requests.Session:
    """Create a requests session with automatic retry for transient errors."""
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

# In-memory stores
oauth_request_tokens: Dict[str, str] = {}
import_progress: Dict[str, Dict] = {}

# Storage
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
APP_NAME = "honeygroove"
storage_key = None

# Stripe
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PLATFORM_FEE_PERCENT = 6.0  # Default, overridden by platform_settings collection
# Hard-coded to production domain to prevent broken email links from env misconfiguration
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://www.thehoneygroove.com")

# Auth
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, username: str = "", email: str = "", is_admin: bool = False, avatar_url: str = "") -> str:
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "username": username,
        "email": email,
        "is_admin": is_admin,
        "avatar_url": avatar_url,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
        return user
    except Exception:
        return None


async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


async def get_hidden_user_ids() -> list:
    """Return IDs of users that should be excluded from public feeds (hidden, test, demo accounts)."""
    hidden = await db.users.find(
        {"$or": [
            {"is_hidden": True},
            {"is_test": True},
            {"email": {"$regex": "@(test|example)\\.com$", "$options": "i"}},
            {"username": {"$regex": "^(demo|test)", "$options": "i"}},
            {"username": "demo"},
        ]},
        {"_id": 0, "id": 1}
    ).to_list(100)
    return [u["id"] for u in hidden]


async def get_blocked_user_ids(user_id: str) -> list:
    """Return IDs of users that user_id has blocked."""
    blocks = await db.blocks.find({"blocker_id": user_id}, {"_id": 0, "blocked_id": 1}).to_list(500)
    return [b["blocked_id"] for b in blocks]


async def get_blocked_by_ids(user_id: str) -> list:
    """Return IDs of users who have blocked user_id."""
    blocks = await db.blocks.find({"blocked_id": user_id}, {"_id": 0, "blocker_id": 1}).to_list(500)
    return [b["blocker_id"] for b in blocks]


async def get_all_blocked_ids(user_id: str) -> list:
    """Return all user IDs that should be invisible to user_id (both directions of blocking)."""
    blocks = await db.blocks.find(
        {"$or": [{"blocker_id": user_id}, {"blocked_id": user_id}]},
        {"_id": 0, "blocker_id": 1, "blocked_id": 1}
    ).to_list(1000)
    ids = set()
    for b in blocks:
        if b["blocker_id"] == user_id:
            ids.add(b["blocked_id"])
        else:
            ids.add(b["blocker_id"])
    return list(ids)


def init_storage():
    global storage_key
    if not EMERGENT_KEY:
        logger.warning("EMERGENT_LLM_KEY not set, storage disabled")
        return
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"app_name": APP_NAME, "emergent_key": EMERGENT_KEY})
        if resp.status_code == 200:
            storage_key = resp.json().get("storage_key")
            if storage_key:
                logger.info("Storage initialized")
            else:
                logger.warning("Storage init returned no key")
        else:
            logger.warning(f"Storage init failed: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        logger.warning(f"Storage init error: {e}")


def put_object(path: str, data: bytes, content_type: str) -> dict:
    if not storage_key:
        raise Exception("Storage not initialized")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"Authorization": f"Bearer {EMERGENT_KEY}", "X-Storage-Key": storage_key, "Content-Type": content_type},
        data=data
    )
    if resp.status_code == 200:
        return resp.json()
    logger.error(f"Storage put failed: {resp.status_code} {resp.text[:200]}")
    return {}


def _ensure_storage():
    """Lazy init: call init_storage if not yet done."""
    global storage_key
    if storage_key is None and EMERGENT_KEY:
        init_storage()


def get_object(path: str) -> tuple:
    _ensure_storage()
    if not storage_key:
        raise Exception("Storage not initialized")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"Authorization": f"Bearer {EMERGENT_KEY}", "X-Storage-Key": storage_key}
    )
    if resp.status_code == 200:
        return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
    return None, None


def search_discogs(query: str, search_type: str = "release") -> List[Dict]:
    headers = {"User-Agent": DISCOGS_USER_AGENT}
    params = {"q": query, "type": search_type, "per_page": 20}
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN
    try:
        s = _discogs_session()
        resp = s.get(f"{DISCOGS_API_BASE}/database/search", params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            results = []
            for item in resp.json().get("results", []):
                parts = item.get("title", "").split(" - ", 1)
                artist = parts[0].strip() if len(parts) > 1 else "Unknown"
                title = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                # Extract color/variant info from formats
                color_variant = None
                format_name = None
                descriptions = []
                for fmt in item.get("formats", []):
                    fname = fmt.get("name", "")
                    if fname and fname not in ("All Media",):
                        format_name = fname
                    ftext = fmt.get("text", "")
                    if ftext:
                        color_variant = ftext
                    descs = fmt.get("descriptions", [])
                    descriptions.extend(descs)
                # If no color_variant from text, check descriptions for variant info
                if not color_variant and descriptions:
                    variant_keywords = {"Picture Disc", "Colored", "White", "Red", "Blue", "Green",
                                        "Yellow", "Orange", "Pink", "Purple", "Clear", "Splatter",
                                        "Marble", "Gold", "Silver", "Translucent", "Transparent",
                                        "Glow In The Dark", "Flexi-disc", "Shape", "Etched"}
                    for d in descriptions:
                        if d in variant_keywords or any(k.lower() in d.lower() for k in variant_keywords):
                            color_variant = d
                            break
                # Fallback: derive tag from edition descriptions or country
                if not color_variant:
                    color_variant = derive_variant_tag(None, item.get("country"), descriptions)
                # Build compact format string
                format_str = format_name or ""
                if descriptions:
                    unique_descs = list(dict.fromkeys(d for d in descriptions if d not in ("Album", "Compilation")))
                    if unique_descs:
                        format_str = f"{format_name} ({', '.join(unique_descs[:2])})" if format_name else ", ".join(unique_descs[:2])
                labels = item.get("label", [])
                main_label = labels[0] if labels else None
                results.append({
                    "discogs_id": item.get("id"),
                    "artist": artist,
                    "title": title,
                    "year": item.get("year"),
                    "genre": item.get("genre", []),
                    "cover_url": item.get("cover_image"),
                    "format": format_str or (item.get("format", [None])[0] if item.get("format") else None),
                    "label": main_label,
                    "catno": item.get("catno"),
                    "country": item.get("country"),
                    "color_variant": color_variant,
                })
            return results
    except Exception as e:
        logger.error(f"Discogs search error: {e}")
    return []


def get_discogs_master_versions(master_id: int, page: int = 1, per_page: int = 100) -> Optional[Dict]:
    """Fetch all versions of a master release from Discogs."""
    headers = {"User-Agent": DISCOGS_USER_AGENT}
    params = {"per_page": per_page, "page": page}
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN
    try:
        s = _discogs_session()
        resp = s.get(
            f"{DISCOGS_API_BASE}/masters/{master_id}/versions",
            params=params, headers=headers, timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"Discogs master versions error for {master_id}: {e}")
    return None


def get_discogs_master(master_id: int) -> Optional[Dict]:
    """Fetch master release data from Discogs (community stats, main image)."""
    headers = {"User-Agent": DISCOGS_USER_AGENT}
    params = {}
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN
    try:
        s = _discogs_session()
        resp = s.get(
            f"{DISCOGS_API_BASE}/masters/{master_id}",
            params=params, headers=headers, timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            images = data.get("images", [])
            cover_url = images[0].get("uri") if images else None
            return {
                "master_id": master_id,
                "title": data.get("title"),
                "year": data.get("year"),
                "cover_url": cover_url,
                "num_for_sale": data.get("num_for_sale", 0),
                "lowest_price": data.get("lowest_price"),
                "most_recent_release": data.get("most_recent_release"),
                "main_release": data.get("main_release"),
            }
        if resp.status_code == 429:
            logger.warning(f"Discogs rate limit on master {master_id}")
    except Exception as e:
        logger.error(f"Discogs master error for {master_id}: {e}")
    return None


def get_discogs_release(release_id: int) -> Optional[Dict]:
    headers = {"User-Agent": DISCOGS_USER_AGENT}
    params = {}
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN
    s = _discogs_session()
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            resp = s.get(f"{DISCOGS_API_BASE}/releases/{release_id}", params=params, headers=headers, timeout=15)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 2))
                logger.warning(f"Discogs rate limit hit for {release_id}, retry {attempt+1}/{max_retries} after {wait}s")
                if attempt < max_retries:
                    _time.sleep(wait)
                    continue
                return None
            if resp.status_code != 200:
                logger.warning(f"Discogs release {release_id}: HTTP {resp.status_code}")
                return None
            data = resp.json()
            artists = ", ".join([a.get("name", "") for a in data.get("artists", [])])
            # Extract label + catno from first label entry
            labels_raw = data.get("labels", [])
            label_names = [l.get("name", "") for l in labels_raw]
            catno = labels_raw[0].get("catno", "") if labels_raw else ""
            # Extract color variant from formats text field
            color_variant = None
            all_descriptions = []
            for fmt in data.get("formats", []):
                ftext = fmt.get("text", "")
                if ftext:
                    color_variant = ftext
                    break
                all_descriptions.extend(fmt.get("descriptions", []))
            # If no color_variant from text, check descriptions for variant info
            if not color_variant and all_descriptions:
                variant_keywords = {"Picture Disc", "Colored", "White", "Red", "Blue", "Green",
                                    "Yellow", "Orange", "Pink", "Purple", "Clear", "Splatter",
                                    "Marble", "Gold", "Silver", "Translucent", "Transparent",
                                    "Glow In The Dark", "Flexi-disc", "Shape", "Etched"}
                for d in all_descriptions:
                    if d in variant_keywords or any(k.lower() in d.lower() for k in variant_keywords):
                        color_variant = d
                        break
            # Fallback: derive tag from edition descriptions or country
            if not color_variant:
                color_variant = derive_variant_tag(None, data.get("country"), all_descriptions)
            community = data.get("community", {})
            # Extract barcode / UPC from identifiers
            barcode = None
            for ident in data.get("identifiers", []):
                if ident.get("type") == "Barcode" and ident.get("value"):
                    barcode = ident["value"].strip()
                    break
            # Image resolution: release images > master_id images > thumb
            cover_url = None
            thumb_url = data.get("thumb")
            if data.get("images"):
                cover_url = data["images"][0].get("uri")
                thumb_url = data["images"][0].get("uri150") or thumb_url
            # Fallback: fetch master_id image if release has none
            if not cover_url and data.get("master_id"):
                try:
                    master_resp = s.get(
                        f"{DISCOGS_API_BASE}/masters/{data['master_id']}",
                        params=params, headers=headers, timeout=15
                    )
                    if master_resp.status_code == 200:
                        master_data = master_resp.json()
                        if master_data.get("images"):
                            cover_url = master_data["images"][0].get("uri")
                            thumb_url = master_data["images"][0].get("uri150") or thumb_url
                except Exception as me:
                    logger.warning(f"Master image fallback failed for master_id={data.get('master_id')}: {me}")
            # Last resort: use thumb as cover
            if not cover_url and thumb_url:
                cover_url = thumb_url
            return {
                "discogs_id": data.get("id"),
                "master_id": data.get("master_id"),
                "artist": artists or "Unknown",
                "title": data.get("title", "Unknown"),
                "year": data.get("year"),
                "genre": data.get("genres", []),
                "style": data.get("styles", []),
                "cover_url": cover_url,
                "thumb_url": thumb_url,
                "tracklist": [{"position": t.get("position"), "title": t.get("title"), "duration": t.get("duration")} for t in data.get("tracklist", [])],
                "format": [f.get("name", "") for f in data.get("formats", [])],
                "format_descriptions": [desc for f in data.get("formats", []) for desc in f.get("descriptions", [])],
                "label": label_names,
                "catno": catno,
                "country": data.get("country"),
                "color_variant": color_variant,
                "notes": data.get("notes"),
                "barcode": barcode,
                "community_have": community.get("have", 0),
                "community_want": community.get("want", 0),
                "num_for_sale": data.get("num_for_sale", 0),
            }
        except Exception as e:
            logger.error(f"Discogs release error (attempt {attempt+1}): {e}")
    return None


def get_discogs_market_data(release_id: int) -> Optional[Dict]:
    """Fetch price statistics from Discogs marketplace for a release.
    Forces USD via curr_abbr parameter to avoid currency mismatches.
    """
    headers = {"User-Agent": DISCOGS_USER_AGENT}
    params = {"curr_abbr": "USD"}
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN
    try:
        s = _discogs_session()

        # Price suggestions with forced USD
        resp = s.get(
            f"{DISCOGS_API_BASE}/marketplace/price_suggestions/{release_id}",
            params=params, headers=headers, timeout=15
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

        # Fallback: release endpoint lowest_price (always USD)
        resp2 = s.get(
            f"{DISCOGS_API_BASE}/releases/{release_id}",
            params=params, headers=headers, timeout=15
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
        logger.error(f"Discogs market data error for {release_id}: {e}")
    return None


async def create_notification(user_id: str, ntype: str, title: str, body: str, data: Dict = None, sender_id: str = None):
    # Check recipient's in-app notification preference
    recipient = await db.users.find_one({"id": user_id}, {"_id": 0, "notification_pref_app": 1, "notification_preference": 1, "following": 1})
    pref = (recipient or {}).get("notification_pref_app") or (recipient or {}).get("notification_preference", "all")
    if pref == "none":
        return  # User opted out of all in-app notifications
    if pref == "following":
        sid = sender_id or (data or {}).get("sender_id") or (data or {}).get("user_id") or (data or {}).get("from_user_id")
        if sid:
            following_list = (recipient or {}).get("following", [])
            if sid not in following_list:
                return  # User only wants notifications from people they follow

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": ntype,
        "title": title,
        "body": body,
        "data": data or {},
        "read": False,
        "created_at": now,
    }
    await db.notifications.insert_one(doc)


async def should_send_notification_email(user_id: str, sender_id: str = None) -> bool:
    """Check if a user should receive notification emails (not Weekly Wax/transactional — those always send)."""
    recipient = await db.users.find_one({"id": user_id}, {"_id": 0, "notification_pref_email": 1, "notification_preference": 1, "following": 1})
    pref = (recipient or {}).get("notification_pref_email") or (recipient or {}).get("notification_preference", "all")
    if pref == "none":
        return False
    if pref == "following" and sender_id:
        following_list = (recipient or {}).get("following", [])
        if sender_id not in following_list:
            return False
    return True
