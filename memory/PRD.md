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
- Smart Match: Auto-links manual album entries to Discogs
- Rarity System: Grail/Ultra Rare/Very Rare/Rare/Uncommon/Common/Obscure/Unknown tiers
- Social feed with server-side filtering, collapsible pinned posts
- Notification preferences (all/following/none)
- Marketplace, valuation system, weekly reports, daily prompts
- Profile page: Collection, Posts, For Sale, Dream List, ISO tabs
- Collection sort: Artist, Title, Newest, Spins, Value, Rarest First, Most Common
- Format submenu: Collection page + profile page filters by Vinyl/CD/Cassette with counts
- Format pills on feed: Posts with records show Vinyl/CD/Cassette pill (Notes/Discussions excluded)
- Ultra-compact variant modal (280px, 5-col unified stats grid, compact buttons)
- Compact ListingDetailModal (sm:max-w-md, reduced padding/art/CTA)
- Compact TradeDetailModal (sm:max-w-md, tighter spacing)
- Haul variant pills: Color variant pills overlaid on album covers in haul posts
- CommunityISOCard: Clickable to open variant modal, shows variant pill on album art

## Recent Changes (March 2026)
- Ultra-compact variant modal (280px max-width, unified 5-col stats: Own|ISO|Posts|Med|High, h-7 buttons)
- Compact ListingDetailModal and TradeDetailModal with reduced sizes
- Format pill only on posts with records (not Notes/Discussions)
- Format submenu on user profile collection tab
- CommunityISOCard clickable with variant modal + variant pill
- Previous: Smart Match, rarity sorting, ISO fixes, collapsible pinned posts, notification prefs

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
