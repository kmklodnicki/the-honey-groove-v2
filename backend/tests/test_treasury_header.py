"""
Backend tests for Treasury Header feature - BLOCK 72.1
Tests valuation endpoints that power the Treasury dashboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for demo user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@test.com",
        "password": "demouser"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def headers(auth_token):
    """Auth headers fixture"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestCollectionValuation:
    """Tests for /api/valuation/collection endpoint - powers Collection Value in Treasury"""
    
    def test_collection_valuation_returns_200(self, headers):
        """Collection valuation endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection", headers=headers)
        assert response.status_code == 200
        
    def test_collection_valuation_structure(self, headers):
        """Collection valuation should return total_value, valued_count, total_count"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection", headers=headers)
        data = response.json()
        
        assert "total_value" in data, "Missing total_value field"
        assert "valued_count" in data, "Missing valued_count field"
        assert "total_count" in data, "Missing total_count field"
        
        # Verify types
        assert isinstance(data["total_value"], (int, float))
        assert isinstance(data["valued_count"], int)
        assert isinstance(data["total_count"], int)
        
    def test_demouser_has_collection_value(self, headers):
        """Demouser should have collection value > 0 (seeded with Igor records)"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection", headers=headers)
        data = response.json()
        
        # Demouser is seeded with 3 Igor records valued at ~$156
        assert data["total_value"] > 0, "Demouser should have positive collection value"
        assert data["valued_count"] > 0, "Demouser should have valued records"
        assert data["total_count"] > 0, "Demouser should have records in collection"
        
        print(f"Collection Value: ${data['total_value']}, Valued: {data['valued_count']}/{data['total_count']}")


class TestDreamlistValuation:
    """Tests for /api/valuation/dreamlist endpoint - powers Dream Records in Treasury"""
    
    def test_dreamlist_valuation_returns_200(self, headers):
        """Dreamlist valuation endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=headers)
        assert response.status_code == 200
        
    def test_dreamlist_valuation_structure(self, headers):
        """Dreamlist valuation should return total_value, valued_count, total_count"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=headers)
        data = response.json()
        
        assert "total_value" in data, "Missing total_value field"
        assert "valued_count" in data, "Missing valued_count field"
        assert "total_count" in data, "Missing total_count field"
        
    def test_dreamlist_zero_for_user_with_no_dreams(self, headers):
        """User with no dream items should have $0 dream value"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=headers)
        data = response.json()
        
        # If user has no wishlist items, all values should be 0
        if data["total_count"] == 0:
            assert data["total_value"] == 0, "Empty dreamlist should have $0 value"
            assert data["valued_count"] == 0, "Empty dreamlist should have 0 valued"
            print("Dreamlist is empty - $0 value confirmed")
        else:
            print(f"User has dream items - Value: ${data['total_value']}")


class TestRefreshEndpoint:
    """Tests for /api/valuation/refresh endpoint - powers Refresh button in Treasury"""
    
    def test_refresh_returns_200(self, headers):
        """Refresh endpoint should return 200"""
        response = requests.post(f"{BASE_URL}/api/valuation/refresh", headers=headers)
        assert response.status_code == 200
        
    def test_refresh_returns_message(self, headers):
        """Refresh should return message and queued count"""
        response = requests.post(f"{BASE_URL}/api/valuation/refresh", headers=headers)
        data = response.json()
        
        assert "message" in data, "Missing message field"
        assert "queued" in data, "Missing queued field"
        
        print(f"Refresh response: {data['message']}, queued: {data['queued']}")


class TestUnauthorizedAccess:
    """Tests for endpoint auth requirements"""
    
    def test_collection_requires_auth(self):
        """Collection valuation should require authentication"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection")
        assert response.status_code in [401, 403], "Should require auth"
        
    def test_dreamlist_requires_auth(self):
        """Dreamlist valuation should require authentication"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist")
        assert response.status_code in [401, 403], "Should require auth"
        
    def test_refresh_requires_auth(self):
        """Refresh endpoint should require authentication"""
        response = requests.post(f"{BASE_URL}/api/valuation/refresh")
        assert response.status_code in [401, 403], "Should require auth"
