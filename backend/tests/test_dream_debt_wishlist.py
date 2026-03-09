"""
Tests for Dream Debt Calculator - GET /api/valuation/wishlist endpoint
and related ISO WISHLIST filtering functionality.

Features tested:
- GET /api/valuation/wishlist returns total_value, valued_count, total_count
- GET /api/valuation/wishlist requires authentication
- GET /api/valuation/wishlist only counts ISO items with status WISHLIST
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@thehoneygroove.com"
TEST_PASSWORD = "admin123"
ALT_EMAIL = "feedverify888@gmail.com"
ALT_PASSWORD = "testpass123"


class TestDreamDebtCalculator:
    """Tests for GET /api/valuation/wishlist endpoint - Dream Debt Calculator"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.user = login_resp.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Could not authenticate: {login_resp.status_code}")

    def test_wishlist_valuation_endpoint_exists(self):
        """Test that GET /api/valuation/wishlist endpoint exists"""
        response = self.session.get(f"{BASE_URL}/api/valuation/wishlist")
        # Should not return 404 - endpoint must exist
        assert response.status_code != 404, "Wishlist valuation endpoint does not exist"
        print(f"Endpoint exists, status: {response.status_code}")

    def test_wishlist_valuation_requires_auth(self):
        """Test that GET /api/valuation/wishlist requires authentication"""
        # Make request without auth header
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/valuation/wishlist")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"Auth required - returns {response.status_code} without token")

    def test_wishlist_valuation_returns_proper_structure(self):
        """Test that GET /api/valuation/wishlist returns correct response structure"""
        response = self.session.get(f"{BASE_URL}/api/valuation/wishlist")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify required fields exist
        assert "total_value" in data, "Missing 'total_value' field"
        assert "valued_count" in data, "Missing 'valued_count' field"
        assert "total_count" in data, "Missing 'total_count' field"
        
        # Verify types
        assert isinstance(data["total_value"], (int, float)), "total_value should be a number"
        assert isinstance(data["valued_count"], int), "valued_count should be an integer"
        assert isinstance(data["total_count"], int), "total_count should be an integer"
        
        print(f"Response structure correct: {data}")

    def test_wishlist_valuation_values_are_non_negative(self):
        """Test that returned values are non-negative"""
        response = self.session.get(f"{BASE_URL}/api/valuation/wishlist")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_value"] >= 0, "total_value should not be negative"
        assert data["valued_count"] >= 0, "valued_count should not be negative"
        assert data["total_count"] >= 0, "total_count should not be negative"
        
        print(f"All values non-negative: total_value={data['total_value']}, valued_count={data['valued_count']}, total_count={data['total_count']}")

    def test_valued_count_not_exceeds_total_count(self):
        """Test that valued_count doesn't exceed total_count"""
        response = self.session.get(f"{BASE_URL}/api/valuation/wishlist")
        assert response.status_code == 200
        
        data = response.json()
        assert data["valued_count"] <= data["total_count"], "valued_count should not exceed total_count"
        print(f"Valued count ({data['valued_count']}) <= Total count ({data['total_count']})")


class TestISOWishlistStatus:
    """Tests related to ISO items with WISHLIST status"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.user = login_resp.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Could not authenticate: {login_resp.status_code}")

    def test_get_iso_items_endpoint(self):
        """Test that GET /api/iso returns user's ISO items"""
        response = self.session.get(f"{BASE_URL}/api/iso")
        assert response.status_code == 200, f"ISO endpoint failed: {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "ISO response should be a list"
        print(f"Found {len(data)} ISO items")
        
        # Check structure of items if any exist
        if data:
            item = data[0]
            assert "id" in item, "ISO item should have 'id'"
            assert "status" in item, "ISO item should have 'status'"
            print(f"Sample ISO item status: {item.get('status')}")

    def test_iso_items_have_status_field(self):
        """Test that ISO items include status field (OPEN, WISHLIST, FOUND)"""
        response = self.session.get(f"{BASE_URL}/api/iso")
        assert response.status_code == 200
        
        data = response.json()
        valid_statuses = ['OPEN', 'WISHLIST', 'FOUND']
        
        for item in data:
            assert "status" in item, f"ISO item {item.get('id')} missing status"
            assert item["status"] in valid_statuses, f"Invalid status '{item.get('status')}' - expected one of {valid_statuses}"
        
        # Count by status
        status_counts = {}
        for item in data:
            status = item.get("status")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"ISO status distribution: {status_counts}")

    def test_wishlist_items_from_iso_endpoint(self):
        """Test filtering ISO items to get WISHLIST items"""
        response = self.session.get(f"{BASE_URL}/api/iso")
        assert response.status_code == 200
        
        data = response.json()
        wishlist_items = [item for item in data if item.get("status") == "WISHLIST"]
        
        print(f"Found {len(wishlist_items)} WISHLIST items out of {len(data)} total ISOs")
        
        # If we have wishlist items, verify they have expected fields
        for item in wishlist_items:
            assert item.get("artist") or item.get("album"), "Wishlist item should have artist or album"
            print(f"  - {item.get('artist')} - {item.get('album')}")


class TestCollectionValuation:
    """Tests for collection valuation endpoint (for comparison)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Could not authenticate: {login_resp.status_code}")

    def test_collection_valuation_endpoint(self):
        """Test that GET /api/valuation/collection works for comparison"""
        response = self.session.get(f"{BASE_URL}/api/valuation/collection")
        assert response.status_code == 200, f"Collection valuation failed: {response.status_code}"
        
        data = response.json()
        assert "total_value" in data
        assert "valued_count" in data
        assert "total_count" in data
        print(f"Collection valuation: {data}")


class TestCreateWishlistFlow:
    """Test creating a WISHLIST item via move-to-wishlist endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.user = login_resp.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Could not authenticate: {login_resp.status_code}")
        
        self.created_record_id = None
        self.created_iso_id = None

    def teardown_method(self):
        """Clean up created test data"""
        # Delete created ISO if exists
        if self.created_iso_id:
            try:
                self.session.delete(f"{BASE_URL}/api/iso/{self.created_iso_id}")
            except:
                pass
        
        # Delete created record if exists
        if self.created_record_id:
            try:
                self.session.delete(f"{BASE_URL}/api/records/{self.created_record_id}")
            except:
                pass

    def test_move_to_wishlist_creates_wishlist_iso(self):
        """Test that moving a record to wishlist creates ISO with WISHLIST status"""
        # First create a test record
        create_resp = self.session.post(f"{BASE_URL}/api/records", json={
            "artist": "TEST_Wishlist Artist",
            "title": "TEST_Wishlist Album",
            "discogs_id": 12345,
            "cover_url": "https://example.com/cover.jpg"
        })
        
        if create_resp.status_code not in [200, 201]:
            pytest.skip(f"Could not create test record: {create_resp.status_code}")
        
        record = create_resp.json()
        self.created_record_id = record.get("id")
        print(f"Created test record: {self.created_record_id}")
        
        # Move to wishlist
        move_resp = self.session.post(f"{BASE_URL}/api/records/{self.created_record_id}/move-to-wishlist")
        assert move_resp.status_code == 200, f"Move to wishlist failed: {move_resp.status_code} - {move_resp.text}"
        
        move_data = move_resp.json()
        self.created_iso_id = move_data.get("iso_id")
        
        # The record should be deleted, so clear the ID
        self.created_record_id = None
        
        # Verify ISO was created with WISHLIST status
        iso_resp = self.session.get(f"{BASE_URL}/api/iso")
        assert iso_resp.status_code == 200
        
        iso_items = iso_resp.json()
        wishlist_item = next((i for i in iso_items if i.get("id") == self.created_iso_id), None)
        
        if wishlist_item:
            assert wishlist_item.get("status") == "WISHLIST", f"Expected WISHLIST status, got {wishlist_item.get('status')}"
            print(f"Verified ISO {self.created_iso_id} has WISHLIST status")
        else:
            # ISO might have been created - check by artist/album
            for item in iso_items:
                if item.get("artist") == "TEST_Wishlist Artist":
                    self.created_iso_id = item.get("id")
                    assert item.get("status") == "WISHLIST"
                    print(f"Found WISHLIST ISO by artist: {item}")
                    break


class TestWishlistValuationConsistency:
    """Test consistency between ISO list and valuation endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Could not authenticate: {login_resp.status_code}")

    def test_wishlist_count_matches_iso_filter(self):
        """Test that valuation total_count matches WISHLIST ISO count"""
        # Get wishlist valuation
        val_resp = self.session.get(f"{BASE_URL}/api/valuation/wishlist")
        assert val_resp.status_code == 200
        val_data = val_resp.json()
        
        # Get ISO items and count WISHLIST
        iso_resp = self.session.get(f"{BASE_URL}/api/iso")
        assert iso_resp.status_code == 200
        iso_items = iso_resp.json()
        
        wishlist_count_from_iso = len([i for i in iso_items if i.get("status") == "WISHLIST"])
        
        assert val_data["total_count"] == wishlist_count_from_iso, \
            f"Valuation total_count ({val_data['total_count']}) doesn't match ISO WISHLIST count ({wishlist_count_from_iso})"
        
        print(f"Counts match: {val_data['total_count']} WISHLIST items")
