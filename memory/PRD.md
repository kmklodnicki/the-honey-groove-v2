# HoneyGroove PRD

## Problem Statement
A social platform for vinyl collectors called **HoneyGroove** (formerly WaxLog). Users can track their vinyl collection, log spins, share activity with friends, and import their Discogs collection.

## Branding
- **Colors:** Honey Gold (#F4B942), Soft Honey (#F9D776), Cream Background (#FFF6E6), Warm Amber Accent (#D98C2F), Vinyl Black Text (#1F1F1F)
- **Fonts:** DM Serif Display (headings), Inter (UI text)
- **Motif:** Subtle bee and honeycomb elements
- **Logo:** User-provided transparent logo, prominent placement

## Core Features

### Implemented (Complete)
1. **User Authentication** - Register, login, JWT tokens, demo account
2. **Vinyl Collection Tracking** - Add records via Discogs search (artist, album, cover, year, notes)
3. **Activity Feed ("The Hive")** - Social feed visible to logged-in users, blurred for guests
4. **Spin Logging** - Log when a record is played
5. **Comments & Likes** - Comment on and like posts in the feed
6. **Shareable Graphics** - Square (1080x1080) and Story (1080x1920) PNG export for "Now Spinning"
7. **Collection Sorting** - 10 sort options: Artist (A-Z, Z-A), Album Title (A-Z, Z-A), Added (Newest, Oldest), Spins (Most, Least), Spun (Recently, Never)
8. **Profile Photos** - Upload custom or use default bee avatar (bee icon + first initial)
9. **Import from Discogs** - Connect Discogs account via OAuth 1.0a or personal token, import full collection with progress UI, "Sync Now" for re-import

### In Progress
- None currently

### Upcoming (P1-P2)
- **Hauls** - Create posts for buying multiple records at once
- **Friends/Following** - Follow/unfollow users, dedicated friend feed
- **Profile Page Improvements** - Show user stats, posts, full collection

### Future/Backlog (P3)
- **HoneyGroove Weekly** - Weekly listening stats summary (top artist/album, mood, spins)
- **JWT Token Persistence** - Proper token refresh/persistence handling

## Architecture
- **Frontend:** React + Tailwind CSS + Shadcn UI
- **Backend:** FastAPI + Motor (async MongoDB)
- **Database:** MongoDB
- **Integrations:** Discogs API (search + OAuth import), Pillow (image generation)

## Key Endpoints
- `/api/auth/{register, login}`
- `/api/users/me`, `/api/users/{user_id}/profile`
- `/api/records`, `/api/records/search`
- `/api/feed`, `/api/posts/{post_id}/comments`, `/api/posts/{post_id}/like`
- `/api/share/generate`
- `/api/discogs/oauth/start`, `/api/discogs/oauth/callback`
- `/api/discogs/connect-token`, `/api/discogs/status`
- `/api/discogs/import`, `/api/discogs/import/progress`
- `/api/discogs/disconnect`

## Test Credentials
- Email: demo@example.com / Password: password123
- Discogs username: katieintheafterglow (connected via personal token)
