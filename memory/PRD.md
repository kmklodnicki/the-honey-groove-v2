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

### Session 8 (2026-03-16)
- **P0 Fix: ISO Search Modal Album Artwork** — Fixed Discogs album artwork not appearing in the ISO search modal. Root cause: `AlbumArt` component used `loading="lazy"` which doesn't trigger in modal/scroll containers, plus a shimmer timeout removed the `<img>` tag entirely after 8s. Fix: Added `priority` prop to `RecordSearchResult`→`AlbumArt` for eager loading, and kept img element rendered during shimmer state. Affects all search dropdowns site-wide (ISO, Listings, Hauls, ComposerBar, Onboarding, etc.).
- **Global Search Accuracy Overhaul** — Rewrote search logic from OR to AND: each query word must match at least one field across the record. "me! taylor swift" now returns 9 ME! variants (was 255 unrelated). Added `_build_and_filter()` helper used by `/search/variants`, `/search/unified`, `/search/records`. Discogs API fallback now always runs for richer coverage.
- **Discogs Structured Search Fallback** — Enhanced `/api/discogs/search` with smart fallback: when initial results don't contain ALL query words, tries Discogs API's `release_title` + `artist` structured params. This finds exact album matches (e.g., "ME!" by Taylor Swift) that the basic `q` param misses.
- **ISO Modal "View More" Button** — Added progressive loading to DiscogsPicker: shows 6 results initially with a "View More (N remaining)" button that loads 6 more per click. Increased max-height from 48 to 60 for better UX.

### Session 9 (2026-03-17) — BLOCK-320
- **CRITICAL: MongoDB Atlas Connection Limit Fix** — M0 cluster exceeded 500 connection threshold. Root cause: `AsyncIOMotorClient` had no pool limits (default maxPoolSize=100), no idle timeout (zombie connections), aggressive backfill tasks. Fix: `maxPoolSize=10`, `minPoolSize=1`, `maxIdleTimeMS=45000`, `socketTimeoutMS=30000`, `retryWrites/retryReads=True`. Reduced backfill batches (500→100, 200→50), increased sleep (1.1s→2s). Enhanced `/api/health` with pool stats.
- **Picture Disc Detection** — Fixed `search_discogs()`, `get_discogs_release()`, `_parse_discogs_raw()` to detect "Picture Disc" from format descriptions array when text field is empty.
- **ISO View More Button Fix** — Moved button OUTSIDE scrollable container on both ComposerBar and Honeypot modals. Added `isoShowCount` state to ComposerBar.
- **ISO Color Variant Storage** — Both `submitISO` functions now send `color_variant` from selected Discogs release.
- **BLOCK-313: ISO Modal Variant Art Fix** — Implemented batch cover resolution: collects all variants missing `cover_url`, does batch lookups against `records` and `discogs_releases` collections, falls back to Discogs API (max 3 calls). Added cover fallback to variant release endpoint and ISO post builder. Zero blank covers in search results.
- **Variant Page Market/Community Fallbacks** — When variant has no market data or 0 community stats, falls back to: (1) sibling releases with same `master_id` in local DB, (2) Discogs master release's `main_release`, (3) master's `lowest_price` estimate. Added `get_discogs_master()` function for `/masters/{id}` endpoint. Fixed slug resolution with fuzzy regex to match titles with special chars (e.g., "Speak Now (Taylor's Version)"). Added `scarcity` and `community` sections to slug endpoint response.

### Session 10 (2026-03-17) — BLOCK-314, BLOCK-317
- **P0 Fix: Mobile Messaging Input Hidden by Keyboard** — Thread container used `height: 100vh` which doesn't account for mobile virtual keyboard. Fix: Added `visualViewport` API hook that listens to `resize` events and dynamically sets container height to `${visualViewport.height}px`. Added `pb-20 md:pb-4` to prevent mobile bottom nav from overlapping the input. Messages auto-scroll to bottom on viewport resize.
- **P0 Fix: Discogs Sync Connection Aborted (BLOCK-317)** — All Discogs API calls (search, release, master, market data, collection import) now use a shared `_discogs_session()` with `urllib3.Retry` (3 retries, 1.5s exponential backoff, retry on 429/500/502/503/504). Collection import `_run_discogs_import` has an additional `_fetch_with_retry` wrapper (3 retries, 2s linear backoff) for page-level connection errors. User-facing error messages are now friendly instead of raw Python exceptions.
- **BLOCK-323: New Message Compose Flow** — Added "+" compose button on the Messages inbox header. Opens a modal with debounced fuzzy user search (profile photos + usernames via `/api/users/search`). Selecting a user checks for existing thread via `/api/dm/conversation-with/{id}` — opens it if found, or initializes a new one.
- **Feed Haul Missing Cover Art** — Enhanced bundle_records cover hydration in `build_post_response` (hive.py) with a 3-pass fallback: 1) records collection, 2) Discogs API via `_get_cached_discogs_release` (includes master release fallback), 3) sibling cover in the same bundle. Also persists resolved covers back to DB for future instant loads.
- **BLOCK-318: PWA Double Notifications** — Root cause: `NotificationBell` rendered twice (desktop + mobile nav), each with independent dedup state. Fix: moved `shownNotifIds` and `prevCount` to module-level globals shared across all instances, so only one browser notification fires per event.
- **BLOCK-319: Granular Notification Toggles (Email vs. App)** — Split single `notification_preference` into `notification_pref_app` and `notification_pref_email`. Backend: `create_notification()` checks app pref, new `should_send_notification_email()` helper gates activity emails (new follower, ISO match, listing alert). Transactional emails (orders, Weekly Wax, password reset) always sent. Frontend: Settings panel redesigned with two independent sections. Backward-compatible with existing `notification_preference` field.
- **BLOCK-315: Recovery Engine — Japanese Pressing Fix** — Added `derive_variant_tag()` utility that auto-generates variant tags from country ("Japanese Pressing", "German Pressing", etc.) and format descriptions ("Club Edition", "Remastered", "Limited Edition", etc.) when no color/variant info exists. Applied across all 4 Discogs parsing paths: `search_discogs()`, `get_discogs_release()`, collection search parser, and import flow. Also applied to slug-based and ID-based variant page endpoints.
- **BLOCK-321: Silent Spin & Deletion Decoupling** — Added `post_to_hive` toggle (default ON) to Now Spinning modal. When OFF, spin logs to Vault only (no feed post). Decoupled post deletion from spin deletion — deleting a Hive post preserves the spin in Vault history.
- **BLOCK-322: Enforce Intentional Posting** — "Spin Now" buttons in the Vault now open the ComposerBar Now Spinning modal (with record pre-selected) instead of auto-posting blank cards. Users must intentionally compose their post with context/comments.
- **BLOCK-316: Crown Jewels — Value Over Rarity** — Hidden Gems (Vault) now sorted by `max(high_value, median_value)` instead of just median, putting truly most expensive items first. Crown Jewels (Explore) re-weighted from 50/50 (scarcity/value) to 80/20 (value-dominant), also using `max(high, estimated)` for value scoring.
- **BLOCK-324: Spotify Deep-Linking (V1)** — New `/api/spotify/link/{discogs_id}` endpoint. Authenticates via Client Credentials, searches by UPC barcode first then artist+album, caches results in `spotify_links` collection. Falls back to generic Spotify search URL if no match. Frontend: green "Listen on Spotify" pill on variant pages (or muted "Search Spotify" for fallback). Also fixed "PRESSING PRESSING" duplication in variant header.

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
- `/app/backend/routes/search.py` — Global search (variants, unified, records) with AND-based `_build_and_filter`
- `/app/backend/routes/collection.py` — Discogs search with structured fallback, image upload, process_image
- `/app/backend/routes/hive.py` — Feed, build_post_response, composer endpoints
- `/app/backend/routes/honeypot.py` — Listings, trades
- `/app/frontend/src/pages/ISOPage.js` — ISO modal with DiscogsPicker and View More button
- `/app/frontend/src/components/RecordSearchResult.js` — Search result card with priority AlbumArt
- `/app/frontend/src/components/AlbumArt.js` — Image component with eager/lazy loading
- `/app/frontend/src/components/ComposerBar.js` — Post creation UI
- `/app/frontend/src/components/PostCards.js` — Feed cards
- `/app/frontend/src/utils/imageUpload.js` — File validation
- `/app/frontend/src/utils/imageUrl.js` — URL rewriting for legacy images

## Test Credentials
- Admin: kmklodnicki@gmail.com / HoneyGroove2026
