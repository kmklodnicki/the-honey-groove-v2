# The HoneyGroove — Product Requirements Document

## Overview
A premium social platform for vinyl collectors. React frontend + FastAPI backend + MongoDB.

## Production URLs
- **Live site**: thehoneygroove.com
- **Production API**: wax-collector-app.emergent.host

## CRITICAL: Active Database
- **DB_NAME**: `groove-social-beta-test_database` (restored Mar 13 — contains all real user activity)
- **DO NOT switch back to `the_honey_groove`** — that DB has only admin data; all user collections, posts, and profiles live in the beta DB
- The merge copied 53 invite tokens, 34 new users, and 2 password syncs from `the_honey_groove` → `groove-social-beta-test_database`

## Current DB Stats (Mar 13, 2026)
- 132 users, 1923 records, 154 posts, 32 spins, 32 followers, 40 likes, 123 invite codes

## Completed — March 13, 2026 (Session 2)
- **DATA EXPORT**: Exported 23 collections from production Atlas to `/app/export/` as JSON files with download endpoints at `/api/export/list`, `/api/export/{filename}`, `/api/export/archive/all`
- **MIGRATION ATTEMPT**: Ran merge script from `master_migration_data.json` — all 181 records and 88 posts were already present in production (previously migrated). Ashsvinyl's data is NOT in this migration file.
- **CSS FIX**: Applied text truncation (`overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:100%`) to all artist/album labels in NowSpinningCard, AddedToCollectionCard, VinylMoodCard, DailyPromptPostCard, NewHaulCard, and default card.
- **HONEYPOT PAGINATION**: Added client-side pagination with `HONEYPOT_PAGE_SIZE=24` and "Show More" buttons to both Shop and Trade listings tabs.
- **ADMIN VERIFIED**: `kmklodnicki@gmail.com` confirmed as `is_admin: true`.

## Completed — March 13, 2026 (Session 1)
- **CRITICAL FIX**: Switched DB_NAME from `the_honey_groove` → `groove-social-beta-test_database` to restore user data
- **DATA MERGE**: Synced invite tokens, new users, and password hashes from old DB to beta DB
- **CAMPAIGN LAUNCHED**: 95 emails sent (47 Group A recovery + 48 Group B fresh invite), 0 failures
- Admin prompts sorted descending
- Honeypot bottom padding fix (pb-32)
- FRONTEND_URL hard-coded to thehoneygroove.com
- PWA banner z-index hierarchy fix
- Invite redemption hardening (case-insensitive, resend fallback, logging)
- Onboarding redirect fix for claim-invite flow
- Email CTA updated to "Join Now"

## P0 — Outstanding Issue
1. **Ashsvinyl Data**: `contact.ashsvinyl@gmail.com` has 0 records and 0 posts in production. Her data was not in the master migration file. Admin needs to locate the original data source.

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
- Web scraper hardening (rotating User-Agents, exponential backoff)

## Refactoring Needed
- Break down monolithic `server.py` into modular route files (partially done — routes/ directory exists)
- Consolidate one-off scripts in `/app/scripts/`

## Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!

## Architecture
```
/app/
├── backend/
│   ├── .env                  # DB_NAME=groove-social-beta-test_database
│   ├── server.py             # Main app with export endpoints
│   ├── routes/               # Modular route files
│   └── scripts/
│       ├── merge_migration.py    # Migration script (data was already present)
│       ├── export_data.py        # Export script for all collections
│       └── send_beta_campaign.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── PostCards.js       # MODIFIED: CSS truncation on all card labels
│       │   └── honeypot/
│       │       └── HoneypotCards.js
│       └── pages/
│           ├── HivePage.js        # Main feed (already has infinite scroll)
│           └── ISOPage.js         # MODIFIED: Pagination with limit 24
├── export/                        # Exported JSON files
│   ├── users.json (132 users)
│   ├── records.json (1922 records)
│   ├── posts.json (153 posts)
│   └── honeygroove_export.tar.gz  # Full archive
└── memory/
    └── PRD.md
```
