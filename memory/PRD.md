# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### BLOCKs 575-578: Notifications + OAuth Toast + Gold Shield (Completed Mar 12, 2026)
- **575/578**: Notification pagination — backend `skip`/`limit` params, frontend "View More" glassy button, Loader2 spinner, "You're all caught up!" empty state
- **576**: OAuth popup → high-priority sonner toast with "Connect Now" action (2s delay, navigates to /settings)
- **577**: Removed all emoji fallbacks (👑, ✅). Founder SVG shield inline (18px, 3-stop gradient). GoldenHiveShield 34px. Katie user ID hard-coded bypass.

### BLOCKs 573-574: OAuth Force-Trigger + Image Pre-Fetch (Completed Mar 12, 2026)
### BLOCKs 571-572: Force Refresh + Instant Failsafe (Completed Mar 12, 2026)
### BLOCKs 566-570: Instant Art Pipeline + Identity Sync (Completed Mar 12, 2026)
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
- ProfilePage.js decomposition (1660+ lines)

### P3 - Future/Backlog
- Record Store Day Proxy Network, Safari loading animation
- Pro memberships, Buyer Protection, Instagram sharing
- Backend search filters, Admin-editable "New Music Friday"

## Test Credentials
- User: test_recovery@test.com / test123
- Katie: kmklodnicki@gmail.com (user ID: 4072aaa7-1171-4cd2-9c8f-20dfca8fdc58)

## Key Files
- Frontend: /app/frontend/src/components/Navbar.js (BLOCK 575/578 notification pagination)
- Frontend: /app/frontend/src/App.js (BLOCK 576 toast)
- Frontend: /app/frontend/src/pages/ProfilePage.js (BLOCK 577 Gold Shield)
- Frontend: /app/frontend/src/components/AlbumArt.js (BLOCKs 565-574)
- Backend: /app/backend/routes/notifications.py (BLOCK 575 skip/limit)
- Backend: /app/backend/server.py (BLOCK 571 admin override by user ID)
