"""
FORENSIC SEARCH: Find ALL traces of user activity across ALL collections and ALL databases.
"""
import asyncio, os, json
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

TARGET_STRINGS = ['sxrtmy', 'travis13bell', 'kellansvinyl']

async def search():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    all_dbs = await client.list_database_names()
    
    print(f'DATABASES ON CLUSTER: {all_dbs}')
    
    for db_name in all_dbs:
        if db_name in ('admin', 'local'):
            continue
        db = client[db_name]
        colls = await db.list_collection_names()
        
        print(f'\n{"="*60}')
        print(f'DATABASE: {db_name} ({len(colls)} collections)')
        print(f'{"="*60}')
        
        # 1. List ALL collections with doc counts
        print(f'\nAll collections:')
        for c in sorted(colls):
            count = await db[c].count_documents({})
            if count > 0:
                print(f'  {c}: {count}')
        
        # 2. Search for target strings in EVERY collection
        for target in TARGET_STRINGS:
            print(f'\n--- Searching for "{target}" ---')
            for c in sorted(colls):
                count = await db[c].count_documents({})
                if count == 0:
                    continue
                
                # Get sample doc to know the fields
                sample = await db[c].find_one({}, {'_id': 0})
                if not sample:
                    continue
                
                # Search ALL string fields for the target
                or_conditions = []
                for key, val in sample.items():
                    if isinstance(val, str):
                        or_conditions.append({key: {'$regex': target, '$options': 'i'}})
                
                if not or_conditions:
                    continue
                
                found = await db[c].count_documents({'$or': or_conditions})
                if found > 0:
                    docs = await db[c].find({'$or': or_conditions}, {'_id': 0}).limit(5).to_list(5)
                    print(f'  FOUND in {c}: {found} docs')
                    for d in docs:
                        # Truncate long values
                        summary = {}
                        for k, v in d.items():
                            if isinstance(v, str) and len(v) > 60:
                                summary[k] = v[:60] + '...'
                            else:
                                summary[k] = v
                        print(f'    {json.dumps(summary, default=str)[:200]}')
        
        # 3. Check for feed/timeline/activity collections specifically
        feed_colls = [c for c in colls if any(kw in c.lower() for kw in 
            ['feed', 'timeline', 'activ', 'action', 'event', 'stream', 'interact'])]
        if feed_colls:
            print(f'\nFeed/Activity collections found: {feed_colls}')
            for fc in feed_colls:
                count = await db[fc].count_documents({})
                sample = await db[fc].find_one({}, {'_id': 0})
                print(f'  {fc}: {count} docs')
                if sample:
                    print(f'    Keys: {list(sample.keys())}')
                    print(f'    Sample: {json.dumps(sample, default=str)[:200]}')
        
        # 4. Comments collection
        comments = await db.comments.find({}, {'_id': 0}).to_list(None)
        if comments:
            print(f'\nCOMMENTS: {len(comments)}')
            for c in comments[:10]:
                print(f'  {json.dumps(c, default=str)[:200]}')
        
        # 5. Notifications collection
        notifs = await db.notifications.find({}, {'_id': 0}).to_list(None)
        if notifs:
            print(f'\nNOTIFICATIONS: {len(notifs)}')
            for n in notifs[:10]:
                print(f'  type={n.get("type")} | {json.dumps(n, default=str)[:150]}')
        
        # 6. Followers/follows
        follows = await db.followers.find({}, {'_id': 0}).to_list(None)
        if follows:
            print(f'\nFOLLOWERS: {len(follows)}')
            for f in follows[:10]:
                # Resolve usernames
                follower = await db.users.find_one({'id': f.get('follower_id')}, {'_id': 0, 'username': 1})
                following = await db.users.find_one({'id': f.get('following_id')}, {'_id': 0, 'username': 1})
                fn = follower.get('username','?') if follower else 'UNKNOWN'
                fg = following.get('username','?') if following else 'UNKNOWN'
                print(f'  @{fn} -> @{fg} ({f.get("created_at","")[:19]})')
        
        # 7. Daily prompts
        for coll_name in ['prompts', 'daily_prompts', 'prompt_responses', 'daily_prompt_answers']:
            if coll_name in colls:
                count = await db[coll_name].count_documents({})
                if count > 0:
                    print(f'\n{coll_name.upper()}: {count} docs')
                    samples = await db[coll_name].find({}, {'_id': 0}).limit(3).to_list(3)
                    for s in samples:
                        print(f'  {json.dumps(s, default=str)[:200]}')
    
    client.close()

asyncio.run(search())
