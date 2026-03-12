# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### BLOCK 581: Global Verification Sync (Completed Mar 12, 2026)
- Universal `VerifiedShield` component at `/components/VerifiedShield.js`
- Integrated in Feed (18px), Listings (16px), Profile (34px, 18px founder inline)
- Portal tooltip on hover/tap with z-index 9999 — "Golden Hive ID" or "Founder" text
- All emoji fallbacks (👑, 🍯, ✅ checkmark) removed from feed/listing username areas

### BLOCKs 575-578: Notifications + OAuth Toast + Gold Shield (Completed Mar 12, 2026)
### BLOCKs 573-574: OAuth Force-Trigger + Image Pre-Fetch (Completed Mar 12, 2026)
### BLOCKs 571-572: Force Refresh + Instant Failsafe (Completed Mar 12, 2026)
### BLOCKs 566-570: Instant Art + Identity Sync (Completed Mar 12, 2026)
### BLOCKs 563-565: Mobile Tooltip + Silk Image (Completed Mar 12, 2026)
### BLOCKs 541-556: Profile/Treasury/Tooltip Overhaul (Completed Mar 12, 2026)
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

## Key Files
- /app/frontend/src/components/VerifiedShield.js (BLOCK 581 — universal component)
- /app/frontend/src/pages/HivePage.js (feed integration)
- /app/frontend/src/components/ListingDetailModal.js (listing integration)
- /app/frontend/src/pages/ProfilePage.js (profile integration)
- /app/frontend/src/components/AlbumArt.js (instant art pipeline)
- /app/backend/services/value_recovery.py (recovery engine)
