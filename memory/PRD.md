# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented (This Session — Blocks 480-534)

### Profile Layout
- BLOCK 533: Report/Block icons moved beside profile photo (horizontal, muted grey)
- BLOCK 534: Right column cleaned — only Follow/Message, Stripe, Golden Hive
- BLOCK 532: Tab order: Collection | For Sale | Dream List | ISO | Trades
- BLOCK 530: New "For Sale" tab with listings, View Listing buttons, Stripe paused notice
- BLOCK 531: Dream List price badges → Honey Gold mini variant

### Security & Auth
- BLOCK 480/481: Dynamic OAuth callback, HMAC-SHA1, error logging
- BLOCK 491/492/500: Dev reset, modal mount fix, Pure Gold success screen
- BLOCK 513/527: Honey Gold connect button, Stripe disconnect guard

### Golden Hive ID
- BLOCK 509/510/511: Shield badge, Stripe webhook auto-approve, admin override
- BLOCK 515/517/523: Right column placement, tooltip, mobile touch

### Activity & Valuation
- BLOCK 519/520: Spin deduplication, real-time count update
- BLOCK 487: Smart Valuation Hierarchy
- BLOCK 483/484/494/495: Price pills, re-linking, Avg. Value

### UI Refinements
- BLOCK 494: Brand watermark #2C2C2C, Mood tab removed
- BLOCK 503/505: "View Full Report" hidden, "Gold Standard" removed
- BLOCK 524/525: Stripe disconnect icon, ISO empty state

## Prioritized Backlog

### P0 - Next
- **BLOCK 476: Value Recovery Engine** - Weekly Wax collection value via OAuth

### P1 - Blocked
- **BLOCK 254: Streaming Service** - Spotify/Apple Music (awaiting callback URL)

### P2 - Upcoming
- Service Worker Daily Prompt pre-cache (BLOCK 321)
- SWR rollout to remaining pages

### P3 - Future/Backlog
- Record Store Day Proxy Network, Safari loading animation
- Pro memberships, Buyer Protection, Instagram sharing
- Backend search filters

## Test Credentials
- Admin: admin@thehoneygroove.com / admin_password
- User: test@example.com / test123 (golden_hive_verified=true)
- Katie: katieintheafterglow (golden_hive_verified + is_admin)
