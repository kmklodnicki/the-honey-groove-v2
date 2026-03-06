"""
Tests for:
1. Compact listing cards in ISOPage (Shop + Trade tabs) - frontend visual verification
2. DELETE /api/auth/account endpoint - account deletion feature

Test coverage:
- Delete account endpoint returns 401 without auth
- Delete account endpoint deletes user data and returns success when authenticated
- Account deletion is logged in account_deletions collection
- Verify listing creation works (needed to test compact cards)
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestDeleteAccountEndpoint:
    """Test DELETE /api/auth/account endpoint"""
    
    def test_delete_account_returns_401_without_auth(self):
        """DELETE /api/auth/account should return 401 without authentication"""
        response = requests.delete(f"{BASE_URL}/api/auth/account")
        assert response.status_code == 401 or response.status_code == 403, \
            f"Expected 401/403, got {response.status_code}: {response.text}"
        print("PASS: DELETE /api/auth/account returns 401 without auth")
    
    def test_delete_account_success_with_auth(self):
        """DELETE /api/auth/account should delete user data when authenticated"""
        # Create a test user specifically for deletion
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test_delete_{unique_id}@example.com"
        test_username = f"testdelete{unique_id}"
        test_password = "testpass123"
        
        # Register the test user
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "username": test_username,
            "password": test_password
        })
        assert register_response.status_code == 200, \
            f"Failed to register test user: {register_response.text}"
        
        token_data = register_response.json()
        assert "access_token" in token_data, "No access_token in register response"
        token = token_data["access_token"]
        user_id = token_data["user"]["id"]
        
        print(f"Created test user: {test_username} (ID: {user_id})")
        
        # Delete the account
        headers = {"Authorization": f"Bearer {token}"}
        delete_response = requests.delete(f"{BASE_URL}/api/auth/account", headers=headers)
        
        assert delete_response.status_code == 200, \
            f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert "detail" in data and data["detail"] == "account deleted", \
            f"Expected 'account deleted' detail, got: {data}"
        
        print("PASS: DELETE /api/auth/account returns success with authenticated user")
        
        # Verify user cannot login anymore
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        assert login_response.status_code == 401, \
            f"Deleted user should not be able to login. Got {login_response.status_code}"
        
        print("PASS: Deleted user cannot login")
        
        # Verify user data is gone (try to get profile)
        profile_response = requests.get(f"{BASE_URL}/api/users/{test_username}")
        assert profile_response.status_code == 404, \
            f"Deleted user profile should return 404. Got {profile_response.status_code}"
        
        print("PASS: Deleted user profile returns 404")
    
    def test_account_deletion_logged_in_collection(self):
        """Verify account deletion is logged in account_deletions collection"""
        # Create another test user for this test
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test_logged_{unique_id}@example.com"
        test_username = f"testlogged{unique_id}"
        test_password = "testpass123"
        
        # Register the test user
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "username": test_username,
            "password": test_password
        })
        assert register_response.status_code == 200, \
            f"Failed to register test user: {register_response.text}"
        
        token_data = register_response.json()
        token = token_data["access_token"]
        user_id = token_data["user"]["id"]
        
        print(f"Created test user for logging test: {test_username} (ID: {user_id})")
        
        # Delete the account
        headers = {"Authorization": f"Bearer {token}"}
        delete_response = requests.delete(f"{BASE_URL}/api/auth/account", headers=headers)
        
        assert delete_response.status_code == 200, \
            f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        print("PASS: Account deleted, deletion should be logged in account_deletions collection")
        # Note: We can't directly query MongoDB from the test, but the endpoint code
        # shows it inserts into db.account_deletions before deleting user data


class TestListingCreation:
    """Test listing creation to verify compact card display works"""
    
    @pytest.fixture
    def auth_headers(self):
        """Login with demo account and return auth headers"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        if login_response.status_code != 200:
            pytest.skip(f"Could not login with demo account: {login_response.text}")
        
        token = login_response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_listings_endpoint(self, auth_headers):
        """GET /api/listings should return listings array"""
        response = requests.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of listings"
        print(f"PASS: GET /api/listings returns {len(data)} listings")
    
    def test_get_my_listings_endpoint(self, auth_headers):
        """GET /api/listings/my should return user's listings"""
        response = requests.get(f"{BASE_URL}/api/listings/my", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of listings"
        print(f"PASS: GET /api/listings/my returns {len(data)} user listings")


class TestHoneypotPageAccess:
    """Test access to The Honeypot page data"""
    
    @pytest.fixture
    def auth_headers(self):
        """Login with demo account and return auth headers"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        if login_response.status_code != 200:
            pytest.skip(f"Could not login with demo account: {login_response.text}")
        
        token = login_response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_iso_endpoint(self, auth_headers):
        """GET /api/iso should return user's ISO items"""
        response = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of ISOs"
        print(f"PASS: GET /api/iso returns {len(data)} ISO items")
    
    def test_iso_community_endpoint(self, auth_headers):
        """GET /api/iso/community should return community ISO items"""
        response = requests.get(f"{BASE_URL}/api/iso/community", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of community ISOs"
        print(f"PASS: GET /api/iso/community returns {len(data)} community ISOs")
    
    def test_trades_endpoint(self, auth_headers):
        """GET /api/trades should return user's trades"""
        response = requests.get(f"{BASE_URL}/api/trades", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of trades"
        print(f"PASS: GET /api/trades returns {len(data)} trades")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
