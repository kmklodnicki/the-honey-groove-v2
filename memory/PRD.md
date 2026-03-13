# The HoneyGroove — Product Requirements Document

## Overview
A premium social platform for vinyl collectors. React frontend + FastAPI backend + MongoDB Atlas.

## Active Database
- **DB_NAME**: `groove-social-beta-test_database` on Atlas
- **Stats**: 132 users, 2,589 records, 155 posts

## Completed — March 13, 2026

### Session 4 — Critical Auth Fix
- **GET /auth/me endpoint**: Added missing `@router.get("/auth/me")` — was only PUT, frontend GET returned 405. Root cause of PFP/admin disappearing after refresh.
- **Password reset 500 fix**: Null-check on user lookup after password update in `reset_password()`
- **Admin password re-hash**: Password hash was stale from data merge; re-hashed to match `HoneyGroove2026!`

### Session 3 — Variant Bug Fix
- Discogs rate limit retry with backoff (2 retries)
- Internal records fallback when Discogs API fails
- "Try Again" button on Variant Not Found page

### Session 2 — Data Export & UI Fixes
- 23 collections exported to `/app/export/` with download endpoints
- CSS truncation on all artist/album labels + global `.card-title, .card-artist` rule
- Honeypot pagination: 24-item limit with "Show More"
- Variant pill max-width capped at all breakpoints (320px desktop, 220px tablet, 150px mobile)
- Password reset token for swiftlylyrical@gmail.com

### Session 1 — Auth & Campaign
- Auth flow with resend-invite fallback
- PWA banner / nav layout fixes
- 95-user email campaign sent

## P0 — Outstanding
- **Ash's Data**: Not in any accessible data source

## P1 — Upcoming
- Instagram Story Export (1080x1920 PNG for Daily Prompt)
- Service Worker Caching (BLOCK 321)

## P2 — Future/Backlog
- Streaming Service Integration (BLOCK 254)
- Record Store Day Proxy Network
- Safari loading animation
- "Pro" memberships / "Verified Seller" badge
- Secret Search Feature
- Dynamic "New Music Friday" in Weekly Wax

## Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!
