"""Check and fix daily prompts in production DB."""
import asyncio
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

async def check():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client['groove-social-beta-test_database']
    
    all_prompts = await db.prompts.find({}, {'_id': 0, 'id': 1, 'text': 1, 'scheduled_date': 1, 'is_active': 1}).sort('scheduled_date', 1).to_list(None)
    print(f'Total prompts: {len(all_prompts)}')
    
    dates = [p.get('scheduled_date','')[:10] for p in all_prompts if p.get('scheduled_date')]
    if dates:
        print(f'Range: {min(dates)} to {max(dates)}')
    
    print(f'\nAll March prompts:')
    march = []
    for p in all_prompts:
        d = (p.get('scheduled_date') or '')[:10]
        if '2026-03' in d:
            march.append(p)
            print(f'  [{d}] active={p.get("is_active","?")} | {p.get("text","?")[:55]}')
    
    if not march:
        print('  NONE! No March prompts at all.')
        # Show the earliest prompts
        print(f'\nEarliest 5 prompts:')
        for p in all_prompts[:5]:
            print(f'  [{p.get("scheduled_date","?")[:10]}] {p.get("text","?")[:55]}')
        print(f'\nLatest 5 prompts:')
        for p in all_prompts[-5:]:
            print(f'  [{p.get("scheduled_date","?")[:10]}] {p.get("text","?")[:55]}')
    
    # Check how the /prompts/today endpoint works
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f'\nToday is: {today}')
    
    # Search for today's prompt with various date formats
    for fmt in [today, f'{today}T', today.replace('-', '')]:
        found = await db.prompts.find_one({'scheduled_date': {'$regex': fmt}}, {'_id': 0})
        if found:
            print(f'  Found with format {fmt}: {found.get("text","?")[:50]}')
            break
    else:
        print(f'  No prompt scheduled for {today}')
    
    # Check prompt_responses
    responses = await db.prompt_responses.find({}, {'_id': 0}).to_list(None)
    print(f'\nPrompt responses: {len(responses)}')
    for r in responses[:3]:
        print(f'  user={r.get("user_id","?")[:12]} | {r.get("text","")[:40]}')
    
    # Check DAILY_PROMPT type posts
    dp_posts = await db.posts.find({'post_type': 'DAILY_PROMPT'}, {'_id': 0}).to_list(None)
    print(f'\nDAILY_PROMPT posts: {len(dp_posts)}')
    for p in dp_posts:
        print(f'  [{p.get("created_at","")[:10]}] {p.get("prompt_text","?")[:40]} | cover={bool(p.get("cover_url"))}')
    
    client.close()

asyncio.run(check())
