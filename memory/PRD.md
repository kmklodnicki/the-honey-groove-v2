# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### BLOCK 565: Silk Image Fix (Completed Mar 12, 2026)
- Removed text overlay from AlbumArt loading/error states
- Replaced yellow shimmer with diagonal silk light-sweep animation (silk-shimmer CSS)
- Smooth 0.4s fade-in transition for loaded images
- Charcoal vinyl Disc icon placeholder (#4A4A4A, 35% opacity) on error — no broken image icon

### BLOCK 563: Mobile Tooltip Trigger Fix (Completed Mar 12, 2026)
- InfoBubble component — dedicated ⓘ icon trigger separated from action buttons
- 44x44px invisible touch target for thumb-friendly tapping
- Action buttons (Refresh, Recover Values) fire immediately without tooltip interference

### BLOCKs 559/561: Golden Hive Shield + Portal Tooltips (Completed Mar 12, 2026)
- GoldenHiveShield: 28px multi-stop metallic gold gradient, 3D embossed drop-shadow
- All tooltips use React Portal (document.body) with z-index 9999
- Smart collision detection — flips above/below based on viewport space

### BLOCKs 550, 553, 555, 556: Tooltip & Card Cleanup (Completed Mar 12, 2026)
- Refresh/Recover tooltips with descriptive copy
- "Value This" buttons removed from cards → "Pending" badge
- Recover Values is sole manual deep-sync trigger

### BLOCKs 541-545: Profile & Treasury Overhaul (Completed Mar 12, 2026)
- Follow/Message relocated to left identity cluster
- Right column streamlined to Control Panel
- Country flag, identity cluster spacing, glassmorphism Treasury

### BLOCK 476: Value Recovery Engine (Completed Mar 12, 2026)
- OAuth-aware Discogs market data, background recovery pipeline
- Recovery endpoints, Weekly Wax email integration, nightly scheduler

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
- Frontend: /app/frontend/src/components/AlbumArt.js (BLOCK 565)
- Frontend: /app/frontend/src/index.css (silk-shimmer CSS)
- Frontend: /app/frontend/src/pages/CollectionPage.js (InfoBubble, TreasuryHeader)
- Frontend: /app/frontend/src/pages/ProfilePage.js (GoldenHiveShield, identity cluster)
- Backend: /app/backend/services/value_recovery.py (Recovery Engine)
