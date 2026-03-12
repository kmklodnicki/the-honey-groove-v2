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

## Blocked
- Spotify/Apple Music integration — waiting for callback URL

## Backlog
- P1: Service Worker pre-caching (BLOCK 321)
- P2: ProfilePage decomposition, centralized user state
- P3: Record Store Day Proxy, Safari animation, Pro memberships, backend search filters

## Credentials
- Admin: `kmklodnicki@gmail.com` / `admin_password` (UID: `4072aaa7-1171-4cd2-9c8f-20dfca8fdc58`)
- Unofficial records: Sirens [24521972], Tristeza De Verano [31878166], Sleepless Nights [31882048], A Night In Paris [31957001], Merry Swiftmas [32442177], Shiny Things [33531981], Beautiful Eyes [27971034]
