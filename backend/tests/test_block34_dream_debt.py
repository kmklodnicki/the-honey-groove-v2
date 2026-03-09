"""
Tests for BLOCK 34.1-34.3: Dream Debt and Reality Header features
- GET /api/valuation/record-value/{discogs_id} - returns median value for single release
- GET /api/valuation/wishlist - returns wishlist total value
- GET /api/valuation/collection - returns collection total value
- PUT /api/iso/{id}/promote - promotes wishlist item to wantlist (Bring to Reality)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_CREDENTIALS = {"email": "admin@thehoneygroove.com", "password": "admin123"}


class TestAuth:
    """Authentication fixture tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Auth headers for requests"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestRecordValueEndpoint(TestAuth):
    """Tests for GET /api/valuation/record-value/{discogs_id} - BLOCK 34.3"""
    
    def test_record_value_returns_200(self, auth_headers):
        """GET /api/valuation/record-value/{discogs_id} returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/record-value/12345",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
    def test_record_value_returns_median_value(self, auth_headers):
        """Response contains median_value field"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/record-value/12345",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "median_value" in data, "Response should contain median_value"
        assert isinstance(data["median_value"], (int, float)), "median_value should be numeric"
        
    def test_record_value_requires_auth(self):
        """Endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/valuation/record-value/12345")
        assert response.status_code == 401, "Should require authentication"
        
    def test_record_value_with_invalid_discogs_id(self, auth_headers):
        """Non-existent discogs_id returns median_value: 0 (no cached data)"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/record-value/999999999",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("median_value") == 0, "Should return 0 for non-cached release"


class TestWishlistValueEndpoint(TestAuth):
    """Tests for GET /api/valuation/wishlist - BLOCK 34.1"""
    
    def test_wishlist_value_returns_200(self, auth_headers):
        """GET /api/valuation/wishlist returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/wishlist",
            headers=auth_headers
        )
        assert response.status_code == 200
        
    def test_wishlist_value_response_structure(self, auth_headers):
        """Response contains required fields"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/wishlist",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data, "Should have total_value"
        assert "valued_count" in data, "Should have valued_count"
        assert "total_count" in data, "Should have total_count"
        
    def test_wishlist_value_requires_auth(self):
        """Endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/valuation/wishlist")
        assert response.status_code == 401


class TestCollectionValueEndpoint(TestAuth):
    """Tests for GET /api/valuation/collection - BLOCK 34.2"""
    
    def test_collection_value_returns_200(self, auth_headers):
        """GET /api/valuation/collection returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/collection",
            headers=auth_headers
        )
        assert response.status_code == 200
        
    def test_collection_value_response_structure(self, auth_headers):
        """Response contains required fields"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/collection",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data, "Should have total_value"
        assert "valued_count" in data, "Should have valued_count"
        assert "total_count" in data, "Should have total_count"


class TestBringToRealityEndpoint(TestAuth):
    """Tests for PUT /api/iso/{id}/promote - BLOCK 34.3 'Bring to Reality' button"""
    
    @pytest.fixture
    def wishlist_item(self, auth_headers):
        """Create a wishlist item (status: WISHLIST) for testing"""
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(
            f"{BASE_URL}/api/iso",
            json={
                "artist": f"TEST_Dream_{unique_id}",
                "album": f"TEST_Dream_Album_{unique_id}",
                "status": "WISHLIST",
                "notes": "Test wishlist item for promote test"
            },
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201], f"Failed to create ISO: {create_response.text}"
        item = create_response.json()
        yield item
        # Cleanup: try to delete the item
        requests.delete(f"{BASE_URL}/api/iso/{item['id']}", headers=auth_headers)
    
    def test_promote_wishlist_to_wantlist(self, auth_headers, wishlist_item):
        """PUT /api/iso/{id}/promote changes status from WISHLIST to OPEN"""
        iso_id = wishlist_item["id"]
        response = requests.put(
            f"{BASE_URL}/api/iso/{iso_id}/promote",
            headers=auth_headers,
            json={}
        )
        assert response.status_code == 200, f"Promote failed: {response.text}"
        
        # Verify the item status changed
        get_response = requests.get(f"{BASE_URL}/api/iso/{iso_id}", headers=auth_headers)
        if get_response.status_code == 200:
            data = get_response.json()
            assert data.get("status") == "OPEN", "Status should be OPEN after promote"
            
    def test_promote_requires_auth(self, wishlist_item):
        """Promote endpoint requires authentication"""
        response = requests.put(f"{BASE_URL}/api/iso/{wishlist_item['id']}/promote", json={})
        assert response.status_code == 401
        
    def test_promote_nonexistent_item_returns_404(self, auth_headers):
        """Promoting non-existent item returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.put(
            f"{BASE_URL}/api/iso/{fake_id}/promote",
            headers=auth_headers,
            json={}
        )
        assert response.status_code == 404


class TestHiddenGemsEndpoint(TestAuth):
    """Tests for hidden gems (top valuable records) used in Reality tab"""
    
    def test_hidden_gems_returns_200(self, auth_headers):
        """GET /api/valuation/hidden-gems returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/hidden-gems",
            headers=auth_headers
        )
        assert response.status_code == 200
        
    def test_hidden_gems_returns_list(self, auth_headers):
        """Response is a list"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/hidden-gems",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
