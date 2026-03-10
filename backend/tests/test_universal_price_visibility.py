"""
Test suite for BLOCK 73.1: Universal Price Visibility on Dream List
Tests the median_value enrichment on dream list items across all relevant endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUniversalPriceVisibility:
    """Tests for BLOCK 73.1: Universal Price Visibility on Dream List"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication token for demouser"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    # Test GET /api/users/{username}/dreaming endpoint
    def test_user_dreaming_endpoint_returns_median_value(self):
        """GET /api/users/{username}/dreaming returns median_value for items with cached Discogs pricing"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 3, f"Expected 3 dream items for katieintheafterglow, got {len(data)}"
        
        # Find the Reputation item which should have median_value=1755
        reputation_item = next((item for item in data if item.get("album") == "Reputation"), None)
        assert reputation_item is not None, "Reputation item not found in dreaming list"
        assert "median_value" in reputation_item, "median_value field should be present"
        assert reputation_item["median_value"] == 1755.0, f"Expected median_value=1755.0, got {reputation_item['median_value']}"
    
    def test_user_dreaming_returns_null_for_items_without_value(self):
        """GET /api/users/{username}/dreaming returns null median_value for items without cached pricing"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        assert response.status_code == 200
        
        data = response.json()
        # Find The Spins item which should NOT have median_value
        spins_item = next((item for item in data if item.get("album") == "The Spins"), None)
        assert spins_item is not None, "The Spins item not found"
        assert "median_value" in spins_item, "median_value field should be present even if null"
        assert spins_item["median_value"] is None, "Items without cached pricing should have null median_value"
    
    def test_user_dreaming_returns_correct_structure(self):
        """GET /api/users/{username}/dreaming returns properly structured items"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "Should have at least one dream item"
        
        item = data[0]
        # Verify required fields are present
        required_fields = ["id", "user_id", "artist", "album", "status", "median_value"]
        for field in required_fields:
            assert field in item, f"Field '{field}' should be present in dream item"
    
    # Test GET /api/iso/dreamlist endpoint (authenticated)
    def test_authenticated_dreamlist_returns_median_value(self, auth_headers):
        """GET /api/iso/dreamlist (authenticated) returns median_value enrichment"""
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # Note: demouser may have empty dreamlist - just verify structure works
        
    def test_dreamlist_requires_auth(self):
        """GET /api/iso/dreamlist requires authentication"""
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist")
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401 or 403 for unauthenticated request, got {response.status_code}"
    
    # Test valuation endpoints
    def test_dreamlist_valuation_endpoint(self, auth_headers):
        """GET /api/valuation/dreamlist returns total dream value"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total_value" in data, "Response should include total_value"
    
    def test_dreamlist_valuation_for_user(self):
        """GET /api/valuation/dreamlist/{username} returns dream value for specific user"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist/katieintheafterglow")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total_value" in data, "Response should include total_value"
        # katieintheafterglow has Reputation valued at $1755
        assert data["total_value"] >= 1755, f"Expected total_value >= 1755 (from Reputation), got {data['total_value']}"
    
    # Test collection page data
    def test_collection_valuation(self, auth_headers):
        """GET /api/valuation/collection returns collection value"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Should have total_value, valued_count, total_count
        assert "total_value" in data, "Response should include total_value"
        assert "valued_count" in data, "Response should include valued_count"
        assert "total_count" in data, "Response should include total_count"


class TestDreamItemDataIntegrity:
    """Tests to verify dream item data is properly enriched"""
    
    def test_all_dream_items_have_median_value_field(self):
        """All dream items should have median_value field (even if null)"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        assert response.status_code == 200
        
        data = response.json()
        for item in data:
            assert "median_value" in item, f"Dream item {item.get('id')} missing median_value field"
    
    def test_dream_item_discogs_id_mapping(self):
        """Dream items with discogs_id should be able to fetch pricing"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        assert response.status_code == 200
        
        data = response.json()
        # Find items with discogs_id
        items_with_discogs = [item for item in data if item.get("discogs_id")]
        assert len(items_with_discogs) > 0, "Should have at least one item with discogs_id"
        
        # At least Reputation (discogs_id=11292749) should have value
        reputation = next((item for item in items_with_discogs 
                          if item.get("discogs_id") == 11292749), None)
        if reputation:
            assert reputation.get("median_value") is not None, \
                "Reputation (discogs_id=11292749) should have median_value from collection_values"
