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
- Integrations: Stripe Connect (live), Discogs API, Resend (partial), Google Analytics, Socket.IO

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
- BLOCK 241: Daily Prompt Shimmer Sync
- BLOCK 242: Live Hive WebSocket Integration
- BLOCK 243: Valuation Visibility Overhaul
- BLOCK 246: Zero-Grey Image Pipeline
- BLOCK 247: Collection Completionist Flow (Valuation Wizard)
- BLOCK 248: Instant-On Prompt Asset (dominant color backgrounds)
- BLOCK 250: Duplicate Detector Utility
- BLOCK 252: Week in Wax Migration to Profile
- BLOCK 254: Streaming Deep Links (Spotify/Apple search pills, MOCKED)
- BLOCK 258: Valuation Wizard Sync
- BLOCK 260/265: Record Card Checkbox UI (bottom-left, drop-shadow)
- BLOCK 263: Profile Component Purge (WaxReportCTA removed)
- BLOCK 264: Weekly Report Route (/reports/weekly)
- **BLOCK 271: Integrated Spin Feed Logic** (March 2026)
  - Randomizer posts now display as "Now Spinning from Randomizer" with Shuffle icon
  - Pill style: soft violet accent (bg-violet-50, text-violet-600, border-violet-200)
  - Feed grouping: "Now Spinning" filter includes RANDOMIZER posts
  - Card rendering: RANDOMIZER already uses NowSpinningCard (unchanged)
  - Files: PostCards.js (pill label + style), HivePage.js (filter logic)

## Backlog (Prioritized)
### P0
- Daily Prompt Archive (BLOCK 224) - View yesterday's prompt responses, slide-over drawer
- "Secret search feature" - needs user clarification

### P1
- Complete Streaming Service Integration (BLOCK 254) - real Spotify/Apple Music API
- Build Weekly Report Page visual polish (BLOCK 264 enhancement)
- Service Worker Prefetch for Daily Prompt images (BLOCK 248)

### P2
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- Buyer Protection features
- Re-enable Instagram sharing
- Admin-editable "New Music Friday" in Weekly Wax
- Backend-powered search filters
- TypeScript migration cleanup (.js -> .tsx)

## Mocked Services
- Resend email integration (except Weekly Wax)
- Streaming Service (Spotify/Apple Music links are search URL placeholders)

## Test Accounts
- User: test@test.com / test123 (username: testuser)
- Admin: admin / admin_password
- Existing user: katieintheafterglow (kmklodnicki@gmail.com)
