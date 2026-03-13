# The HoneyGroove — Product Requirements Document

## Overview
A premium social platform for vinyl collectors. React frontend + FastAPI backend + MongoDB Atlas.

## Active Database
- **DB_NAME**: `groove-social-beta-test_database` on Atlas
- **Stats**: 132 users, 2,589 records, 155 posts

## Completed — March 13, 2026

### Session 3 — Variant Bug Fix
- **Discogs Rate Limit Handling**: Added retry with backoff (2 retries, Retry-After header) in `database.py`
- **Internal Records Fallback**: If Discogs API fails, variant page builds response from internal DB records instead of showing error
- **Frontend Retry UX**: "Variant Not Found" page now has "Try Again" button instead of dead-end

### Session 2 — Data Export & UI Fixes
- **Data Export**: All 23 collections exported to `/app/export/` with download endpoints
- **CSS Truncation**: Applied to all artist/album labels in PostCards.js, HoneypotCards.js, ISOPage.js + global `.card-title, .card-artist` rule in index.css
- **Honeypot Pagination**: Limited to 24 items with "Show More" on Shop/Trade tabs
- **User Unblock**: Generated password reset token for swiftlylyrical@gmail.com

### Session 1 — Auth & Campaign
- Auth flow overhaul with resend-invite fallback
- PWA banner / nav layout fixes
- Admin prompts sorted, admin role set
- 95-user email campaign sent

## P0 — Outstanding
- **Ash's Data**: `contact.ashsvinyl@gmail.com` has 0 records — data in frozen fork (March 8-11), not accessible from current environment

## P1 — Upcoming
- Instagram Story Export (1080x1920 PNG for Daily Prompt)
- Service Worker Caching (BLOCK 321)

## P2 — Future/Backlog
- Streaming Service Integration (BLOCK 254)
- Record Store Day Proxy Network
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Secret Search Feature
- Dynamic "New Music Friday" in Weekly Wax email
- Web scraper hardening

## Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!
