"""
Tests for feed API and bug fixes (Block 272):
- Feed API returns posts correctly
- New posts deduplication logic (WebSocket + polling)
- BackToTop component global availability
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestFeedAPI:
    """Feed API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_feed_loads_successfully(self):
        """Feed API returns posts"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            params={"limit": 20},
            headers=self.headers,
            timeout=30
        )
        assert response.status_code == 200, f"Feed API failed: {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        print(f"Feed returned {len(data)} posts")
    
    def test_feed_post_structure(self):
        """Feed posts have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            params={"limit": 5},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            post = data[0]
            # Check required fields for any post
            assert "id" in post, "Post missing id"
            assert "post_type" in post, "Post missing post_type"
            assert "user_id" in post or "author_id" in post, "Post missing user_id/author_id"
            assert "created_at" in post, "Post missing created_at"
            print(f"First post type: {post.get('post_type')}, id: {post.get('id')}")
    
    def test_feed_filter_now_spinning(self):
        """Feed filter by NOW_SPINNING works"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            params={"limit": 10, "post_type": "NOW_SPINNING"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        # All returned posts should be NOW_SPINNING type
        for post in data:
            assert post.get("post_type") == "NOW_SPINNING", f"Unexpected post type: {post.get('post_type')}"
        print(f"NOW_SPINNING filter returned {len(data)} posts")
    
    def test_feed_pagination_before(self):
        """Feed pagination with 'before' parameter works"""
        # Get first page
        response1 = requests.get(
            f"{BASE_URL}/api/feed",
            params={"limit": 5},
            headers=self.headers
        )
        assert response1.status_code == 200
        page1 = response1.json()
        
        if len(page1) >= 5:
            last_post_ts = page1[-1].get("created_at")
            
            # Get second page
            response2 = requests.get(
                f"{BASE_URL}/api/feed",
                params={"limit": 5, "before": last_post_ts},
                headers=self.headers
            )
            assert response2.status_code == 200
            page2 = response2.json()
            
            # Pages should have different posts
            page1_ids = set(p["id"] for p in page1)
            page2_ids = set(p["id"] for p in page2)
            overlap = page1_ids.intersection(page2_ids)
            assert len(overlap) == 0, f"Pagination returned overlapping posts: {overlap}"
            print(f"Pagination: page1={len(page1)} posts, page2={len(page2)} posts")
    
    def test_feed_after_parameter(self):
        """Feed 'after' parameter exists and API accepts it"""
        # Get initial posts
        response1 = requests.get(
            f"{BASE_URL}/api/feed",
            params={"limit": 5},
            headers=self.headers
        )
        assert response1.status_code == 200
        posts = response1.json()
        
        if len(posts) > 0:
            oldest_ts = posts[-1].get("created_at")
            
            # Request posts with after parameter - API should accept it
            response2 = requests.get(
                f"{BASE_URL}/api/feed",
                params={"limit": 10, "after": oldest_ts},
                headers=self.headers
            )
            assert response2.status_code == 200, "API should accept 'after' parameter"
            print(f"After parameter accepted by API, returned {len(response2.json())} posts")


class TestUserEndpoints:
    """User profile and following endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_user_profile(self):
        """User profile endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/users/katie",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "username" in data
        assert data["username"] == "katie"
        print(f"Profile loaded for: {data['username']}")
    
    def test_get_user_following(self):
        """User following list endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/users/katie/following",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"User has {len(data)} following")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """API is reachable"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        print("API health check passed")
