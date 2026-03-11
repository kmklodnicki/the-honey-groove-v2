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
- Migration modal mount fix — triggers on has_seen_security_migration===false (BLOCK 492)
- Dev-only migration reset tool for @katie (BLOCK 491)
- "Authentication: Pure Gold" success screen with gold confetti (BLOCK 500)

### Golden Hive ID System
- **BLOCK 509:** Premium shield SVG badge, metallic gold gradient "Golden Hive Verified", shimmer animation
- **BLOCK 510:** Stripe webhook auto-approves Golden Hive on payment, admin email to katie@thehoneygroove.com (exempt for @katie), in-app notification
- **BLOCK 511:** Admin override — @katieintheafterglow hard-coded as golden_hive_verified + is_admin on every startup

### Valuation & Price Display
- Smart Valuation Hierarchy: Market > Personal > Dash (BLOCK 487)
- Honey Gold price pill overlays (BLOCK 483/484)
- Avg. Value stat in Week in Wax (BLOCK 494/495)

### UI Refinements
- Brand watermark "THE HONEY GROOVE" in dark charcoal #2C2C2C (BLOCK 494)
- Mood tab removed (BLOCK 494)
- "View Full Report" link hidden/flagged (BLOCK 503)
- "Gold Standard" promo text removed from CollectionPage (BLOCK 505)
- **BLOCK 513:** "Connect to Discogs" button in Honey Gold (#FFBF00), dark border (#DAA520), hover #E5AB00

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

## Key API Endpoints
- `/api/golden-hive/status` (GET) - Current user's Golden Hive verification status
- `/api/webhook/stripe` (POST) - Handles payment_intent.succeeded + checkout.session.completed
- `/api/valuation/collection/{username}` (GET) - Returns total_value, avg_value
- `/api/debug/reset-migration` (POST) - Dev-only reset (@katie only)

## Test Credentials
- Admin: admin@thehoneygroove.com / admin_password
- User: test@example.com / test123 (has golden_hive_verified=true)
- Katie: katieintheafterglow (golden_hive_verified=true, is_admin=true)
