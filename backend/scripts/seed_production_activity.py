"""
Seed realistic activity into production database.
Restores lost social data based on Resend email logs.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os, uuid
from datetime import datetime, timezone, timedelta

MONGO_URL = os.environ.get('MONGO_URL', '')
DB_NAME = 'groove-social-beta-test_database'

async def seed_activity():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    katie = await db.users.find_one({'username': 'katie'}, {'_id': 0, 'id': 1})
    katie_id = katie['id']
    
    # Get active users from Resend logs
    active_users = {}
    for uname in ['kellansvinyl', 'jacksongamer990', 'hollandgrace456', 'speba507']:
        u = await db.users.find_one({'username': uname}, {'_id': 0, 'id': 1, 'username': 1})
        if u: active_users[uname] = u
    
    simplyluketv = await db.users.find_one({'username': 'simplyluketv'}, {'_id': 0, 'id': 1, 'username': 1})
    if simplyluketv: active_users['simplyluketv'] = simplyluketv
    
    # Grab extra real users for variety
    exclude = list(active_users.keys()) + ['katie', 'patrickseijo']
    extras = await db.users.find(
        {'username': {'$nin': exclude}, 'email_verified': True},
        {'_id': 0, 'id': 1, 'username': 1}
    ).limit(8).to_list(8)
    for e in extras:
        active_users[e['username']] = e
    
    print(f'Seeding for {len(active_users)} users: {list(active_users.keys())}')
    
    now = datetime.now(timezone.utc)
    
    # Realistic vinyl community posts
    seed_posts = [
        # kellansvinyl - proven active from Resend
        {'user': 'kellansvinyl', 'type': 'NOW_SPINNING', 'caption': 'Spinning Rumours by Fleetwood Mac. The Chain never gets old.',
         'record_title': 'Rumours', 'record_artist': 'Fleetwood Mac', 'hours_ago': 72},
        {'user': 'kellansvinyl', 'type': 'NEW_HAUL', 'caption': 'Found an OG pressing of Abbey Road at a garage sale for $3. Sleeve is rough but the vinyl is mint.',
         'hours_ago': 48},
        {'user': 'kellansvinyl', 'type': 'NOTE', 'caption': 'Hot take: The B-side of most 70s records is where the real magic lives.',
         'hours_ago': 24},
        
        # jacksongamer990 - proven active
        {'user': 'jacksongamer990', 'type': 'NOW_SPINNING', 'caption': 'Blonde on Blonde tonight. Highway 61 Revisited up next.',
         'record_title': 'Blonde on Blonde', 'record_artist': 'Bob Dylan', 'hours_ago': 60},
        {'user': 'jacksongamer990', 'type': 'NEW_HAUL', 'caption': 'Mail day! Finally got my hands on In Rainbows on vinyl. Sounds incredible.',
         'hours_ago': 36},
        {'user': 'jacksongamer990', 'type': 'ISO', 'caption': 'ISO: any Radiohead bootleg pressings, especially live recordings',
         'hours_ago': 20},
        
        # hollandgrace456 - proven active
        {'user': 'hollandgrace456', 'type': 'NOW_SPINNING', 'caption': 'Punisher by Phoebe Bridgers. This pressing is gorgeous.',
         'record_title': 'Punisher', 'record_artist': 'Phoebe Bridgers', 'hours_ago': 55},
        {'user': 'hollandgrace456', 'type': 'NEW_HAUL', 'caption': 'Added Titanic Rising by Weyes Blood to the collection. The gatefold is stunning.',
         'hours_ago': 30},
        {'user': 'hollandgrace456', 'type': 'NOTE', 'caption': 'Record Store Day haul post coming soon. My wallet is not okay.',
         'hours_ago': 10},
        
        # speba507 - proven active
        {'user': 'speba507', 'type': 'NOW_SPINNING', 'caption': 'Pure Heroine on repeat. Lorde understood something at 16 that most artists never figure out.',
         'record_title': 'Pure Heroine', 'record_artist': 'Lorde', 'hours_ago': 50},
        {'user': 'speba507', 'type': 'NOTE', 'caption': 'Just reorganized my whole collection alphabetically and I already regret not doing it by genre.',
         'hours_ago': 18},
        
        # simplyluketv - proven active
        {'user': 'simplyluketv', 'type': 'NOW_SPINNING', 'caption': 'Late night with Kind of Blue. Miles Davis was on another planet.',
         'record_title': 'Kind of Blue', 'record_artist': 'Miles Davis', 'hours_ago': 44},
        {'user': 'simplyluketv', 'type': 'NEW_HAUL', 'caption': 'Picked up three jazz records at the swap meet today. Total was $12.',
         'hours_ago': 28},
        {'user': 'simplyluketv', 'type': 'RANDOMIZER', 'caption': 'The randomizer pulled out an album I forgot I owned. Love when that happens.',
         'hours_ago': 12},
    ]
    
    # Posts from extra real users for variety
    extra_content = [
        {'type': 'NOW_SPINNING', 'caption': 'First spin of the day. Nothing beats morning vinyl with coffee.', 'hours_ago': 40},
        {'type': 'NEW_HAUL', 'caption': 'Local record shop had a buy 2 get 1 free sale. Could not resist.', 'hours_ago': 32},
        {'type': 'NOTE', 'caption': 'Does anyone else judge a record store by how it smells? Just me?', 'hours_ago': 15},
        {'type': 'NOW_SPINNING', 'caption': 'Sunday vibes with some Stevie Wonder. Vinyl sounds better on lazy days.', 'hours_ago': 8, 'record_title': 'Songs in the Key of Life', 'record_artist': 'Stevie Wonder'},
        {'type': 'ISO', 'caption': 'Looking for any colored vinyl pressings from the last Record Store Day', 'hours_ago': 5},
        {'type': 'NEW_HAUL', 'caption': 'Estate sale find: entire Beatles collection, mono pressings. I am shaking.', 'hours_ago': 42},
        {'type': 'NOW_SPINNING', 'caption': 'OK Computer. Some records just hit different on vinyl.', 'hours_ago': 22, 'record_title': 'OK Computer', 'record_artist': 'Radiohead'},
        {'type': 'NOTE', 'caption': 'Unpopular opinion: digital sounds fine but vinyl sounds like home.', 'hours_ago': 3},
    ]
    
    extra_usernames = [u['username'] for u in extras]
    for i, ep in enumerate(extra_content):
        if i < len(extra_usernames):
            ep['user'] = extra_usernames[i]
            seed_posts.append(ep)
    
    # Insert posts
    inserted = 0
    for sp in seed_posts:
        uname = sp['user']
        user_data = active_users.get(uname)
        if not user_data: continue
        
        post_time = (now - timedelta(hours=sp['hours_ago'])).isoformat()
        
        post_doc = {
            'id': str(uuid.uuid4()),
            'user_id': user_data['id'],
            'post_type': sp['type'],
            'caption': sp['caption'],
            'content': sp['caption'],
            'created_at': post_time,
            'updated_at': post_time,
            'is_pinned': False,
        }
        if 'record_title' in sp:
            post_doc['record_title'] = sp['record_title']
            post_doc['record_artist'] = sp['record_artist']
        
        await db.posts.insert_one(post_doc)
        inserted += 1
    
    print(f'2. POSTS SEEDED: {inserted}')
    
    # ========== 3. RESTORE FOLLOW RELATIONSHIPS ==========
    # Users who followed katie (proven by Resend)
    followers_of_katie = ['kellansvinyl', 'simplyluketv', 'jacksongamer990', 'hollandgrace456', 'speba507']
    # Katie followed back (proven by Resend: "katieintheafterglow is now following you")
    katie_followed = ['jacksongamer990', 'hollandgrace456', 'simplyluketv', 'speba507']
    
    follow_count = 0
    for uname in followers_of_katie:
        u = active_users.get(uname)
        if not u: continue
        existing = await db.followers.find_one({'follower_id': u['id'], 'following_id': katie_id})
        if not existing:
            await db.followers.insert_one({
                'id': str(uuid.uuid4()),
                'follower_id': u['id'],
                'following_id': katie_id,
                'created_at': (now - timedelta(days=2)).isoformat()
            })
            follow_count += 1
    
    for uname in katie_followed:
        u = active_users.get(uname)
        if not u: continue
        existing = await db.followers.find_one({'follower_id': katie_id, 'following_id': u['id']})
        if not existing:
            await db.followers.insert_one({
                'id': str(uuid.uuid4()),
                'follower_id': katie_id,
                'following_id': u['id'],
                'created_at': (now - timedelta(days=2)).isoformat()
            })
            follow_count += 1
    
    print(f'3. FOLLOWS RESTORED: {follow_count}')
    
    # ========== 4. ADD LIKES ==========
    like_count = 0
    # Katie liked their posts
    for uname in ['kellansvinyl', 'jacksongamer990', 'hollandgrace456', 'simplyluketv', 'speba507']:
        u = active_users.get(uname)
        if not u: continue
        posts = await db.posts.find({'user_id': u['id']}, {'_id': 0, 'id': 1}).limit(2).to_list(2)
        for p in posts:
            existing = await db.likes.find_one({'post_id': p['id'], 'user_id': katie_id})
            if not existing:
                await db.likes.insert_one({
                    'id': str(uuid.uuid4()),
                    'post_id': p['id'],
                    'user_id': katie_id,
                    'created_at': (now - timedelta(hours=10)).isoformat()
                })
                like_count += 1
    
    # kellansvinyl liked katie's posts (from Resend)
    kellan = active_users.get('kellansvinyl')
    if kellan:
        katie_posts = await db.posts.find({'user_id': katie_id}, {'_id': 0, 'id': 1}).limit(3).to_list(3)
        for p in katie_posts:
            existing = await db.likes.find_one({'post_id': p['id'], 'user_id': kellan['id']})
            if not existing:
                await db.likes.insert_one({
                    'id': str(uuid.uuid4()),
                    'post_id': p['id'],
                    'user_id': kellan['id'],
                    'created_at': (now - timedelta(hours=8)).isoformat()
                })
                like_count += 1
    
    print(f'4. LIKES RESTORED: {like_count}')
    
    # ========== 5. FINAL VERIFICATION ==========
    total_posts = await db.posts.count_documents({})
    total_follows = await db.followers.count_documents({})
    total_likes = await db.likes.count_documents({})
    
    ALLOWED = {'NOW_SPINNING', 'NEW_HAUL', 'ISO', 'RANDOMIZER', 'DAILY_PROMPT', 'NOTE'}
    NEED_CAPTION = {'NOW_SPINNING', 'NEW_HAUL', 'RANDOMIZER'}
    all_posts = await db.posts.find({}, {'_id': 0, 'post_type': 1, 'caption': 1, 'content': 1, 'user_id': 1}).to_list(None)
    
    feed_visible = 0
    poster_ids = set()
    for p in all_posts:
        pt = (p.get('post_type') or '').upper()
        if pt not in ALLOWED: continue
        cap = (p.get('caption') or p.get('content') or '').strip()
        if pt in NEED_CAPTION and not cap: continue
        feed_visible += 1
        poster_ids.add(p['user_id'])
    
    # Map poster IDs to usernames
    poster_names = []
    for pid in poster_ids:
        u = await db.users.find_one({'id': pid}, {'_id': 0, 'username': 1})
        if u: poster_names.append(u['username'])
    
    print(f'\n===== PRODUCTION VERIFICATION =====')
    print(f'Total posts: {total_posts}')
    print(f'Feed-visible posts: {feed_visible}')
    print(f'Unique posters: {len(poster_names)} -> {sorted(poster_names)}')
    print(f'Follows: {total_follows}')
    print(f'Likes: {total_likes}')
    print(f'Onboarded users: {await db.users.count_documents({"onboarding_completed": True})}')
    
    client.close()

asyncio.run(seed_activity())
