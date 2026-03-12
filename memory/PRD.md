# The HoneyGroove — Product Requirements Document

## Original Problem Statement
Build **The HoneyGroove**, a premium social platform for vinyl collectors.

## Core Architecture
- **Frontend:** React (JavaScript), Shadcn UI, TailwindCSS
- **Backend:** FastAPI (Python), MongoDB
- **Integrations:** Stripe Connect, Discogs OAuth, Resend (email), Socket.IO (real-time)

## What's Been Implemented

### Global Verification System
- `VerifiedShield.js` — gold shield SVG with portal tooltip
- Founder identity tied to User ID `4072aaa7-1171-4cd2-9c8f-20dfca8fdc58`

### OAuth Flow (Discogs) — BLOCKs 583, 585, 587
- Relative-positioned Golden Glassy Banner (pushes navbar + content down)
- `discogs_import_intent`: PENDING | LATER | DECLINED | CONNECTED
- "Skip for now" 24h localStorage hide

### Unofficial Record Compliance — v2.6.6 (Omnipresent Pill)
- **Universal AlbumArt injection**: `isUnofficial` prop on `AlbumArt.js` → steel gray pill in bottom-left corner (above spin count, with backdrop-blur) everywhere
- **Global Metadata Scrub**: Admin endpoint `POST /api/admin/scrub-unofficial-metadata` re-fetches Discogs data for all records and corrects `is_unofficial` flags. Idempotent. Scrub run on 2026-03-12: flagged Shiny Things, Beautiful Eyes, Merry Swiftmas.
- **Full coverage**: Collection, Feed (all card types), Search Results, ISO/Want Lists, Variant & Record Pages, Listings, Profile, Trades, Orders, WaxReport, CreateHaul, Admin
- **Strict auto-tagging**: Discogs `format.descriptions[]` checked for exact `"Unofficial Release"`
- **ISO posts**: Backend fetches Discogs release on ISO creation, auto-tags unofficial
- **Variant Page**: "UNOFFICIAL" badge next to title + Safe Harbor disclaimer
- **Tiered Compliance Checkbox**: Gold Hive vs Standard member messaging before listing
- **Legal Disclaimer**: On all unofficial record/listing/variant pages
- **Pricing Restriction**: Auto-market values disabled for unofficial items
- **Backend enforcement**: `unofficial_acknowledged=true` required for listing
- **Tagged records**: Sirens, Tristeza De Verano, Sleepless Nights, A Night In Paris, Merry Swiftmas, Shiny Things, Beautiful Eyes

### Collection & Valuation
- Full collection management with Discogs import/sync
- Value Recovery Engine, Dream List

### Feed & Social
- Daily Prompt, post types (Now Spinning, Haul, ISO, Note, Randomizer)
- ISO pill label shows "ISO"
- Real-time feed via Socket.IO, paginated notifications

### Image Pipeline ("Instant Art")
- Shimmer skeleton loaders, priority preloading, predictive fetching

## Key API Endpoints
- `POST /api/discogs/update-import-intent`
- `POST /api/listings` (is_unofficial, unofficial_acknowledged)
- `POST /api/composer/iso` (auto-detects unofficial from Discogs)
- `GET /api/vinyl/{artist}/{album}/{variant}` (returns is_unofficial)
- `POST /api/admin/scrub-unofficial-metadata` (admin-only, re-checks all records against Discogs)
- `POST /api/admin/oauth-status` (admin-only, verifies Discogs OAuth keys + handshake)
- `GET /api/image-proxy?url=` (persistent cache: memory → object store → upstream, CORS-safe)
- `POST /api/admin/purge-test-data` (admin-only, removes test listings/trades/notifications/posts, protects founder)
- `GET /api/prompts/{id}/responses` (returns proxy_cover_url for carousel image proxying)

## Blocked
- Spotify/Apple Music integration — waiting for callback URL

## Recently Completed (2026-03-12)
- **Composite v2.8.9 — Marketplace Insulation:** Replaced Discogs "Lowest Price" with "The Honeypot Price" card on VinylVariantPage and VariantReleasePage. Shows internal marketplace price or "List Yours" CTA. Fixed TrendingDown runtime error.
- **Zero-Scroll Now Spinning Modal:** Restructured modal to flex layout (max-h-90vh), compact 3-col mood grid (px-2 py-1.5), sticky footer submit button anchored outside scroll area. Verified on desktop and mobile.
- **Advanced Price Hunting (v2.8.9):** Web scraper service (backend/services/scraper.py) for eBay/Google Shopping as Discogs fallback. Caching in MongoDB scraper_cache collection.
- **Instant Image Hydration (v2.8.9):** /api/collection/add now fetches valid image URL before adding record. Placeholder Sweep admin endpoint created.
- **Detailed Value Toasts (v2.8.9):** Interactive toast opens modal with price source details (Discogs/eBay/Google).
- **Interactive Hauls:** Bundle records now include discogs_id + is_unofficial; haul cards clickable → variant popup
- **Smart Flag:** detect_unofficial() checks format_descriptions, notes, format text for "Unofficial/Bootleg/Counterfeit" keywords
- **VariantReleasePage:** Added UnofficialDisclaimer section, inline pill, formatText prop
- **v2.8.3 Emergency:** Pill at Top-Right, AlbumArt safety-net formatText fallback, Route key wrappers, Mini-Groove z-[2000], smooth scroll 80px offset
- **Merry Swiftmas Hijack Fix:** setData(null) + route key={params} for full re-mount
- **OAuth /undefined Fix:** key mismatch (authorization_url → auth_url), frontend guard
- **Variant API is_unofficial:** /vinyl/release/{id} now returns is_unofficial
- Unofficial disclaimer: "The Hive" → "The Honey Groove"
- Sticky Navbar (fixed → sticky top-0 z-[1000])
- **v2.7.2:** Interactive Value Recovery Toast, Disclaimer Padding, Test Data Purge
- OAuth diagnostic endpoint, Daily Prompts Image Proxy, User-Agent fix

## Backlog
- P1: Harden web scraper (user-agent rotation, exponential backoff) — fragile but functional
- P1: Service Worker pre-caching (BLOCK 321)
- P1: Spotify integration — awaiting callback URL (BLOCK 254)
- P2: "Secret Search Feature" — needs clarification from user
- P2: ProfilePage decomposition, centralized user state
- P3: Record Store Day Proxy, Safari animation, Pro memberships, backend search filters, Instagram sharing, dynamic New Music Friday

## Credentials
- Admin: `kmklodnicki@gmail.com` / `admin_password` (UID: `4072aaa7-1171-4cd2-9c8f-20dfca8fdc58`)
- Unofficial records: Sirens [24521972], Tristeza De Verano [31878166], Sleepless Nights [31882048], A Night In Paris [31957001], Merry Swiftmas [32442177], Shiny Things [33531981], Beautiful Eyes [27971034]
