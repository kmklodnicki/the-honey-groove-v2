"""Fix ISO posts: add cover_url and iso_item entries."""
import asyncio, os, uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

ISO_DATA = [
    {
        'caption_match': 'colored vinyl pressings',
        'album': 'Record Store Day 2025 Releases',
        'artist': 'Various Artists',
        'cover_url': 'https://i.discogs.com/vX7t4jYeEb6e_C_1oj1sSWjZq7PYxMHZPr7gINpb7r4/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTMyOTU2/MzEtMTMyNTc2Mjcw/MS5qcGVn.jpeg',
        'intent': 'hunting',
        'priority': 'MEDIUM',
    },
    {
        'caption_match': 'radiohead bootleg',
        'album': 'Live Recordings (Bootleg)',
        'artist': 'Radiohead',
        'cover_url': 'https://i.discogs.com/4OtEJe3oX3Q1f0bWwZcY0bdXuib3rdEh-Xl9V_UrqMg/rs:fit/g:sm/q:90/h:592/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTMyNjIy/My0xNDU4MzAzNDIz/LTQ0ODEuanBlZw.jpeg',
        'intent': 'hunting',
        'priority': 'LOW',
    },
]

async def fix_isos():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client['groove-social-beta-test_database']
    
    iso_posts = await db.posts.find({'post_type': 'ISO'}, {'_id': 0}).to_list(None)
    print(f'ISO posts to fix: {len(iso_posts)}')
    
    fixed = 0
    for post in iso_posts:
        # Skip if already has iso_id
        if post.get('iso_id'):
            print(f'  Already linked: {(post.get("caption") or "")[:40]}')
            continue
        
        caption = (post.get('caption') or '').lower()
        
        matched = None
        for data in ISO_DATA:
            if data['caption_match'] in caption:
                matched = data
                break
        
        if not matched:
            matched = ISO_DATA[0]
        
        iso_id = str(uuid.uuid4())
        iso_item = {
            'id': iso_id,
            'album': matched['album'],
            'artist': matched['artist'],
            'cover_url': matched['cover_url'],
            'user_id': post['user_id'],
            'status': 'WISHLIST',
            'priority': matched.get('priority', 'LOW'),
            'created_at': post['created_at'],
        }
        
        await db.iso_items.insert_one(iso_item)
        
        await db.posts.update_one(
            {'id': post['id']},
            {'$set': {
                'iso_id': iso_id,
                'cover_url': matched['cover_url'],
                'record_title': matched['album'],
                'record_artist': matched['artist'],
                'intent': matched.get('intent', 'hunting'),
            }}
        )
        
        print(f'  Fixed: {matched["artist"]} - {matched["album"]}')
        fixed += 1
    
    # Verify
    all_isos = await db.posts.find({'post_type': 'ISO'}, {'_id': 0, 'id': 1, 'caption': 1, 'cover_url': 1, 'iso_id': 1, 'record_title': 1}).to_list(None)
    print(f'\n=== FINAL ISO STATUS ({len(all_isos)} posts) ===')
    for p in all_isos:
        print(f'  [{p.get("record_title", "?")}] cover={"YES" if p.get("cover_url") else "NO"} iso={"YES" if p.get("iso_id") else "NO"}')
    
    client.close()

asyncio.run(fix_isos())
