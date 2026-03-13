# The HoneyGroove — Product Requirements Document

## Overview
A premium social platform for vinyl collectors. React frontend + FastAPI backend + MongoDB.

## Active Database
- **DB_NAME**: `groove-social-beta-test_database` on Atlas
- **Stats**: 132 users, 2,589 records, 155 posts

## Completed — March 13, 2026
- **Data Export**: All 23 collections exported to `/app/export/` with download endpoints
- **Migration**: master_migration_data.json merged (all data already present)
- **CSS Fix**: Global `.card-title, .card-artist` truncation in index.css + inline styles on all card components (PostCards.js, HoneypotCards.js, ISOPage.js)
- **Honeypot Pagination**: Limited to 24 items with "Show More" on Shop/Trade tabs
- **Admin**: kmklodnicki@gmail.com confirmed `is_admin: true`

## P0 — Outstanding
- **Ash's Data**: `contact.ashsvinyl@gmail.com` has 0 records — data was in frozen fork (March 8-11), not accessible

## P1 — Upcoming
- Instagram Story Export (1080x1920 PNG for Daily Prompt)
- Service Worker Caching (BLOCK 321)
- Streaming Service Integration (BLOCK 254)

## P2 — Future/Backlog
- Record Store Day Proxy Network
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Secret Search Feature
- Dynamic "New Music Friday" in Weekly Wax email

## Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!
