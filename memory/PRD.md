# The HoneyGroove - Product Requirements Document

## Overview
The HoneyGroove is a premium social platform for vinyl collectors built with React frontend, FastAPI backend, and MongoDB.

## Core Features
- Social feed with post aggregation, cursor-based pagination
- User collections (vinyl records via Discogs API)
- Marketplace ("Honeypot") with Stripe Connect
- Trade dispute system
- Golden ID paid verification workflow (Stripe -> ID Upload)
- User discovery ("Nectar") with follow/follow-back
- DMs, notifications (browser push)
- Admin panel with user management
- Onboarding flow
- "Honey Essentials" upsell section
- Global search (Fuse.js client-side)

## Tech Stack
- Frontend: React (JS/JSX), Tailwind CSS, Shadcn/UI, Lucide icons
- Backend: FastAPI (Python), Motor (async MongoDB)
- Database: MongoDB
- Integrations: Stripe Connect (live), Discogs API, Resend (partial), Google Analytics

## What's Been Implemented
- Full social feed with cursor-based pagination (BLOCK 184)
- Golden ID paid verification workflow (BLOCK 204, 207)
- Follow Back feature (BLOCK 195)
- Clickable usernames throughout app (BLOCK 202)
- Admin panel polish with user count (BLOCK 200)
- Desktop dropdown clipping fix (BLOCK 197)
- Sub-dollar transaction logic (BLOCK 193)
- Discovery exclusivity fix (BLOCK 188)
- Mobile profile tab scrolling fix
- BLOCK 215: Mobile Profile Dropdown "God Mode" - React Portal fix
- BLOCK 221: Variant Teleportation Logic - Clickable variant pills
- BLOCK 228: Back-to-Top Button - Smart floating BTT on CollectionPage + ProfilePage
- **BLOCK 229: Dream Value Re-Calculator** (March 2026)
  - 3-tier value resolution: Discogs median -> Community valuation -> User manual price -> "pending"
  - `community_valuations` collection with trimmed mean (top/bottom 5% discarded)
  - `manual_price` field on `iso_items`
  - Valuation Assistant Modal — clickable (+N pending) opens modal to manually value unpriced records
  - `?filter=pending_value` URL param auto-opens modal on Collection page
  - Profile page pending count links to collection with filter
  - Shimmer loading state for dream values
  - Backend endpoints: GET /valuation/pending-items, PUT /valuation/manual-value/{iso_id}
  - All 11 tests passing (100%)

## DB Schema Updates
- `iso_items`: Added `manual_price: float` (optional)
- `community_valuations` (new collection): `release_id`, `average_value`, `contribution_count`, `contributions[]`, timestamps

## Backlog (Prioritized)
### P0
- "Secret search feature" - needs user clarification
- Daily Prompt Archive (BLOCK 222/224) - View yesterday's prompt responses from Hive feed

### P1
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Buyer Protection features

### P2
- Re-enable Instagram sharing
- Admin-editable "New Music Friday" in Weekly Wax
- Backend-powered search filters
- TypeScript migration cleanup (.js -> .tsx)

## Mocked Services
- Resend email integration (except Weekly Wax)

## Test Accounts
- User: test@test.com / test123
- Existing user: katieintheafterglow (kmklodnicki@gmail.com)
