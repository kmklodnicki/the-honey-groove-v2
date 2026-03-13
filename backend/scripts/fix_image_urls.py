"""Fix broken Discogs image URLs by fetching fresh ones from the API."""
import asyncio, os, time
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

DISCOGS_TOKEN = os.environ.get('DISCOGS_TOKEN', '')
DISCOGS_UA = os.environ.get('DISCOGS_USER_AGENT', 'WaxLog/1.0')

# Album -> Discogs release ID mapping for quick lookups
ALBUM_SEARCH = {
    'Rumours': 'Fleetwood Mac Rumours',
    'Abbey Road': 'Beatles Abbey Road',
    'Blonde on Blonde': 'Bob Dylan Blonde on Blonde',
    'Punisher': 'Phoebe Bridgers Punisher',
    'Pure Heroine': 'Lorde Pure Heroine',
    'Kind of Blue': 'Miles Davis Kind of Blue',
    'Songs in the Key of Life': 'Stevie Wonder Songs Key Life',
    'OK Computer': 'Radiohead OK Computer',
    'In Rainbows': 'Radiohead In Rainbows',
    'Titanic Rising': 'Weyes Blood Titanic Rising',
    'Amnesiac': 'Radiohead Amnesiac',
    "Fearless (Taylor's Version)": 'Taylor Swift Fearless Taylors Version vinyl',
    'Record Store Day 2025 Releases': 'Record Store Day',
    'Live Recordings (Bootleg)': 'Radiohead live bootleg',
}

async def fetch_cover(session, query):
    """Fetch a cover image URL from Discogs API."""
    url = f'https://api.discogs.com/database/search?q={query}&type=release&per_page=1'
    headers = {
        'Authorization': f'Discogs token={DISCOGS_TOKEN}',
        'User-Agent': DISCOGS_UA,
    }
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = data.get('results', [])
                if results:
                    cover = results[0].get('cover_image', '')
                    thumb = results[0].get('thumb', '')
                    # Prefer cover_image over thumb
                    return cover or thumb
            elif resp.status == 429:
                print(f'  Rate limited, waiting...')
                await asyncio.sleep(3)
                return await fetch_cover(session, query)
            else:
                print(f'  API error {resp.status} for: {query}')
    except Exception as e:
        print(f'  Fetch error: {e}')
    return None

async def fix():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client['groove-social-beta-test_database']
    
    # Find all posts with cover_url that might be broken (403)
    posts_with_cover = await db.posts.find(
        {'cover_url': {'$exists': True, '$ne': None}},
        {'_id': 0, 'id': 1, 'cover_url': 1, 'record_title': 1, 'record_artist': 1, 'post_type': 1, 'user_id': 1}
    ).to_list(None)
    
    print(f'Posts with cover_url: {len(posts_with_cover)}')
    
    async with aiohttp.ClientSession() as session:
        fixed = 0
        for post in posts_with_cover:
            cover = post.get('cover_url', '')
            
            # Test if current URL works
            try:
                async with session.head(cover, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        continue  # Working fine
                    else:
                        print(f'  BROKEN ({resp.status}): {post.get("record_title","?")} | {cover[:60]}')
            except:
                print(f'  TIMEOUT: {post.get("record_title","?")}')
            
            # Need to fetch a new URL
            title = post.get('record_title', '')
            artist = post.get('record_artist', '')
            
            query = ALBUM_SEARCH.get(title, f'{artist} {title}')
            if not query:
                query = f'{artist} {title}'
            
            print(f'  Searching Discogs: "{query}"')
            new_cover = await fetch_cover(session, query)
            
            if new_cover:
                await db.posts.update_one(
                    {'id': post['id']},
                    {'$set': {'cover_url': new_cover}}
                )
                print(f'  FIXED: {title} -> {new_cover[:60]}')
                fixed += 1
                
                # Also update matching iso_items
                if post.get('post_type') == 'ISO':
                    await db.iso_items.update_many(
                        {'user_id': post['user_id']},
                        {'$set': {'cover_url': new_cover}}
                    )
            else:
                print(f'  NO RESULT for: {query}')
            
            # Rate limit: Discogs allows ~60 req/min
            await asyncio.sleep(1.2)
        
        print(f'\nFixed {fixed} broken URLs')
    
    # Final verification
    print('\n=== VERIFICATION ===')
    all_posts = await db.posts.find(
        {'cover_url': {'$exists': True, '$ne': None}},
        {'_id': 0, 'cover_url': 1, 'record_title': 1}
    ).to_list(None)
    
    async with aiohttp.ClientSession() as session:
        ok = 0
        broken = 0
        for p in all_posts:
            try:
                async with session.head(p['cover_url'], timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        ok += 1
                    else:
                        broken += 1
                        print(f'  Still broken: {p.get("record_title","?")} ({resp.status})')
            except:
                broken += 1
                print(f'  Still broken (timeout): {p.get("record_title","?")}')
        
        print(f'\nWorking: {ok}, Broken: {broken}')
    
    client.close()

asyncio.run(fix())
