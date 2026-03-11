# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### Security & Auth
- Discogs OAuth 1.0a flow with HMAC-SHA1 (BLOCK 453/455/462/480/481)
- "The Great Disconnect" migration (BLOCK 472/473)
- Migration modal "The Honey Groove" branding (BLOCK 492)
- Dev-only migration reset tool (BLOCK 491)
- **BLOCK 500:** "Authentication: Pure Gold" success screen with gold confetti after OAuth

### Valuation & Price Display
- **BLOCK 487:** Smart Valuation Hierarchy — Market price > Personal valuation (pencil icon) > Dash fallback
- **BLOCK 483/484:** Honey Gold price pill overlays, priority re-linking after OAuth
- **BLOCK 494/495:** Avg. Value stat in Week in Wax (`total_value / total_count`), replaces redundant "Total"

### Profile UI
- **BLOCK 494:** Brand watermark "THE HONEY GROOVE" in dark charcoal (#2C2C2C)
- **BLOCK 494:** Mood tab removed from profile navigation
- **BLOCK 494:** Symmetrical 3-stat layout: Added | Spins | Avg. Value

### Performance
- SWR client-side caching (Profile, Explore pages)
- React.lazy() code splitting, service worker, MongoDB indexes

### Features
- Test Listing Filter Guard, Express Checkout (Stripe)
- Marketplace, trades, DMs, notifications, Daily prompts, Weekly Wax

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
- Pro memberships / Verified Seller badge, Buyer Protection
- Instagram sharing, Editable "New Music Friday", Backend search filters
- "Secret Search Feature" (needs clarification)

## Key API Endpoints
- `/api/valuation/collection/{username}` (GET) - Returns total_value, valued_count, total_count, avg_value
- `/api/valuation/record-values` (GET) - Map of record_id -> median_value
- `/api/valuation/priority-relink` (POST) - Background price fetch for first 50 records
- `/api/debug/reset-migration` (POST) - Dev-only: reset migration flags (@katie only)
- `/api/discogs/oauth/start?frontend_origin=` (GET) - Start OAuth with dynamic callback

## Test Credentials
- Admin: admin@thehoneygroove.com / admin_password
- User: test@example.com / test123
