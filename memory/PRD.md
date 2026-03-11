# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented (This Session — Blocks 480-524)

### Security & Auth
- BLOCK 480: Dynamic OAuth callback via window.location.origin
- BLOCK 481: Comprehensive Discogs error logging, explicit HMAC-SHA1
- BLOCK 491: Dev-only migration reset tool (@katie)
- BLOCK 492: Migration modal mount fix
- BLOCK 500: "Authentication: Pure Gold" success screen
- BLOCK 513: Honey Gold Connect to Discogs button (#FFBF00)

### Golden Hive ID System
- BLOCK 509: Premium shield SVG badge + shimmer
- BLOCK 510: Stripe webhook auto-approves + admin email + notification
- BLOCK 511: @katieintheafterglow admin override
- BLOCK 515: Badge moved to right action column, dark charcoal text
- BLOCK 517: Hover tooltip with dark charcoal background
- BLOCK 523: Mobile touch-to-reveal (button element, tooltip side=top)

### Activity Tracking
- BLOCK 519: Spin deduplication (same record within 5 min), spun_at timestamp
- BLOCK 520: Real-time local state update on spin click

### Valuation & Price Display
- BLOCK 487: Smart Valuation Hierarchy (Market > Personal > Dash)
- BLOCK 483/484: Honey Gold price pills + priority re-linking
- BLOCK 494/495: Avg. Value stat in Week in Wax

### UI Refinements
- BLOCK 494: Brand watermark #2C2C2C, Mood tab removed
- BLOCK 503: "View Full Report" hidden
- BLOCK 505: "Gold Standard" promo text removed
- BLOCK 524: Stripe disconnect icon + mobile scaling

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
- Editable "New Music Friday", Backend search filters

## Test Credentials
- Admin: admin@thehoneygroove.com / admin_password
- User: test@example.com / test123 (golden_hive_verified=true)
- Katie: katieintheafterglow (golden_hive_verified + is_admin)
