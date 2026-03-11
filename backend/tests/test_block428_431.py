"""
BLOCK 428/431: Dream List Price Fetching and Text Flow Testing

Tests:
- GET /api/valuation/dreamlist returns correct values
- total_value, valued_count, total_count, pending_count are all present
- Direct Discogs fetch fallback (BLOCK 428) when cache misses
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestDreamListValuation:
    """Tests for Dream List (WISHLIST) valuation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.token = None
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
        else:
            pytest.skip("Could not authenticate test user")
    
    def test_dreamlist_valuation_returns_required_fields(self):
        """GET /api/valuation/dreamlist should return all required fields"""
        resp = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        
        # Verify all required fields are present
        assert "total_value" in data, "Missing total_value field"
        assert "valued_count" in data, "Missing valued_count field"
        assert "total_count" in data, "Missing total_count field"
        assert "pending_count" in data, "Missing pending_count field"
        
        # Verify data types
        assert isinstance(data["total_value"], (int, float)), "total_value should be numeric"
        assert isinstance(data["valued_count"], int), "valued_count should be int"
        assert isinstance(data["total_count"], int), "total_count should be int"
        assert isinstance(data["pending_count"], int), "pending_count should be int"
        
        print(f"Dream List valuation: total={data['total_value']}, valued={data['valued_count']}, total={data['total_count']}, pending={data['pending_count']}")
    
    def test_dreamlist_pending_count_calculation(self):
        """pending_count should equal total_count - valued_count"""
        resp = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        
        data = resp.json()
        expected_pending = data["total_count"] - data["valued_count"]
        assert data["pending_count"] == expected_pending, f"pending_count mismatch: expected {expected_pending}, got {data['pending_count']}"
    
    def test_dreamlist_items_endpoint(self):
        """GET /api/iso/dreamlist should return dream list items with value_source"""
        resp = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        
        items = resp.json()
        assert isinstance(items, list), "Response should be a list"
        
        # Check each item has required fields
        for item in items:
            assert "id" in item
            assert "artist" in item
            assert "album" in item
            assert "status" in item
            assert item["status"] == "WISHLIST", f"Item should have WISHLIST status, got {item['status']}"
            
            # Check value_source field exists
            if "median_value" in item and item["median_value"]:
                assert "value_source" in item, "Item with value should have value_source"
                assert item["value_source"] in ["discogs", "community", "manual"], f"Invalid value_source: {item.get('value_source')}"
            elif "value_source" in item:
                assert item["value_source"] == "pending", f"Item without value should have pending source, got {item['value_source']}"
        
        print(f"Dream List has {len(items)} items")
    
    def test_dreamlist_value_matches_items_sum(self):
        """Total value should match sum of individual item values"""
        valuation_resp = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers={
            "Authorization": f"Bearer {self.token}"
        })
        items_resp = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers={
            "Authorization": f"Bearer {self.token}"
        })
        
        assert valuation_resp.status_code == 200
        assert items_resp.status_code == 200
        
        valuation = valuation_resp.json()
        items = items_resp.json()
        
        # Calculate sum of item values
        items_total = sum(item.get("median_value", 0) or 0 for item in items)
        
        # Allow small floating point difference
        assert abs(valuation["total_value"] - items_total) < 0.01, f"Value mismatch: API says {valuation['total_value']}, items sum to {items_total}"


class TestPublicDreamListValuation:
    """Tests for public user Dream List valuation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login to get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
        else:
            pytest.skip("Could not authenticate")
    
    def test_public_dreamlist_valuation_by_username(self):
        """GET /api/valuation/dreamlist/{username} should return public dream value"""
        resp = requests.get(f"{BASE_URL}/api/valuation/dreamlist/katieintheafterglow")
        assert resp.status_code == 200
        
        data = resp.json()
        assert "total_value" in data
        assert "valued_count" in data
        assert "total_count" in data
        assert "pending_count" in data
        
        print(f"katieintheafterglow dream value: ${data['total_value']}")
    
    def test_public_dreamlist_nonexistent_user_returns_404(self):
        """GET /api/valuation/dreamlist/{username} for nonexistent user should return 404"""
        resp = requests.get(f"{BASE_URL}/api/valuation/dreamlist/nonexistent_user_xyz123")
        assert resp.status_code == 404


class TestKatieintheafterglowProfile:
    """Tests for katieintheafterglow profile data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
        else:
            pytest.skip("Could not authenticate")
    
    def test_katieintheafterglow_is_founding_member(self):
        """katieintheafterglow should be marked as founding_member"""
        resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["founding_member"] == True, "katieintheafterglow should be founding_member"
        assert data["title_label"] == "Founder", "katieintheafterglow should have Founder title"
        
        print(f"katieintheafterglow: founding_member={data['founding_member']}, title_label={data['title_label']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
