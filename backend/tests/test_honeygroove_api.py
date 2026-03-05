"""
HoneyGroove API Tests
Tests for vinyl collector social network backend APIs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"

class TestAuthEndpoints:
    """Authentication API tests"""
    
    def test_root_endpoint(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "HoneyGroove" in data["message"]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestRecordsEndpoints:
    """Records/Collection API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_get_records(self, auth_token):
        """Test fetching user's record collection"""
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Demo user should have some records
        if len(data) > 0:
            assert "title" in data[0]
            assert "artist" in data[0]
    
    def test_get_user_records_public(self):
        """Test fetching user records publicly"""
        response = requests.get(f"{BASE_URL}/api/users/demo/records")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestFeedEndpoints:
    """Feed/Activity API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_get_feed(self, auth_token):
        """Test fetching user's feed"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_explore(self):
        """Test explore feed (public)"""
        response = requests.get(f"{BASE_URL}/api/explore")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestUserEndpoints:
    """User profile API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_get_user_profile(self):
        """Test fetching user profile publicly"""
        response = requests.get(f"{BASE_URL}/api/users/demo")
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert data["username"] == "demo"
        assert "collection_count" in data
        assert "spin_count" in data
        assert "followers_count" in data
        assert "following_count" in data
    
    def test_get_current_user(self, auth_token):
        """Test fetching current authenticated user"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL


class TestSpinsEndpoints:
    """Spin tracking API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_get_spins(self, auth_token):
        """Test fetching user's spin history"""
        response = requests.get(
            f"{BASE_URL}/api/spins",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestInteractionsEndpoints:
    """Like and Comment API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def post_id(self, auth_token):
        """Get a post ID for testing"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200 and len(response.json()) > 0:
            return response.json()[0]["id"]
        pytest.skip("No posts available")
    
    def test_get_comments(self, auth_token, post_id):
        """Test fetching post comments"""
        response = requests.get(
            f"{BASE_URL}/api/posts/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestWeeklySummaryEndpoints:
    """Weekly summary API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_get_weekly_summary(self, auth_token):
        """Test fetching weekly summary"""
        response = requests.get(
            f"{BASE_URL}/api/weekly-summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_spins" in data
        assert "top_artist" in data
        assert "listening_mood" in data


class TestBuzzingEndpoints:
    """Buzzing/trending records API tests"""
    
    def test_get_buzzing(self):
        """Test fetching trending records"""
        response = requests.get(f"{BASE_URL}/api/buzzing")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestStatsEndpoints:
    """Global stats API tests"""
    
    def test_get_global_stats(self):
        """Test fetching global stats"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "records" in data
        assert "spins" in data
        assert "hauls" in data


class TestShareEndpoints:
    """Share graphic generation API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_generate_weekly_share_graphic(self, auth_token):
        """Test generating weekly summary share graphic"""
        response = requests.post(
            f"{BASE_URL}/api/share/generate",
            json={"graphic_type": "weekly_summary", "format": "square"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "image/png"
