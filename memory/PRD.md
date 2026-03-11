# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented (This Session)

### Security & Auth
- Discogs OAuth dynamic callback via window.location.origin (BLOCK 480)
- Comprehensive Discogs error logging, explicit HMAC-SHA1 (BLOCK 481)
- Migration modal mount fix (BLOCK 492), Dev-only reset tool (BLOCK 491)
- "Authentication: Pure Gold" success screen with gold confetti (BLOCK 500)

### Golden Hive ID System
- **BLOCK 509:** Premium shield SVG badge with metallic gold gradient + shimmer
- **BLOCK 510:** Stripe webhook auto-approves + admin email + in-app notification
- **BLOCK 511:** @katieintheafterglow hard-coded as golden_hive_verified + is_admin
- **BLOCK 515:** Badge moved to right-side action column, dark charcoal text #2C2C2C, bold, darker shield outline
- **BLOCK 517:** Hover tooltip with dark charcoal background, "Golden Hive ID" headline, trust message

### Valuation & Price Display
- Smart Valuation Hierarchy: Market > Personal > Dash (BLOCK 487)
- Honey Gold price pill overlays (BLOCK 483/484)
- Avg. Value stat in Week in Wax (BLOCK 494/495)

### UI Refinements
- Brand watermark "THE HONEY GROOVE" in dark charcoal #2C2C2C (BLOCK 494)
- Mood tab removed (BLOCK 494), "View Full Report" hidden (BLOCK 503)
- "Gold Standard" promo text removed (BLOCK 505)
- **BLOCK 513:** Honey Gold Connect to Discogs button (#FFBF00)

## Prioritized Backlog

### P0 - Next
- **BLOCK 476: Value Recovery Engine** - Use OAuth tokens for Weekly Wax collection value

### P1 - Blocked
- **BLOCK 254: Streaming Service** - Spotify/Apple Music links (awaiting callback URL)

### P2 - Upcoming
- Service Worker Daily Prompt pre-cache (BLOCK 321)
- SWR rollout to Marketplace, CollectionPage, ListingDetailModal

### P3 - Future/Backlog
- Record Store Day Proxy Network, Safari loading animation
- Pro memberships, Buyer Protection, Instagram sharing
- Editable "New Music Friday", Backend search filters
- "Secret Search Feature" (needs clarification)

## Test Credentials
- Admin: admin@thehoneygroove.com / admin_password
- User: test@example.com / test123 (golden_hive_verified=true)
- Katie: katieintheafterglow (golden_hive_verified + is_admin)
