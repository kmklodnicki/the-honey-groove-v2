"""
Test file for Block 184 - Feed Pagination with cursor-based 'before' parameter
Tests GET /api/feed endpoint with cursor-based pagination
"""
import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestFeedPagination:
    """Tests for GET /api/feed endpoint with cursor-based pagination"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@honeygroove.com",
            "password": "test123"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed - skipping tests")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_feed_returns_posts(self, auth_headers):
        """Test that GET /api/feed returns posts with correct structure"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=20", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        
        # Check post structure if any posts exist
        if len(data) > 0:
            post = data[0]
            assert "id" in post, "Post should have id"
            assert "post_type" in post, "Post should have post_type"
            assert "created_at" in post, "Post should have created_at"
            print(f"SUCCESS: Feed returned {len(data)} posts")
    
    def test_feed_respects_limit(self, auth_headers):
        """Test that limit parameter is respected"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=1", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1, f"Expected max 1 post, got {len(data)}"
        print(f"SUCCESS: Limit parameter works - returned {len(data)} posts")
    
    def test_feed_cursor_pagination_with_before(self, auth_headers):
        """Test cursor-based pagination using 'before' timestamp parameter"""
        # First, get initial posts
        initial_response = requests.get(f"{BASE_URL}/api/feed?limit=10", headers=auth_headers)
        assert initial_response.status_code == 200
        initial_posts = initial_response.json()
        
        if len(initial_posts) < 1:
            pytest.skip("Not enough posts to test pagination")
        
        # Get the timestamp of the first post (most recent)
        first_post_timestamp = initial_posts[0]["created_at"]
        
        # Request posts BEFORE this timestamp (should not include this post)
        paginated_response = requests.get(
            f"{BASE_URL}/api/feed?limit=10&before={first_post_timestamp}",
            headers=auth_headers
        )
        
        assert paginated_response.status_code == 200
        paginated_posts = paginated_response.json()
        
        # Verify that posts returned are older than the cursor timestamp
        for post in paginated_posts:
            assert post["created_at"] < first_post_timestamp, \
                f"Post {post['id']} has timestamp {post['created_at']} which is not before {first_post_timestamp}"
        
        print(f"SUCCESS: Cursor pagination works - {len(paginated_posts)} older posts returned")
    
    def test_feed_allowed_post_types_only(self, auth_headers):
        """Test that feed only returns allowed post types"""
        ALLOWED_TYPES = {"NOW_SPINNING", "NEW_HAUL", "ISO", "RANDOMIZER", "DAILY_PROMPT", "NOTE"}
        
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=auth_headers)
        assert response.status_code == 200
        posts = response.json()
        
        for post in posts:
            post_type = post.get("post_type", "")
            assert post_type in ALLOWED_TYPES, \
                f"Post type '{post_type}' should be in allowed types: {ALLOWED_TYPES}"
        
        print(f"SUCCESS: All {len(posts)} posts have allowed types")
    
    def test_feed_has_required_fields_for_frontend(self, auth_headers):
        """Test that feed posts have fields needed for frontend pagination"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=20", headers=auth_headers)
        assert response.status_code == 200
        posts = response.json()
        
        if len(posts) == 0:
            pytest.skip("No posts available to test fields")
        
        # These fields are critical for frontend pagination logic
        required_fields = ["id", "post_type", "created_at", "user"]
        
        for post in posts:
            for field in required_fields:
                assert field in post, f"Post missing required field: {field}"
        
        print(f"SUCCESS: All posts have required fields for frontend")
    
    def test_before_parameter_empty_result_when_no_older_posts(self, auth_headers):
        """Test that using a very old timestamp returns empty result"""
        # Use an ancient timestamp
        ancient_timestamp = "2000-01-01T00:00:00+00:00"
        
        response = requests.get(
            f"{BASE_URL}/api/feed?limit=10&before={ancient_timestamp}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        posts = response.json()
        assert len(posts) == 0, f"Expected 0 posts before ancient timestamp, got {len(posts)}"
        
        print("SUCCESS: No posts returned for ancient timestamp (expected)")


class TestExploreEndpoint:
    """Tests for GET /api/explore endpoint to verify same post type filtering"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@honeygroove.com",
            "password": "test123"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_explore_returns_allowed_types(self, auth_headers):
        """Test that explore endpoint also filters to allowed types"""
        ALLOWED_TYPES = {"NOW_SPINNING", "NEW_HAUL", "ISO", "RANDOMIZER", "DAILY_PROMPT", "NOTE"}
        
        response = requests.get(f"{BASE_URL}/api/explore?limit=50", headers=auth_headers)
        assert response.status_code == 200
        posts = response.json()
        
        for post in posts:
            post_type = post.get("post_type", "")
            assert post_type in ALLOWED_TYPES, \
                f"Explore: Post type '{post_type}' should be in allowed types"
        
        print(f"SUCCESS: Explore endpoint returns only allowed types ({len(posts)} posts)")
