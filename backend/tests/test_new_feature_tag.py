"""
Test suite for New Feature tag system for Hive posts.
Tests:
- POST /api/posts/{post_id}/new-feature (admin toggle)
- Non-admin 403 restriction
- is_new_feature field in PostResponse
- Feed returns is_new_feature in post data
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from previous iteration
ADMIN_EMAIL = "admin@thehoneygroove.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "testexplore@test.com"
TEST_USER_PASSWORD = "testpass123"


class TestNewFeatureTag:
    """Tests for the New Feature tag system."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def regular_user_token(self):
        """Get regular (non-admin) user token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Regular user login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def test_post_id(self, admin_token):
        """Create a test post and return its ID for testing."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # First get user's records
        records_resp = requests.get(f"{BASE_URL}/api/records", headers=headers)
        if records_resp.status_code == 200 and len(records_resp.json()) > 0:
            record_id = records_resp.json()[0]["id"]
            # Create a now spinning post
            post_resp = requests.post(f"{BASE_URL}/api/composer/now-spinning", json={
                "record_id": record_id,
                "caption": f"TEST_NewFeature_{uuid.uuid4().hex[:8]}"
            }, headers=headers)
            if post_resp.status_code == 200:
                return post_resp.json()["id"]
        # Try creating a note post
        note_resp = requests.post(f"{BASE_URL}/api/composer/note", json={
            "text": f"TEST_NewFeature_Note_{uuid.uuid4().hex[:8]}"
        }, headers=headers)
        if note_resp.status_code == 200:
            return note_resp.json()["id"]
        pytest.skip("Could not create test post")
    
    def test_new_feature_endpoint_requires_auth(self):
        """Test that /posts/{post_id}/new-feature requires authentication."""
        fake_post_id = "test-post-id"
        response = requests.post(f"{BASE_URL}/api/posts/{fake_post_id}/new-feature")
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print("PASS: /posts/{post_id}/new-feature requires authentication")
    
    def test_non_admin_gets_403(self, regular_user_token, test_post_id):
        """Test that non-admin users get 403 when calling new-feature endpoint."""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = requests.post(f"{BASE_URL}/api/posts/{test_post_id}/new-feature", headers=headers)
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}: {response.text}"
        print(f"PASS: Non-admin user gets 403 when trying to toggle new-feature")
    
    def test_admin_can_toggle_new_feature_on(self, admin_token, test_post_id):
        """Test that admin can toggle is_new_feature ON."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # First ensure it's off
        response = requests.post(f"{BASE_URL}/api/posts/{test_post_id}/new-feature", headers=headers)
        assert response.status_code == 200, f"Failed to toggle new-feature: {response.status_code} - {response.text}"
        data = response.json()
        assert "is_new_feature" in data, "Response should contain is_new_feature"
        first_value = data["is_new_feature"]
        print(f"PASS: Admin toggled is_new_feature to {first_value}")
        return first_value
    
    def test_admin_can_toggle_new_feature_off(self, admin_token, test_post_id):
        """Test that admin can toggle is_new_feature OFF (second toggle)."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Toggle again to reverse the state
        response = requests.post(f"{BASE_URL}/api/posts/{test_post_id}/new-feature", headers=headers)
        assert response.status_code == 200, f"Failed to toggle new-feature: {response.status_code} - {response.text}"
        data = response.json()
        assert "is_new_feature" in data, "Response should contain is_new_feature"
        print(f"PASS: Admin toggled is_new_feature to {data['is_new_feature']}")
    
    def test_post_response_includes_is_new_feature(self, admin_token, test_post_id):
        """Test that GET /posts/{post_id} returns is_new_feature field."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/posts/{test_post_id}", headers=headers)
        assert response.status_code == 200, f"Failed to get post: {response.status_code}"
        data = response.json()
        assert "is_new_feature" in data, "PostResponse should include is_new_feature field"
        assert isinstance(data["is_new_feature"], bool), "is_new_feature should be a boolean"
        print(f"PASS: PostResponse includes is_new_feature={data['is_new_feature']}")
    
    def test_feed_returns_is_new_feature(self, admin_token):
        """Test that /feed endpoint returns is_new_feature in post data."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/feed?limit=10", headers=headers)
        assert response.status_code == 200, f"Failed to get feed: {response.status_code}"
        posts = response.json()
        if len(posts) > 0:
            post = posts[0]
            assert "is_new_feature" in post, "Feed posts should include is_new_feature field"
            print(f"PASS: Feed endpoint returns is_new_feature in posts (sample: {post.get('is_new_feature')})")
        else:
            print("SKIP: No posts in feed to verify is_new_feature field")
    
    def test_explore_returns_is_new_feature(self, admin_token):
        """Test that /explore endpoint returns is_new_feature in post data."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/explore?limit=10", headers=headers)
        assert response.status_code == 200, f"Failed to get explore feed: {response.status_code}"
        posts = response.json()
        if len(posts) > 0:
            post = posts[0]
            assert "is_new_feature" in post, "Explore posts should include is_new_feature field"
            print(f"PASS: Explore endpoint returns is_new_feature in posts")
        else:
            print("SKIP: No posts in explore to verify is_new_feature field")
    
    def test_toggle_on_nonexistent_post_returns_404(self, admin_token):
        """Test that toggling new-feature on non-existent post returns 404."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_id = f"nonexistent-{uuid.uuid4().hex}"
        response = requests.post(f"{BASE_URL}/api/posts/{fake_id}/new-feature", headers=headers)
        assert response.status_code == 404, f"Expected 404 for non-existent post, got {response.status_code}"
        print("PASS: Non-existent post returns 404")


class TestNewFeatureTagCleanup:
    """Cleanup test data."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")
    
    def test_cleanup_test_posts(self, admin_token):
        """Clean up TEST_ prefixed posts created during testing."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Get feed and delete test posts
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=headers)
        if response.status_code == 200:
            posts = response.json()
            deleted = 0
            for post in posts:
                caption = post.get("caption") or post.get("content") or ""
                if caption.startswith("TEST_NewFeature_"):
                    del_resp = requests.delete(f"{BASE_URL}/api/posts/{post['id']}", headers=headers)
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"PASS: Cleaned up {deleted} test posts")
