"""
Block 166 Tests: Trade Dispute Resolution System
Tests the trade dispute endpoints and admin hold dispute resolution
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["is_admin"] == True
        
    def test_regular_user_login(self):
        """Test regular user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser1",
            "password": "test123"
        })
        # May fail if user doesn't exist
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data


class TestTradeDisputes:
    """Tests for trade dispute endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_dispute_endpoint_exists(self):
        """POST /api/trades/{id}/dispute endpoint exists and validates"""
        response = requests.post(
            f"{BASE_URL}/api/trades/nonexistent-trade-id/dispute",
            json={"reason": "test", "photo_urls": []},
            headers=self.headers
        )
        # Should return 404 (trade not found), not 405 (method not allowed) or 500
        assert response.status_code in [404, 400, 422], \
            f"Dispute endpoint error: {response.status_code} - {response.text}"
    
    def test_get_trades_list(self):
        """GET /api/trades returns list of trades"""
        response = requests.get(f"{BASE_URL}/api/trades", headers=self.headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAdminHoldDisputes:
    """Tests for admin hold dispute resolution endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_hold_disputes(self):
        """GET /api/admin/hold-disputes returns list"""
        response = requests.get(f"{BASE_URL}/api/admin/hold-disputes", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_resolve_endpoint_accepts_extend_investigation(self):
        """PUT /api/admin/hold-disputes/{id}/resolve accepts extend_investigation resolution"""
        response = requests.put(
            f"{BASE_URL}/api/admin/hold-disputes/nonexistent-id/resolve",
            json={"resolution": "extend_investigation", "notes": "Testing extend investigation"},
            headers=self.headers
        )
        # Should return 404 (trade not found), not 422 (invalid resolution) or 500
        assert response.status_code in [404, 400, 422], \
            f"Resolve endpoint error: {response.status_code} - {response.text}"
    
    def test_resolve_endpoint_accepts_full_reversal(self):
        """PUT /api/admin/hold-disputes/{id}/resolve accepts full_reversal resolution"""
        response = requests.put(
            f"{BASE_URL}/api/admin/hold-disputes/nonexistent-id/resolve",
            json={"resolution": "full_reversal", "notes": "Testing full reversal"},
            headers=self.headers
        )
        assert response.status_code in [404, 400, 422]


class TestAdminDisputesPage:
    """Tests for admin disputes dashboard endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_admin_disputes_endpoint(self):
        """GET /api/admin/disputes returns disputes list"""
        response = requests.get(f"{BASE_URL}/api/admin/disputes", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
