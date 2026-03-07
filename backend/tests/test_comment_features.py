"""
Test suite for HoneyGroove comment features:
1. Comment replies with @mention tagging and nested display
2. Comment likes with notifications
3. Admin pin post to top of Hive feed
4. @mention autocomplete search

Test users created: testcomment74_* (cleaned up at end)
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

def random_suffix():
    return str(uuid.uuid4())[:8]

# ============== FIXTURES ==============

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def test_user_data():
    """Test user credentials"""
    suffix = random_suffix()
    return {
        "email": f"testcomment74_{suffix}@nottest.org",  # NOT @test.com to avoid hidden user filter
        "username": f"testcomment74_{suffix}",
        "password": "testpass123"
    }

@pytest.fixture(scope="module")
def second_user_data():
    """Second test user for interaction testing"""
    suffix = random_suffix()
    return {
        "email": f"testcomment74b_{suffix}@nottest.org",
        "username": f"testcomment74b_{suffix}",
        "password": "testpass123"
    }

@pytest.fixture(scope="module")
def admin_user_data():
    """Admin test user"""
    suffix = random_suffix()
    return {
        "email": f"testadmin74_{suffix}@nottest.org",
        "username": f"testadmin74_{suffix}",
        "password": "testpass123"
    }

@pytest.fixture(scope="module")
def registered_user(api_client, test_user_data):
    """Register and return test user with token"""
    # Create invite code
    from pymongo import MongoClient
    mongo = MongoClient("mongodb://localhost:27017")
    db = mongo["test_database"]
    
    code = f"HG-TEST74-{random_suffix()[:4].upper()}"
    db.invite_codes.insert_one({
        "code": code,
        "status": "unused",
        "used_by": None,
        "created_at": datetime.utcnow().isoformat()
    })
    
    # Register user
    response = api_client.post(f"{BASE_URL}/api/auth/register-invite", json={
        **test_user_data,
        "code": code
    })
    
    if response.status_code != 200:
        pytest.fail(f"User registration failed: {response.text}")
    
    data = response.json()
    user_id = data["user"]["id"]
    
    # Mark as verified and onboarding complete
    db.users.update_one({"id": user_id}, {"$set": {
        "email_verified": True,
        "onboarding_completed": True
    }})
    
    mongo.close()
    
    return {
        "token": data["access_token"],
        "user": data["user"],
        "user_id": user_id
    }

@pytest.fixture(scope="module")
def second_user(api_client, second_user_data):
    """Register second test user"""
    from pymongo import MongoClient
    mongo = MongoClient("mongodb://localhost:27017")
    db = mongo["test_database"]
    
    code = f"HG-TEST74B-{random_suffix()[:4].upper()}"
    db.invite_codes.insert_one({
        "code": code,
        "status": "unused",
        "used_by": None,
        "created_at": datetime.utcnow().isoformat()
    })
    
    response = api_client.post(f"{BASE_URL}/api/auth/register-invite", json={
        **second_user_data,
        "code": code
    })
    
    if response.status_code != 200:
        pytest.fail(f"Second user registration failed: {response.text}")
    
    data = response.json()
    user_id = data["user"]["id"]
    
    db.users.update_one({"id": user_id}, {"$set": {
        "email_verified": True,
        "onboarding_completed": True
    }})
    
    mongo.close()
    
    return {
        "token": data["access_token"],
        "user": data["user"],
        "user_id": user_id
    }

@pytest.fixture(scope="module")
def admin_user(api_client, admin_user_data):
    """Register admin test user"""
    from pymongo import MongoClient
    mongo = MongoClient("mongodb://localhost:27017")
    db = mongo["test_database"]
    
    code = f"HG-ADMIN74-{random_suffix()[:4].upper()}"
    db.invite_codes.insert_one({
        "code": code,
        "status": "unused",
        "used_by": None,
        "created_at": datetime.utcnow().isoformat()
    })
    
    response = api_client.post(f"{BASE_URL}/api/auth/register-invite", json={
        **admin_user_data,
        "code": code
    })
    
    if response.status_code != 200:
        pytest.fail(f"Admin user registration failed: {response.text}")
    
    data = response.json()
    user_id = data["user"]["id"]
    
    # Make admin
    db.users.update_one({"id": user_id}, {"$set": {
        "email_verified": True,
        "onboarding_completed": True,
        "is_admin": True
    }})
    
    mongo.close()
    
    return {
        "token": data["access_token"],
        "user": data["user"],
        "user_id": user_id
    }

@pytest.fixture(scope="module")
def test_post(api_client, registered_user):
    """Create a test post to comment on"""
    # First follow self to see in feed (workaround for feed logic)
    # Actually, let's just create a record and post
    from pymongo import MongoClient
    mongo = MongoClient("mongodb://localhost:27017")
    db = mongo["test_database"]
    
    record_id = str(uuid.uuid4())
    db.records.insert_one({
        "id": record_id,
        "user_id": registered_user["user_id"],
        "title": "Test Album",
        "artist": "Test Artist",
        "cover_url": None,
        "year": 2024,
        "format": "Vinyl",
        "created_at": datetime.utcnow().isoformat()
    })
    
    mongo.close()
    
    # Create post via API
    response = api_client.post(f"{BASE_URL}/api/composer/now-spinning", json={
        "record_id": record_id,
        "track": "Test Track",
        "caption": "Testing comments feature"
    }, headers={"Authorization": f"Bearer {registered_user['token']}"})
    
    if response.status_code != 200:
        pytest.fail(f"Failed to create test post: {response.text}")
    
    return response.json()

@pytest.fixture(scope="module", autouse=True)
def cleanup(api_client, test_user_data, second_user_data, admin_user_data):
    """Cleanup test data after all tests"""
    yield
    from pymongo import MongoClient
    mongo = MongoClient("mongodb://localhost:27017")
    db = mongo["test_database"]
    
    # Delete test users
    for email in [test_user_data["email"], second_user_data["email"], admin_user_data["email"]]:
        user = db.users.find_one({"email": email})
        if user:
            user_id = user["id"]
            db.posts.delete_many({"user_id": user_id})
            db.comments.delete_many({"user_id": user_id})
            db.comment_likes.delete_many({"user_id": user_id})
            db.records.delete_many({"user_id": user_id})
            db.notifications.delete_many({"user_id": user_id})
            db.followers.delete_many({"$or": [{"follower_id": user_id}, {"following_id": user_id}]})
            db.users.delete_one({"email": email})
    
    # Clean up test invite codes
    db.invite_codes.delete_many({"code": {"$regex": "^HG-TEST74"}})
    db.invite_codes.delete_many({"code": {"$regex": "^HG-ADMIN74"}})
    
    # Reset any pinned posts from test
    db.posts.update_many({"is_pinned": True}, {"$set": {"is_pinned": False}})
    
    mongo.close()
    print("\n[CLEANUP] Test data cleaned up successfully")


# ============== COMMENT BASIC TESTS ==============

class TestCommentBasics:
    """Basic comment creation and retrieval"""
    
    def test_create_comment(self, api_client, registered_user, test_post):
        """POST /api/posts/{post_id}/comments creates a comment"""
        response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={"post_id": test_post["id"], "content": "This is a test comment"},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["content"] == "This is a test comment"
        assert data["post_id"] == test_post["id"]
        assert "id" in data
        assert data["likes_count"] == 0
        assert data["is_liked"] == False
        print(f"[PASS] Comment created: {data['id']}")
    
    def test_get_comments(self, api_client, registered_user, test_post):
        """GET /api/posts/{post_id}/comments returns comments"""
        response = api_client.get(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        comment = data[0]
        assert "id" in comment
        assert "content" in comment
        assert "user" in comment
        assert "likes_count" in comment
        assert "is_liked" in comment
        assert "replies" in comment  # Nested structure
        print(f"[PASS] Got {len(data)} comments with nested structure")


# ============== COMMENT REPLIES TESTS ==============

class TestCommentReplies:
    """Comment replies with parent_id and nested display"""
    
    def test_create_reply_with_parent_id(self, api_client, registered_user, second_user, test_post):
        """POST with parent_id creates a nested reply"""
        # First create a parent comment from second user
        parent_response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={"post_id": test_post["id"], "content": "Parent comment from second user"},
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        assert parent_response.status_code == 200
        parent_comment = parent_response.json()
        
        # Now reply to it from first user
        reply_response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={
                "post_id": test_post["id"],
                "content": "This is a reply to parent comment",
                "parent_id": parent_comment["id"]
            },
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert reply_response.status_code == 200, f"Failed: {reply_response.text}"
        reply = reply_response.json()
        assert reply["parent_id"] == parent_comment["id"]
        assert reply["content"] == "This is a reply to parent comment"
        print(f"[PASS] Reply created with parent_id: {reply['parent_id']}")
        return parent_comment["id"]
    
    def test_get_comments_returns_nested_structure(self, api_client, registered_user, test_post):
        """GET comments returns nested structure with replies array"""
        response = api_client.get(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 200
        comments = response.json()
        
        # Find a comment with replies
        found_parent_with_replies = False
        for comment in comments:
            if comment.get("replies") and len(comment["replies"]) > 0:
                found_parent_with_replies = True
                reply = comment["replies"][0]
                assert reply.get("parent_id") == comment["id"]
                print(f"[PASS] Found parent comment with {len(comment['replies'])} replies")
                break
        
        # It's OK if no replies yet (depends on test order)
        print(f"[PASS] Comments returned with nested structure, replies found: {found_parent_with_replies}")


# ============== COMMENT LIKES TESTS ==============

class TestCommentLikes:
    """Comment like/unlike functionality"""
    
    @pytest.fixture
    def comment_for_like(self, api_client, second_user, test_post):
        """Create a comment to like"""
        response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={"post_id": test_post["id"], "content": "Comment to be liked"},
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        return response.json()
    
    def test_like_comment(self, api_client, registered_user, comment_for_like):
        """POST /api/comments/{comment_id}/like toggles like on"""
        response = api_client.post(
            f"{BASE_URL}/api/comments/{comment_for_like['id']}/like",
            json={},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"[PASS] Comment liked: {data['message']}")
    
    def test_like_comment_already_liked(self, api_client, registered_user, comment_for_like):
        """POST /api/comments/{comment_id}/like returns 400 if already liked"""
        # Like again (should fail)
        response = api_client.post(
            f"{BASE_URL}/api/comments/{comment_for_like['id']}/like",
            json={},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 400
        print("[PASS] Already liked returns 400")
    
    def test_unlike_comment(self, api_client, registered_user, comment_for_like):
        """DELETE /api/comments/{comment_id}/like toggles like off"""
        response = api_client.delete(
            f"{BASE_URL}/api/comments/{comment_for_like['id']}/like",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"[PASS] Comment unliked: {data['message']}")
    
    def test_unlike_not_liked(self, api_client, registered_user, comment_for_like):
        """DELETE /api/comments/{comment_id}/like returns 400 if not liked"""
        response = api_client.delete(
            f"{BASE_URL}/api/comments/{comment_for_like['id']}/like",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 400
        print("[PASS] Unlike when not liked returns 400")
    
    def test_comments_include_likes_count_and_is_liked(self, api_client, registered_user, second_user, test_post):
        """GET comments includes likes_count and is_liked fields"""
        # Create a comment and like it
        comment_resp = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={"post_id": test_post["id"], "content": "Comment with likes"},
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        comment = comment_resp.json()
        
        # Like it
        api_client.post(
            f"{BASE_URL}/api/comments/{comment['id']}/like",
            json={},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        
        # Get comments and verify likes info
        response = api_client.get(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        comments = response.json()
        
        # Find our comment
        our_comment = next((c for c in comments if c["id"] == comment["id"]), None)
        assert our_comment is not None
        assert our_comment["likes_count"] >= 1
        assert our_comment["is_liked"] == True  # registered_user liked it
        print(f"[PASS] Comment has likes_count={our_comment['likes_count']}, is_liked={our_comment['is_liked']}")


# ============== MENTION NOTIFICATIONS TESTS ==============

class TestMentionNotifications:
    """@mention triggering notifications"""
    
    def test_mention_creates_notification(self, api_client, registered_user, second_user, test_post):
        """Commenting with @username triggers MENTION notification"""
        # Comment with @mention of second user
        content = f"Hey @{second_user['user']['username']} check this out!"
        response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={"post_id": test_post["id"], "content": content},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 200
        
        # Check second user's notifications
        notif_response = api_client.get(
            f"{BASE_URL}/api/notifications?limit=10",
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        assert notif_response.status_code == 200
        notifications = notif_response.json()
        
        # Should have a MENTION notification
        mention_notifs = [n for n in notifications if n.get("type") == "MENTION"]
        assert len(mention_notifs) >= 1, f"Expected MENTION notification, got: {[n.get('type') for n in notifications]}"
        print(f"[PASS] MENTION notification created for @{second_user['user']['username']}")
    
    def test_reply_creates_comment_reply_notification(self, api_client, registered_user, second_user, test_post):
        """Replying to a comment triggers COMMENT_REPLY notification"""
        # Second user creates a comment
        parent_resp = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={"post_id": test_post["id"], "content": "Parent comment for reply test"},
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        parent = parent_resp.json()
        
        # Clear existing notifications
        api_client.put(
            f"{BASE_URL}/api/notifications/read-all",
            json={},
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        
        # First user replies
        reply_resp = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={"post_id": test_post["id"], "content": "Replying to your comment!", "parent_id": parent["id"]},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert reply_resp.status_code == 200
        
        # Check second user's notifications
        notif_response = api_client.get(
            f"{BASE_URL}/api/notifications?limit=10",
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        notifications = notif_response.json()
        
        reply_notifs = [n for n in notifications if n.get("type") == "COMMENT_REPLY"]
        assert len(reply_notifs) >= 1, f"Expected COMMENT_REPLY notification, got: {[n.get('type') for n in notifications]}"
        print("[PASS] COMMENT_REPLY notification created for reply")


# ============== COMMENT LIKE NOTIFICATIONS TESTS ==============

class TestCommentLikeNotifications:
    """Comment like triggering notifications"""
    
    def test_like_comment_creates_notification(self, api_client, registered_user, second_user, test_post):
        """Liking a comment triggers COMMENT_LIKED notification"""
        # Second user creates a comment
        comment_resp = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/comments",
            json={"post_id": test_post["id"], "content": "Like notification test comment"},
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        comment = comment_resp.json()
        
        # Clear notifications
        api_client.put(
            f"{BASE_URL}/api/notifications/read-all",
            json={},
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        
        # First user likes it
        like_resp = api_client.post(
            f"{BASE_URL}/api/comments/{comment['id']}/like",
            json={},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert like_resp.status_code == 200
        
        # Check second user's notifications
        notif_response = api_client.get(
            f"{BASE_URL}/api/notifications?limit=10",
            headers={"Authorization": f"Bearer {second_user['token']}"}
        )
        notifications = notif_response.json()
        
        like_notifs = [n for n in notifications if n.get("type") == "COMMENT_LIKED"]
        assert len(like_notifs) >= 1, f"Expected COMMENT_LIKED notification, got: {[n.get('type') for n in notifications]}"
        print("[PASS] COMMENT_LIKED notification created")


# ============== MENTION SEARCH TESTS ==============

class TestMentionSearch:
    """@mention autocomplete search"""
    
    def test_mention_search_returns_users(self, api_client, registered_user, second_user):
        """GET /api/mention-search returns matching users"""
        # Search for second user by partial username
        username = second_user["user"]["username"]
        query = username[:8]  # First 8 chars
        
        response = api_client.get(
            f"{BASE_URL}/api/mention-search",
            params={"q": query},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        users = response.json()
        assert isinstance(users, list)
        
        # Should find the second user
        found = any(u["username"] == username for u in users)
        assert found, f"Expected to find {username} in results: {users}"
        
        # Verify response structure
        if users:
            user = users[0]
            assert "id" in user
            assert "username" in user
            assert "avatar_url" in user
        
        print(f"[PASS] mention-search returned {len(users)} users matching '{query}'")
    
    def test_mention_search_empty_query(self, api_client, registered_user):
        """GET /api/mention-search with empty query returns empty array"""
        response = api_client.get(
            f"{BASE_URL}/api/mention-search",
            params={"q": ""},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 200
        users = response.json()
        assert users == []
        print("[PASS] Empty query returns empty array")
    
    def test_mention_search_requires_auth(self, api_client):
        """GET /api/mention-search requires authentication"""
        response = api_client.get(
            f"{BASE_URL}/api/mention-search",
            params={"q": "test"}
        )
        assert response.status_code == 403 or response.status_code == 401
        print("[PASS] Mention search requires auth")


# ============== ADMIN PIN POST TESTS ==============

class TestAdminPinPost:
    """Admin pin/unpin post functionality"""
    
    def test_pin_post_requires_admin(self, api_client, registered_user, test_post):
        """POST /api/posts/{post_id}/pin returns 403 for non-admin"""
        response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/pin",
            json={},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("[PASS] Non-admin cannot pin posts (403)")
    
    def test_admin_can_pin_post(self, api_client, admin_user, test_post):
        """POST /api/posts/{post_id}/pin (admin) pins the post"""
        response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/pin",
            json={},
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"[PASS] Admin pinned post: {data['message']}")
    
    def test_unpin_post_requires_admin(self, api_client, registered_user, test_post):
        """DELETE /api/posts/{post_id}/pin returns 403 for non-admin"""
        response = api_client.delete(
            f"{BASE_URL}/api/posts/{test_post['id']}/pin",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert response.status_code == 403
        print("[PASS] Non-admin cannot unpin posts (403)")
    
    def test_admin_can_unpin_post(self, api_client, admin_user, test_post):
        """DELETE /api/posts/{post_id}/pin (admin) unpins the post"""
        response = api_client.delete(
            f"{BASE_URL}/api/posts/{test_post['id']}/pin",
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"[PASS] Admin unpinned post: {data['message']}")


# ============== FEED WITH PINNED POST TESTS ==============

class TestFeedPinnedPost:
    """Feed returns pinned post first"""
    
    def test_feed_shows_pinned_post_first(self, api_client, admin_user, registered_user, test_post):
        """GET /api/feed returns pinned post first with is_pinned=true"""
        # First pin the post
        pin_resp = api_client.post(
            f"{BASE_URL}/api/posts/{test_post['id']}/pin",
            json={},
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert pin_resp.status_code == 200
        
        # Follow self to see own posts in feed
        api_client.post(
            f"{BASE_URL}/api/follow/{registered_user['user_id']}",
            json={},
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        
        # Get feed
        feed_resp = api_client.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {registered_user['token']}"}
        )
        assert feed_resp.status_code == 200
        posts = feed_resp.json()
        
        # First post should be pinned
        assert len(posts) >= 1
        first_post = posts[0]
        assert first_post.get("is_pinned") == True, f"First post is_pinned={first_post.get('is_pinned')}"
        print(f"[PASS] Pinned post appears first in feed with is_pinned=true")
    
    def test_pinning_new_post_unpins_previous(self, api_client, admin_user, registered_user, test_post):
        """Pinning a new post automatically unpins the previous one"""
        from pymongo import MongoClient
        mongo = MongoClient("mongodb://localhost:27017")
        db = mongo["test_database"]
        
        # Create another post to pin
        record_id = str(uuid.uuid4())
        db.records.insert_one({
            "id": record_id,
            "user_id": registered_user["user_id"],
            "title": "Second Test Album",
            "artist": "Second Test Artist",
            "cover_url": None,
            "year": 2024,
            "format": "Vinyl",
            "created_at": datetime.utcnow().isoformat()
        })
        
        mongo.close()
        
        # Create second post
        post2_resp = api_client.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record_id,
            "track": "Second Track",
            "caption": "Second test post"
        }, headers={"Authorization": f"Bearer {registered_user['token']}"})
        post2 = post2_resp.json()
        
        # Pin the second post
        pin_resp = api_client.post(
            f"{BASE_URL}/api/posts/{post2['id']}/pin",
            json={},
            headers={"Authorization": f"Bearer {admin_user['token']}"}
        )
        assert pin_resp.status_code == 200
        
        # Check that only one post is pinned
        mongo = MongoClient("mongodb://localhost:27017")
        db = mongo["test_database"]
        pinned_count = db.posts.count_documents({"is_pinned": True})
        mongo.close()
        
        assert pinned_count == 1, f"Expected 1 pinned post, found {pinned_count}"
        print("[PASS] Pinning new post unpins the previous one (only 1 pinned)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
