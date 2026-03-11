"""
BLOCK 450: SWR Data Caching - Backend API Tests
Tests all endpoints used by ProfilePage and ExplorePage SWR hooks
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBlock450SWREndpoints:
    """Test all API endpoints used by SWR hooks in BLOCK 450"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.user = login_resp.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed: {login_resp.status_code}")
    
    # ============== ProfilePage SWR Endpoints ==============
    
    def test_profile_user_endpoint(self):
        """ProfilePage: GET /api/users/{username} - user profile data"""
        username = self.user.get("username", "testuser1")
        resp = self.session.get(f"{BASE_URL}/api/users/{username}")
        assert resp.status_code == 200, f"Profile endpoint failed: {resp.text}"
        data = resp.json()
        assert "username" in data
        assert "followers_count" in data or "collection_count" in data
        print(f"PASS: /api/users/{username} returns profile data")
    
    def test_profile_records_endpoint(self):
        """ProfilePage: GET /api/users/{username}/records - user's records"""
        username = self.user.get("username", "testuser1")
        resp = self.session.get(f"{BASE_URL}/api/users/{username}/records")
        assert resp.status_code == 200, f"Records endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASS: /api/users/{username}/records returns {len(data)} records")
    
    def test_profile_ratings_endpoint(self):
        """ProfilePage: GET /api/users/{username}/ratings - trade ratings"""
        username = self.user.get("username", "testuser1")
        resp = self.session.get(f"{BASE_URL}/api/users/{username}/ratings")
        # May return 200 or 404 if no ratings exist
        assert resp.status_code in [200, 404], f"Ratings endpoint failed: {resp.text}"
        print(f"PASS: /api/users/{username}/ratings - status {resp.status_code}")
    
    def test_profile_collection_value_endpoint(self):
        """ProfilePage: GET /api/valuation/collection/{username} - collection valuation"""
        username = self.user.get("username", "testuser1")
        resp = self.session.get(f"{BASE_URL}/api/valuation/collection/{username}")
        assert resp.status_code in [200, 404], f"Collection value endpoint failed: {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert "total_value" in data or isinstance(data, dict)
        print(f"PASS: /api/valuation/collection/{username} - status {resp.status_code}")
    
    def test_profile_prompt_streak_endpoint(self):
        """ProfilePage: GET /api/prompts/streak/{username} - prompt streak"""
        username = self.user.get("username", "testuser1")
        resp = self.session.get(f"{BASE_URL}/api/prompts/streak/{username}")
        assert resp.status_code in [200, 404], f"Prompt streak endpoint failed: {resp.text}"
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)
        print(f"PASS: /api/prompts/streak/{username} - status {resp.status_code}")
    
    def test_profile_dream_value_endpoint(self):
        """ProfilePage: GET /api/valuation/dreamlist/{username} - dream list valuation"""
        username = self.user.get("username", "testuser1")
        resp = self.session.get(f"{BASE_URL}/api/valuation/dreamlist/{username}")
        assert resp.status_code in [200, 404], f"Dream value endpoint failed: {resp.text}"
        print(f"PASS: /api/valuation/dreamlist/{username} - status {resp.status_code}")
    
    # ============== ExplorePage SWR Endpoints ==============
    
    def test_explore_trending_endpoint(self):
        """ExplorePage: GET /api/explore/trending - trending records"""
        resp = self.session.get(f"{BASE_URL}/api/explore/trending?limit=10")
        assert resp.status_code == 200, f"Trending endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASS: /api/explore/trending returns {len(data)} trending records")
    
    def test_explore_suggested_collectors_endpoint(self):
        """ExplorePage: GET /api/explore/suggested-collectors - suggested users"""
        resp = self.session.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=8")
        assert resp.status_code == 200, f"Suggested collectors endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASS: /api/explore/suggested-collectors returns {len(data)} users")
    
    def test_explore_trending_collections_endpoint(self):
        """ExplorePage: GET /api/explore/trending-in-collections - trending in collections"""
        resp = self.session.get(f"{BASE_URL}/api/explore/trending-in-collections?limit=12")
        assert resp.status_code == 200, f"Trending collections endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASS: /api/explore/trending-in-collections returns {len(data)} records")
    
    def test_explore_crown_jewels_endpoint(self):
        """ExplorePage: GET /api/explore/crown-jewels - rare/valuable records"""
        resp = self.session.get(f"{BASE_URL}/api/explore/crown-jewels?limit=12")
        assert resp.status_code == 200, f"Crown jewels endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASS: /api/explore/crown-jewels returns {len(data)} records")
    
    def test_explore_most_wanted_endpoint(self):
        """ExplorePage: GET /api/explore/most-wanted - most wanted records"""
        resp = self.session.get(f"{BASE_URL}/api/explore/most-wanted?limit=20")
        assert resp.status_code == 200, f"Most wanted endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASS: /api/explore/most-wanted returns {len(data)} records")
    
    def test_explore_near_you_endpoint(self):
        """ExplorePage: GET /api/explore/near-you - nearby collectors/listings"""
        resp = self.session.get(f"{BASE_URL}/api/explore/near-you")
        assert resp.status_code == 200, f"Near you endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, dict)
        # Should have collectors and listings arrays or needs_location flag
        print(f"PASS: /api/explore/near-you returns data")
    
    # ============== Navbar Prefetch Endpoints ==============
    
    def test_listings_endpoint_for_prefetch(self):
        """Navbar: GET /api/listings - honeypot prefetch"""
        resp = self.session.get(f"{BASE_URL}/api/listings?limit=20")
        assert resp.status_code == 200, f"Listings endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, (list, dict))
        print(f"PASS: /api/listings returns listings data")
    
    def test_records_endpoint_for_prefetch(self):
        """Navbar: GET /api/records - collection prefetch"""
        resp = self.session.get(f"{BASE_URL}/api/records")
        assert resp.status_code == 200, f"Records endpoint failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASS: /api/records returns {len(data)} records")


class TestBlock450RouteNavigation:
    """Test that all major routes load correctly after SWR integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.user = login_resp.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Login failed: {login_resp.status_code}")
    
    def test_api_health(self):
        """Verify API is accessible"""
        resp = self.session.get(f"{BASE_URL}/api/")
        assert resp.status_code == 200, f"API health check failed: {resp.text}"
        print("PASS: API is healthy")
