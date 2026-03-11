# The HoneyGroove - Product Requirements Document

## Overview
The HoneyGroove is a premium social platform for vinyl collectors built with React frontend, FastAPI backend, and MongoDB.

## Tech Stack
- Frontend: React (JS/JSX), Tailwind CSS, Shadcn/UI, Lucide icons, html2canvas
- Backend: FastAPI (Python), Motor (async MongoDB)
- Database: MongoDB
- Integrations: Stripe Connect, Discogs API, Resend (partial), Socket.IO, colorgram.py

## What's Been Implemented

### Core Platform
- Social feed, Golden ID verification, Follow/Follow Back, DMs, Notifications
- Marketplace with Stripe Connect, Trade disputes, Admin panel
- User discovery, Global search, Onboarding

### Session Work (March 2026)
- BLOCK 242: Live Hive WebSocket
- BLOCK 243: Valuation Visibility
- BLOCK 246/248: Zero-Grey Image Pipeline
- BLOCK 247: Valuation Wizard
- BLOCK 250: Duplicate Detector
- BLOCK 252: Week in Wax to Profile
- BLOCK 254: Streaming Deep Links
- BLOCK 258: Valuation Wizard Sync
- BLOCK 260/265: Record Card Checkbox UI
- BLOCK 263: Profile Component Purge
- BLOCK 264: Weekly Report Route
- BLOCK 271: Integrated Spin Feed Logic
- BLOCK 281: Collection Cleanse UI (Remove button + confirm modal + fade)
- BLOCK 284: Valuation Wizard True Finish (auto re-fetch, onSave callback)
- BLOCK 285: Desktop Profile Dashboard (2-col then unified)
- BLOCK 287: Weekly Report Data Fix (no blank screen, Fresh Start pivot)
- BLOCK 290: Daily Prompt Instant-On (decoding sync, kill shimmer)
- BLOCK 291: Weekly Report Story Mode (7 slides, snap scroll, Ken Burns)
- BLOCK 292: Instagram Story Export (1080x1920, safe zones)
- BLOCK 293: Branded Export (THE HONEY GROOVE watermark)
- BLOCK 298: Streaming Everywhere (ghost icons on art — later removed per BLOCK 303)

- **BLOCK 303: Analog Animation Deploy** (March 2026)
  - Removed Spotify/Apple Music overlays from album art
  - Spinning vinyl disc slides out from behind right side of sleeve (vinylSpin CSS, 44px SVG)
  - 4-bar white glow equalizer in bottom-right of album art
  - Streaming links relocated below album art as text pill links
  - Files: PostCards.js, App.css
  - Tested: PASS

- **Golden Vault Layout** (March 2026)
  - Merged 2 split cards into single unified DashboardHero card
  - 3-column desktop grid: Identity (1fr) | Stats (1.5fr) | Actions (1fr)
  - 20% gold vertical dividers between sections
  - "THE HONEY GROOVE" watermark at top-left (serif, tracked, 25% opacity)
  - Hero stats: oversized Records + Value with editorial letter-spacing
  - Inline valuation progress bar (replaces popup interruption)
  - Button hierarchy: Golden Hive = primary with gold glow, Stripe = outline
  - Cream background (#FAF6EE) + 1px gold border + cohesive box-shadow
  - Files: ProfilePage.js
  - Tested: PASS

- **Valuation Wizard Logic Leak Fix** (March 2026)
  - Success confetti only fires when isFullyValued (queue.length === 0 after refetch)
  - "Loading next batch..." spinner when local batch ends but more exist
  - Inline progress bar in profile stats card tracks unvalued count
  - Files: ValuationWizard.js, ProfilePage.js
  - Tested: PASS (code review)

## Backlog (Prioritized)
### P0
- Daily Prompt Archive (BLOCK 224) - forgotten twice, slide-over drawer

### P1
- Real Spotify/Apple Music API (currently search URL placeholders)
- Service Worker Prefetch (BLOCK 248)
- "Secret search feature" - needs clarification

### P2
- Safari loading animation, Pro memberships, Buyer Protection
- Instagram sharing, Admin-editable New Music Friday
- Backend search filters, TypeScript migration

## Mocked Services
- Resend email (except Weekly Wax)
- Streaming links (search URL placeholders)

## Test Accounts
- User: test@test.com / test123 (username: testuser)
- Admin: admin / admin_password
