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
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 168))

# Discogs
DISCOGS_TOKEN = os.environ.get('DISCOGS_TOKEN', '')
DISCOGS_USER_AGENT = os.environ.get('DISCOGS_USER_AGENT', 'HoneyGroove/1.0')
DISCOGS_CONSUMER_KEY = os.environ.get('DISCOGS_CONSUMER_KEY', '')
DISCOGS_CONSUMER_SECRET = os.environ.get('DISCOGS_CONSUMER_SECRET', '')
DISCOGS_REQUEST_TOKEN_URL = "https://api.discogs.com/oauth/request_token"
DISCOGS_AUTHORIZE_URL = "https://www.discogs.com/oauth/authorize"
DISCOGS_ACCESS_TOKEN_URL = "https://api.discogs.com/oauth/access_token"
DISCOGS_API_BASE = "https://api.discogs.com"

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
PLATFORM_FEE_PERCENT = 4.0
FRONTEND_URL = os.environ.get("FRONTEND_URL", "")

# Auth
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
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


def init_storage():
    global storage_key
    if not EMERGENT_KEY:
        logger.warning("EMERGENT_LLM_KEY not set, storage disabled")
        return
    try:
        resp = requests.get(f"{STORAGE_URL}/key", headers={"Authorization": f"Bearer {EMERGENT_KEY}"}, params={"app_name": APP_NAME})
        if resp.status_code == 200:
            storage_key = resp.json().get("key")
    except Exception as e:
        logger.warning(f"Storage init error: {e}")


def put_object(path: str, data: bytes, content_type: str) -> dict:
    if not storage_key:
        raise Exception("Storage not initialized")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{storage_key}/{path}",
        headers={"Authorization": f"Bearer {EMERGENT_KEY}", "Content-Type": content_type},
        data=data
    )
    return resp.json() if resp.status_code == 200 else {}


def get_object(path: str) -> tuple:
    if not storage_key:
        raise Exception("Storage not initialized")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{storage_key}/{path}",
        headers={"Authorization": f"Bearer {EMERGENT_KEY}"}
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
        resp = requests.get(f"{DISCOGS_API_BASE}/database/search", params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            results = []
            for item in resp.json().get("results", []):
                parts = item.get("title", "").split(" - ", 1)
                artist = parts[0].strip() if len(parts) > 1 else "Unknown"
                title = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                results.append({
                    "discogs_id": item.get("id"),
                    "artist": artist,
                    "title": title,
                    "year": item.get("year"),
                    "genre": item.get("genre", []),
                    "cover_url": item.get("cover_image"),
                    "format": item.get("format", []),
                    "label": item.get("label", []),
                })
            return results
    except Exception as e:
        logger.error(f"Discogs search error: {e}")
    return []


def get_discogs_release(release_id: int) -> Optional[Dict]:
    headers = {"User-Agent": DISCOGS_USER_AGENT}
    params = {}
    if DISCOGS_TOKEN:
        params["token"] = DISCOGS_TOKEN
    try:
        resp = requests.get(f"{DISCOGS_API_BASE}/releases/{release_id}", params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            artists = ", ".join([a.get("name", "") for a in data.get("artists", [])])
            return {
                "discogs_id": data.get("id"),
                "artist": artists or "Unknown",
                "title": data.get("title", "Unknown"),
                "year": data.get("year"),
                "genre": data.get("genres", []),
                "style": data.get("styles", []),
                "cover_url": data.get("images", [{}])[0].get("uri") if data.get("images") else None,
                "tracklist": [{"position": t.get("position"), "title": t.get("title"), "duration": t.get("duration")} for t in data.get("tracklist", [])],
                "format": [f.get("name", "") for f in data.get("formats", [])],
                "label": [l.get("name", "") for l in data.get("labels", [])],
                "country": data.get("country"),
                "notes": data.get("notes"),
            }
    except Exception as e:
        logger.error(f"Discogs release error: {e}")
    return None


async def create_notification(user_id: str, ntype: str, title: str, body: str, data: Dict = None):
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
