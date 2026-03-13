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
- **P0 FIXED**: PostCards fallback logic — all card components handle missing nested objects
- **FIXED**: PWA Smart App Banner — visible on iOS/Android, hidden on desktop/standalone
- **P0 DONE**: Beta Welcome Email Campaign — 49 emails resent with FIXED CTA link
- **P0 DONE**: "So Sorry" Re-engagement Campaign — 46 emails resent with FIXED CTA link
- **P0 FIXED (Mar 13)**: Admin prompts sorted descending (newest first) in `/api/prompts/admin/all`
- **P0 FIXED (Mar 13)**: Honeypot page bottom padding increased to pb-32 for bottom nav clearance
- **P0 FIXED (Mar 13)**: FRONTEND_URL hard-coded to `https://www.thehoneygroove.com` in `database.py` to prevent broken email links from env misconfiguration
- Database migration from `the_honey_groove` to `groove-social-beta-test_database`
- Seeded 54 posts, 27 follows, 31 likes for 23 real users
- Fixed broken Discogs CDN image URLs
- Fixed ISO post images
- Daily Prompts restored
- Onboarding flag fixed for all users
- Test data cleanup
- Token-based "Claim Invite" system
- Enriched JWT tokens for frontend hydration
- Resend click-tracking disabled at domain level

## P0 — Next Priority
1. **Instagram Story Export** — Export Daily Prompt as 1080x1920 PNG
2. **CRITICAL: User must redeploy production** after the FRONTEND_URL hard-code to take effect

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
- server.py monolith should be broken into route files (already partially done)

## Key Files
- `frontend/src/components/PostCards.js` — All post card components
- `backend/routes/hive.py` — Feed API, build_post_response
- `backend/server.py` — Main FastAPI app
- `backend/database.py` — DB config, FRONTEND_URL, auth helpers
- `backend/routes/daily_prompts.py` — Daily Prompts system + admin endpoints
- `frontend/src/pages/ISOPage.js` — The Honeypot marketplace page

## Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!
