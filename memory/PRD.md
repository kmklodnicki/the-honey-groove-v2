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
- **BLOCK 242: Live Hive WebSocket Integration** (March 2026)
  - Backend: `live_hive.py` — Socket.IO async server with `emit_new_post()` broadcast
  - Backend: `server.py` — `combined_app` wraps FastAPI with Socket.IO at `/api/ws/socket.io`
  - Backend: All composer endpoints (`now-spinning`, `note`, `new-haul`, `iso`, `randomizer`, `vinyl-mood`) emit `NEW_POST` via `_emit_and_return()`
  - Frontend: `SocketContext.js` — global provider managing Socket.IO connection lifecycle
  - Frontend: `HivePage.js` — listens for `NEW_POST`, queues new posts, shows floating "N new posts" button
  - Author filtering: users don't see their own posts in the notification
  - Live Feed indicator: shows connected/disconnected state with animated honey dot
  - Tested: 100% backend (11/11), frontend visual verification passed
- **BLOCK 243: Valuation Visibility Overhaul** (March 2026)
  - Backend: `POST /valuation/community-value/{discogs_id}` — submit community valuation for any record
  - Backend: `GET /valuation/community-average/{discogs_id}` — get trimmed-mean community average
  - Frontend: `ValuationAssistantModal.js` — full rewrite with `focusItem` prop for single-record valuation mode
  - Frontend: `RecordCard` in CollectionPage — "Value This" amber-bordered button when price is null/0 and record has discogs_id
  - Frontend: TreasuryHeader — amber "⚠️ N records pending valuation" warning under Dream Value
  - Frontend: ProfilePage — matching amber pending link under Dream Value
  - Persistence: saving value instantly updates RecordCard from "Value This" → price badge (no refresh)
  - Data Sync: focus mode shows "Hive Average: $XX.XX" from community trimmed mean
  - Tested: 100% backend (13/13), 100% frontend verification
- **BLOCK 246: Zero-Grey Image Pipeline** (March 2026)
  - Backend: `_generate_blur_data_url()` — generates 10px base64 JPEG from Discogs 150px thumbnails
  - Backend: `cache_discogs_image()` — now also stores `thumb_url` and `blur_data_url` in image_cache
  - Backend: `GET /image/blur-placeholder` — returns cached blur data for any image URL
  - Backend: `POST /image/blur-batch` — batch blur lookup for multiple cover URLs
  - Backend: Prompt responses endpoint enriches with `blur_data_url` and `thumb_url`
  - Frontend: `AlbumArt.js` — accepts `blurDataUrl`, `thumbSrc`, `priority` props; shows blurred placeholder instead of grey shimmer
  - Frontend: `DailyPromptCard` — passes blur data + `fetchpriority="high"` + preload link injection for LCP
  - Frontend: `useBlurPlaceholders` hook — batch-fetches blur data for collection records
  - CSS: `honey-shimmer-overlay` plays over blurred image (not grey)
  - Backfilled 6 existing image_cache entries with blur data
- **BLOCK 247: Collection Completionist Flow** (March 2026)
  - Backend: `GET /valuation/unvalued-queue` — returns records without market/community value
  - Backend: `POST /valuation/wizard-save/{discogs_id}` — saves to community_valuations + collection_values
  - Frontend: `ValuationWizard.js` — full-screen sequential wizard with slide animations
  - TreasuryHeader: "X of Y records valued" + "Add Missing Values" CTA button
  - Wizard UX: one record at a time, large art, Hive Benchmark, currency input
  - Navigation: Save & Next (slide animation), Skip, Done for now
  - Progress bar: "Record X of Y remaining"
  - Celebration state: "Collection Fully Valued! The Hive thanks you."
  - Tested: 100% backend (10/10), 100% frontend verification
- **BLOCK 248: Instant-On Prompt Asset** (March 2026)
  - Backend: `_extract_dominant_color()` — extracts 1px dominant hex color from Discogs thumbnail
  - Backend: `cache_discogs_image()` now stores `dominant_color` in image_cache
  - Backend: Prompt responses include `dominant_color` field
  - Frontend: DailyPromptCard album art container uses dominant color as background (no grey flash)
  - Frontend: GPU acceleration via `transform: translateZ(0)` + `will-change: transform`
  - Frontend: `<link rel="preload">` injection for first response's cover_url
- **BLOCK 250: Duplicate Detector Utility** (March 2026)
  - Backend: `GET /records/duplicates` — groups records by discogs_id, flags those with different notes for review
  - Backend: `DELETE /records/duplicates/clean` — removes extra copies keeping oldest, skips review groups
  - Frontend: "Duplicates" button in CollectionPage filter bar
  - Frontend: Confirmation modal with record list, dupe counts, review warnings
  - Frontend: "No Duplicates Found" clean state with sparkle icon
- **BLOCK 252: Week in Wax Migration** (March 2026)
  - Removed WaxReportCTA from CollectionPage
  - Added "Your Week in Wax" section to ProfilePage below bio/stats, above tabs
  - Shows 7-day Added/Spins/Total stats with link to full Wax Report
  - Only visible for own profile when collection has records
  - Tested: 100% backend (11/11), all frontend verified

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
