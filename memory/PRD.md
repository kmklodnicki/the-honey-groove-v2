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
- Golden Glassy Banner at z-[200000], CSS variable `--oauth-banner-h` pushes navbar
- `discogs_import_intent`: PENDING | LATER | DECLINED | CONNECTED
- "Skip for now" 24h localStorage hide
- DiscogsSecurityModal: Connect / Maybe Later / Proceed Without

### Unofficial Record Compliance — BLOCK 592, v2.5.2, v2.5.3 + Metadata Re-Mapping
- **Strict auto-tagging**: Discogs sync checks for exact `"Unofficial Release"` in `format.descriptions[]`
- **"Unofficial" Pill**: Steel gray (#4A4A4A) overlay + inline across Collection, Feed, Record Detail, Listing Modal, HoneypotCards
- **Tiered Compliance Checkbox**: Gold Hive vs Standard member messaging before listing unofficial items
- **Legal Disclaimer**: On all unofficial record/listing pages
- **Pricing Restriction**: Auto-market values disabled for unofficial items
- **Backend enforcement**: `unofficial_acknowledged=true` required
- **Metadata Re-Mapping**: Pink Pony Club cleared (official reissue). 5 actual bootlegs tagged: Sirens, Tristeza De Verano, Sleepless Nights, A Night In Paris, Merry Swiftmas
- **Enhanced Discogs release API**: Returns `format_descriptions` for better unofficial detection

### Collection & Valuation
- Full collection management with Discogs import/sync
- Value Recovery Engine (batch valuation)
- Dream List feature

### Feed & Social
- Daily Prompt, post types, real-time feed, paginated notifications

### Image Pipeline ("Instant Art")
- Shimmer skeleton loaders, priority preloading, predictive fetching

### Other Features
- Weekly Wax email, Stripe Connect, Golden Hive membership, Collector Bingo, Mood Board

## Known Issues
- Service Worker caching incomplete (BLOCK 321)
- Beautiful Eyes not in collection (will auto-tag when imported)

## Blocked
- Spotify/Apple Music integration — waiting for callback URL

## Backlog
- P1: Service Worker pre-caching (BLOCK 321)
- P2: "Secret Search Feature" (needs clarification)
- P2: ProfilePage decomposition
- P2: Centralize user state
- P3: Record Store Day Proxy, Safari animation, Pro memberships, Buyer Protection, Instagram sharing, admin email editing, backend search filters

## Credentials
- Admin: `kmklodnicki@gmail.com` / `admin_password` (UID: `4072aaa7-1171-4cd2-9c8f-20dfca8fdc58`)
- Unofficial test records: Sirens [24521972], Tristeza De Verano [31878166], Sleepless Nights [31882048], A Night In Paris [31957001], Merry Swiftmas [32442177]
