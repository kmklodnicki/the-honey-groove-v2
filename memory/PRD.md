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
- One-time security migration modal for existing users
- **BLOCK 480:** Dynamic OAuth callback URL via `window.location.origin`, no Vercel dependency
- **BLOCK 481:** Comprehensive Discogs response logging, explicit HMAC-SHA1, full error diagnostics

### Performance
- SWR client-side caching (Profile, Explore pages)
- React.lazy() code splitting for pages
- Service worker static asset pre-caching
- MongoDB indexes on startup
- Image prefetch engine for Daily Prompt carousel

### Valuation & Price Display
- **BLOCK 483:** Honey Gold price pill overlays on ProfilePage and CollectionPage collection grids (top-right, `rgba(255,191,0,0.85)`, hover scale 1.1, zero-value hiding)
- **BLOCK 484:** Priority value re-linking after OAuth re-auth (background fetch for first 50 records, `/api/valuation/priority-relink` endpoint, auto-trigger on OAuth callback)
- Collection valuation, rarity engine, dream value, taste reports
- Community valuations, pricing assist, hidden gems

### Features
- Test Listing Filter Guard (admin can hide test listings)
- Express Checkout (Stripe Apple/Google Pay)
- Marketplace, trades, DMs, notifications
- Daily prompts, mood boards, bingo
- Weekly Wax email reports

## Prioritized Backlog

### P0 - Next
- **BLOCK 476: Value Recovery Engine** - Use new OAuth tokens to fetch/store collection value in Weekly Wax report

### P1 - Blocked
- **BLOCK 254: Streaming Service Integration** - Spotify/Apple Music links (awaiting user's Spotify callback URL)

### P2 - Upcoming
- Service Worker Daily Prompt pre-cache on install event (BLOCK 321)
- SWR rollout to Marketplace, CollectionPage, ListingDetailModal

### P3 - Future/Backlog
- Record Store Day Proxy Network
- Safari-compatible loading animation
- Pro memberships / Verified Seller badge
- Buyer Protection features
- Instagram sharing re-enable
- Editable "New Music Friday" in Weekly Wax
- Backend-powered search filters
- "Secret Search Feature" (needs user clarification)

## Key DB Schema
- `users`: discogs_oauth_verified, has_seen_security_migration, imposter_flag
- `discogs_tokens`: oauth_token, oauth_token_secret, discogs_username, auth_type
- `listings`: is_test_listing, status (includes HIDDEN_PENDING_VERIFICATION)
- `collection_values`: release_id, median_value, low_value, high_value, last_updated

## Key API Endpoints
- `/api/valuation/record-values` (GET) - Map of record_id -> median_value for user's collection
- `/api/valuation/priority-relink` (POST) - Trigger background price fetch for first 50 records
- `/api/discogs/oauth/start?frontend_origin=` (GET) - Start OAuth with dynamic callback
- `/api/discogs/oauth/callback` (GET) - Handle OAuth return, trigger priority relink

## Test Credentials
- Admin: admin@thehoneygroove.com / admin_password
- User: test@example.com / test123
