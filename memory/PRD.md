# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### BLOCKs 573-574: OAuth Force-Trigger + Image Pre-Fetch Bypass (Completed Mar 12, 2026)
- **573**: "Action Required" banner when Discogs OAuth missing (sticky top, gold Connect btn, dismiss). Gold-highlighted Connect Discogs button with glow. Post-OAuth verification re-check triggers Gold Shield.
- **574**: All collection images `loading='eager'`. Internal proxy cascade first on error for faster fallback.

### BLOCKs 571-572: Force Refresh + Instant Failsafe (Completed Mar 12, 2026)
- Admin override by user ID + email fallback. Cache-bust v=2.3.9. 50ms thumb preview. Shimmer indefinitely on timeout.

### BLOCKs 566-570: Instant Art Pipeline + Identity Sync (Completed Mar 12, 2026)
- Priority preloading, IntersectionObserver prefetch, CacheStorage, WebP, Gold Shield 32px 3-stop gradient, admin tied to user ID

### BLOCKs 563-565: Mobile Tooltip Fix + Silk Image (Completed Mar 12, 2026)
### BLOCKs 559/561: Portal Tooltips (Completed Mar 12, 2026)
### BLOCKs 550-556: Tooltip & Card Cleanup (Completed Mar 12, 2026)
### BLOCKs 541-545: Profile & Treasury Overhaul (Completed Mar 12, 2026)
### BLOCK 476: Value Recovery Engine (Completed Mar 12, 2026)

## Prioritized Backlog

### P1 - Blocked
- **BLOCK 254: Streaming Service** - Spotify/Apple Music (awaiting callback URL)

### P2 - Upcoming
- Service Worker Daily Prompt pre-cache (BLOCK 321)
- SWR rollout to remaining pages
- ProfilePage.js decomposition (1600+ lines)

### P3 - Future/Backlog
- Record Store Day Proxy Network, Safari loading animation
- Pro memberships, Buyer Protection, Instagram sharing
- Backend search filters, Admin-editable "New Music Friday"

## Test Credentials
- User: test_recovery@test.com / test123
- Katie: kmklodnicki@gmail.com (user ID: 4072aaa7-1171-4cd2-9c8f-20dfca8fdc58)

## Key Files
- Frontend: /app/frontend/src/App.js (BLOCK 573 action banner)
- Frontend: /app/frontend/src/components/AlbumArt.js (BLOCKs 565-574)
- Frontend: /app/frontend/src/components/DiscogsImport.js (BLOCK 573 gold button + re-check)
- Frontend: /app/frontend/src/pages/CollectionPage.js (BLOCK 567 IntersectionObserver)
- Frontend: /app/frontend/src/pages/ProfilePage.js (GoldenHiveShield, identity cluster)
- Backend: /app/backend/server.py (BLOCK 571 admin override by user ID)
