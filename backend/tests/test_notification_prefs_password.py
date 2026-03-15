"""
Test notification preferences and password update features.
Features tested:
1. PUT /api/auth/me with notification_preference field
2. GET /api/auth/me returns notification_preference in response
3. PUT /api/auth/update-password works with correct current_password
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "HoneyGroove2026"


class TestNotificationPreferences:
    """Test notification_preference field in user model."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for admin user."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response missing access_token field"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API requests."""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_me_includes_notification_preference(self, auth_headers):
        """GET /api/auth/me should include notification_preference in response."""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200, f"GET /api/auth/me failed: {response.text}"
        data = response.json()
        assert "notification_preference" in data, "Response missing notification_preference field"
        assert data["notification_preference"] in ["all", "following", "none"], \
            f"Invalid notification_preference value: {data['notification_preference']}"
        print(f"GET /api/auth/me returns notification_preference: {data['notification_preference']}")
    
    def test_update_notification_preference_following(self, auth_headers):
        """PUT /api/auth/me with notification_preference='following' should update and return new value."""
        response = requests.put(
            f"{BASE_URL}/api/auth/me", 
            headers=auth_headers,
            json={"notification_preference": "following"}
        )
        assert response.status_code == 200, f"PUT /api/auth/me failed: {response.text}"
        data = response.json()
        assert data.get("notification_preference") == "following", \
            f"Expected notification_preference='following', got '{data.get('notification_preference')}'"
        print("PUT notification_preference='following' - PASS")
    
    def test_update_notification_preference_none(self, auth_headers):
        """PUT /api/auth/me with notification_preference='none' should update and return 'none'."""
        response = requests.put(
            f"{BASE_URL}/api/auth/me", 
            headers=auth_headers,
            json={"notification_preference": "none"}
        )
        assert response.status_code == 200, f"PUT /api/auth/me failed: {response.text}"
        data = response.json()
        assert data.get("notification_preference") == "none", \
            f"Expected notification_preference='none', got '{data.get('notification_preference')}'"
        print("PUT notification_preference='none' - PASS")
    
    def test_update_notification_preference_all(self, auth_headers):
        """PUT /api/auth/me with notification_preference='all' should update and return 'all'."""
        response = requests.put(
            f"{BASE_URL}/api/auth/me", 
            headers=auth_headers,
            json={"notification_preference": "all"}
        )
        assert response.status_code == 200, f"PUT /api/auth/me failed: {response.text}"
        data = response.json()
        assert data.get("notification_preference") == "all", \
            f"Expected notification_preference='all', got '{data.get('notification_preference')}'"
        print("PUT notification_preference='all' - PASS")
    
    def test_verify_notification_preference_persisted(self, auth_headers):
        """Verify the notification_preference is persisted after update."""
        # First update to a known value
        requests.put(
            f"{BASE_URL}/api/auth/me",
            headers=auth_headers,
            json={"notification_preference": "following"}
        )
        # Then GET to verify persistence
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("notification_preference") == "following", \
            f"notification_preference not persisted. Expected 'following', got '{data.get('notification_preference')}'"
        print("Notification preference persistence verified - PASS")
        # Reset to 'all'
        requests.put(
            f"{BASE_URL}/api/auth/me",
            headers=auth_headers,
            json={"notification_preference": "all"}
        )


class TestPasswordUpdate:
    """Test PUT /api/auth/update-password endpoint."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for admin user."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API requests."""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_update_password_wrong_current(self, auth_headers):
        """PUT /api/auth/update-password with wrong current_password should fail."""
        response = requests.put(
            f"{BASE_URL}/api/auth/update-password",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword123",
                "new_password": "NewPassword123"
            }
        )
        assert response.status_code == 400, f"Expected 400 for wrong password, got {response.status_code}"
        data = response.json()
        assert "incorrect" in data.get("detail", "").lower() or "invalid" in data.get("detail", "").lower(), \
            f"Expected error about incorrect password, got: {data}"
        print("PUT /api/auth/update-password with wrong current_password - correctly returns 400")
    
    def test_update_password_missing_fields(self, auth_headers):
        """PUT /api/auth/update-password with missing fields should fail."""
        response = requests.put(
            f"{BASE_URL}/api/auth/update-password",
            headers=auth_headers,
            json={"current_password": ADMIN_PASSWORD}  # Missing new_password
        )
        assert response.status_code == 400, f"Expected 400 for missing fields, got {response.status_code}"
        print("PUT /api/auth/update-password with missing new_password - correctly returns 400")
    
    def test_update_password_too_short(self, auth_headers):
        """PUT /api/auth/update-password with short new_password should fail."""
        response = requests.put(
            f"{BASE_URL}/api/auth/update-password",
            headers=auth_headers,
            json={
                "current_password": ADMIN_PASSWORD,
                "new_password": "12345"  # Less than 6 chars
            }
        )
        assert response.status_code == 400, f"Expected 400 for short password, got {response.status_code}"
        print("PUT /api/auth/update-password with short password - correctly returns 400")
    
    def test_update_password_success(self, auth_headers):
        """PUT /api/auth/update-password with correct current_password should succeed."""
        # Note: We'll change to a new password and then change back to avoid breaking future tests
        new_temp_password = "TempPassword2026"
        
        # Change to temp password
        response = requests.put(
            f"{BASE_URL}/api/auth/update-password",
            headers=auth_headers,
            json={
                "current_password": ADMIN_PASSWORD,
                "new_password": new_temp_password
            }
        )
        assert response.status_code == 200, f"Password update failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status='ok', got: {data}"
        print("PUT /api/auth/update-password successful (changed to temp password)")
        
        # Verify can login with new password
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": new_temp_password
        })
        assert login_response.status_code == 200, "Cannot login with new password"
        new_token = login_response.json()["access_token"]
        print("Verified login works with new password")
        
        # Change back to original password
        revert_response = requests.put(
            f"{BASE_URL}/api/auth/update-password",
            headers={"Authorization": f"Bearer {new_token}"},
            json={
                "current_password": new_temp_password,
                "new_password": ADMIN_PASSWORD
            }
        )
        assert revert_response.status_code == 200, f"Password revert failed: {revert_response.text}"
        print("Password reverted back to original successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
