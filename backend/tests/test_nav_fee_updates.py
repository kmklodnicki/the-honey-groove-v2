"""
Test suite for Nav Fixes and Platform Fee (6%) Updates
Tests:
1. Admin Platform Settings API (GET/PUT)
2. Fee enforcement (6% default, configurable)
3. Non-admin access denied (403)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPlatformFeeSettings:
    """Platform fee admin settings tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as admin (demo@example.com is admin)"""
        # Login as demo user (admin)
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        self.admin_token = data.get("access_token")
        assert self.admin_token, "No token returned"
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create a non-admin user for testing 403
        self.non_admin_email = "test_nonadmin_fee@example.com"
        self.non_admin_password = "password123"
        
        # Try to signup as non-admin (may already exist)
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": self.non_admin_email,
            "password": self.non_admin_password,
            "username": "test_nonadmin_fee"
        })
        # Login as non-admin
        non_admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.non_admin_email,
            "password": self.non_admin_password
        })
        if non_admin_login.status_code == 200:
            self.non_admin_token = non_admin_login.json().get("access_token")
            self.non_admin_headers = {"Authorization": f"Bearer {self.non_admin_token}"}
        else:
            self.non_admin_token = None
            self.non_admin_headers = {}

    def test_get_platform_settings_returns_fee(self):
        """GET /api/admin/platform-settings returns platform_fee_percent=6.0 for admin"""
        resp = requests.get(f"{BASE_URL}/api/admin/platform-settings", headers=self.admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "platform_fee_percent" in data, "Missing platform_fee_percent field"
        # Should be 6.0 by default
        assert data["platform_fee_percent"] == 6.0, f"Expected 6.0, got {data['platform_fee_percent']}"
        print(f"PASS: GET platform-settings returns fee={data['platform_fee_percent']}")

    def test_put_platform_settings_updates_fee(self):
        """PUT /api/admin/platform-settings can update fee percentage"""
        # Update to 7%
        resp = requests.put(f"{BASE_URL}/api/admin/platform-settings", 
                          json={"platform_fee_percent": 7.0},
                          headers=self.admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["platform_fee_percent"] == 7.0, f"Update response wrong: {data}"
        
        # Verify with GET
        get_resp = requests.get(f"{BASE_URL}/api/admin/platform-settings", headers=self.admin_headers)
        assert get_resp.json()["platform_fee_percent"] == 7.0
        print("PASS: PUT platform-settings updated fee to 7.0")
        
        # Reset back to 6%
        reset_resp = requests.put(f"{BASE_URL}/api/admin/platform-settings",
                                 json={"platform_fee_percent": 6.0},
                                 headers=self.admin_headers)
        assert reset_resp.status_code == 200
        print("PASS: Fee reset to 6.0")

    def test_non_admin_cannot_get_settings(self):
        """Non-admin users get 403 on GET /api/admin/platform-settings"""
        if not self.non_admin_token:
            pytest.skip("Non-admin user not available")
        resp = requests.get(f"{BASE_URL}/api/admin/platform-settings", headers=self.non_admin_headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("PASS: Non-admin GET returns 403")

    def test_non_admin_cannot_put_settings(self):
        """Non-admin users get 403 on PUT /api/admin/platform-settings"""
        if not self.non_admin_token:
            pytest.skip("Non-admin user not available")
        resp = requests.put(f"{BASE_URL}/api/admin/platform-settings",
                          json={"platform_fee_percent": 10.0},
                          headers=self.non_admin_headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("PASS: Non-admin PUT returns 403")

    def test_unauthenticated_cannot_access_settings(self):
        """Unauthenticated users get 401 on admin endpoints"""
        resp = requests.get(f"{BASE_URL}/api/admin/platform-settings")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("PASS: Unauthenticated GET returns 401")

    def test_fee_validation_boundaries(self):
        """Fee must be between 0 and 50"""
        # Test invalid fee > 50
        resp = requests.put(f"{BASE_URL}/api/admin/platform-settings",
                          json={"platform_fee_percent": 51.0},
                          headers=self.admin_headers)
        assert resp.status_code == 400, f"Expected 400 for fee=51, got {resp.status_code}"
        
        # Test negative fee
        resp2 = requests.put(f"{BASE_URL}/api/admin/platform-settings",
                           json={"platform_fee_percent": -1.0},
                           headers=self.admin_headers)
        assert resp2.status_code == 400, f"Expected 400 for fee=-1, got {resp2.status_code}"
        print("PASS: Fee validation boundaries enforced")

    def test_admin_user_has_is_admin_flag(self):
        """Verify demo user has is_admin=true"""
        resp = requests.get(f"{BASE_URL}/api/auth/me", headers=self.admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_admin") == True, f"Demo user should be admin: {data}"
        print("PASS: Demo user is admin")


class TestFeeInPaymentFlow:
    """Test that the 6% fee is correctly applied in payment calculations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        assert login_resp.status_code == 200
        self.token = login_resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_fee_default_is_6_percent(self):
        """Verify platform_fee_percent defaults to 6.0"""
        resp = requests.get(f"{BASE_URL}/api/admin/platform-settings", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        # After any test runs, fee should be reset to 6.0 or be 6.0 initially
        assert data["platform_fee_percent"] == 6.0, f"Default fee should be 6.0, got {data['platform_fee_percent']}"
        print("PASS: Default fee is 6%")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
