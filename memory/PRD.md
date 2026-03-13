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

## Current DB Stats
- 132 users, 1222 records, 78 posts, 29 followers, 32 likes, 56 invite tokens

## Completed — March 13, 2026
- **CRITICAL FIX**: Switched DB_NAME from `the_honey_groove` → `groove-social-beta-test_database` to restore user data (771 records for kalie.kaufman, 14+ active users)
- **DATA MERGE**: Synced invite tokens, new users, and password hashes from old DB to beta DB
- **CAMPAIGN LAUNCHED**: 95 emails sent (47 Group A recovery + 48 Group B fresh invite), 0 failures
- Admin prompts sorted descending
- Honeypot bottom padding fix (pb-32)
- FRONTEND_URL hard-coded to thehoneygroove.com
- PWA banner z-index hierarchy fix
- Invite redemption hardening (case-insensitive, resend fallback, logging)
- Onboarding redirect fix for claim-invite flow
- Email CTA updated to "Join Now"

## P0 — Next Priority
1. **Redeploy production** with DB_NAME = `groove-social-beta-test_database`
2. Instagram Story Export (1080x1920 PNG)

## P1 — Upcoming
- Service Worker Caching (BLOCK 321)
- Streaming Service Integration (BLOCK 254)

## P2 — Future/Backlog
- Record Store Day Proxy Network
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Secret Search Feature

## Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026!
