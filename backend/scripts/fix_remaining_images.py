"""Fix remaining broken image URLs."""
import asyncio, os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

DISCOGS_TOKEN = os.environ.get('DISCOGS_TOKEN', '')
DISCOGS_UA = os.environ.get('DISCOGS_USER_AGENT', 'WaxLog/1.0')

async def fetch_cover(session, query):
    url = f'https://api.discogs.com/database/search?q={query}&type=release&per_page=1'
    headers = {
        'Authorization': f'Discogs token={DISCOGS_TOKEN}',
        'User-Agent': DISCOGS_UA,
    }
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
            results = data.get('results', [])
            if results:
                return results[0].get('cover_image', '') or results[0].get('thumb', '')
        elif resp.status == 429:
            await asyncio.sleep(3)
            return await fetch_cover(session, query)
    return None

async def fix():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client['groove-social-beta-test_database']
    
    posts = await db.posts.find(
        {'cover_url': {'$exists': True, '$ne': None}},
        {'_id': 0, 'id': 1, 'cover_url': 1, 'record_title': 1, 'record_artist': 1, 'post_type': 1, 'user_id': 1}
    ).to_list(None)
    
    # Specific search queries for remaining broken ones
    SPECIFIC_SEARCHES = {
        'Rumours': 'Fleetwood Mac Rumours vinyl LP',
        'Amnesiac': 'Radiohead Amnesiac vinyl LP',
        "Fearless (Taylor's Version)": 'Taylor Swift Fearless vinyl LP',
        'TEST_Unofficial_Album_Success': None,  # Delete this test post
        'TEST_Official_Album': None,  # Delete this test post
    }
    
    async with aiohttp.ClientSession() as session:
        fixed = 0
        for post in posts:
            cover = post.get('cover_url', '')
            title = post.get('record_title', '')
            
            # Test current URL
            try:
                async with session.head(cover, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        continue
            except:
                pass
            
            # Check if it's a test post to delete
            if title and title.startswith('TEST_'):
                await db.posts.delete_one({'id': post['id']})
                print(f'  DELETED test post: {title}')
                continue
            
            # For posts with no record_title, try to find what they are
            if not title:
                # These are generic posts - use a real album search
                search = 'vinyl record collection'
                new_cover = await fetch_cover(session, search)
                if new_cover:
                    await db.posts.update_one({'id': post['id']}, {'$set': {'cover_url': new_cover}})
                    print(f'  FIXED generic post with collection image')
                    fixed += 1
                await asyncio.sleep(1.2)
                continue
            
            # Specific search
            search = SPECIFIC_SEARCHES.get(title, f'{post.get("record_artist","")} {title} vinyl LP')
            if search is None:
                continue
            
            print(f'  Searching: "{search}"')
            new_cover = await fetch_cover(session, search)
            if new_cover:
                await db.posts.update_one({'id': post['id']}, {'$set': {'cover_url': new_cover}})
                print(f'  FIXED: {title} -> {new_cover[:60]}')
                fixed += 1
            
            await asyncio.sleep(1.2)
        
        print(f'\nFixed {fixed} more URLs')
    
    # Final verification
    print('\n=== FINAL VERIFICATION ===')
    all_posts = await db.posts.find(
        {'cover_url': {'$exists': True, '$ne': None}},
        {'_id': 0, 'cover_url': 1, 'record_title': 1}
    ).to_list(None)
    
    async with aiohttp.ClientSession() as session:
        ok = broken = 0
        for p in all_posts:
            try:
                async with session.head(p['cover_url'], timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        ok += 1
                    else:
                        broken += 1
                        print(f'  STILL BROKEN ({resp.status}): {p.get("record_title","?")} | {p["cover_url"][:60]}')
            except:
                broken += 1
        print(f'\nWorking: {ok}, Broken: {broken}')
    
    client.close()

asyncio.run(fix())
