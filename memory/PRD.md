# The HoneyGroove - Product Requirements Document

## Original Problem Statement
The HoneyGroove is a vinyl record social platform where users can track collections, share hauls, hunt ISOs, and trade with the community. The admin has requested iterative UI/UX refinements, feature additions, bug fixes, and admin tools.

## Architecture
- **Frontend:** React (port 3000)
- **Backend:** FastAPI (port 8001)
- **Database:** MongoDB Atlas
- **Image Storage:** Cloudinary
- **Email:** Resend
- **Payments:** Stripe Connect
- **Album Data:** Discogs API
- **Hosting (Production):** Vercel

## Completed Features & Fixes

### Session 1-6 (Prior)
- "Optimal Density" redesign for VariantOptionsModal, ListingDetailModal, TradeDetailModal
- "Smart Match" Discogs enrichment for manual albums
- Collection sorting by rarity and format (Vinyl/CD/Cassette)
- Format submenu on Collection and Profile pages
- Format selector on Add Record and Create Haul pages
- Format pill on feed posts (corrected logic for Note posts)
- Clickable Community ISO cards and Daily Prompt variants
- Collapsible admin pinned post
- User notification preferences
- Password update modal
- Posts tab on user profiles with infinite scroll
- Client-side URL rewriting for broken profile photos (imageUrl.js)
- Mass email system with rate-limiting and duplicate prevention
- Sent platform update email to 115 users

### Session 7 (2026-03-16)
- **P0 Fix: HEIC Image Uploads** — Added file validation to ComposerBar's handlePhotoSelect, improved backend error logging in process_image, expanded upload endpoint to accept HEIC via extension even with generic content types
- **P0 Fix: Now Spinning Image Uploads** — Added try/catch with user-friendly error messages in uploadPostPhoto, improved backend error detail
- **P0 Fix: Album Art in Haul/ISO Feed** — Added cover_url hydration in build_post_response for bundle_records (via record_id or discogs_id lookup) and haul items (via discogs_id lookup)
- **Living Landing Page** — Replaced static `honey-drip.png` with looping `honey-drip.mp4` video on both LandingPage and BetaSignupPage. Pixel-perfect edge-to-edge "ooze" effect with overscan fix (scale 1.05), poster fallback for Low Power Mode, proper z-index layering.

## Backlog

### P1 - Upcoming
- Instagram Story Export (Daily Prompt → 1080x1920 PNG)
- Re-enable "Mini Groove" feature (yesterday's hive posts)
- Login Pre-fetching (profile + feed during animation)
- Update "Crown Jewels" Logic

### P2 - Future
- Record Store Day Proxy Network
- Safari-compatible loading animation
- "Pro" memberships / "Verified Seller" badge
- "Secret Search Feature"
- Editable "New Music Friday" in Weekly Wax email
- Service Worker Caching
- Streaming Service Integration
- Discogs API SSL error resilience (intermittent, Vercel-specific)

## Key Files
- `/app/backend/routes/collection.py` — Image upload, process_image
- `/app/backend/routes/hive.py` — Feed, build_post_response, composer endpoints
- `/app/backend/routes/honeypot.py` — Listings, trades
- `/app/frontend/src/components/ComposerBar.js` — Post creation UI
- `/app/frontend/src/components/PostCards.js` — Feed cards
- `/app/frontend/src/utils/imageUpload.js` — File validation
- `/app/frontend/src/utils/imageUrl.js` — URL rewriting for legacy images

## Test Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026
