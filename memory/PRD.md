# The HoneyGroove - Product Requirements Document

## Original Problem Statement
The HoneyGroove is a vinyl record collector social platform with collection management, social feed, marketplace, and valuation features. Deployed on Vercel with Cloudinary for images.

## Tech Stack
- **Frontend**: React (CRA + Craco), TailwindCSS, Shadcn/UI
- **Backend**: FastAPI (Python), MongoDB Atlas
- **Deployment**: Vercel (production), Emergent preview (staging)
- **Integrations**: Cloudinary (images), Stripe Connect (payments), Discogs API (record metadata), Resend (emails)

## Core Features (Implemented)
- User auth, collection management, Discogs import via OAuth
- **Smart Match**: Auto-links manual album entries to Discogs (cover art, tracklist, community data)
- **Rarity System**: Grail/Ultra Rare/Very Rare/Rare/Uncommon/Common/Obscure/Unknown tiers from Discogs community have/want data
- Social feed with server-side filtering, collapsible pinned posts
- Notification preferences (all/following/none)
- Marketplace, valuation system, weekly reports, daily prompts
- Profile page: Collection, Posts, For Sale, Dream List, ISO tabs
- Collection sort: Artist, Title, Newest, Spins, Value, Rarest First, Most Common
- **Format submenu**: Collection page filters by Vinyl/CD/Cassette with counts
- **Format pills on feed**: Every feed post shows Vinyl/CD/Cassette format pill
- **Compact variant modal**: Scaled down to 300px max-width with ultra-compact layout
- **Haul variant pills**: Color variant pills overlaid on album covers in haul posts

## Recent Changes (March 2026)
- Compact variant modal (300px max-width, 14x14 album art, 9px metadata)
- Haul variant pills on album covers in auto-bundle haul posts
- Format pill on every feed post (Vinyl/CD/Cassette)
- Collection format filter submenu (All/Vinyl/CD/Cassette with counts)
- Smart Match on manual add (high-confidence Discogs auto-linking)
- Rarity badge logic: "Unknown" for no discogs_id
- Collection sort by rarity
- ISO auto-populate from Discogs
- Collapsible pinned posts, notification preferences, password modal
- Feed server-side filtering, Profile Posts tab

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
