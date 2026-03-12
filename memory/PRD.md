# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### BLOCKs 541-545: Profile & Treasury Overhaul (Completed Mar 12, 2026)
- **541**: Follow/Message buttons relocated from right column to left identity cluster, next to avatar
- **542**: Right column streamlined to "Control Panel" — only Taste Match, Stripe, Golden Hive
- **543**: Country flag emoji displayed next to location text (via countryFlag utility)
- **544**: Identity cluster vertical flow finalized: Report/Block → Follow/Message → Username → Location+Flag
- **545**: TreasuryHeader upgraded to glassmorphism — frosted cream glass with backdrop-blur(12px), soft ambient shadow, deeper gold accents

### BLOCK 476: Value Recovery Engine (Completed Mar 12, 2026)
- OAuth-aware Discogs market data fetcher for higher rate limits
- Background recovery pipeline: systematically values all unvalued records
- Recovery endpoints: POST /api/valuation/recovery/start, GET /api/valuation/recovery/status
- Weekly Wax email now includes collection value summary + top gem
- Frontend TreasuryHeader: "Recover Values" button + live progress badge
- Nightly scheduled recovery for all OAuth-connected users (3 AM UTC)

### Profile Layout (BLOCKs 530-542)
- Report/Block icons moved beside profile photo
- Right column cleaned — only Taste Match, Stripe, Golden Hive
- Tab order: Collection | For Sale | Dream List | ISO | Trades
- New "For Sale" tab with listings, View Listing buttons, Stripe paused notice
- Dream List price badges → Honey Gold mini variant
- "Live Trades" tab, Blocked Users management

### Security & Auth (BLOCKs 480-527)
- Dynamic OAuth callback, HMAC-SHA1, error logging
- Dev reset, modal mount fix, Pure Gold success screen
- Honey Gold connect button, Stripe disconnect guard

### Golden Hive ID (BLOCKs 509-523)
- Shield badge, Stripe webhook auto-approve, admin override
- Right column placement, tooltip, mobile touch

### Activity & Valuation (BLOCKs 483-520)
- Spin deduplication, real-time count update
- Smart Valuation Hierarchy
- Price pills, re-linking, Avg. Value

## Prioritized Backlog

### P1 - Blocked
- **BLOCK 254: Streaming Service** - Spotify/Apple Music (awaiting callback URL)

### P2 - Upcoming
- Service Worker Daily Prompt pre-cache (BLOCK 321)
- SWR rollout to remaining pages
- ProfilePage.js decomposition (1500+ lines)

### P3 - Future/Backlog
- Record Store Day Proxy Network, Safari loading animation
- Pro memberships, Buyer Protection, Instagram sharing
- Backend search filters
- Admin-editable "New Music Friday" section
- "Secret Search Feature" (needs clarification)

## Test Credentials
- Admin: admin@thehoneygroove.com / admin_password
- User: test_recovery@test.com / test123
- Katie: katieintheafterglow (golden_hive_verified + is_admin)

## Key Files
- Backend: /app/backend/services/value_recovery.py (BLOCK 476)
- Backend: /app/backend/routes/valuation.py (recovery endpoints)
- Backend: /app/backend/routes/weekly_wax.py (email integration)
- Frontend: /app/frontend/src/pages/ProfilePage.js (BLOCKs 541-544)
- Frontend: /app/frontend/src/pages/CollectionPage.js (BLOCK 545 glassmorphism)
