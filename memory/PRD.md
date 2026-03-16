# The HoneyGroove - Product Requirements Document

## Original Problem Statement
The HoneyGroove is a vinyl record collector social platform with collection management, social feed, marketplace, and valuation features.

## Tech Stack
- **Frontend**: React (CRA + Craco), TailwindCSS, Shadcn/UI
- **Backend**: FastAPI (Python), MongoDB Atlas
- **Deployment**: Vercel (production), Emergent preview (staging)
- **Integrations**: Cloudinary (images), Stripe Connect (payments), Discogs API (record metadata), Resend (emails)

## Core Features (Implemented)
- User auth, collection management, Discogs import via OAuth
- Smart Match: Auto-links manual album entries to Discogs
- Rarity System with Unknown fallback
- Social feed with server-side filtering, collapsible pinned posts
- Notification preferences (all/following/none)
- Marketplace, valuation system, weekly reports, daily prompts
- Profile page: Collection, Posts, For Sale, Dream List, ISO tabs
- Collection sort: Artist, Title, Newest, Spins, Value, Rarest First, Most Common
- Format submenu (Vinyl/CD/Cassette) on collection + profile pages
- Format pills on feed for posts with records
- **Format picker** on Add Record and Create Haul pages (auto-detects from Discogs)
- Optimal Density Variant Modal (340px-420px, horizontal stats, 40px touch targets)
- **Compact Listing/Trade modals** (340px-420px sizing, matching variant modal)
- **Daily prompt variant → variant modal** (not page navigation)
- Haul variant pills on album covers, CommunityISOCard clickable with variant modal

## Recent Changes (March 2026)
- Format picker (Vinyl/CD/Cassette) on AddRecord and CreateHaul pages with Discogs auto-detection
- Daily prompt variant pill now opens variant modal instead of navigating
- Listing Detail Modal + Trade Detail Modal optimized to 340-420px sizing
- Variant Modal Optimal Density redesign
- Format submenu on collection and profile pages

## Upcoming
- Instagram Story Export (P1)
- Re-enable Mini Groove (P1)
- Login pre-fetching (P1)
- Update Crown Jewels Logic (P1)

## Future/Backlog
- Record Store Day Proxy Network
- Safari-compatible loading animation
- Pro memberships / Verified Seller badge
- Secret Search Feature
- New Music Friday dynamic editing
- Service Worker Caching
- Streaming Service Integration
- Discogs API SSL error resilience (P2)
