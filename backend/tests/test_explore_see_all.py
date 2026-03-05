"""
Tests for Explore See All pages backend APIs
Tests explore endpoints with higher limits as used by See All pages:
- GET /api/explore/trending?limit=50
- GET /api/explore/suggested-collectors?limit=50
- GET /api/explore/fresh-pressings?limit=50
- GET /api/explore/most-wanted?limit=100
- GET /api/explore/near-you?collector_limit=50&listing_limit=30
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestExploreSeeAllEndpoints:
    """Backend API tests for Explore See All pages with higher limits"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Login failed - skipping authenticated tests")
    
    # ===== Trending Endpoint Tests =====
    
    def test_trending_requires_auth(self):
        """Trending endpoint should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/explore/trending?limit=50")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASS: Trending endpoint requires auth")
    
    def test_trending_with_limit_50(self):
        """GET /api/explore/trending?limit=50 should return up to 50 records"""
        resp = self.session.get(f"{BASE_URL}/api/explore/trending?limit=50")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        assert len(data) <= 50, f"Expected max 50 records, got {len(data)}"
        
        # Verify each record has required fields
        if len(data) > 0:
            record = data[0]
            assert "id" in record, "Record missing 'id' field"
            assert "title" in record or "album" in record, "Record missing title/album field"
            assert "artist" in record, "Record missing 'artist' field"
            assert "trending_spins" in record, "Record missing 'trending_spins' field"
        
        print(f"PASS: Trending endpoint returned {len(data)} records with limit=50")
    
    # ===== Suggested Collectors (Taste Match) Tests =====
    
    def test_suggested_collectors_requires_auth(self):
        """Suggested collectors endpoint should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=50")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASS: Suggested collectors endpoint requires auth")
    
    def test_suggested_collectors_with_limit_50(self):
        """GET /api/explore/suggested-collectors?limit=50 should return up to 50 users"""
        resp = self.session.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=50")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        assert len(data) <= 50, f"Expected max 50 users, got {len(data)}"
        
        # Verify each user has required fields if data exists
        if len(data) > 0:
            user = data[0]
            assert "id" in user, "User missing 'id' field"
            assert "username" in user, "User missing 'username' field"
            # shared_artists is expected for taste match
            if "shared_artists" in user:
                assert isinstance(user["shared_artists"], int), "shared_artists should be int"
        
        print(f"PASS: Suggested collectors endpoint returned {len(data)} users with limit=50")
    
    # ===== Fresh Pressings Tests =====
    
    def test_fresh_pressings_requires_auth(self):
        """Fresh pressings endpoint should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/explore/fresh-pressings?limit=50")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASS: Fresh pressings endpoint requires auth")
    
    def test_fresh_pressings_with_limit_50(self):
        """GET /api/explore/fresh-pressings?limit=50 should return Discogs releases"""
        resp = self.session.get(f"{BASE_URL}/api/explore/fresh-pressings?limit=50")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        assert len(data) <= 50, f"Expected max 50 releases, got {len(data)}"
        
        # Verify Discogs release structure if data exists
        if len(data) > 0:
            release = data[0]
            # Discogs releases have title/artist or similar fields
            assert "title" in release or "artist" in release, "Release missing title/artist"
        
        print(f"PASS: Fresh pressings endpoint returned {len(data)} releases with limit=50")
    
    # ===== Most Wanted Tests =====
    
    def test_most_wanted_requires_auth(self):
        """Most wanted endpoint should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/explore/most-wanted?limit=100")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASS: Most wanted endpoint requires auth")
    
    def test_most_wanted_with_limit_100(self):
        """GET /api/explore/most-wanted?limit=100 should return up to 100 wanted records"""
        resp = self.session.get(f"{BASE_URL}/api/explore/most-wanted?limit=100")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
        assert len(data) <= 100, f"Expected max 100 records, got {len(data)}"
        
        # Verify each record has required fields
        if len(data) > 0:
            record = data[0]
            assert "artist" in record, "Record missing 'artist' field"
            assert "album" in record, "Record missing 'album' field"
            assert "want_count" in record, "Record missing 'want_count' field"
            assert isinstance(record["want_count"], int), "want_count should be int"
        
        print(f"PASS: Most wanted endpoint returned {len(data)} records with limit=100")
    
    # ===== Near You Tests =====
    
    def test_near_you_requires_auth(self):
        """Near you endpoint should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/explore/near-you?collector_limit=50&listing_limit=30")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASS: Near you endpoint requires auth")
    
    def test_near_you_with_new_params(self):
        """GET /api/explore/near-you?collector_limit=50&listing_limit=30 should accept new params"""
        resp = self.session.get(f"{BASE_URL}/api/explore/near-you?collector_limit=50&listing_limit=30")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, dict), "Expected dict response"
        
        # Should have collectors, listings, or needs_location
        assert "collectors" in data or "needs_location" in data, "Response missing expected fields"
        
        if data.get("needs_location"):
            print("PASS: Near you returns needs_location=True (user has no location set)")
        else:
            collectors = data.get("collectors", [])
            listings = data.get("listings", [])
            assert len(collectors) <= 50, f"Expected max 50 collectors, got {len(collectors)}"
            assert len(listings) <= 30, f"Expected max 30 listings, got {len(listings)}"
            print(f"PASS: Near you endpoint returned {len(collectors)} collectors and {len(listings)} listings")
    
    def test_near_you_default_params(self):
        """GET /api/explore/near-you without params should still work"""
        resp = self.session.get(f"{BASE_URL}/api/explore/near-you")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, dict), "Expected dict response"
        print("PASS: Near you endpoint works without custom params")
    
    # ===== Trending Posts for Modal Tests =====
    
    def test_trending_posts_requires_auth(self):
        """Trending posts endpoint should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/explore/trending/fake-id/posts")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASS: Trending posts endpoint requires auth")
    
    def test_trending_posts_returns_404_for_invalid_id(self):
        """GET /api/explore/trending/{invalid_id}/posts should return 404"""
        resp = self.session.get(f"{BASE_URL}/api/explore/trending/non-existent-record-id/posts")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("PASS: Trending posts returns 404 for invalid record ID")


class TestExploreSeeAllPageRoutes:
    """Test that See All page routes are properly mapped"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Login failed - skipping authenticated tests")
    
    def test_main_explore_page_accessible(self):
        """Main explore page should be accessible"""
        resp = requests.get(f"{BASE_URL}/explore")
        # Frontend routes - should return HTML
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print("PASS: Main explore page accessible at /explore")
    
    def test_api_root_endpoint(self):
        """API root should return welcome message"""
        resp = self.session.get(f"{BASE_URL}/api/")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "message" in data, "Response missing message"
        print(f"PASS: API root returns: {data['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
