# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### BLOCKs 550, 553, 555, 556: Tooltip & Card Cleanup (Completed Mar 12, 2026)
- **550**: Refresh tooltip: "Quick Sync: Refresh current market prices." / Recover tooltip: "Deep Search: Use the Recovery Engine to find prices for all unvalued or $0 records in your collection at once."
- **553**: MobileTooltip component — tap-to-open, tap-outside-to-close, z-index 999, X close button on mobile
- **555**: Removed "Value This" and "Set Value" buttons from record/wishlist cards. Replaced with "Pending" badge with tooltip directing to Recover Values
- **556**: Recover Values is now the sole manual trigger for deep collection valuation. Retains secondary glassy style

### BLOCKs 541-545: Profile & Treasury Overhaul (Completed Mar 12, 2026)
- **541**: Follow/Message buttons relocated to left identity cluster next to avatar
- **542**: Right column streamlined to Control Panel — Taste Match, Stripe, Golden Hive only
- **543**: Country flag emoji next to location text
- **544**: Identity cluster vertical flow: Report/Block → Follow/Message → Username → Location+Flag
- **545**: TreasuryHeader glassmorphism — frosted cream glass, backdrop-blur(12px), soft shadow

### BLOCK 476: Value Recovery Engine (Completed Mar 12, 2026)
- OAuth-aware Discogs market data fetcher
- Background recovery pipeline with endpoints: POST /api/valuation/recovery/start, GET /api/valuation/recovery/status
- Weekly Wax email collection value section + top gem
- Frontend "Recover Values" button + live progress badge
- Nightly scheduled recovery at 3 AM UTC

### Profile Layout (BLOCKs 530-542)
- Tab order: Collection | For Sale | Dream List | ISO | Trades
- "For Sale" tab, "Live Trades" tab, Blocked Users management

### Earlier Work
- Security/Auth (BLOCKs 480-527), Golden Hive ID (BLOCKs 509-523), Activity/Valuation (BLOCKs 483-520)

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
- Backend search filters, Admin-editable "New Music Friday"
- "Secret Search Feature" (needs clarification)

## Test Credentials
- User: test_recovery@test.com / test123
- Katie: katieintheafterglow (golden_hive_verified + is_admin)

## Key Files
- Frontend: /app/frontend/src/pages/CollectionPage.js (MobileTooltip, TreasuryHeader, RecordCard, WishlistCard)
- Frontend: /app/frontend/src/pages/ProfilePage.js (Identity cluster, Control Panel)
- Backend: /app/backend/services/value_recovery.py (Recovery Engine)
- Backend: /app/backend/routes/valuation.py (recovery endpoints)
