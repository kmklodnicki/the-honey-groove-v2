# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### BLOCKs 571-572: Force Refresh & Instant Failsafe (Completed Mar 12, 2026)
- **571**: Admin override hard-coded by user ID (4072aaa7...) + email fallback. Cache-bust v=2.3.9 on all image URLs. Gold Shield SVG fully inline (no 404 risk).
- **572**: 50ms thumb preview (showThumb state). 8s timeout → 'shimmer' state (not 'error') = silk-shimmer indefinitely, never broken icon. Error cascade: proxy → WebP fallback → charcoal Disc.

### BLOCKs 566-570: Instant Art Pipeline + Identity Sync (Completed Mar 12, 2026)
- Priority preloading (first 12 eager+high), IntersectionObserver prefetch 2 rows ahead
- CacheStorage blob caching, WebP conversion, Gold Shield 32px 3-stop gradient
- Admin override tied to user ID/email (not username)

### BLOCKs 563-565: Mobile Tooltip Fix + Silk Image (Completed Mar 12, 2026)
- InfoBubble with 44x44px touch target, separated from action buttons
- Diagonal silk light-sweep shimmer, 0.4s fade-in, charcoal error placeholder

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
- "Secret Search Feature" (needs clarification)

## Test Credentials
- User: test_recovery@test.com / test123
- Katie: kmklodnicki@gmail.com (user ID: 4072aaa7-1171-4cd2-9c8f-20dfca8fdc58, golden_hive_verified + is_admin)

## Key Files
- Frontend: /app/frontend/src/components/AlbumArt.js (BLOCKs 565-572)
- Frontend: /app/frontend/src/pages/CollectionPage.js (BLOCK 567 IntersectionObserver)
- Frontend: /app/frontend/src/pages/ProfilePage.js (GoldenHiveShield, identity cluster)
- Backend: /app/backend/server.py (BLOCK 571 admin override by user ID)
- Backend: /app/backend/services/value_recovery.py (BLOCK 476)
