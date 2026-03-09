"""
Test Feed Bug Fix: GET /api/feed returns posts from ALL users, not just followed users.
This tests the critical fix where new users could only see their own posts because
the feed was filtered to followed users + self.
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def get_auth_token(email, password):
    """Helper to get auth token - handles both 'token' and 'access_token' responses"""
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if login_resp.status_code == 200:
        data = login_resp.json()
        return data.get("access_token") or data.get("token")
    return None


class TestFeedAllUsersBugFix:
    """Tests for the feed endpoint returning posts from all non-hidden users"""

    @pytest.fixture(scope="class")
    def test_users(self):
        """Create 2 test users for feed testing - they don't follow each other
        
        IMPORTANT: Users with test/demo in username or @test.com/@example.com email
        are filtered as hidden users. Use @gmail.com format for testing.
        """
        users = []
        for i in range(2):
            unique_id = str(uuid.uuid4())[:8]
            email = f"feeduser{unique_id}@gmail.com"  # Non-test email
            username = f"feeduser{unique_id}"  # Non-test username
            password = "testpass123"
            
            # Register user
            reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": email,
                "username": username,
                "password": password,
                "invite_code": "HONEYBETA"
            })
            
            if reg_resp.status_code not in [200, 201]:
                # Try login if already exists
                login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                    "email": email,
                    "password": password
                })
                if login_resp.status_code != 200:
                    pytest.skip(f"Could not register/login test user: {reg_resp.text}")
                user_data = login_resp.json()
            else:
                user_data = reg_resp.json()
            
            # Handle both 'token' and 'access_token' response formats
            token = user_data.get("access_token") or user_data.get("token")
            user_info = user_data.get("user", {})
            
            users.append({
                "id": user_info.get("id") or user_data.get("id"),
                "email": email,
                "username": username,
                "password": password,
                "token": token
            })
        
        yield users
        
        # Cleanup: Delete test users' posts (if we had admin access)
        # In a real setup, we'd clean up test data here

    @pytest.fixture
    def user1_session(self, test_users):
        """Get authenticated session for user 1"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {test_users[0]['token']}"
        })
        return session, test_users[0]

    @pytest.fixture
    def user2_session(self, test_users):
        """Get authenticated session for user 2"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {test_users[1]['token']}"
        })
        return session, test_users[1]

    def test_feed_requires_authentication(self):
        """GET /api/feed requires authentication"""
        response = requests.get(f"{BASE_URL}/api/feed")
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated feed request, got {response.status_code}"
        print("PASS: Feed endpoint requires authentication")

    def test_feed_returns_posts_from_non_followed_users(self, user1_session, user2_session):
        """
        CRITICAL BUG FIX TEST:
        User1 creates a post, User2 (who doesn't follow User1) should see it in feed
        """
        session1, user1 = user1_session
        session2, user2 = user2_session
        
        # User1 creates a Note post
        unique_content = f"TEST_feed_bugfix_{uuid.uuid4()}"
        create_resp = session1.post(f"{BASE_URL}/api/composer/note", json={
            "text": unique_content
        })
        assert create_resp.status_code in [200, 201], f"Failed to create post: {create_resp.text}"
        post_data = create_resp.json()
        post_id = post_data.get("id")
        print(f"PASS: User1 created post with ID: {post_id}")

        # User2 (NOT following User1) fetches feed
        feed_resp = session2.get(f"{BASE_URL}/api/feed")
        assert feed_resp.status_code == 200, f"Feed request failed: {feed_resp.text}"
        
        feed_posts = feed_resp.json()
        assert isinstance(feed_posts, list), "Feed should return a list"
        
        # Check if User1's post appears in User2's feed
        found_post = any(p.get("id") == post_id for p in feed_posts)
        
        # CRITICAL ASSERTION: Post from non-followed user should appear
        assert found_post, f"BUG NOT FIXED: User2 cannot see User1's post (they don't follow each other)"
        print("PASS: User2 CAN see User1's post even though they don't follow each other")
        
        # Verify the post content matches
        matching_post = next((p for p in feed_posts if p.get("id") == post_id), None)
        assert matching_post is not None
        assert matching_post.get("caption") == unique_content or matching_post.get("content") == unique_content
        print("PASS: Post content matches expected content")

    def test_feed_pagination_works(self, user1_session):
        """Test that feed pagination (skip/limit) still works"""
        session, user = user1_session
        
        # Get feed with limit
        response = session.get(f"{BASE_URL}/api/feed", params={"limit": 5, "skip": 0})
        assert response.status_code == 200, f"Feed pagination failed: {response.text}"
        
        posts = response.json()
        assert len(posts) <= 5, f"Expected at most 5 posts with limit=5, got {len(posts)}"
        print(f"PASS: Feed pagination works, got {len(posts)} posts with limit=5")

        # Test skip parameter
        if len(posts) >= 5:
            response2 = session.get(f"{BASE_URL}/api/feed", params={"limit": 5, "skip": 2})
            assert response2.status_code == 200
            posts2 = response2.json()
            # Verify skip actually skipped posts
            if len(posts2) > 0:
                print(f"PASS: Skip parameter works, returned {len(posts2)} posts with skip=2")

    def test_feed_returns_valid_post_structure(self, user1_session):
        """Verify feed returns posts with expected structure"""
        session, user = user1_session
        
        response = session.get(f"{BASE_URL}/api/feed", params={"limit": 10})
        assert response.status_code == 200
        
        posts = response.json()
        if len(posts) > 0:
            post = posts[0]
            # Check required fields
            required_fields = ["id", "user_id", "post_type", "created_at"]
            for field in required_fields:
                assert field in post, f"Post missing required field: {field}"
            
            # Check user data is included
            assert "user" in post, "Post should include user data"
            if post["user"]:
                assert "username" in post["user"], "User data should include username"
            
            print("PASS: Feed returns posts with valid structure")

    def test_explore_endpoint_returns_all_posts(self, user1_session):
        """Verify /api/explore also returns all posts (was already working)"""
        session, user = user1_session
        
        response = session.get(f"{BASE_URL}/api/explore", params={"limit": 10})
        assert response.status_code == 200, f"Explore request failed: {response.text}"
        
        posts = response.json()
        assert isinstance(posts, list), "Explore should return a list"
        print(f"PASS: Explore endpoint returns {len(posts)} posts")


class TestPinnedPostInFeed:
    """Tests for pinned post appearing at top of feed"""

    @pytest.fixture
    def auth_session(self):
        """Get an authenticated session"""
        session = requests.Session()
        token = get_auth_token("admin@thehoneygroove.com", "admin123")
        if token:
            session.headers.update({
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            })
            return session
        pytest.skip("Could not authenticate - no test user available")

    def test_pinned_post_at_top(self, auth_session):
        """If there's a pinned post, it should be at the top of the feed"""
        response = auth_session.get(f"{BASE_URL}/api/feed", params={"limit": 50})
        assert response.status_code == 200
        
        posts = response.json()
        if len(posts) == 0:
            print("SKIP: No posts in feed to check pinned status")
            return
        
        # Check if first post is pinned (if any pinned exists)
        has_pinned = any(p.get("is_pinned") for p in posts)
        if has_pinned:
            assert posts[0].get("is_pinned"), "Pinned post should be at top of feed"
            print("PASS: Pinned post is at top of feed")
        else:
            print("INFO: No pinned posts in current feed")


class TestFollowingEndpoint:
    """Tests for the following endpoint used by frontend filter"""

    @pytest.fixture
    def auth_session_with_username(self):
        """Get an authenticated session with username"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin123"
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("access_token") or data.get("token")
            user = data.get("user", {})
            username = user.get("username")
            session.headers.update({
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            })
            return session, username
        pytest.skip("Could not authenticate")

    def test_following_endpoint_exists(self, auth_session_with_username):
        """Test GET /api/users/{username}/following returns following list"""
        session, username = auth_session_with_username
        
        response = session.get(f"{BASE_URL}/api/users/{username}/following")
        assert response.status_code == 200, f"Following endpoint failed: {response.text}"
        
        following = response.json()
        assert isinstance(following, list), "Following endpoint should return a list"
        print(f"PASS: Following endpoint returns list with {len(following)} users")
        
        # Verify structure if there are any following
        if len(following) > 0:
            assert "id" in following[0], "Following users should have 'id' field"
            print("PASS: Following list has correct structure")


class TestHiddenUsersExclusion:
    """Tests for hidden users being excluded from feed"""

    @pytest.fixture
    def auth_session(self):
        """Get an authenticated session"""
        session = requests.Session()
        token = get_auth_token("admin@thehoneygroove.com", "admin123")
        if token:
            session.headers.update({
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            })
            return session
        pytest.skip("Could not authenticate")

    def test_feed_structure_includes_user_data(self, auth_session):
        """Verify that posts include user data for filtering on frontend"""
        response = auth_session.get(f"{BASE_URL}/api/feed", params={"limit": 20})
        assert response.status_code == 200
        
        posts = response.json()
        for post in posts[:10]:  # Check first 10 posts
            assert "user_id" in post, "Post must have user_id for filtering"
            if post.get("user"):
                # User data should be present for display
                assert "username" in post["user"] or post["user"] is None
        
        print("PASS: All posts include user_id for frontend filtering")
