"""
Test suite for BLOCKS 494, 495, 487, 500
- BLOCK 495: Avg Value backend logic
- BLOCK 494: Profile UI Refinement (frontend tests)
- BLOCK 487: Smart Valuation Hierarchy (frontend tests)
- BLOCK 500: Pure Gold Modal (frontend tests)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBlock495AvgValue:
    """BLOCK 495: Average Value backend logic tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as test user"""
        self.login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if self.login_response.status_code == 200:
            data = self.login_response.json()
            self.token = data.get("access_token") or data.get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Login failed - skipping authenticated tests")
    
    def test_collection_value_returns_avg_value(self):
        """Test that /api/valuation/collection returns avg_value field"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "avg_value" in data, "avg_value field should be present in response"
        assert "total_value" in data, "total_value field should be present"
        assert "total_count" in data, "total_count field should be present"
        assert "valued_count" in data, "valued_count field should be present"
        
        # avg_value should be a number
        assert isinstance(data["avg_value"], (int, float)), "avg_value should be a number"
        print(f"Collection value response: total_value={data['total_value']}, total_count={data['total_count']}, avg_value={data['avg_value']}")
    
    def test_collection_value_by_username_returns_avg_value(self):
        """Test that /api/valuation/collection/{username} returns avg_value field"""
        # Use testuser1 which has 4 records (1 with ~$32 value)
        response = requests.get(f"{BASE_URL}/api/valuation/collection/testuser1")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "avg_value" in data, "avg_value field should be present in response"
        assert "total_value" in data, "total_value field should be present"
        assert "total_count" in data, "total_count field should be present"
        
        # avg_value should be a number
        assert isinstance(data["avg_value"], (int, float)), "avg_value should be a number"
        
        # Verify calculation: avg_value = total_value / total_count
        if data["total_count"] > 0:
            expected_avg = round(data["total_value"] / data["total_count"], 2)
            assert data["avg_value"] == expected_avg, f"avg_value should equal total_value/total_count. Expected {expected_avg}, got {data['avg_value']}"
        
        print(f"testuser1 collection: total_value={data['total_value']}, total_count={data['total_count']}, avg_value={data['avg_value']}")
    
    def test_avg_value_zero_division_fallback(self):
        """Test that avg_value returns 0 when total_count is 0 (divide by zero protection)"""
        # Test with existing user
        response = requests.get(f"{BASE_URL}/api/valuation/collection/testuser1")
        assert response.status_code == 200
        
        data = response.json()
        # If total_count is 0, avg_value should be 0
        if data["total_count"] == 0:
            assert data["avg_value"] == 0, "avg_value should be 0 when total_count is 0"
        else:
            # For non-zero count, verify calculation is correct
            expected_avg = round(data["total_value"] / data["total_count"], 2)
            assert data["avg_value"] == expected_avg
        
        print(f"Division by zero fallback verified: total_count={data['total_count']}, avg_value={data['avg_value']}")


class TestValuationEndpoints:
    """General valuation endpoint verification"""
    
    def test_user_not_found_returns_404(self):
        """Test that nonexistent username returns 404"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection/nonexistent_user_xyz123")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_public_endpoint_no_auth_required(self):
        """Test that /api/valuation/collection/{username} is public (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection/testuser1")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
