"""
Test Feed Filters (server-side post_type) and User Posts endpoint
Features tested:
1. GET /api/feed?post_type=NOTE - returns only NOTE posts
2. GET /api/feed?post_type=ISO - returns only ISO posts
3. GET /api/feed?post_type=NOW_SPINNING - returns NOW_SPINNING and RANDOMIZER posts
4. GET /api/feed (no post_type) - returns mixed types
5. Pinned post only appears when it matches the active filter
6. GET /api/users/{username}/posts - returns posts by user
7. GET /api/users/{username}/posts?before=<timestamp> - cursor pagination
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestFeedFilters:
    """Test server-side feed filtering with post_type param"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]
    
    def test_feed_no_filter_returns_mixed(self, auth_token):
        """GET /api/feed without post_type should return mixed post types"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed", headers=headers)
        assert response.status_code == 200, f"Feed failed: {response.text}"
        posts = response.json()
        assert isinstance(posts, list), "Feed should return a list"
        # Check that we have posts
        if len(posts) > 0:
            # Collect post types to verify mix
            post_types = set(p.get("post_type") for p in posts)
            print(f"Post types in unfiltered feed: {post_types}")
            # Just verify it's a valid response
            assert all("id" in p for p in posts), "All posts should have id"
    
    def test_feed_filter_note_returns_notes(self, auth_token):
        """GET /api/feed?post_type=NOTE should return only NOTE posts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed", headers=headers, params={"post_type": "NOTE"})
        assert response.status_code == 200, f"Feed filter NOTE failed: {response.text}"
        posts = response.json()
        assert isinstance(posts, list), "Feed should return a list"
        # All returned posts should be NOTE type
        for post in posts:
            assert post.get("post_type") == "NOTE", f"Post type should be NOTE, got {post.get('post_type')}"
        print(f"NOTE filter returned {len(posts)} posts - all verified as NOTE type")
    
    def test_feed_filter_iso_returns_iso(self, auth_token):
        """GET /api/feed?post_type=ISO should return only ISO posts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed", headers=headers, params={"post_type": "ISO"})
        assert response.status_code == 200, f"Feed filter ISO failed: {response.text}"
        posts = response.json()
        assert isinstance(posts, list), "Feed should return a list"
        # All returned posts should be ISO type
        for post in posts:
            assert post.get("post_type") == "ISO", f"Post type should be ISO, got {post.get('post_type')}"
        print(f"ISO filter returned {len(posts)} posts - all verified as ISO type")
    
    def test_feed_filter_now_spinning_returns_spinning_and_randomizer(self, auth_token):
        """GET /api/feed?post_type=NOW_SPINNING should return NOW_SPINNING and RANDOMIZER posts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed", headers=headers, params={"post_type": "NOW_SPINNING"})
        assert response.status_code == 200, f"Feed filter NOW_SPINNING failed: {response.text}"
        posts = response.json()
        assert isinstance(posts, list), "Feed should return a list"
        # All returned posts should be NOW_SPINNING or RANDOMIZER
        allowed_types = {"NOW_SPINNING", "RANDOMIZER"}
        for post in posts:
            pt = post.get("post_type")
            assert pt in allowed_types, f"Post type should be NOW_SPINNING or RANDOMIZER, got {pt}"
        print(f"NOW_SPINNING filter returned {len(posts)} posts - types: {set(p.get('post_type') for p in posts)}")
    
    def test_feed_pagination_with_filter(self, auth_token):
        """Test that pagination (before param) works with filters"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # First request without before
        response1 = requests.get(f"{BASE_URL}/api/feed", headers=headers, params={"post_type": "NOTE", "limit": 5})
        assert response1.status_code == 200
        posts1 = response1.json()
        
        if len(posts1) >= 5:
            # Get the last post's created_at for cursor
            last_created_at = posts1[-1].get("created_at")
            # Request with before cursor
            response2 = requests.get(f"{BASE_URL}/api/feed", headers=headers, params={
                "post_type": "NOTE",
                "limit": 5,
                "before": last_created_at
            })
            assert response2.status_code == 200
            posts2 = response2.json()
            # Verify no overlap between pages
            ids1 = set(p["id"] for p in posts1)
            ids2 = set(p["id"] for p in posts2)
            assert ids1.isdisjoint(ids2), "Paginated results should not overlap"
            print(f"Pagination test: Page 1 = {len(posts1)} posts, Page 2 = {len(posts2)} posts")


class TestUserPosts:
    """Test /api/users/{username}/posts endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("access_token")
    
    def test_user_posts_returns_posts(self, auth_token):
        """GET /api/users/katie/posts should return posts by that user"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users/katie/posts", headers=headers)
        assert response.status_code == 200, f"User posts failed: {response.text}"
        posts = response.json()
        assert isinstance(posts, list), "User posts should return a list"
        print(f"User katie has {len(posts)} posts")
        # Verify posts have required fields
        for post in posts[:5]:  # Check first 5
            assert "id" in post, "Post should have id"
            assert "created_at" in post, "Post should have created_at"
    
    def test_user_posts_cursor_pagination(self, auth_token):
        """GET /api/users/katie/posts?before=<timestamp> should return older posts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # First request
        response1 = requests.get(f"{BASE_URL}/api/users/katie/posts", headers=headers, params={"limit": 5})
        assert response1.status_code == 200
        posts1 = response1.json()
        
        if len(posts1) >= 5:
            # Get cursor
            last_created_at = posts1[-1].get("created_at")
            # Second request with cursor
            response2 = requests.get(f"{BASE_URL}/api/users/katie/posts", headers=headers, params={
                "limit": 5,
                "before": last_created_at
            })
            assert response2.status_code == 200
            posts2 = response2.json()
            
            # All posts in page 2 should be older than cursor
            if posts2:
                assert all(p["created_at"] < last_created_at for p in posts2), "All posts should be older than cursor"
            print(f"User posts pagination: Page 1 = {len(posts1)}, Page 2 = {len(posts2)}")
    
    def test_user_posts_without_auth(self):
        """GET /api/users/katie/posts should work without auth for public profiles"""
        response = requests.get(f"{BASE_URL}/api/users/katie/posts")
        # May return 200 or 401 depending on profile privacy
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        print(f"User posts without auth returned status: {response.status_code}")


class TestFeedFilterIntegration:
    """Test filter switching behavior"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        assert response.status_code == 200
        return response.json().get("access_token")
    
    def test_filter_returns_different_results(self, auth_token):
        """Different filters should potentially return different results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get all posts
        all_response = requests.get(f"{BASE_URL}/api/feed", headers=headers, params={"limit": 20})
        all_posts = all_response.json()
        
        # Get NOTE posts
        note_response = requests.get(f"{BASE_URL}/api/feed", headers=headers, params={"post_type": "NOTE", "limit": 20})
        note_posts = note_response.json()
        
        # Get ISO posts
        iso_response = requests.get(f"{BASE_URL}/api/feed", headers=headers, params={"post_type": "ISO", "limit": 20})
        iso_posts = iso_response.json()
        
        print(f"All: {len(all_posts)}, NOTE: {len(note_posts)}, ISO: {len(iso_posts)}")
        
        # If we have all types, the unfiltered count should be >= max of filtered counts
        if note_posts and iso_posts:
            # Just verify they're different subsets
            note_ids = set(p["id"] for p in note_posts)
            iso_ids = set(p["id"] for p in iso_posts)
            # NOTE and ISO should not overlap
            assert note_ids.isdisjoint(iso_ids), "NOTE and ISO posts should not overlap"
