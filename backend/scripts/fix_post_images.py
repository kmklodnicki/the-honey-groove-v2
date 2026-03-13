"""
Fix seeded posts: add cover_url from Discogs for album art.
"""
import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv()

# Map record_title+artist to known Discogs cover URLs
COVER_MAP = {
    'Rumours|Fleetwood Mac': 'https://i.discogs.com/2FKFnWr-6pWNEs5MV7FiBK4eVMD1JGPHwYpjVmVXeIQ/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTExNTk3/MjgtMTUxOTMxNjQ4/OC0zMjYwLmpwZWc.jpeg',
    'Blonde on Blonde|Bob Dylan': 'https://i.discogs.com/HKww7s6iBMXbbvxPjnw-g4SCjON_wy_PXnxAkz-F3CQ/rs:fit/g:sm/q:90/h:596/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTIxMTc1/NjYtMTI2NTIwMDcw/Ni5qcGVn.jpeg',
    'Punisher|Phoebe Bridgers': 'https://i.discogs.com/FCKrNrG1FH4IYqJ4hhW1CtPYWEqP4x4hnCqSYkS0mlc/rs:fit/g:sm/q:90/h:597/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTE1NDYx/NjU3LTE1OTM0MTUz/OTAtOTMzMS5qcGVn.jpeg',
    'Pure Heroine|Lorde': 'https://i.discogs.com/1j2mO0HUc1_2LhMqXpIbgMOsDv_d3v8vxFBaGXR0veA/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTU0NDgy/NzItMTM5NTc3MTMx/NS03NjcxLmpwZWc.jpeg',
    'Kind of Blue|Miles Davis': 'https://i.discogs.com/xDJqRJaTGYYD5xAYt15U0bJk8t8aKjP3xqpOJPVQpjc/rs:fit/g:sm/q:90/h:587/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTE1MDU0/MzEtMTQ3NzI2NjA3/MC04NzIxLmpwZWc.jpeg',
    'Songs in the Key of Life|Stevie Wonder': 'https://i.discogs.com/D8R0gTLFwh3w1R30cQLW6EKE3a9NbgDfyTqm2BFn7x0/rs:fit/g:sm/q:90/h:590/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTE2NDI2/MDktMTIzMDU1MzY5/OC5qcGVn.jpeg',
    'OK Computer|Radiohead': 'https://i.discogs.com/4OtEJe3oX3Q1f0bWwZcY0bdXuib3rdEh-Xl9V_UrqMg/rs:fit/g:sm/q:90/h:592/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTMyNjIy/My0xNDU4MzAzNDIz/LTQ0ODEuanBlZw.jpeg',
    'In Rainbows|Radiohead': 'https://i.discogs.com/C4CASwRBFx3-YZMhOo-4owWjrYk4zoiJ3UVWTLhWP64/rs:fit/g:sm/q:90/h:595/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTExOTAw/MzItMTUyMzY1MDY4/NC01NjY3LmpwZWc.jpeg',
    'Titanic Rising|Weyes Blood': 'https://i.discogs.com/2m-GSJZ7bJtZLNqZF0b5Xz9EBWTrPxQCL50qSSXH_iw/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTEzNDU5/MTIyLTE1NTQ3OTE1/MDgtNDY2My5qcGVn.jpeg',
    'Abbey Road|The Beatles': 'https://i.discogs.com/GOGTc71ZYfVVFx-MYoYqVwQEOoiVaSLEGBPqNPCqFmk/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTE0ODUw/OTYtMTUyNjY1MjY0/Ny02MjE2LmpwZWc.jpeg',
}

# Generic vinyl placeholder for posts without specific albums
GENERIC_VINYL = 'https://i.discogs.com/vX7t4jYeEb6e_C_1oj1sSWjZq7PYxMHZPr7gINpb7r4/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTMyOTU2/MzEtMTMyNTc2Mjcw/MS5qcGVn.jpeg'

async def fix_images():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client['groove-social-beta-test_database']
    
    katie = await db.users.find_one({'username': 'katie'}, {'_id': 0, 'id': 1})
    
    # Find all seeded posts (no record_id, no cover_url)
    seeded = await db.posts.find({
        'user_id': {'$ne': katie['id']},
        'record_id': {'$exists': False},
        'cover_url': {'$exists': False}
    }, {'_id': 0, 'id': 1, 'record_title': 1, 'record_artist': 1, 'post_type': 1, 'caption': 1}).to_list(None)
    
    print(f'Found {len(seeded)} seeded posts to fix')
    
    fixed = 0
    for post in seeded:
        title = post.get('record_title', '')
        artist = post.get('record_artist', '')
        key = f'{title}|{artist}'
        
        cover = COVER_MAP.get(key)
        
        # For posts without explicit record_title, try to extract from caption
        if not cover:
            caption = (post.get('caption') or '').lower()
            for map_key, url in COVER_MAP.items():
                album, art = map_key.split('|')
                if album.lower() in caption or art.lower() in caption:
                    cover = url
                    # Also set record_title and record_artist
                    title = album
                    artist = art
                    break
        
        if cover:
            update = {'$set': {'cover_url': cover}}
            if title and not post.get('record_title'):
                update['$set']['record_title'] = title
            if artist and not post.get('record_artist'):
                update['$set']['record_artist'] = artist
            await db.posts.update_one({'id': post['id']}, update)
            print(f'  Fixed: [{post.get("post_type")}] {title} by {artist}')
            fixed += 1
        else:
            # No specific album - leave as text-only post (NOTE, ISO don't need images)
            pt = post.get('post_type', '')
            if pt in ('NOW_SPINNING', 'NEW_HAUL', 'RANDOMIZER'):
                # These should have an image - use generic vinyl
                await db.posts.update_one({'id': post['id']}, {'$set': {'cover_url': GENERIC_VINYL}})
                print(f'  Generic: [{pt}] {(post.get("caption") or "")[:40]}')
                fixed += 1
            else:
                print(f'  Text-only OK: [{pt}] {(post.get("caption") or "")[:40]}')
    
    print(f'\nFixed {fixed} posts with cover art')
    
    # Also check Katie's posts that might have broken image URLs
    katie_posts = await db.posts.find({
        'user_id': katie['id'],
        'image_url': {'$exists': True, '$ne': None}
    }, {'_id': 0, 'id': 1, 'image_url': 1, 'post_type': 1}).to_list(None)
    
    broken_katie = 0
    for p in katie_posts:
        url = p.get('image_url', '')
        if url and ('localhost' in url or 'preview.emergentagent' in url or 'emergent.host' in url):
            broken_katie += 1
            print(f'  Katie broken img: {url[:60]}')
    
    if broken_katie:
        print(f'\nKatie has {broken_katie} posts with potentially broken image URLs')
    
    # Verify
    all_posts = await db.posts.find({}, {'_id': 0, 'id': 1, 'post_type': 1, 'cover_url': 1, 'record_id': 1, 'image_url': 1, 'user_id': 1}).to_list(None)
    
    with_art = sum(1 for p in all_posts if p.get('cover_url') or p.get('record_id') or p.get('image_url'))
    text_only = sum(1 for p in all_posts if not p.get('cover_url') and not p.get('record_id') and not p.get('image_url'))
    
    print(f'\n=== FINAL IMAGE STATUS ===')
    print(f'Posts with album art: {with_art}')
    print(f'Text-only posts: {text_only}')
    
    client.close()

asyncio.run(fix_images())
