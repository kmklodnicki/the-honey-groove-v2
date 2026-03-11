# The HoneyGroove - Product Requirements Document

## Original Problem Statement
Premium social platform for vinyl collectors. Features include collection management, marketplace, Discogs integration, community feed, trading, and valuation tools.

## Core Architecture
- **Frontend:** React + TypeScript, SWR caching, Shadcn/UI
- **Backend:** FastAPI (Python), MongoDB (Motor async driver)
- **Integrations:** Stripe Connect, Discogs OAuth 1.0a, Resend email, Socket.IO real-time

## What's Been Implemented

### Security & Auth
- Discogs OAuth 1.0a flow (replaces manual username input)
- Imposter protection (flags accounts already linked to other users)
- "The Great Disconnect" database migration (purged all old credentials)
- One-time security migration modal ("The Honey Groove" branded, BLOCK 462/492)
- **BLOCK 480:** Dynamic OAuth callback URL via `window.location.origin`
- **BLOCK 481:** Comprehensive Discogs response logging, explicit HMAC-SHA1
- **BLOCK 491:** Dev-only migration flag reset tool (SettingsPage, restricted to @katie)
- **BLOCK 492:** Fixed modal mounting — triggers when `has_seen_security_migration === false`

### Valuation & Price Display
- **BLOCK 483:** Honey Gold price pill overlays on ProfilePage and CollectionPage
- **BLOCK 484:** Priority value re-linking after OAuth re-auth (background fetch for first 50 records)
- Collection valuation, rarity engine, dream value, taste reports

### Performance
- SWR client-side caching (Profile, Explore pages)
- React.lazy() code splitting for pages
- Service worker static asset pre-caching
- MongoDB indexes on startup

### Features
- Test Listing Filter Guard (admin can hide test listings)
- Express Checkout (Stripe Apple/Google Pay)
- Marketplace, trades, DMs, notifications
- Daily prompts, mood boards, bingo
- Weekly Wax email reports

## Prioritized Backlog

### P0 - Next
- **BLOCK 476: Value Recovery Engine** - Use OAuth tokens for Weekly Wax collection value

### P1 - Blocked
- **BLOCK 254: Streaming Service** - Spotify/Apple Music links (awaiting Spotify callback URL)

### P2 - Upcoming
- Service Worker Daily Prompt pre-cache (BLOCK 321)
- SWR rollout to Marketplace, CollectionPage, ListingDetailModal

### P3 - Future/Backlog
- Record Store Day Proxy Network
- Safari-compatible loading animation
- Pro memberships / Verified Seller badge
- Buyer Protection, Instagram sharing
- Editable "New Music Friday" in Weekly Wax
- Backend-powered search filters
- "Secret Search Feature" (needs clarification)

## Key API Endpoints
- `/api/debug/reset-migration` (POST) - Dev-only: reset migration flags (@katie only)
- `/api/valuation/priority-relink` (POST) - Background price fetch for first 50 records
- `/api/valuation/record-values` (GET) - Map of record_id -> median_value
- `/api/discogs/oauth/start?frontend_origin=` (GET) - Start OAuth with dynamic callback
- `/api/auth/me` (GET) - Returns needs_discogs_migration flag

## Test Credentials
- Admin: admin@thehoneygroove.com / admin_password
- User: test@example.com / test123
