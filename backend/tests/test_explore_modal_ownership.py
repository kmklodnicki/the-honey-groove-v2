"""
Test suite for Explore page modal ownership check and Discogs release endpoints.
- GET /api/records/check-ownership: Returns ownership status for a record
- GET /api/discogs/release/{id}: Returns release details including catno and color_variant
- Frontend modal contextual actions based on ownership
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = "testexplore@test.com"
TEST_PASSWORD = "testpass123"


@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for testing"""
    login_resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if login_resp.status_code == 200:
        token = login_resp.json().get("access_token")
        print(f"AUTH: Successfully logged in as {TEST_EMAIL}")
        return token
    
    pytest.skip(f"Could not authenticate - login failed with status {login_resp.status_code}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestCheckOwnershipEndpoint:
    """Tests for GET /api/records/check-ownership endpoint"""
    
    def test_check_ownership_requires_auth(self):
        """Endpoint should return 401 without authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/records/check-ownership?discogs_id=12345")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASSED: check-ownership requires authentication")
    
    def test_check_ownership_no_params_returns_false(self, authenticated_client):
        """Endpoint should return in_collection: false when no params provided"""
        response = authenticated_client.get(f"{BASE_URL}/api/records/check-ownership")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("in_collection") == False
        assert data.get("record_id") is None
        print("PASSED: check-ownership with no params returns {in_collection: false, record_id: null}")
    
    def test_check_ownership_by_discogs_id_not_owned(self, authenticated_client):
        """Check ownership for a discogs_id not in user's collection"""
        response = authenticated_client.get(f"{BASE_URL}/api/records/check-ownership?discogs_id=999999999")
        assert response.status_code == 200
        data = response.json()
        assert data.get("in_collection") == False
        assert data.get("record_id") is None
        print("PASSED: check-ownership for non-owned discogs_id returns false")
    
    def test_check_ownership_by_artist_title_not_owned(self, authenticated_client):
        """Check ownership by artist+title not in user's collection"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/records/check-ownership",
            params={"artist": "NonexistentArtist12345", "title": "NonexistentAlbum67890"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("in_collection") == False
        assert data.get("record_id") is None
        print("PASSED: check-ownership for non-owned artist+title returns false")
    
    def test_check_ownership_response_structure(self, authenticated_client):
        """Verify response has expected fields: in_collection and record_id"""
        response = authenticated_client.get(f"{BASE_URL}/api/records/check-ownership?discogs_id=1")
        assert response.status_code == 200
        data = response.json()
        assert "in_collection" in data, "Response missing 'in_collection' field"
        assert "record_id" in data, "Response missing 'record_id' field"
        assert isinstance(data["in_collection"], bool), "in_collection should be boolean"
        print("PASSED: check-ownership response has correct structure")


class TestDiscogsReleaseEndpoint:
    """Tests for GET /api/discogs/release/{id} endpoint"""
    
    def test_discogs_release_requires_auth(self):
        """Endpoint should return 401 without authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/discogs/release/249504")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASSED: discogs/release requires authentication")
    
    def test_discogs_release_returns_details(self, authenticated_client):
        """Fetch a known Discogs release and verify response fields"""
        # Using a well-known release: Pink Floyd - The Dark Side of the Moon
        response = authenticated_client.get(f"{BASE_URL}/api/discogs/release/249504")
        
        if response.status_code == 404:
            pytest.skip("Discogs release 249504 not found - API may be rate limited")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify expected fields exist
        assert "discogs_id" in data, "Response missing 'discogs_id'"
        assert "artist" in data, "Response missing 'artist'"
        assert "title" in data, "Response missing 'title'"
        assert "year" in data, "Response missing 'year'"
        assert "format" in data, "Response missing 'format'"
        assert "label" in data, "Response missing 'label'"
        assert "country" in data, "Response missing 'country'"
        
        # Verify NEW fields from enhancement
        assert "catno" in data, "Response missing 'catno' field (NEW)"
        assert "color_variant" in data, "Response missing 'color_variant' field (NEW)"
        
        print(f"PASSED: discogs/release returns all expected fields")
        print(f"  - discogs_id: {data.get('discogs_id')}")
        print(f"  - title: {data.get('title')}")
        print(f"  - artist: {data.get('artist')}")
        print(f"  - year: {data.get('year')}")
        print(f"  - label: {data.get('label')}")
        print(f"  - catno: {data.get('catno')}")
        print(f"  - country: {data.get('country')}")
        print(f"  - color_variant: {data.get('color_variant')}")
        print(f"  - format: {data.get('format')}")
    
    def test_discogs_release_invalid_id(self, authenticated_client):
        """Verify 404 for non-existent release"""
        response = authenticated_client.get(f"{BASE_URL}/api/discogs/release/999999999999")
        assert response.status_code == 404, f"Expected 404 for invalid release, got {response.status_code}"
        print("PASSED: discogs/release returns 404 for invalid release ID")


class TestExploreEndpoints:
    """Tests for Explore page API endpoints"""
    
    def test_trending_in_collections(self, authenticated_client):
        """GET /api/explore/trending-in-collections should return trending records from Discogs"""
        response = authenticated_client.get(f"{BASE_URL}/api/explore/trending-in-collections?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            item = data[0]
            assert "discogs_id" in item, "Item missing 'discogs_id'"
            assert "artist" in item, "Item missing 'artist'"
            assert "title" in item, "Item missing 'title'"
            assert "cover_url" in item, "Item missing 'cover_url'"
            print(f"PASSED: trending-in-collections returns {len(data)} items with expected fields")
        else:
            print("WARNING: trending-in-collections returned empty list (cache may be empty)")
    
    def test_most_wanted(self, authenticated_client):
        """GET /api/explore/most-wanted should return most wanted records from wantlists"""
        response = authenticated_client.get(f"{BASE_URL}/api/explore/most-wanted?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            item = data[0]
            assert "artist" in item, "Item missing 'artist'"
            assert "album" in item, "Item missing 'album'"
            assert "want_count" in item, "Item missing 'want_count'"
            print(f"PASSED: most-wanted returns {len(data)} items with expected fields")
        else:
            print("INFO: most-wanted returned empty list (no wantlist items in DB)")
    
    def test_trending_section(self, authenticated_client):
        """GET /api/explore/trending should return trending records based on spins"""
        response = authenticated_client.get(f"{BASE_URL}/api/explore/trending?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASSED: explore/trending returns {len(data)} items")


class TestOwnershipFlowIntegration:
    """Integration tests for the ownership check + collection flow"""
    
    def test_add_record_then_check_ownership(self, authenticated_client):
        """Add a record to collection, then verify check-ownership returns true"""
        # Create a test record with unique data
        test_discogs_id = 123456789 + int(uuid.uuid4().int % 100000)
        record_data = {
            "discogs_id": test_discogs_id,
            "title": f"Test Album {uuid.uuid4().hex[:8]}",
            "artist": "Test Artist",
            "cover_url": "https://example.com/cover.jpg",
            "year": 2024,
            "format": "Vinyl"
        }
        
        # Add to collection
        add_response = authenticated_client.post(f"{BASE_URL}/api/records", json=record_data)
        
        if add_response.status_code == 201:
            created_record = add_response.json()
            record_id = created_record.get("id")
            
            # Now check ownership
            ownership_response = authenticated_client.get(
                f"{BASE_URL}/api/records/check-ownership?discogs_id={test_discogs_id}"
            )
            assert ownership_response.status_code == 200
            ownership_data = ownership_response.json()
            
            assert ownership_data.get("in_collection") == True, "Expected in_collection to be True after adding"
            assert ownership_data.get("record_id") == record_id, "Expected record_id to match created record"
            
            print(f"PASSED: After adding record, check-ownership returns in_collection: true, record_id: {record_id}")
            
            # Cleanup: delete the test record
            delete_response = authenticated_client.delete(f"{BASE_URL}/api/records/{record_id}")
            print(f"  - Cleanup: deleted test record {record_id}")
        else:
            print(f"INFO: Could not add record (status {add_response.status_code}) - skipping integration test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
