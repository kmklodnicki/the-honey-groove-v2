# The HoneyGroove — Product Requirements Document

## Original Problem Statement
Build **The HoneyGroove**, a premium social platform for vinyl collectors.

## Core Architecture
- **Frontend:** React (JavaScript), Shadcn UI, TailwindCSS
- **Backend:** FastAPI (Python), MongoDB
- **Integrations:** Stripe Connect, Discogs OAuth, Resend (email), Socket.IO (real-time)

## What's Been Implemented

### Global Verification System
- `VerifiedShield.js` — gold shield SVG with portal tooltip
- Founder identity tied to User ID `4072aaa7-1171-4cd2-9c8f-20dfca8fdc58`

### OAuth Flow (Discogs) — BLOCKs 583, 585, 587
- Relative-positioned Golden Glassy Banner (pushes navbar + content down)
- `discogs_import_intent`: PENDING | LATER | DECLINED | CONNECTED
- "Skip for now" 24h localStorage hide

### Unofficial Record Compliance — v2.6.6 (Omnipresent Pill)
- **Universal AlbumArt injection**: `isUnofficial` prop on `AlbumArt.js` → steel gray pill in bottom-left corner (above spin count, with backdrop-blur) everywhere
- **Global Metadata Scrub**: Admin endpoint `POST /api/admin/scrub-unofficial-metadata` re-fetches Discogs data for all records and corrects `is_unofficial` flags. Idempotent. Scrub run on 2026-03-12: flagged Shiny Things, Beautiful Eyes, Merry Swiftmas.
- **Full coverage**: Collection, Feed (all card types), Search Results, ISO/Want Lists, Variant & Record Pages, Listings, Profile, Trades, Orders, WaxReport, CreateHaul, Admin
- **Strict auto-tagging**: Discogs `format.descriptions[]` checked for exact `"Unofficial Release"`
- **ISO posts**: Backend fetches Discogs release on ISO creation, auto-tags unofficial
- **Variant Page**: "UNOFFICIAL" badge next to title + Safe Harbor disclaimer
- **Tiered Compliance Checkbox**: Gold Hive vs Standard member messaging before listing
- **Legal Disclaimer**: On all unofficial record/listing/variant pages
- **Pricing Restriction**: Auto-market values disabled for unofficial items
- **Backend enforcement**: `unofficial_acknowledged=true` required for listing
- **Tagged records**: Sirens, Tristeza De Verano, Sleepless Nights, A Night In Paris, Merry Swiftmas, Shiny Things, Beautiful Eyes

### Collection & Valuation
- Full collection management with Discogs import/sync
- Value Recovery Engine, Dream List

### Feed & Social
- Daily Prompt, post types (Now Spinning, Haul, ISO, Note, Randomizer)
- ISO pill label shows "ISO"
- Real-time feed via Socket.IO, paginated notifications

### Image Pipeline ("Instant Art")
- Shimmer skeleton loaders, priority preloading, predictive fetching

## Key API Endpoints
- `POST /api/auth/login` (accepts email OR username, case-insensitive, no password stripping)
- `POST /api/auth/forgot-password` (sends reset email, rate-limited 3/10min)
- `POST /api/auth/reset-password` (token + new password, 1hr expiry)
- `POST /api/admin/login-diagnostic` (admin-only: debug login for any identifier)
- `POST /api/discogs/update-import-intent`
- `POST /api/listings` (is_unofficial, unofficial_acknowledged)
- `POST /api/composer/iso` (auto-detects unofficial from Discogs)
- `GET /api/vinyl/{artist}/{album}/{variant}` (returns is_unofficial)
- `POST /api/admin/scrub-unofficial-metadata` (admin-only, re-checks all records against Discogs)
- `POST /api/admin/oauth-status` (admin-only, verifies Discogs OAuth keys + handshake)
- `GET /api/image-proxy?url=` (persistent cache: memory → object store → upstream, CORS-safe)
- `POST /api/admin/purge-test-data` (admin-only, removes test listings/trades/notifications/posts, protects founder)
- `GET /api/prompts/{id}/responses` (returns proxy_cover_url for carousel image proxying)

## Blocked
- Spotify/Apple Music integration — waiting for callback URL

## Recently Completed (2026-03-13)
- **Critical Production CORS/Preflight Fix:** Added global OPTIONS middleware that intercepts all preflight requests and returns 200 with correct CORS headers (origin-specific, credentials=true, max-age=86400). This sits outside CORSMiddleware as a safety net for production proxy chains.
- **CORS hardening:** Explicit `allow_methods` list (GET/POST/PUT/DELETE/OPTIONS/PATCH/HEAD), `max_age=86400`, dynamic FRONTEND_URL inclusion in origins.
- **Health endpoint:** `GET /health` and `GET /api/health` for monitoring.
- **Missing imports fixed:** `datetime`, `timezone`, `hash_password` now imported in server.py (was broken for fresh DB admin seeding).
- **FRONTEND_URL updated:** Now points to `https://www.thehoneygroove.com` for correct password reset email links. Both .env and database.py default updated.
- **Discogs OAuth Onboarding Flow:** Replaced manual Discogs username entry with OAuth button in onboarding. New `BuildingHivePage.js` shows "Building your Hive..." loading state with animated progress during import. Backend callback now detects non-onboarded users and redirects to `/onboarding/building`.
- **Tag/Category Refactor:** Updated to final 10-tag system: New Arrival, Deep Listening, High Fidelity, Solo Session, Cleaning Session, Spin Party, Limited Edition, Vibe Check, Late Night, Background Wax. Stored in DB. Old post-type filters (Now Spinning, Haul, ISO, etc.) removed from feed filter bar — only custom tags remain. Backward compat preserved for legacy moods on existing posts.
- **Honeypot Background Sync:** Updated ISOPage glass header to match Collection page styling exactly (`rgba(252,248,232,0.5)`, `blur(12px)`, `saturate(180%)`, matching gradient overlay).
- **Album Tracklist Dropdown:** Already fully implemented in ComposerBar.js — auto-fetches from `/api/discogs/release/{id}`, searchable dropdown, loading spinner, manual entry fallback.
- **Mobile Filter Optimization:** Tighter padding/font for mobile (`11px`), wraps naturally into 2-3 rows on small screens.
- **OAuth Success State & Confetti:** BuildingHivePage shows full-screen confetti + "Collection Connected!" popup with record count + "Start Spinning" CTA. Sets `has_connected_discogs` flag.
- **Auth Persistence (30-day JWT):** JWT from 7→30 days. AuthContext no longer logs out on network timeout — only on 401/403. Timeout increased to 15s for mobile.
- **Infinite Scroll Feed:** Replaced "Load More" with IntersectionObserver infinite scroll (200px rootMargin).
- **Image Lazy Loading:** AlbumArt now uses `loading="lazy"` for non-priority images.
- **Mobile Collection Grid:** Essentials `grid-cols-2` on mobile. RecordCard padding tightened (`p-2 sm:p-3`).
- **Honeypot Background Sync:** ISOPage glass header matches Collection page exactly.
- **12-Mood Filter System → 6 Action Filters (Final):** Now Spinning, ISO, Haul, Notes, For Sale, For Trade. Randomizer posts show "Now Spinning from Randomizer" badge. Mobile: `grid-cols-3` (3 per row, 2 rows + All). Hover: Dark Honey (#C8861A) with black text. 12-mood tags remain available in Composer (MOOD_CONFIG) for post categorization.
- **Tracklist Dropdown Auto-Open:** Dropdown now automatically opens when tracks are fetched — no extra click required. User sees tracks immediately after selecting a record.
- **Streak Recalculation:** Recalculated streaks for 3 users with spins (Katie: 6-day streak). Fields `current_streak`, `longest_streak`, `total_spin_days` added to user model and API response. Spin streak pill added to profile page.
- **AlbumArt Priority Loading:** First 4 images eager (LCP), rest lazy. Changed from 12→4 priority threshold.
- **Nav Hover States:** Essentials nav button changed from `variant="outline"` to `variant="ghost"` to match all other nav items. Mobile nav already consistent.
- **Essentials 2-Col Grid:** Mobile grid updated from `grid-cols-1` to `grid-cols-2` for Essentials page. Collection page tighter padding (`p-2 sm:p-3`).
- **Founding Member Copy:** Replaced "First 50 members" / "founding member spots. limited." with "Limited Founding Members. join the hive." on landing page and beta signup page.
- **Nav Hover States (Final):** Added CSS hover rule: Dark Honey (#C8861A) background with White (#FFF) text on hover for ALL nav links via `.nav-honey-link:hover button`. Smooth `transition: 0.2s`.
- **Filter Pills Polish:** 6 action filters centered via `flex-wrap justify-center`, `padding: 6px 14px`, `whitespace-nowrap`, `text-xs`. 2-row layout on mobile with comfortable sizing.

## Recently Completed (2026-03-12)
- **P0 Login Fix v2 (Comprehensive):** Removed dangerous `password.strip()`, added username-based login (4-step lookup: exact email → regex email → exact username → regex username), fixed regex injection (re.escape), email normalization on registration, detailed server-side login logging, admin login-diagnostic endpoint, frontend updated to accept "Email or Username". All 15 tests passed.
- **PhotoLightbox TypeError Fix:** Fixed `src.indexOf is not a function` crash in `resolveImageUrl` by adding type-safety guards (handles objects, null, non-strings). Fixed PostCards.js passing `{url: "..."}` objects instead of string URLs to PhotoLightbox.
- **Account Recovery System:** Built full password reset flow — `POST /api/auth/forgot-password` sends branded reset email via Resend, `POST /api/auth/reset-password` accepts token + new password (1hr expiry). Frontend: ForgotPasswordPage + ResetPasswordPage + "Forgot password?" link on login page. End-to-end tested: email sent, token valid, password updated, old password rejected, token consumed.
- **Uniform Collection Cards:** Fixed RecordCard — `line-clamp-2` title in `min-h-[2.5rem]`, `line-clamp-1` artist in `min-h-[1.25rem]`, fixed badge row, `mt-auto` Spin Now button. Perfect horizontal alignment across grid.
- **Photo Upload in Modals:** Now Spinning and Haul modals have "Add a photo" Camera button, thumbnail preview, upload to `/api/upload`, photo_url/image_url sent with post.
- **Feed Photo Display:** NowSpinningCard and NewHaulCard show user-uploaded photos prominently above album metadata. Falls back to standard album cover if no photo.
- **JSX Syntax Fixes:** Fixed build-breaking errors in DiscogsSecurityModal.js (unclosed Button/div), PromptArchiveDrawer.js (broken span attributes), CollectionPage.js (React.Fragment instead of RecordCard, duplicate TabsContent, orphan code block)
- **Composite v2.9.5 — Smart De-Duplication:** Prioritize hydrated (real image) records, merge spins from deleted duplicates, removed 'review' badge. New endpoints: GET /api/records/duplicates (with is_hydrated, total_spins), DELETE /api/records/duplicates/clean (with spins_merged)
- **Composite v2.9.5 — Deep Asset Hydration:** POST /api/records/hard-refresh-images endpoint + "Fix Images" button in collection toolbar
- **Composite v2.9.5 — Terminology Lock:** All "Honey Market" → "The Honeypot Price" across VinylVariantPage.js and VariantReleasePage.js
- **Composite v2.9.5 — Spin Now Alignment:** RecordCard flex-col layout with flex-grow text area (min-height 80px) pushing Spin Now to bottom
- **Composite v2.8.9 — Marketplace Insulation:** Replaced Discogs "Lowest Price" with "The Honeypot Price" card on VinylVariantPage and VariantReleasePage
- **Zero-Scroll Now Spinning Modal:** Restructured modal to flex layout (max-h-90vh), compact 3-col mood grid (px-2 py-1.5), sticky footer submit button anchored outside scroll area. Verified on desktop and mobile.
- **Advanced Price Hunting (v2.8.9):** Web scraper service (backend/services/scraper.py) for eBay/Google Shopping as Discogs fallback. Caching in MongoDB scraper_cache collection.
- **Instant Image Hydration (v2.8.9):** /api/collection/add now fetches valid image URL before adding record. Placeholder Sweep admin endpoint created.
- **Detailed Value Toasts (v2.8.9):** Interactive toast opens modal with price source details (Discogs/eBay/Google).
- **Interactive Hauls:** Bundle records now include discogs_id + is_unofficial; haul cards clickable → variant popup
- **Smart Flag:** detect_unofficial() checks format_descriptions, notes, format text for "Unofficial/Bootleg/Counterfeit" keywords
- **VariantReleasePage:** Added UnofficialDisclaimer section, inline pill, formatText prop
- **v2.8.3 Emergency:** Pill at Top-Right, AlbumArt safety-net formatText fallback, Route key wrappers, Mini-Groove z-[2000], smooth scroll 80px offset
- **Merry Swiftmas Hijack Fix:** setData(null) + route key={params} for full re-mount
- **OAuth /undefined Fix:** key mismatch (authorization_url → auth_url), frontend guard
- **Variant API is_unofficial:** /vinyl/release/{id} now returns is_unofficial
- Unofficial disclaimer: "The Hive" → "The Honey Groove"
- Sticky Navbar (fixed → sticky top-0 z-[1000])
- **v2.7.2:** Interactive Value Recovery Toast, Disclaimer Padding, Test Data Purge
- OAuth diagnostic endpoint, Daily Prompts Image Proxy, User-Agent fix

## Recently Completed (2026-03-13 — Session 2)
- **FINAL FILTER LOCK — The Essential Six:** 🍯 All, 🐝 Now Spinning, 🔍 ISO, 📦 Haul, 📝 Notes, 🏷️ For Sale/Trade. Mobile: 2×3 grid. Desktop: 1×6 row. Both centered.
- **Re-pollinate → Daily Prompt Card:** Moved from profile page to Daily Prompt card. Only shows when spin streak is broken (gap > 24hrs from `last_spin_date`) but within 48hr grace period (< 72hrs total). Links to Stripe $1.99 checkout.
- **Collection → The Vault Rebrand:** Global rename across nav (desktop+mobile), page headings ("My Vault"), tabs ("Vault (N)"), search placeholders, value headers ("Vault Value"), buttons ("Add to Your Vault"), empty states, ComposerBar, FAQ, About, Landing, Welcome, Building, ISO, Explore, Trades, Weekly Report, Essentials pages. Route stays `/collection`.
- **Download App in Settings:** Permanent "Download The Honey Groove App!" button in Settings page. Triggers native PWA install prompt or shows instruction toast.
- **PWA Banner localStorage:** Uses `honey_groove_installed` key for persistent hide. Global `window.__pwaPrompt` for Settings button access.
- **Weekly Wax Auto-Subscribe:** All 132 users retroactively subscribed. New users auto-subscribe on registration.
- **Pull-to-Refresh:** Honey-colored spinner on HivePage and EssentialsPage.
- **Global Empty State:** "No posts yet." / "No [filter] posts yet."
- **Streak Logic Refined (Prompt-Based):** Streaks now calculated from `daily_prompt_answers` only. Added `_check_missed_yesterday()` to backend and `missed_yesterday` field to `/api/prompts/today` response. Re-pollinate button on Daily Prompt card now uses this flag.
- **3/12 Streak Protection:** Backend backfill script ran successfully — all users with prompt history got a protected response for March 12, 2026.
- **Track Selector → Native `<select>`:** ComposerBar track selection converted from custom dropdown to native `<select>` with "Select a track..." placeholder. Cleaner, more accessible.
- **First Name Field:** Added `first_name` to UserResponse/UserUpdate models. Settings page has required "First Name *" field with validation. Onboarding modal has Step 0 "What should we call you? 🐝" (conditional, only if first_name is empty).
- **Filter Emoji Position:** Emojis moved to AFTER text: "All 🍯", "Now Spinning 🐝", "ISO 🔍", "Haul 📦", "Notes 📝", "For Sale/Trade 🏷️".

## Backlog
- P1: Harden web scraper (user-agent rotation, exponential backoff) — fragile but functional
- P1: Service Worker pre-caching (BLOCK 321)
- P1: Spotify integration — awaiting callback URL (BLOCK 254)
- P2: "Secret Search Feature" — needs clarification from user
- P2: ProfilePage decomposition, centralized user state
- P3: Record Store Day Proxy, Safari animation, Pro memberships, backend search filters, Instagram sharing, dynamic New Music Friday

## Credentials
- Master Admin: `kmklodnicki@gmail.com` / username: `katie` / `password123` (UID: `4072aaa7-1171-4cd2-9c8f-20dfca8fdc58`)
- Test user: `test@example.com` / username: `testuser1` / `test123`
- Debug user: `testuser_debug@test.com` / username: `testuser_debug` / `testpass`
- Unofficial records: Sirens [24521972], Tristeza De Verano [31878166], Sleepless Nights [31882048], A Night In Paris [31957001], Merry Swiftmas [32442177], Shiny Things [33531981], Beautiful Eyes [27971034]
