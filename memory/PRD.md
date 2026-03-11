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
- BLOCK 229: Dream Value Re-Calculator
- BLOCK 231: Snap-Load Shimmer (2-pulse animation, honey-fade-in transitions)
- BLOCK 237: Community Benchmark Logic
- **BLOCK 241: Daily Prompt Shimmer Sync** (March 2026)
  - AlbumArt component: replaced infinite `animate-shimmer` with 2-pulse `honey-shimmer`
  - Image fade-in: 300ms `transition-opacity` on img element (opacity 0 -> 1 when loaded)
  - Glass fallback uses `honey-fade-in` transition
  - Legacy `@keyframes shimmer` in App.css replaced with `honeyShimmer` reference
  - Mobile verified: Daily Prompt card + all album arts have smooth 2-pulse -> fade-in flow

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
