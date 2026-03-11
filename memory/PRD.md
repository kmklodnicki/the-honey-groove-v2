# The HoneyGroove - Product Requirements Document

## Overview
The HoneyGroove is a premium social platform for vinyl collectors built with React frontend, FastAPI backend, and MongoDB.

## Tech Stack
- Frontend: React (JS/JSX), Tailwind CSS, Shadcn/UI, Lucide icons, html2canvas
- Backend: FastAPI (Python), Motor (async MongoDB)
- Database: MongoDB
- Integrations: Stripe Connect, Discogs API, Resend (partial), Socket.IO, colorgram.py

## What's Been Implemented

### Core Platform
- Social feed, Golden ID verification, Follow/Follow Back, DMs, Notifications
- Marketplace with Stripe Connect, Trade disputes, Admin panel
- User discovery, Global search, Onboarding

### Session Work (March 2026)
- BLOCK 242: Live Hive WebSocket
- BLOCK 243: Valuation Visibility
- BLOCK 246/248: Zero-Grey Image Pipeline
- BLOCK 247: Valuation Wizard
- BLOCK 250: Duplicate Detector
- BLOCK 252: Week in Wax to Profile
- BLOCK 254: Streaming Deep Links
- BLOCK 258: Valuation Wizard Sync
- BLOCK 260/265: Record Card Checkbox UI
- BLOCK 263: Profile Component Purge
- BLOCK 264: Weekly Report Route
- BLOCK 271: Integrated Spin Feed Logic
- BLOCK 281: Collection Cleanse UI (Remove button + confirm modal + fade)
- BLOCK 284: Valuation Wizard True Finish (auto re-fetch, onSave callback)
- BLOCK 285: Desktop Profile Dashboard (2-col then unified)
- BLOCK 287: Weekly Report Data Fix (no blank screen, Fresh Start pivot)
- BLOCK 290: Daily Prompt Instant-On (decoding sync, kill shimmer)
- BLOCK 291: Weekly Report Story Mode (7 slides, snap scroll, Ken Burns)
- BLOCK 292: Instagram Story Export (1080x1920, safe zones)
- BLOCK 293: Branded Export (THE HONEY GROOVE watermark)
- BLOCK 298: Streaming Everywhere
- BLOCK 303: Analog Animation Deploy (spinning vinyl disc, 4-bar equalizer)
- BLOCK 306/317/340: Icon-Only Streaming Links (permanently colored SVG icons)
- BLOCK 324: Founder Badge Hierarchy
- BLOCK 327: Report Image Pipeline Fix (ReportImg component)
- BLOCK 330: Report Compression (removed Vibe Map, reduced spacing)
- **BLOCK 333: Time & Volume Report Update** (March 2026) — COMPLETED
  - Added date range subtitle to IntroSlide (e.g. "March 4 – March 11, 2026")
  - Added "Records Added This Week" (weekAdds) metric to StatsSlide
  - Fixed missing dateRange prop being passed to IntroSlide
  - Files: WeeklyReportPage.js
  - Tested: PASS
- **BLOCK 224: Daily Prompt Archive** (March 2026) — COMPLETED
  - Backend: GET /api/prompts/archive returns last 14 prompts before today with response_count and user_responded
  - Frontend: "See what the Hive said yesterday" link on Daily Prompt card
  - Frontend: Sheet slide-over drawer (PromptArchiveDrawer.js) showing past prompts
  - Each prompt links to /hive?prompt_id={id} for deep-linking
  - Shows dates (Yesterday, X days ago), response counts, and checkmark for responded prompts
  - Files: daily_prompts.py, DailyPrompt.js, PromptArchiveDrawer.js
  - Tested: PASS
- **BLOCK 346: The Mini-Groove Sidebar** (March 2026) — COMPLETED
  - Overhauled archive drawer into non-clickable Mini-Card display
  - Each card has "DAILY PROMPT" small-caps gold label header
  - 40px rounded album cover artwork from featured response
  - User PFP + @handle shown above the prompt answer
  - 24px vertical spacing between cards (gap-6)
  - All interactivity removed (cursor:default, no onClick/Links)
  - Backend enriched with featured response data (cover, user, caption)
  - Files: PromptArchiveDrawer.js, daily_prompts.py
  - Tested: PASS
- **BLOCK 349: Image Recovery (CORS-Safe Canvas Export)** (March 2026) — COMPLETED
  - Backend: Created /api/image-proxy endpoint (httpx + in-memory LRU cache) serving external images with CORS headers
  - Frontend: proxyImageUrl() wraps external URLs through proxy, passes local URLs through
  - ReportImg component supports fallback chain (spotify_image_url, apple_artwork_url)
  - Pre-flight image loading before html2canvas export
  - All report images use crossOrigin="anonymous"
  - ShareCard uses proxied + fallback-aware image rendering
  - Files: image_proxy.py, server.py, WeeklyReportPage.js
  - Tested: PASS
- **BLOCK 369: Mobile Image Emergency Fix** (March 2026) — COMPLETED
  - Service Worker (/sw.js) with skipWaiting + clients.claim for stale cache flush
  - HTTPS enforcement in resolveImageUrl() and backend proxy (http→https conversion)
  - Explicit CORS OPTIONS pre-flight handler (204) + Access-Control-Allow-Origin: * on all proxy responses
  - Priority/eager loading for first 5 feed images (via imgPriority prop chain) and Daily Prompt
  - Files: sw.js, index.js, imageUrl.js, image_proxy.py, AlbumArt.js, PostCards.js, HivePage.js
  - Tested: PASS
- **Feed Navigation Overhaul + Badge Rename + BLOCK 379** (March 2026) — COMPLETED
  - Feed filter pills renamed: All, Now Spinning, Haul, ISO, Sale/Trade, Note, New Feature
  - Active pill: honey (#FFB800) background with black text; Inactive: transparent with cream border
  - Mobile: flex-wrap, 10px padding, 12px font, invisible scrollbar
  - PostTypeBadge "Album Note" → "Note"
  - BLOCK 379: Archive link centered below Daily Prompt with → arrow; buzz count moved to top-right
  - Files: HivePage.js, PostCards.js, DailyPrompt.js
  - Tested: PASS
- **BLOCK 383: High-Contrast Header Fix** (March 2026) — COMPLETED
  - Removed decorative yellow circle from Daily Prompt card top-right
  - Buzz count text uses dark brown (#8B6914) with font-weight 600 for accessibility
  - Text vertically aligned with DAILY PROMPT label via flex row
  - Files: DailyPrompt.js
  - Tested: PASS
- **BLOCK 387: Centered Cloud Filters** (March 2026) — COMPLETED
  - Filter bar centered with justify-content:center, max-width:600px, margin:0 auto
  - Flex-wrap enabled for mobile stacking
  - Consistent gap:10px between pills
  - Files: HivePage.js
  - Tested: PASS
- **BLOCK 391: History Jump Sidebar** (March 2026) — COMPLETED
  - Re-enabled onClick on archive mini-cards with navigation to /hive?post={post_id}
  - Added cursor:pointer, hover:translateY(-2px), hover:border-brightening, hover:shadow-sm
  - Mini-cards still show user handle (@username), album art, prompt text
  - Backend enriched with post_id in featured response
  - Files: PromptArchiveDrawer.js, daily_prompts.py
  - Tested: PASS
- **BLOCK 399: Flex-Variant Mobile Fix** (March 2026) — COMPLETED
  - Variant pill containers wrapped in flex with flex-wrap:wrap and gap:4px
  - Truncation for long variant names: max-width:150px, text-overflow:ellipsis, overflow:hidden
  - Mobile (<480px): font-size forced to 11px via CSS media query
  - Note badge confirmed as "Note"
  - Files: PostCards.js, App.css
  - Tested: PASS
- **BLOCK 407: Equalizer Repositioning** (March 2026) — COMPLETED
  - Removed LiveEqualizer from absolute overlay on album art
  - Repositioned inline in StreamingLinks row, right after Apple Music button
  - Resized to 24px height to match Spotify/Apple button scale
  - Animation remains active (bouncing bars)
  - Files: PostCards.js
  - Tested: PASS

### Layout & Design Features
- Golden Vault Layout (ProfilePage unified dashboard)
- Valuation Wizard Logic Leak Fix
- Analog Feed Animations (CSS vinylSpin, equalizer)

## Backlog (Prioritized)

### P1
- Real Spotify/Apple Music API (currently search URL placeholders) — BLOCK 254
- Service Worker Prefetch (BLOCK 248/321) — pre-fetch Daily Prompt image
- "Secret search feature" — needs clarification from user

### P2
- Safari loading animation
- Pro memberships / Verified Seller badge
- Buyer Protection features
- Instagram sharing
- Admin-editable New Music Friday
- Backend search filters
- Full TypeScript migration
- Record Store Day Proxy Network

## Mocked Services
- Resend email (except Weekly Wax)
- Streaming links (search URL placeholders, not real API integration)

## Test Accounts
- User: test@test.com / test123 (username: testuser)
- Admin: admin / admin_password
