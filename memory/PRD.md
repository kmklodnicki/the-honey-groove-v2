# The HoneyGroove — Product Requirements Document

## Original Problem Statement
Build **The HoneyGroove**, a premium social platform for vinyl collectors. Features include collection tracking, social feed, trading, Discogs integration, and community engagement tools.

## Core Architecture
- **Frontend:** React (JavaScript), Shadcn UI, TailwindCSS
- **Backend:** FastAPI (Python), MongoDB
- **Integrations:** Stripe Connect, Discogs OAuth, Resend (email), Socket.IO (real-time)

## What's Been Implemented

### Global Verification System
- `VerifiedShield.js` component — gold shield SVG with portal tooltip
- Integrated across Feed, Profile, Search, Navbar menus
- Founder identity tied to User ID `4072aaa7-1171-4cd2-9c8f-20dfca8fdc58`

### OAuth Flow (Discogs) — BLOCKs 583, 585, 587
- User-initiated "Golden Glassy Banner" for Discogs connection
- Fixed z-index (`z-[200000]`) above navbar (`z-[100000]`)
- CSS variable `--oauth-banner-h` dynamically pushes navbar down
- Honey-gold gradient, friendly copy
- "Skip for now" link — hides banner for 24h via localStorage
- `discogs_import_intent` field: PENDING | LATER | DECLINED | CONNECTED
- DiscogsSecurityModal with 3 options: Connect / Maybe Later / Proceed Without
- Golden Hive verification independent of Discogs

### Unofficial Record Compliance — BLOCK 592, v2.5.2, v2.5.3
- **Auto-tagging**: Discogs sync detects "Unofficial Release" → sets `is_unofficial: true`
- **"Unofficial" Pill**: Steel gray (#4A4A4A) pill badge — overlay on album art + inline in metadata
- **Deployed across**: Collection grid, Feed (NowSpinning, Haul, AddedToCollection), Record Detail, Listing Modal, HoneypotCards
- **Tiered Compliance Checkbox**: Gold Hive members see status-protecting message; Standard members see trust-building message
- **Legal Disclaimer**: "NOTICE: This release is identified as 'Unofficial'..." on all unofficial pages
- **Pricing Restriction**: Auto-market values disabled for unofficial items; manual price only
- **Backend enforcement**: `unofficial_acknowledged=true` required before listing unofficial items

### Collection & Valuation
- Full collection management with Discogs import/sync
- Value Recovery Engine (batch valuation)
- "Add Missing Values" button removed
- Dream List feature

### Feed & Social
- Daily Prompt, post types, real-time feed, paginated notifications

### Image Pipeline ("Instant Art")
- Shimmer skeleton loaders, priority preloading, predictive fetching

### Other Features
- Weekly Wax email, Stripe Connect, Golden Hive membership, Collector Bingo, Mood Board

## Key API Endpoints
- `POST /api/discogs/update-import-intent` — Update intent (PENDING/LATER/DECLINED/CONNECTED)
- `POST /api/listings` — Now accepts `is_unofficial` and `unofficial_acknowledged`
- `GET /api/records` — Now includes `is_unofficial` in response
- `GET /api/notifications` — Paginated
- `POST /api/valuation/start` — Value Recovery Engine

## Known Issues
- Service Worker caching incomplete (BLOCK 321)

## Blocked
- Spotify/Apple Music integration — waiting for user's callback URL

## Backlog (Prioritized)
- P1: Service Worker pre-caching (BLOCK 321)
- P2: "Secret Search Feature" (needs user clarification)
- P2: ProfilePage decomposition
- P2: Centralize user state (Context/Zustand)
- P3: Record Store Day Proxy Network
- P3: Safari-compatible loading animation
- P3: "Pro" memberships / "Verified Seller" badge
- P3: Buyer Protection features
- P3: Re-enable Instagram sharing
- P3: Dynamic "New Music Friday" admin editing
- P3: Backend-powered search filters

## Credentials
- Admin: `kmklodnicki@gmail.com` / `admin_password` (User ID: `4072aaa7-1171-4cd2-9c8f-20dfca8fdc58`)
- Test unofficial record: `cdd4fe7d-5cf1-4e40-b2f9-faec1600545c` (Pink Pony Club by Chappell Roan)
