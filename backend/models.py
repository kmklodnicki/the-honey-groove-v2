"""All Pydantic models for HoneyGroove API."""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any


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
    setup: Optional[str] = None
    location: Optional[str] = None
    favorite_genre: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    created_at: str
    collection_count: int = 0
    spin_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    completed_transactions: int = 0
    onboarding_completed: bool = False
    founding_member: bool = False
    is_admin: bool = False
    email_verified: bool = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    setup: Optional[str] = None
    location: Optional[str] = None
    favorite_genre: Optional[str] = None
    avatar_url: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    onboarding_completed: Optional[bool] = None

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
    label: Optional[str] = None
    catno: Optional[str] = None
    color_variant: Optional[str] = None
    genre: Optional[List[str]] = None

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
POST_TYPE_MAP = {"spin": "NOW_SPINNING", "haul": "NEW_HAUL", "record_added": "ADDED_TO_COLLECTION", "weekly_summary": "WEEKLY_WRAP"}

class PostCreate(BaseModel):
    post_type: str
    caption: Optional[str] = None
    image_url: Optional[str] = None
    record_id: Optional[str] = None
    haul_id: Optional[str] = None
    iso_id: Optional[str] = None
    weekly_wrap_id: Optional[str] = None
    track: Optional[str] = None
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
    prompt_text: Optional[str] = None
    record_title: Optional[str] = None
    record_artist: Optional[str] = None
    cover_url: Optional[str] = None
    created_at: str
    likes_count: int = 0
    comments_count: int = 0
    user: Optional[Dict[str, Any]] = None
    record: Optional[Dict[str, Any]] = None
    haul: Optional[Dict[str, Any]] = None
    iso: Optional[Dict[str, Any]] = None
    is_liked: bool = False
    is_pinned: bool = False
    content: Optional[str] = None

# Comment Models
class CommentCreate(BaseModel):
    post_id: str
    content: str
    parent_id: Optional[str] = None  # For replies

class CommentResponse(BaseModel):
    id: str
    post_id: str
    user_id: str
    content: str
    created_at: str
    parent_id: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    likes_count: int = 0
    is_liked: bool = False
    replies: Optional[List[Any]] = None

# ISO Models
class ISOCreate(BaseModel):
    artist: str
    album: str
    record_id: Optional[str] = None
    priority: str = "MED"
    pressing_notes: Optional[str] = None
    condition_pref: Optional[str] = None
    tags: Optional[List[str]] = None
    target_price_min: Optional[float] = None
    target_price_max: Optional[float] = None

class ISOResponse(BaseModel):
    id: str
    user_id: str
    artist: str
    album: str
    record_id: Optional[str] = None
    discogs_id: Optional[int] = None
    cover_url: Optional[str] = None
    year: Optional[int] = None
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

class NowSpinningCreate(BaseModel):
    record_id: str
    track: Optional[str] = None
    caption: Optional[str] = None
    mood: Optional[str] = None

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
    discogs_id: Optional[int] = None
    cover_url: Optional[str] = None
    year: Optional[int] = None

class VinylMoodCreate(BaseModel):
    mood: str
    caption: Optional[str] = None
    record_id: Optional[str] = None

class NoteCreate(BaseModel):
    text: str
    record_id: Optional[str] = None
    image_url: Optional[str] = None

# Marketplace Listing Models
LISTING_TYPES = ["BUY_NOW", "MAKE_OFFER", "TRADE"]
LISTING_CONDITIONS = ["Mint", "Near Mint", "Very Good Plus", "Very Good", "Good Plus", "Good", "Fair"]

class ListingCreate(BaseModel):
    record_id: Optional[str] = None
    discogs_id: Optional[int] = None
    artist: str
    album: str
    cover_url: Optional[str] = None
    year: Optional[int] = None
    condition: Optional[str] = None
    pressing_notes: Optional[str] = None
    listing_type: str
    price: Optional[float] = None
    description: Optional[str] = None
    photo_urls: List[str] = Field(..., min_length=1, max_length=10)
    insured: Optional[bool] = None

class ListingResponse(BaseModel):
    id: str
    user_id: str
    record_id: Optional[str] = None
    discogs_id: Optional[int] = None
    artist: str
    album: str
    cover_url: Optional[str] = None
    year: Optional[int] = None
    condition: Optional[str] = None
    pressing_notes: Optional[str] = None
    listing_type: str
    price: Optional[float] = None
    description: Optional[str] = None
    photo_urls: List[str] = []
    insured: Optional[bool] = None
    offplatform_flagged: Optional[bool] = None
    status: str = "ACTIVE"
    created_at: str
    user: Optional[Dict[str, Any]] = None

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

class ShareGraphicRequest(BaseModel):
    graphic_type: str
    format: str = "square"
    record_id: Optional[str] = None
    haul_id: Optional[str] = None
    summary_id: Optional[str] = None

class DiscogsImportStatus(BaseModel):
    status: str
    total: int = 0
    imported: int = 0
    skipped: int = 0
    error_message: Optional[str] = None
    discogs_username: Optional[str] = None
    last_synced: Optional[str] = None

# Trade Models
TRADE_STATUSES = ["PROPOSED", "COUNTERED", "ACCEPTED", "DECLINED", "CANCELLED",
                  "HOLD_PENDING", "SHIPPING", "CONFIRMING", "COMPLETED", "DISPUTED"]

class TradePropose(BaseModel):
    listing_id: str
    offered_record_id: str
    offered_condition: Optional[str] = None
    offered_photo_urls: Optional[List[str]] = None
    boot_amount: Optional[float] = None
    boot_direction: Optional[str] = None
    message: Optional[str] = None
    hold_amount: Optional[float] = None  # auto-suggested if not provided, $10 min enforced

class TradeCounter(BaseModel):
    requested_record_id: Optional[str] = None
    boot_amount: Optional[float] = None
    boot_direction: Optional[str] = None
    message: Optional[str] = None

class TradeResponse(BaseModel):
    id: str
    listing_id: str
    initiator_id: str
    responder_id: str
    offered_record_id: str
    offered_condition: Optional[str] = None
    offered_photo_urls: Optional[List[str]] = None
    listing_record_id: Optional[str] = None
    boot_amount: Optional[float] = None
    boot_direction: Optional[str] = None
    status: str
    messages: List[Dict[str, Any]] = []
    counter: Optional[Dict[str, Any]] = None
    shipping: Optional[Dict[str, Any]] = None
    shipping_deadline: Optional[str] = None
    confirmation_deadline: Optional[str] = None
    confirmations: Optional[Dict[str, Any]] = None
    dispute: Optional[Dict[str, Any]] = None
    ratings: Optional[Dict[str, Any]] = None
    hold_enabled: Optional[bool] = False
    hold_amount: Optional[float] = None
    hold_status: Optional[str] = None
    hold_suggested_amount: Optional[float] = None
    hold_charges: Optional[Dict[str, Any]] = None
    hold_confirmation_deadline: Optional[str] = None
    created_at: str
    updated_at: str
    initiator: Optional[Dict[str, Any]] = None
    responder: Optional[Dict[str, Any]] = None
    offered_record: Optional[Dict[str, Any]] = None
    listing_record: Optional[Dict[str, Any]] = None
    counter_record: Optional[Dict[str, Any]] = None
    listing: Optional[Dict[str, Any]] = None

class TradeShipInput(BaseModel):
    tracking_number: str
    carrier: Optional[str] = None

class TradeDisputeInput(BaseModel):
    reason: str
    photo_urls: List[str] = []

class TradeDisputeResponse(BaseModel):
    response_text: str
    photo_urls: List[str] = []

class TradeRatingInput(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = None

class AdminDisputeResolve(BaseModel):
    resolution: str
    notes: str
    partial_amount: Optional[float] = None

class HoldAccept(BaseModel):
    """Accept or counter the hold amount during trade negotiation."""
    action: str  # "accept" or "counter"
    hold_amount: Optional[float] = None  # required if action is "counter"

class AdminHoldResolve(BaseModel):
    """Admin resolves a mutual hold dispute."""
    resolution: str  # "full_reversal", "penalize_initiator", "penalize_responder", "partial"
    notes: str
    partial_refund_initiator: Optional[float] = None
    partial_refund_responder: Optional[float] = None

class DiscogsTokenConnect(BaseModel):
    personal_token: str

class DMCreate(BaseModel):
    recipient_id: str
    text: str
    context: Optional[Dict[str, Any]] = None

class DMSend(BaseModel):
    text: str
