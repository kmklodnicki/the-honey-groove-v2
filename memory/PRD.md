# The HoneyGroove - Product Requirements Document

## Overview
The HoneyGroove is a premium social platform for vinyl collectors built with React frontend, FastAPI backend, and MongoDB.

## Core Features
- Social feed with post aggregation, cursor-based pagination
- User collections (vinyl records via Discogs API)
- Marketplace ("Honeypot") with Stripe Connect
- Trade dispute system, Golden ID verification
- User discovery ("Nectar") with follow/follow-back
- DMs, notifications (browser push), Admin panel
- Global search (Fuse.js), Onboarding flow
- Real-time WebSocket feed (Socket.IO)

## Tech Stack
- Frontend: React (JS/JSX), Tailwind CSS, Shadcn/UI, Lucide icons, html2canvas
- Backend: FastAPI (Python), Motor (async MongoDB)
- Database: MongoDB
- Integrations: Stripe Connect, Discogs API, Resend (partial), Socket.IO, colorgram.py

## What's Been Implemented (Complete)
### Core Platform
- Full social feed with cursor-based pagination
- Golden ID paid verification, Follow Back, Clickable usernames
- Admin panel, Desktop/Mobile dropdown fixes
- Sub-dollar transactions, Discovery exclusivity
- Clickable variant pills, Back-to-Top, Dream Value Re-Calculator
- Snap-Load Shimmer, Community Benchmark Logic

### Recent Session Work
- BLOCK 242: Live Hive WebSocket Integration
- BLOCK 243: Valuation Visibility Overhaul
- BLOCK 246/248: Zero-Grey Image Pipeline
- BLOCK 247: Collection Completionist Flow (Valuation Wizard)
- BLOCK 250: Duplicate Detector Utility
- BLOCK 252: Week in Wax Migration to Profile
- BLOCK 254: Streaming Deep Links (Spotify/Apple search pills)
- BLOCK 258: Valuation Wizard Sync
- BLOCK 260/265: Record Card Checkbox UI (bottom-left, drop-shadow)
- BLOCK 263: Profile Component Purge (WaxReportCTA removed)
- BLOCK 264: Weekly Report Route
- BLOCK 271: Integrated Spin Feed Logic (Randomizer = "Now Spinning from Randomizer")

### Current Session (March 2026)
- **BLOCK 281: Collection Cleanse UI**
  - Replaced Dreamify/Huntify with single "Remove" button (ghost/red, trash icon)
  - Confirmation modal: "Remove this record? Deletes valuation, spin history, notes."
  - [Cancel] + [Remove Forever] (red gradient)
  - Fade-out animation on removed cards (isFading prop)
  - Tested: PASS

- **BLOCK 284: Valuation Wizard True Finish**
  - Auto re-fetch queue when local batch ends (fetchQueue with isRefill)
  - Only show celebration when global unvalued count = 0
  - onSave callback decrements header count in real-time
  - globalTotal state tracks actual remaining across batches
  - Tested: PASS (code review)

- **BLOCK 285: Desktop Profile Dashboard**
  - 2-column grid: Identity Card (left, 3 cols) + Stats Card (right, 2 cols)
  - Container expanded to max-w-5xl on desktop
  - Sticky tabs (sticky top-14 z-30 backdrop-blur-md)
  - Mobile: stacks vertically
  - Tested: PASS

- **BLOCK 298: Streaming Everywhere**
  - StreamingOverlay component: ghost-style icons (white/translucent, full color on hover)
  - Added to NowSpinningCard album art (bottom-right, z-[7])
  - Added to DailyPrompt carousel album art
  - Consistent sizing across all card types
  - Tested: PASS

- **BLOCK 287: Weekly Report Data Fix**
  - No more blank/black screen
  - "Digging through the crates..." branded loading state
  - If 0 spins: pivots to "A Fresh Start in the Hive" with total collection value
  - Fetches collection value from /api/valuation/collection-value
  - Tested: PASS

- **BLOCK 290: Daily Prompt Instant-On**
  - decoding="sync" on priority AlbumArt images
  - Preload link injection already existed
  - Dominant color placeholder already existed
  - Killed Skeleton shimmer, replaced with warm-toned placeholder bars
  - Tested: PASS

- **BLOCK 291: Weekly Report Story Mode**
  - Full vertical slide-through experience with snap scrolling
  - IntroSlide: "THE HONEY GROOVE" + "@username's Week in the Hive"
  - HeroSlide: Top Spin or Newest Gem with Ken Burns animation
  - FreshStartSlide: Fallback for 0 spins
  - StatsSlide: Spins/Added/Collection Value with oversized typography
  - GenreSlide: Vibe Map with percentage bars
  - MilestoneSlide: Record count + "Only X away from Y!"
  - NewAdditionsSlide: 2x2 grid of recent additions
  - Dynamic theming from dominant color of hero album art
  - Desktop: Blurred wallpaper background
  - Tested: PASS

- **BLOCK 292: Instagram Story Export**
  - 1080x1920 canvas with IG-safe zones (250px top, 300px bottom)
  - html2canvas for high-quality export
  - Native share sheet on mobile, download on desktop
  - "Share Your Week" button with loading state
  - Tested: PASS

- **BLOCK 293: Branded Export**
  - "THE HONEY GROOVE" header (serif, uppercase, tracked, 50% opacity)
  - "Your Weekly Hive Summary" tagline
  - Centered album art hero
  - Bottom stats: Total Value + Records count
  - Vibrant gradient background from album art dominant color
  - Tested: PASS

## Backlog (Prioritized)
### P0
- Daily Prompt Archive (BLOCK 224) - forgotten twice, slide-over drawer with past prompts

### P1
- Real Spotify/Apple Music API integration (currently search URL placeholders)
- Service Worker Prefetch for Daily Prompt images (BLOCK 248)
- "Secret search feature" - needs user clarification

### P2
- Safari-compatible loading animation
- Pro memberships / Verified Seller badge
- Buyer Protection features
- Re-enable Instagram sharing
- Admin-editable "New Music Friday"
- Backend-powered search filters
- TypeScript migration

## Mocked Services
- Resend email (except Weekly Wax)
- Streaming links (search URL placeholders, not real API)

## Test Accounts
- User: test@test.com / test123 (username: testuser)
- Admin: admin / admin_password
- Existing user: katieintheafterglow (kmklodnicki@gmail.com)
