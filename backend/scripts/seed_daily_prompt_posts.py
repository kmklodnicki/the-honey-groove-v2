"""Seed Daily Prompt responses as feed posts with album art."""
import asyncio, os, uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

PROMPT_RESPONSES = [
    {
        'username': 'kellansvinyl',
        'prompt_text': 'the album that got you into vinyl',
        'caption': 'Abbey Road. My dad had an original pressing and I remember hearing Come Together through floor speakers. Changed everything.',
        'record_title': 'Abbey Road',
        'record_artist': 'The Beatles',
        'cover_url': 'https://i.discogs.com/GOGTc71ZYfVVFx-MYoYqVwQEOoiVaSLEGBPqNPCqFmk/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTE0ODUw/OTYtMTUyNjY1MjY0/Ny02MjE2LmpwZWc.jpeg',
        'hours_ago': 36,
    },
    {
        'username': 'jacksongamer990',
        'prompt_text': 'a record everyone sleeps on',
        'caption': 'Amnesiac by Radiohead. Everyone talks about Kid A but this one is just as good. Maybe better.',
        'record_title': 'Amnesiac',
        'record_artist': 'Radiohead',
        'cover_url': 'https://i.discogs.com/u-9a5nH6qC8A7u_dPPRR1lqVMpCvZMJZVYyg7XLQjI8/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTExNzMy/MTAtMTU0NjkwMjQ3/Ni0xMjg5LmpwZWc.jpeg',
        'hours_ago': 28,
    },
    {
        'username': 'hollandgrace456',
        'prompt_text': 'the one that started it all',
        'caption': 'Fearless (Taylor\'s Version). My first vinyl purchase ever. The gold pressing. I held it like a newborn.',
        'record_title': "Fearless (Taylor's Version)",
        'record_artist': 'Taylor Swift',
        'cover_url': 'https://i.discogs.com/6uVF3CfFHBuMMBH2YyDjqwK3yrg4f-RfKsywVdY69cA/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTE4MTY4/NjExLTE2MjE2MDc0/MzYtMjQ5MC5qcGVn.jpeg',
        'hours_ago': 14,
    },
]

async def seed():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client['groove-social-beta-test_database']
    
    now = datetime.now(timezone.utc)
    seeded = 0
    
    for resp in PROMPT_RESPONSES:
        user = await db.users.find_one({'username': resp['username']}, {'_id': 0, 'id': 1})
        if not user:
            print(f'  User not found: {resp["username"]}')
            continue
        
        post_time = (now - timedelta(hours=resp['hours_ago'])).isoformat()
        
        post = {
            'id': str(uuid.uuid4()),
            'user_id': user['id'],
            'post_type': 'DAILY_PROMPT',
            'prompt_text': resp['prompt_text'],
            'caption': resp['caption'],
            'content': resp['caption'],
            'record_title': resp['record_title'],
            'record_artist': resp['record_artist'],
            'cover_url': resp['cover_url'],
            'created_at': post_time,
            'updated_at': post_time,
            'is_pinned': False,
        }
        
        await db.posts.insert_one(post)
        seeded += 1
        print(f'  Seeded: [{resp["username"]}] {resp["prompt_text"][:40]} -> {resp["record_title"]}')
    
    # Verify
    dp_posts = await db.posts.find({'post_type': 'DAILY_PROMPT'}, {'_id': 0, 'id': 1, 'prompt_text': 1, 'cover_url': 1, 'record_title': 1, 'user_id': 1}).to_list(None)
    print(f'\nTotal DAILY_PROMPT posts: {len(dp_posts)}')
    for p in dp_posts:
        u = await db.users.find_one({'id': p['user_id']}, {'_id': 0, 'username': 1})
        print(f'  [{(u or {}).get("username","?")}] {p.get("record_title","?")} | cover={"YES" if p.get("cover_url") else "NO"}')
    
    client.close()

asyncio.run(seed())
