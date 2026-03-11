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
- Desktop/Mobile dropdown fixes (BLOCK 197, 215)
- Sub-dollar transaction logic (BLOCK 193)
- Discovery exclusivity fix (BLOCK 188)
- BLOCK 221: Clickable variant pills
- BLOCK 228: Back-to-Top Button
- BLOCK 229: Dream Value Re-Calculator (3-tier resolution, manual pricing, Valuation Assistant)
- BLOCK 231: Snap-Load Shimmer (2-pulse animation, honey-fade-in transitions)
- **BLOCK 237: Community Benchmark Logic** (March 2026)
  - "The Hive Says..." UI — Valuation Assistant shows community average with "Accept Hive" button
  - Anti-inflation trimmed mean bumped to 10% (top/bottom 10% discarded)
  - Pending items endpoint enriched with `hive_average` and `hive_count`
  - Consistency trigger: new users adding same record see community price as suggested value
  - Success state: "Benchmark Set!" banner with personalized copy
  - "The Hive Pricing Standard" info section explaining trimmed mean
  - Tooltip on pending links: "The Hive doesn't have a price for these grails yet"
  - All UI copy matches user specifications exactly

## DB Collections
- `community_valuations`: release_id, average_value, contribution_count, contributions[], timestamps
- `iso_items`: Added manual_price field

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
