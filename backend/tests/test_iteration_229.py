"""
Test iteration 229: Filter system lock (6 filters), Re-pollinate checkout, Newsletter status, PWA localStorage key
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "katie"
TEST_PASSWORD = "HoneyGroove2026!"


class TestAuthentication:
    """Test authentication to get token for other tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_returns_token(self, auth_token):
        """Verify login returns a valid token"""
        assert auth_token is not None
        assert len(auth_token) > 10
        print(f"✓ Login successful, token length: {len(auth_token)}")


class TestRepollinate:
    """Test Re-pollinate streak recovery endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_repollinate_checkout_returns_stripe_url(self, auth_token):
        """POST /api/repollinate/checkout should return a Stripe checkout URL"""
        response = requests.post(
            f"{BASE_URL}/api/repollinate/checkout",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Repollinate checkout failed: {response.text}"
        data = response.json()
        
        # Verify URL is returned
        assert "url" in data, "No 'url' in response"
        assert data["url"].startswith("https://checkout.stripe.com"), f"URL doesn't look like Stripe: {data['url']}"
        
        # Verify session_id is returned
        assert "session_id" in data, "No 'session_id' in response"
        assert data["session_id"].startswith("cs_"), f"Session ID doesn't look valid: {data['session_id']}"
        
        print(f"✓ Re-pollinate checkout returns valid Stripe URL")
        print(f"  URL prefix: {data['url'][:60]}...")
        print(f"  Session ID: {data['session_id']}")


class TestNewsletter:
    """Test Newsletter (Weekly Wax) status endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_newsletter_status_returns_subscribed(self, auth_token):
        """GET /api/newsletter/status should return subscribed=true for test user"""
        response = requests.get(
            f"{BASE_URL}/api/newsletter/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Newsletter status failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "subscribed" in data, "No 'subscribed' in response"
        assert "email" in data, "No 'email' in response"
        
        # Verify user is subscribed (all 132 users were auto-subscribed)
        assert data["subscribed"] == True, f"User should be subscribed but got: {data['subscribed']}"
        
        print(f"✓ Newsletter status: subscribed={data['subscribed']}, email={data['email']}")


class TestFeedEndpoint:
    """Test Feed endpoint to verify posts exist"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_feed_returns_posts(self, auth_token):
        """GET /api/feed should return posts"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Feed failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Feed should return a list"
        print(f"✓ Feed returned {len(data)} posts")
        
        # Check post types in feed
        post_types = set()
        for post in data:
            if "post_type" in post:
                post_types.add(post["post_type"])
        
        print(f"  Post types found: {post_types}")


class TestUserProfile:
    """Test user profile to verify Re-pollinate context"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_profile_katie_accessible(self, auth_token):
        """GET /api/users/katie should return profile data"""
        response = requests.get(
            f"{BASE_URL}/api/users/katie",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Profile fetch failed: {response.text}"
        data = response.json()
        
        assert "username" in data, "No 'username' in profile"
        assert data["username"] == "katie", f"Expected username 'katie', got {data['username']}"
        
        print(f"✓ Profile accessible for @{data['username']}")
        if "current_streak" in data:
            print(f"  Current streak: {data.get('current_streak', 0)}")
