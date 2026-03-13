"""Import recovered signups into Atlas: users, beta_signups, newsletter_subscribers."""
import asyncio
import uuid
import bcrypt
import csv
import io
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

ATLAS_URI = "os.environ.get("MONGO_URL")"

CSV_DATA = """First Name,Email,Role
Contact,contact@kathrynklodnicki.com,Member
Kmklodnicki,kmklodnicki@gmail.com,Admin
Kathryn,kathryn.klodnicki@gmail.com,Member
Contact,contact@katieintheafterglow.com,Member
Danabrigoli,danabrigoli@ymail.com,Member
Swiftlylyrical,swiftlylyrical@gmail.com,Member
Michellereadsandspins,michellereadsandspins@gmail.com,Member
Kellanharringtonpham,kellanharringtonpham@gmail.com,Member
Craftingnatory123,craftingnatory123@gmail.com,Member
Megpug10,megpug10@gmail.com,Member
Cynjean1119,cynjean1119@yahoo.com,Member
Hayleyav1,hayleyav1@gmail.com,Member
Stramonte21,stramonte21@icloud.com,Member
Speba507,speba507@student.otago.ac.nz,Member
Jacksongamer990,jacksongamer990@gmail.com,Member
Angelinasmyntyna,angelinasmyntyna@gmail.com,Member
Daria,daria_bensinger@aol.com,Member
Sutterfield,sutterfield.allison@yahoo.com,Member
M,m.m.mendoz@gmail.com,Member
Torturedmomschairman,torturedmomschairman@gmail.com,Member
Clsnyder1997,clsnyder1997@gmail.com,Member
Vinylbymarcus,vinylbymarcus@gmail.com,Member
Grace,grace.shalee@gmail.com,Member
Wlkelly09,wlkelly09@icloud.com,Member
Jordansilvers671,jordansilvers671@gmail.com,Member
Gerardops2001,gerardops2001@gmail.com,Member
Contact,contact.ashsvinyl@gmail.com,Member
Kaleb,kaleb.mayfield@icloud.com,Member
Karmadone2016,karmadone2016@yahoo.com,Member
Andrewhart0218,andrewhart0218@gmail.com,Member
Usahoyt,usahoyt@aol.com,Member
Yguindin,yguindin@hotmail.com,Member
Testregister,testregister@gmail.com,Member
Regtest2,regtest2@gmail.com,Member
Gaperez63,gaperez63@gmail.com,Member
Ellaspinsvinyl,ellaspinsvinyl@gmail.com,Member
S,s.nash2965@yahoo.com,Member
Test,test_verify_flow@example.com,Member
Test,test_1772858402@testuser.com,Member
Test,test_prod_1772858473@testflow.com,Member
Test,test_prod_1772858666@testflow.com,Member
Konikolaou,konikolaou@outlook.com,Member
Gfwaters1602,gfwaters1602@gmail.com,Member
Tornadosplash44,tornadosplash44@gmail.com,Member
Hello,hello@thehoneygroove.com,Member
Gabbydoesreading,gabbydoesreading@gmail.com,Member
M,m.p.m.debruijn@outlook.com,Member
Invitetest,invitetest@testflow.com,Member
Test,test_invite_199c43@test.com,Member
Kellansvinyl,kellansvinyl@gmail.com,Member
Albumtest,albumtest@test.com,Member
Navtest,navtest@test.com,Member
Feat1,feat1@test.com,Member
Jlpennington2014,jlpennington2014@gmail.com,Member
Testcomment74,testcomment74_2f36398c@nottest.org,Member
Testadmin74,testadmin74_83ef3ce4@nottest.org,Member
Curltest74,curltest74_fe6dd8a0@nottest.org,Member
Testcomment74,testcomment74_0807e31b@nottest.org,Member
Test,test_us_seller_1772916796@honey.io,Member
Gb,gb_buyer_test@honey.io,Member
Noverify,noverify@honey.io,Member
Noverify2,noverify2@honey.io,Member
Simplyluketv,simplyluketv@gmail.com,Member
Hollandgrace456,hollandgrace456@gmail.com,Member
Follow1,follow1@honey.io,Member
Natalivinyl,natalivinyl@gmail.com,Member
Kimklodnicki,kimklodnicki@yahoo.com,Member
Swiftlylyric,swiftlylyric@gmail.com,Member
Britsnail27,britsnail27@gmail.com,Member
Jaycemason11,jaycemason11@gmail.com,Member
Evanwhnenquiries,evanwhnenquiries@gmail.com,Member
Blakenjensen07,blakenjensen07@gmail.com,Member
Kalie,kalie.kaufman@gmail.com,Member
Reema,reema.malkani@gmail.com,Member
Greg,greg.pybus@icloud.com,Member
Tucker,tucker.parks190@gmail.com,Member
Lock,lock.helenea@gmail.com,Member
Messerly,messerly_tris@icloud.com,Member
Cameron,cameron.fintan.reid@gmail.com,Member
Emilymclean766,emilymclean766@yahoo.com,Member
Ward281,ward281@ymail.com,Member
Kerrilgreene,kerrilgreene@gmail.com,Member
Macdagienski,macdagienski@gmail.com,Member
Cd1102,cd1102@hotmail.com,Member
Beautybylandsel,beautybylandsel@gmail.com,Member
Kayelizabeth1024,kayelizabeth1024@gmail.com,Member
Alissa200,alissa200@gmail.com,Member
Kevincatchall,kevincatchall@icloud.com,Member
Angeldimick3,angeldimick3@gmail.com,Member
Patrick,patrick.seijo@gmail.com,Member
Travis13bell,travis13bell@gmail.com,Member
Jschildknecht,jschildknecht@gmail.com,Member
Spang714,spang714@gmail.com,Member
Maizygrace56,maizygrace56@gmail.com,Member
Aarnett365,aarnett365@gmail.com,Member
Katie,katie@thehoneygroove.com,Admin
Caroline,caroline.dissing@hotmail.con,Member
Kylie,kylie.quinonez@gmail.com,Member
Sophiewatson2019,sophiewatson2019@icloud.com,Member
Marcusbyork,marcusbyork@gmail.com,Member
Jenziboi,jenziboi@gmail.com,Member
Ronjafan123,ronjafan123@gmail.com,Member
Appleconner,appleconner@me.com,Member
Kylievonkittie,kylievonkittie@gmail.com,Member
Queennickib1tch,queennickib1tch@gmail.com,Member
Coleevan04,coleevan04@gmail.com,Member
Misurecmatej,misurecmatej@protonmail.com,Member
Kbstella99,kbstella99@gmail.com,Member
Mctyler521,mctyler521@gmail.com,Member
Haleychilders2,haleychilders2@gmail.com,Member
Mackenziedoehr63,mackenziedoehr63@gmail.com,Member
Hannah,hannah.griffis77@gmail.com,Member
Noidc537,noidc537@gmail.com,Member
Vinylcharms,vinylcharms@gmail.com,Member
Clementebrito355,clementebrito355@gmail.com,Member"""

ADMIN_EMAILS = {"kmklodnicki@gmail.com", "katie@thehoneygroove.com"}

async def run():
    client = AsyncIOMotorClient(ATLAS_URI)
    db = client["the_honey_groove"]
    now = datetime.now(timezone.utc).isoformat()

    reader = csv.DictReader(io.StringIO(CSV_DATA))
    rows = list(reader)
    print(f"CSV rows: {len(rows)}")

    users_created = 0
    users_existed = 0
    beta_upserted = 0
    newsletter_upserted = 0

    for row in rows:
        first_name = row["First Name"].strip()
        email = row["Email"].strip().lower()
        is_admin = email in ADMIN_EMAILS

        # 1. Upsert beta_signups
        result = await db.beta_signups.update_one(
            {"email": email},
            {"$setOnInsert": {"email": email, "name": first_name, "submitted_at": now, "source": "resend_recovery"}},
            upsert=True,
        )
        if result.upserted_id:
            beta_upserted += 1

        # 2. Upsert newsletter_subscribers
        result = await db.newsletter_subscribers.update_one(
            {"email": email},
            {"$setOnInsert": {"email": email, "subscribed_at": now, "source": "resend_recovery"}},
            upsert=True,
        )
        if result.upserted_id:
            newsletter_upserted += 1

        # 3. Upsert users (skip if already exists)
        existing = await db.users.find_one({"email": email})
        if existing:
            # Just ensure admin flag is correct
            if is_admin and not existing.get("is_admin"):
                await db.users.update_one({"email": email}, {"$set": {"is_admin": True}})
            users_existed += 1
            continue

        # Generate a random password hash (forces password reset flow)
        random_hash = bcrypt.hashpw(uuid.uuid4().hex.encode(), bcrypt.gensalt()).decode()
        username = email.split("@")[0].replace(".", "").replace("_", "").replace("-", "").lower()

        # Ensure username uniqueness
        if await db.users.find_one({"username": username}):
            username = f"{username}{uuid.uuid4().hex[:4]}"

        user_doc = {
            "id": str(uuid.uuid4()),
            "email": email,
            "username": username,
            "firstName": first_name,
            "password_hash": random_hash,
            "avatar_url": f"https://api.dicebear.com/7.x/miniavs/svg?seed={username}",
            "bio": None,
            "setup": None,
            "location": None,
            "favorite_genre": None,
            "onboarding_completed": False,
            "founding_member": True,
            "email_verified": True,
            "is_admin": is_admin,
            "status": "active",
            "created_at": now,
            "source": "resend_recovery",
        }
        await db.users.insert_one(user_doc)
        users_created += 1

    # Final counts
    total_users = await db.users.count_documents({})
    total_beta = await db.beta_signups.count_documents({})
    total_newsletter = await db.newsletter_subscribers.count_documents({})

    print(f"\n{'='*50}")
    print(f"IMPORT COMPLETE")
    print(f"  Users created:  {users_created}")
    print(f"  Users existed:  {users_existed}")
    print(f"  Beta upserted:  {beta_upserted}")
    print(f"  Newsletter upserted: {newsletter_upserted}")
    print(f"{'='*50}")
    print(f"ATLAS TOTALS:")
    print(f"  users:                  {total_users}")
    print(f"  beta_signups:           {total_beta}")
    print(f"  newsletter_subscribers: {total_newsletter}")
    print(f"{'='*50}")

asyncio.run(run())
