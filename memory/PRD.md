# The HoneyGroove — Product Requirements Document

## Overview
A premium social platform for vinyl collectors. React frontend + FastAPI backend + MongoDB.

## Production URLs
- **Live site**: thehoneygroove.com
- **Production API**: wax-collector-app.emergent.host
- **Production DB**: `groove-social-beta-test_database` (MongoDB Atlas)
- **Source DB**: `the_honey_groove`

## Core Features (Implemented)
- User auth (JWT), onboarding flow
- Feed (The Hive) with multiple post types: Now Spinning, New Haul, ISO, Daily Prompt, Note, Vinyl Mood, Weekly Wrap, Randomizer, Listings
- "Essential Six" feed filters
- "The Vault" (collection) rebranding
- "Re-pollinate" Stripe feature
- Daily Prompts system
- Album art with spinning vinyl animation
- Streaming links (Spotify/Apple Music)
- Variant/Edition pills
- Mention system, photo lightbox
- Listing (sale/trade) cards

## Completed — March 2026
- **P0 FIXED (Mar 13)**: Admin prompts sorted descending (newest first)
- **P0 FIXED (Mar 13)**: Honeypot page bottom padding pb-32 for bottom nav clearance
- **P0 FIXED (Mar 13)**: FRONTEND_URL hard-coded to `https://www.thehoneygroove.com`
- **P0 FIXED (Mar 13)**: Sticky top banner hierarchy — PWA banner (z:101) stacks above mobile nav (z:100) via CSS variable `--pwa-banner-h`
- **P0 FIXED (Mar 13)**: Invite redemption error — case-insensitive token lookup, validate-invite is now read-only (doesn't burn token), new `POST /api/auth/resend-invite` endpoint, frontend "Send me a fresh invite link" fallback button
- **P0 DONE**: Test invite email sent to `contact@kathrynklodnicki.com`
- PostCards fallback logic for missing nested objects
- PWA Smart App Banner for iOS/Android
- Beta Welcome & "So Sorry" email campaigns (95 users)
- Token-based "Claim Invite" system
- Enriched JWT tokens for frontend hydration
- Resend click-tracking disabled at domain level

## P0 — Next Priority
1. **Instagram Story Export** — Export Daily Prompt as 1080x1920 PNG
2. **CRITICAL: User must redeploy production** for all fixes to take effect

## P1 — Upcoming
- Service Worker Caching (BLOCK 321) — pre-cache key assets
- Streaming Service Integration (BLOCK 254) — needs Spotify callback URL

## P2 — Future/Backlog
- Record Store Day Proxy Network
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Secret Search Feature
- Dynamic "New Music Friday" for Weekly Wax email

## Known Issues
- Web scraper fragile (backend/services/scraper.py) — needs rotating User-Agents
- Service Worker caching incomplete
- server.py monolith should be broken into route files (partially done)

## Key Files
- `backend/routes/auth.py` — Auth endpoints including invite flow, resend-invite
- `frontend/src/pages/ClaimInvitePage.js` — Claim invite page with error fallback UI
- `frontend/src/components/PWAInstallBanner.js` — PWA banner with CSS var coordination
- `frontend/src/components/Navbar.js` — Top/bottom nav, reads --pwa-banner-h
- `backend/database.py` — DB config, FRONTEND_URL hard-coded
- `backend/routes/daily_prompts.py` — Daily Prompts + admin endpoints

## API Endpoints (Invite Flow)
- `GET /api/auth/validate-invite?token=` — Read-only validation, case-insensitive
- `POST /api/auth/resend-invite` — `{email}` → generates fresh token + sends email
- `POST /api/auth/claim-invite` — `{token, password}` → burns token, returns JWT

## Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!
