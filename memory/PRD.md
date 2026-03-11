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
- BLOCK 221: Variant Teleportation Logic - Clickable variant pills linking to /variant/{discogs_id}
- **BLOCK 228: Back-to-Top Button ("Digger's Elevator")** - Smart floating BTT on CollectionPage and ProfilePage. Appears after 400px scroll, glassmorphism styling, z-index 100003, mobile-aware positioning (bottom: 80px on mobile). (March 2026)

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
