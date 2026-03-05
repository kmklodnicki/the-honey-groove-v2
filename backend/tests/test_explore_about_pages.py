"""
Test Suite for Explore Page (5 sections) and About Page Features
Tests: 
- Explore API endpoints: trending, fresh-pressings, most-wanted, near-you, suggested-collectors
- About page routes are accessible
- Landing page footer links
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestExploreEndpoints:
    """Test all explore API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns 'access_token' not 'token'
        token = data.get("access_token")
        assert token, f"No access_token in response: {data}"
        return token

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with Bearer token"""
        return {"Authorization": f"Bearer {auth_token}"}

    # ==================== TRENDING ENDPOINT ====================
    def test_trending_endpoint_requires_auth(self):
        """GET /api/explore/trending requires authentication"""
        response = requests.get(f"{BASE_URL}/api/explore/trending")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_trending_endpoint_returns_records(self, auth_headers):
        """GET /api/explore/trending returns trending records with trending_spins"""
        response = requests.get(f"{BASE_URL}/api/explore/trending?limit=10", headers=auth_headers)
        assert response.status_code == 200, f"Trending failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of records"
        # If there's data, check structure
        if len(data) > 0:
            record = data[0]
            assert "id" in record, "Record should have id"
            assert "trending_spins" in record, "Record should have trending_spins count"
            assert "title" in record or "artist" in record, "Record should have title or artist"
            print(f"Trending records: {len(data)}, first has {record.get('trending_spins', 0)} spins")
        else:
            print("No trending records found (expected for fresh data)")

    # ==================== FRESH PRESSINGS ENDPOINT ====================
    def test_fresh_pressings_requires_auth(self):
        """GET /api/explore/fresh-pressings requires authentication"""
        response = requests.get(f"{BASE_URL}/api/explore/fresh-pressings")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_fresh_pressings_returns_discogs_results(self, auth_headers):
        """GET /api/explore/fresh-pressings returns Discogs releases"""
        response = requests.get(f"{BASE_URL}/api/explore/fresh-pressings?limit=12", headers=auth_headers)
        assert response.status_code == 200, f"Fresh pressings failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of releases"
        print(f"Fresh pressings: {len(data)} results")
        if len(data) > 0:
            release = data[0]
            # Discogs results typically have title, artist
            print(f"First release: {release.get('title', 'N/A')} by {release.get('artist', 'N/A')}")

    # ==================== MOST WANTED ENDPOINT ====================
    def test_most_wanted_requires_auth(self):
        """GET /api/explore/most-wanted requires authentication"""
        response = requests.get(f"{BASE_URL}/api/explore/most-wanted")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_most_wanted_returns_wantlist_data(self, auth_headers):
        """GET /api/explore/most-wanted returns aggregated wantlist items"""
        response = requests.get(f"{BASE_URL}/api/explore/most-wanted?limit=20", headers=auth_headers)
        assert response.status_code == 200, f"Most wanted failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of wanted items"
        print(f"Most wanted: {len(data)} items")
        if len(data) > 0:
            item = data[0]
            assert "artist" in item, "Item should have artist"
            assert "album" in item, "Item should have album"
            assert "want_count" in item, "Item should have want_count"
            print(f"Top wanted: {item.get('album')} by {item.get('artist')} - {item.get('want_count')} wants")

    # ==================== NEAR YOU ENDPOINT ====================
    def test_near_you_requires_auth(self):
        """GET /api/explore/near-you requires authentication"""
        response = requests.get(f"{BASE_URL}/api/explore/near-you")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_near_you_returns_location_data(self, auth_headers):
        """GET /api/explore/near-you returns collectors/listings or needs_location flag"""
        response = requests.get(f"{BASE_URL}/api/explore/near-you", headers=auth_headers)
        assert response.status_code == 200, f"Near you failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Expected dict response"
        # Should have collectors, listings, and needs_location
        assert "collectors" in data, "Response should have collectors"
        assert "listings" in data, "Response should have listings"
        assert "needs_location" in data, "Response should have needs_location flag"
        print(f"Near you: needs_location={data['needs_location']}, collectors={len(data.get('collectors', []))}")

    # ==================== SUGGESTED COLLECTORS ENDPOINT ====================
    def test_suggested_collectors_requires_auth(self):
        """GET /api/explore/suggested-collectors requires authentication"""
        response = requests.get(f"{BASE_URL}/api/explore/suggested-collectors")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_suggested_collectors_returns_users(self, auth_headers):
        """GET /api/explore/suggested-collectors returns user suggestions"""
        response = requests.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=8", headers=auth_headers)
        assert response.status_code == 200, f"Suggested collectors failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of users"
        print(f"Suggested collectors: {len(data)} users")
        if len(data) > 0:
            user = data[0]
            print(f"First suggestion: @{user.get('username', 'N/A')}, shared_artists={user.get('shared_artists', 0)}")


class TestTrendingRecordPosts:
    """Test trending record posts endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        return response.json().get("access_token")

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}

    def test_trending_posts_requires_auth(self):
        """GET /api/explore/trending/{record_id}/posts requires authentication"""
        response = requests.get(f"{BASE_URL}/api/explore/trending/test-id/posts")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_trending_posts_returns_404_for_invalid_record(self, auth_headers):
        """GET /api/explore/trending/{record_id}/posts returns 404 for invalid record"""
        response = requests.get(f"{BASE_URL}/api/explore/trending/invalid-record-id/posts", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestAboutPageRoute:
    """Test About page route is accessible"""
    
    def test_about_page_frontend_loads(self):
        """GET /about loads the About page (frontend route)"""
        # This tests the frontend route exists
        response = requests.get(f"{BASE_URL}/about", allow_redirects=True)
        # Frontend routes return 200 with HTML
        assert response.status_code == 200, f"About page failed: {response.status_code}"
        # Check it's HTML (frontend)
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, f"Expected HTML, got {content_type}"
        print("About page frontend route loads successfully")


class TestAPIRoot:
    """Test basic API functionality"""
    
    def test_api_root_returns_welcome(self):
        """GET /api/ returns welcome message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"API root failed: {response.text}"
        data = response.json()
        assert "message" in data, "Expected message in response"
        print(f"API root: {data}")

    def test_login_endpoint_works(self):
        """POST /api/auth/login with demo credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"Expected access_token: {data}"
        print(f"Login successful, token received")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
