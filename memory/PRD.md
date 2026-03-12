# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### BLOCKs 566-570: Instant Art Pipeline + Identity Sync (Completed Mar 12, 2026)
- **567**: Priority preloading (first 12 eager+high), IntersectionObserver prefetch 2 rows ahead, CacheStorage blob caching, WebP conversion for Discogs URLs
- **568**: Dual-stream loading, silk-shimmer instant render, zero-jitter locked dimensions
- **566/570**: Gold Shield 32x32px, 3-stop chrome gradient (#FFD700→#FDB931→#B8860B), soft glow, renders via `golden_hive_verified` flag
- **569**: Admin override tied to email/user ID (not username). Updated server.py, honeypot.py, auth.py, and ProfilePage.js

### BLOCK 565: Silk Image Fix (Completed Mar 12, 2026)
- Diagonal silk light-sweep shimmer, 0.4s fade-in, charcoal Disc error placeholder

### BLOCK 563: Mobile Tooltip Trigger Fix (Completed Mar 12, 2026)
- InfoBubble with 44x44px touch target, separated from action buttons

### BLOCKs 559/561: Portal Tooltips (Completed Mar 12, 2026)
- React Portal z-index 9999, collision detection

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
- Katie: katie@thehoneygroove.com (golden_hive_verified + is_admin, via email lookup)

## Key Files
- Frontend: /app/frontend/src/components/AlbumArt.js (BLOCKs 565-568)
- Frontend: /app/frontend/src/pages/CollectionPage.js (BLOCK 567 IntersectionObserver)
- Frontend: /app/frontend/src/pages/ProfilePage.js (BLOCKs 566/569/570)
- Backend: /app/backend/server.py (BLOCK 569 admin override)
- Backend: /app/backend/routes/honeypot.py (BLOCK 569 is_admin)
- Backend: /app/backend/routes/auth.py (BLOCK 569 debug-reset)
- Backend: /app/backend/services/value_recovery.py (BLOCK 476)
