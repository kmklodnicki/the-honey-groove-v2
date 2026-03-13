"""
Seed community posts for real users who signed up but never posted.
Creates authentic vinyl-community content with fresh Discogs album art.
"""
import asyncio, os, uuid, random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

DISCOGS_TOKEN = os.environ.get('DISCOGS_TOKEN', '')
DISCOGS_UA = os.environ.get('DISCOGS_USER_AGENT', 'WaxLog/1.0')

# Real albums with search queries for fresh Discogs covers
ALBUMS = [
    {'q': 'Taylor Swift 1989 vinyl', 'title': '1989', 'artist': 'Taylor Swift'},
    {'q': 'Fleetwood Mac Dreams vinyl', 'title': 'Tango in the Night', 'artist': 'Fleetwood Mac'},
    {'q': 'SZA Ctrl vinyl', 'title': 'Ctrl', 'artist': 'SZA'},
    {'q': 'Frank Ocean Blonde vinyl', 'title': 'Blonde', 'artist': 'Frank Ocean'},
    {'q': 'Harry Styles Fine Line vinyl', 'title': 'Fine Line', 'artist': 'Harry Styles'},
    {'q': 'Olivia Rodrigo SOUR vinyl', 'title': 'SOUR', 'artist': 'Olivia Rodrigo'},
    {'q': 'Tyler Creator Flower Boy vinyl', 'title': 'Flower Boy', 'artist': 'Tyler, the Creator'},
    {'q': 'Billie Eilish Happier Than Ever vinyl', 'title': 'Happier Than Ever', 'artist': 'Billie Eilish'},
    {'q': 'Arctic Monkeys AM vinyl', 'title': 'AM', 'artist': 'Arctic Monkeys'},
    {'q': 'Lana Del Rey Norman Rockwell vinyl', 'title': 'Norman Fucking Rockwell!', 'artist': 'Lana Del Rey'},
    {'q': 'Mac Miller Swimming vinyl', 'title': 'Swimming', 'artist': 'Mac Miller'},
    {'q': 'Hozier Wasteland Baby vinyl', 'title': 'Wasteland, Baby!', 'artist': 'Hozier'},
    {'q': 'Nirvana Nevermind vinyl', 'title': 'Nevermind', 'artist': 'Nirvana'},
    {'q': 'Kendrick Lamar good kid vinyl', 'title': 'good kid, m.A.A.d city', 'artist': 'Kendrick Lamar'},
    {'q': 'Tame Impala Currents vinyl', 'title': 'Currents', 'artist': 'Tame Impala'},
    {'q': 'Doja Cat Planet Her vinyl', 'title': 'Planet Her', 'artist': 'Doja Cat'},
    {'q': 'The Weeknd After Hours vinyl', 'title': 'After Hours', 'artist': 'The Weeknd'},
    {'q': 'Kacey Musgraves Golden Hour vinyl', 'title': 'Golden Hour', 'artist': 'Kacey Musgraves'},
    {'q': 'Paramore After Laughter vinyl', 'title': 'After Laughter', 'artist': 'Paramore'},
    {'q': 'Mitski Be the Cowboy vinyl', 'title': 'Be the Cowboy', 'artist': 'Mitski'},
    {'q': 'Bon Iver For Emma vinyl', 'title': 'For Emma, Forever Ago', 'artist': 'Bon Iver'},
    {'q': 'Maggie Rogers Heard It vinyl', 'title': "Heard It in a Past Life", 'artist': 'Maggie Rogers'},
    {'q': 'Chappell Roan Rise Fall vinyl', 'title': 'The Rise and Fall of a Midwest Princess', 'artist': 'Chappell Roan'},
    {'q': 'Sabrina Carpenter emails vinyl', 'title': 'emails i cant send', 'artist': 'Sabrina Carpenter'},
    {'q': 'Gracie Abrams Good Riddance vinyl', 'title': 'Good Riddance', 'artist': 'Gracie Abrams'},
]

# User -> post templates (each user gets 2-3 posts)
USER_POSTS = {
    'travis13bell': [
        {'type': 'NOW_SPINNING', 'tpl': 'Late night spin. {title} by {artist} on repeat. This pressing sounds unreal.', 'album_idx': 0},
        {'type': 'NEW_HAUL', 'tpl': 'Record store haul today. Grabbed {title} and two others. {artist} has been on my list for months.', 'album_idx': 7},
        {'type': 'NOTE', 'tpl': 'Vinyl collecting is less about the music and more about the ritual. Setting the needle down, sitting back. Nothing else like it.'},
    ],
    'swiftlylyrical': [
        {'type': 'NOW_SPINNING', 'tpl': '{title} on vinyl is a completely different experience. {artist} in every crackle.', 'album_idx': 0},
        {'type': 'NEW_HAUL', 'tpl': 'The {title} vinyl ARRIVED. {artist} pressing is gorgeous. The sleeve alone is worth it.', 'album_idx': 4},
        {'type': 'DAILY_PROMPT', 'tpl': '{title} by {artist}. No question.', 'album_idx': 0, 'prompt_text': 'the album that defined your year'},
    ],
    'danabrigoli': [
        {'type': 'NOW_SPINNING', 'tpl': '{title} by {artist}. This is the vinyl that got me into collecting.', 'album_idx': 2},
        {'type': 'ISO', 'tpl': 'ISO: {title} by {artist} on colored vinyl. Anyone seen one recently?', 'album_idx': 3},
    ],
    'michellereadsandspins': [
        {'type': 'NOW_SPINNING', 'tpl': 'Reading and spinning. {title} by {artist} is the perfect soundtrack.', 'album_idx': 11},
        {'type': 'NOTE', 'tpl': 'Books and vinyl. Name a better combination. I dare you.'},
        {'type': 'NEW_HAUL', 'tpl': 'Used bookstore had a vinyl section. Left with {title} by {artist} for $8.', 'album_idx': 20},
    ],
    'kellanharringtonpham': [
        {'type': 'NOW_SPINNING', 'tpl': 'Sunday morning with {title}. {artist} just hits different on wax.', 'album_idx': 17},
        {'type': 'NEW_HAUL', 'tpl': 'Scored {title} by {artist} at a flea market. Cleaned it up and it plays perfectly.', 'album_idx': 12},
    ],
    'megpug10': [
        {'type': 'NOW_SPINNING', 'tpl': '{title} while making dinner. {artist} is non-negotiable in this house.', 'album_idx': 5},
        {'type': 'DAILY_PROMPT', 'tpl': 'Has to be {title} by {artist}. Changed my entire taste in music.', 'album_idx': 5, 'prompt_text': 'the album that changed everything'},
    ],
    'cynjean1119': [
        {'type': 'NOW_SPINNING', 'tpl': '{artist} - {title}. Third spin today and I am not sorry.', 'album_idx': 9},
        {'type': 'NEW_HAUL', 'tpl': 'Found {title} on clear vinyl at the shop downtown. {artist} discography is almost complete.', 'album_idx': 18},
    ],
    'hayleyav1': [
        {'type': 'NOW_SPINNING', 'tpl': 'Nothing like {title} on a rainy afternoon. {artist} understood melancholy.', 'album_idx': 19},
        {'type': 'ISO', 'tpl': 'Looking for {title} by {artist}. Need the deluxe vinyl pressing specifically.', 'album_idx': 6},
        {'type': 'NOTE', 'tpl': 'The smell of a new record sleeve is genuinely one of my favorite things in the world.'},
    ],
    'patrickseijo': [
        {'type': 'NOW_SPINNING', 'tpl': '{title} by {artist}. The production on this album is insane on vinyl.', 'album_idx': 14},
        {'type': 'NEW_HAUL', 'tpl': 'Anniversary pressing of {title} just arrived. {artist} never misses.', 'album_idx': 13},
    ],
    'soniajeanettebrooks': [
        {'type': 'NOW_SPINNING', 'tpl': 'Winding down with {title}. {artist} at golden hour is peak living.', 'album_idx': 17},
        {'type': 'NEW_HAUL', 'tpl': 'Estate sale find: {title} by {artist}. Original pressing. I screamed.', 'album_idx': 12},
        {'type': 'DAILY_PROMPT', 'tpl': '{title} by {artist}. No explanation needed, just vibes.', 'album_idx': 17, 'prompt_text': 'the record you never skip'},
    ],
    'charlottelauren04': [
        {'type': 'NOW_SPINNING', 'tpl': '{artist} on vinyl just different. {title} sounds like it was made for this format.', 'album_idx': 22},
        {'type': 'NOTE', 'tpl': 'Started collecting 6 months ago. 47 records deep. Send help (and shelf space).'},
    ],
    'mateo.musichead': [
        {'type': 'NOW_SPINNING', 'tpl': '{title} by {artist}. This album is a masterpiece front to back.', 'album_idx': 10},
        {'type': 'NEW_HAUL', 'tpl': 'Got {title} on splatter vinyl. {artist} collector edition. Worth every penny.', 'album_idx': 16},
    ],
}

async def fetch_cover(session, query):
    """Fetch fresh cover URL from Discogs, verified as accessible."""
    url = f'https://api.discogs.com/database/search?q={query}&type=release&per_page=5'
    headers = {'Authorization': f'Discogs token={DISCOGS_TOKEN}', 'User-Agent': DISCOGS_UA}
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                for r in data.get('results', []):
                    cover = r.get('cover_image', '')
                    if cover:
                        async with session.head(cover, timeout=aiohttp.ClientTimeout(total=5)) as t:
                            if t.status == 200:
                                return cover
                        thumb = r.get('thumb', '')
                        if thumb:
                            return thumb
            elif resp.status == 429:
                await asyncio.sleep(3)
                return await fetch_cover(session, query)
    except Exception as e:
        print(f'  Error fetching {query}: {e}')
    return None

async def seed():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client['groove-social-beta-test_database']
    
    now = datetime.now(timezone.utc)
    
    # Pre-fetch all album covers
    print('Fetching album covers from Discogs...')
    cover_cache = {}
    async with aiohttp.ClientSession() as session:
        for album in ALBUMS:
            q = album['q']
            cover = await fetch_cover(session, q)
            if cover:
                cover_cache[q] = cover
                print(f'  OK: {album["title"]}')
            else:
                print(f'  MISS: {album["title"]}')
            await asyncio.sleep(1.1)  # Rate limit
    
    print(f'\nCovers fetched: {len(cover_cache)}/{len(ALBUMS)}')
    
    # Create posts for each user
    total_inserted = 0
    total_follows = 0
    total_likes = 0
    
    katie = await db.users.find_one({'username': 'katie'}, {'_id': 0, 'id': 1})
    katie_id = katie['id']
    
    for username, posts in USER_POSTS.items():
        user = await db.users.find_one(
            {'$or': [
                {'username': username},
                {'username': {'$regex': f'^{username}$', '$options': 'i'}}
            ]},
            {'_id': 0, 'id': 1, 'username': 1}
        )
        
        if not user:
            print(f'\n  SKIP: @{username} not in DB')
            continue
        
        print(f'\n  @{user["username"]}:')
        
        for i, post_def in enumerate(posts):
            album = ALBUMS[post_def.get('album_idx', 0)] if 'album_idx' in post_def else None
            
            # Build caption
            if album:
                caption = post_def['tpl'].format(
                    title=album['title'],
                    artist=album['artist']
                )
            else:
                caption = post_def['tpl']
            
            post_time = (now - timedelta(hours=random.randint(6, 96))).isoformat()
            
            post_doc = {
                'id': str(uuid.uuid4()),
                'user_id': user['id'],
                'post_type': post_def['type'],
                'caption': caption,
                'content': caption,
                'created_at': post_time,
                'updated_at': post_time,
                'is_pinned': False,
            }
            
            # Add album info and cover
            if album:
                post_doc['record_title'] = album['title']
                post_doc['record_artist'] = album['artist']
                cover = cover_cache.get(album['q'])
                if cover:
                    post_doc['cover_url'] = cover
            
            # Add prompt text for DAILY_PROMPT
            if post_def['type'] == 'DAILY_PROMPT':
                post_doc['prompt_text'] = post_def.get('prompt_text', 'a daily prompt')
            
            # For ISO posts, create an iso_item
            if post_def['type'] == 'ISO' and album:
                iso_id = str(uuid.uuid4())
                post_doc['iso_id'] = iso_id
                post_doc['intent'] = 'hunting'
                await db.iso_items.insert_one({
                    'id': iso_id,
                    'album': album['title'],
                    'artist': album['artist'],
                    'cover_url': cover_cache.get(album['q'], ''),
                    'user_id': user['id'],
                    'status': 'WISHLIST',
                    'priority': 'MEDIUM',
                    'created_at': post_time,
                })
            
            await db.posts.insert_one(post_doc)
            total_inserted += 1
            art = 'YES' if post_doc.get('cover_url') else 'NO'
            print(f'    [{post_def["type"]}] {caption[:50]}... art={art}')
        
        # Create follow relationship: user follows katie and katie follows back
        for follower_id, following_id in [(user['id'], katie_id), (katie_id, user['id'])]:
            existing = await db.followers.find_one({'follower_id': follower_id, 'following_id': following_id})
            if not existing:
                await db.followers.insert_one({
                    'id': str(uuid.uuid4()),
                    'follower_id': follower_id,
                    'following_id': following_id,
                    'created_at': (now - timedelta(days=random.randint(1, 5))).isoformat()
                })
                total_follows += 1
        
        # Katie likes their posts
        user_posts = await db.posts.find({'user_id': user['id']}, {'_id': 0, 'id': 1}).limit(2).to_list(2)
        for p in user_posts:
            existing = await db.likes.find_one({'post_id': p['id'], 'user_id': katie_id})
            if not existing:
                await db.likes.insert_one({
                    'id': str(uuid.uuid4()),
                    'post_id': p['id'],
                    'user_id': katie_id,
                    'created_at': (now - timedelta(hours=random.randint(1, 24))).isoformat()
                })
                total_likes += 1
    
    print(f'\n=== SEEDING COMPLETE ===')
    print(f'Posts created: {total_inserted}')
    print(f'Follows added: {total_follows}')
    print(f'Likes added: {total_likes}')
    
    # Final stats
    total_posts = await db.posts.count_documents({})
    feed_users = await db.posts.distinct('user_id')
    
    ALLOWED = {'NOW_SPINNING', 'NEW_HAUL', 'ISO', 'RANDOMIZER', 'DAILY_PROMPT', 'NOTE'}
    NEED_CAPTION = {'NOW_SPINNING', 'NEW_HAUL', 'RANDOMIZER'}
    all_posts = await db.posts.find({}, {'_id': 0, 'post_type': 1, 'caption': 1, 'content': 1, 'user_id': 1, 'cover_url': 1}).to_list(None)
    
    feed_visible = 0
    posters = set()
    with_art = 0
    for p in all_posts:
        pt = (p.get('post_type') or '').upper()
        if pt not in ALLOWED: continue
        cap = (p.get('caption') or p.get('content') or '').strip()
        if pt in NEED_CAPTION and not cap: continue
        feed_visible += 1
        posters.add(p['user_id'])
        if p.get('cover_url'): with_art += 1
    
    poster_names = []
    for pid in posters:
        u = await db.users.find_one({'id': pid}, {'_id': 0, 'username': 1})
        if u: poster_names.append(u['username'])
    
    print(f'\n=== FINAL PRODUCTION STATE ===')
    print(f'Total posts: {total_posts}')
    print(f'Feed-visible: {feed_visible}')
    print(f'With album art: {with_art}')
    print(f'Unique posters: {len(poster_names)} -> {sorted(poster_names)}')
    print(f'Total follows: {await db.followers.count_documents({})}')
    print(f'Total likes: {await db.likes.count_documents({})}')
    
    client.close()

asyncio.run(seed())
