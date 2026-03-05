# HoneyGroove PRD

## Problem Statement
A social platform for vinyl collectors called **HoneyGroove**. Users can track their vinyl collection, log spins, share activity with friends, import from Discogs, and interact through a rich social feed.

## Branding
- **Colors:** Honey Gold (#F4B942), Soft Honey (#F9D776), Cream Background (#FFF6E6), Warm Amber Accent (#D98C2F), Vinyl Black Text (#1F1F1F)
- **Fonts:** DM Serif Display (headings), Inter (UI text)
- **Motif:** Subtle bee and honeycomb elements

## Core Features

### Implemented (Complete)
1. **User Authentication** - Register, login, JWT tokens, demo account (demo@example.com / password123)
2. **Vinyl Collection Tracking** - Add records via Discogs search, full CRUD
3. **Import from Discogs** - OAuth 1.0a or personal token connection, full collection import with progress UI, Sync Now
4. **Activity Feed ("The Hive")** - Social feed with post_type-specific card layouts, blurred for guests
5. **Unified Posts System** - 6 post types: NOW_SPINNING, NEW_HAUL, ISO, ADDED_TO_COLLECTION, WEEKLY_WRAP, VINYL_MOOD
6. **Composer Bar** - Twitter-like bar at top of feed with 4 chips (Now Spinning, New Haul, ISO, Vinyl Mood)
7. **Post Type Modals:**
   - Now Spinning: Record selector + Track + Caption
   - New Haul: Discogs search multi-add + Store name + Caption
   - ISO: Artist + Album + Pressing notes + Budget range + Caption
   - Vinyl Mood: 12 mood presets grid + Record link + Note
8. **Post Type Cards:**
   - NOW_SPINNING: Album art + artist/title + track + caption
   - NEW_HAUL: Store name + record grid (up to 6 shown)
   - ISO: Blue card with OPEN/FOUND status + pressing notes + budget
   - ADDED_TO_COLLECTION: Album art + artist/title
   - WEEKLY_WRAP: Gradient card with summary text
   - VINYL_MOOD: Mood preset pill + linked record + caption
9. **Comments & Likes** - On all post types
10. **Shareable Graphics** - Square (1080x1080) and Story (1080x1920) PNG export
11. **Collection Sorting** - 10 sort options (Artist, Album Title, Added, Spins, Spun)
12. **Profile Photos** - Upload custom or use default bee avatar
13. **Spin Logging** - Track plays with optional track/notes
14. **ISO Management** - GET /api/iso for list, PUT /api/iso/{id}/found to mark as found

### Upcoming (P1-P2)
- **Friends/Following UI** - Follow/unfollow buttons, follower lists, filtered feed
- **Profile Page Improvements** - Show user stats, posts, full collection
- **Hauls Page** - Dedicated page to browse and create hauls

### Future/Backlog (P3)
- **HoneyGroove Weekly** - Automated weekly listening stats summary
- **Full OAuth 1.0a Flow** - Requires Discogs Consumer Key/Secret

## Architecture
- **Frontend:** React + Tailwind CSS + Shadcn UI
- **Backend:** FastAPI + Motor (async MongoDB)
- **Database:** MongoDB
- **Integrations:** Discogs API (search + OAuth import), Pillow (image generation)

## Data Model (Posts System)
```
posts: id, user_id, post_type, caption, image_url, share_card_square_url, share_card_story_url, record_id, haul_id, iso_id, weekly_wrap_id, track, mood, created_at
records: id, user_id, discogs_id, artist, title, cover_url, year, format, notes, source, created_at
spins: id, user_id, record_id, notes, created_at
hauls: id, user_id, store_name, title, description, image_url, items[], purchased_at, created_at
iso_items: id, user_id, artist, album, pressing_notes, condition_pref, target_price_min, target_price_max, status, created_at, found_at
likes: id, user_id, post_id, created_at
comments: id, user_id, post_id, content, created_at
followers: follower_id, following_id, created_at
```

## Key Endpoints
- `/api/auth/{register, login}`
- `/api/composer/{now-spinning, new-haul, iso, vinyl-mood}` (one-shot post creation)
- `/api/feed`, `/api/explore`
- `/api/records`, `/api/records/search`, `/api/spins`
- `/api/posts/{id}/comments`, `/api/posts/{id}/like`
- `/api/iso`, `/api/iso/{id}/found`
- `/api/share/generate`
- `/api/discogs/{oauth/start, oauth/callback, connect-token, status, import, import/progress, disconnect}`

## Test Credentials
- Email: demo@example.com / Password: password123
- Discogs: katieintheafterglow (connected via personal token, 143+ records)
