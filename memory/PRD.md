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
- Honey-gold gradient for high-priority alert appearance
- Friendly copy: "Want to import your collection? Connect your Discogs account to sync your library instantly."
- "Skip for now" link — hides banner for 24h via localStorage
- X dismiss also hides banner
- `discogs_import_intent` field: PENDING | LATER | DECLINED | CONNECTED
  - LATER: shows banner
  - DECLINED/CONNECTED: permanently hides banner
- DiscogsSecurityModal with 3 options: Connect Discogs / Maybe Later / Proceed without Discogs
- Golden Hive verification independent of Discogs — skipping doesn't affect trust

### Collection & Valuation
- Full collection management with Discogs import/sync
- Value Recovery Engine (batch valuation)
- "Add Missing Values" button removed (2026-03-12)
- Dream List feature

### Feed & Social
- Daily Prompt system
- Post types: Now Spinning, Haul, ISO, Note, Randomizer
- Real-time feed via Socket.IO
- Paginated notifications with "View More"

### Image Pipeline ("Instant Art")
- Shimmer skeleton loaders
- Priority preloading, predictive fetching via IntersectionObserver

### Other Features
- Weekly Wax email reports
- Stripe Connect for seller payouts
- Golden Hive membership system
- Collector Bingo, Mood Board

## Key API Endpoints
- `POST /api/discogs/update-import-intent` — Update discogs_import_intent (PENDING/LATER/DECLINED/CONNECTED)
- `GET /api/notifications` — Paginated (skip, limit params)
- `POST /api/valuation/start` — Start Value Recovery Engine
- `GET /api/valuation/status` — Recovery run status

## Known Issues
- Service Worker caching incomplete (BLOCK 321) — only on-demand, not pre-cached on install

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
- Test: `test@example.com` / `testuser1`
