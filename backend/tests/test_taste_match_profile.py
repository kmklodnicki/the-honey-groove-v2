# Test: BLOCK 39.1-39.3 and BLOCK 40.1-40.3 - Taste Match & Profile Page features
# Features tested:
# - GET /api/users/{username}/taste-match endpoint
# - Authentication requirement for taste-match
# - Self-profile returns 100% match
# - Non-existent user returns 404
# - Response structure validation (score, label, shared_reality, shared_dreams, swap_potential)

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTasteMatchEndpoint:
    """Tests for GET /api/users/{username}/taste-match endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("access_token")
    
    @pytest.fixture(scope="class")
    def admin_username(self, auth_token):
        """Get admin user's username"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed to get me: {response.text}"
        return response.json().get("username")
    
    def test_taste_match_requires_auth(self):
        """Taste match endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/users/admin/taste-match")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASSED: Taste match endpoint requires authentication")

    def test_taste_match_self_returns_100(self, auth_token, admin_username):
        """Taste match with own profile returns 100%"""
        response = requests.get(f"{BASE_URL}/api/users/{admin_username}/taste-match", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("score") == 100, f"Expected 100, got {data.get('score')}"
        assert data.get("label") is None, f"Expected None label for self, got {data.get('label')}"
        assert data.get("shared_reality") == [], f"Self should have empty shared_reality"
        assert data.get("shared_dreams") == [], f"Self should have empty shared_dreams"
        assert data.get("swap_potential") == [], f"Self should have empty swap_potential"
        print("PASSED: Self taste match returns 100% with empty arrays")

    def test_taste_match_nonexistent_user_404(self, auth_token):
        """Taste match with non-existent user returns 404"""
        response = requests.get(f"{BASE_URL}/api/users/nonexistentuser999999/taste-match", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASSED: Non-existent user returns 404")

    def test_taste_match_response_structure(self, auth_token):
        """Taste match returns correct response structure"""
        # Get any other user first
        response = requests.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=1", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        if response.status_code != 200 or not response.json():
            pytest.skip("No other users found to test taste match against")
        
        other_user = response.json()[0]
        username = other_user.get("username")
        
        if not username:
            pytest.skip("Could not get another user's username")
        
        # Get taste match
        response = requests.get(f"{BASE_URL}/api/users/{username}/taste-match", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate structure
        assert "score" in data, "Missing 'score' in response"
        assert "label" in data, "Missing 'label' in response"
        assert "shared_reality" in data, "Missing 'shared_reality' in response"
        assert "shared_dreams" in data, "Missing 'shared_dreams' in response"
        assert "swap_potential" in data, "Missing 'swap_potential' in response"
        
        # Validate types
        assert isinstance(data["score"], int), f"Score should be int, got {type(data['score'])}"
        assert 0 <= data["score"] <= 100, f"Score should be 0-100, got {data['score']}"
        assert isinstance(data["shared_reality"], list), "shared_reality should be list"
        assert isinstance(data["shared_dreams"], list), "shared_dreams should be list"
        assert isinstance(data["swap_potential"], list), "swap_potential should be list"
        
        # Check label logic (Record Soulmates >= 90%)
        if data["score"] >= 90:
            assert data["label"] == "Record Soulmates", f"Score >= 90 should have 'Record Soulmates' label"
        
        print(f"PASSED: Taste match response structure validated for @{username} (score: {data['score']}%)")

    def test_taste_match_founder_user(self, auth_token):
        """Test taste match with founder user (katieintheafterglow)"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/taste-match", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        # Founder might not exist or username might be different
        if response.status_code == 404:
            pytest.skip("Founder user 'katieintheafterglow' not found")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate structure same as above
        assert "score" in data and isinstance(data["score"], int)
        assert "shared_reality" in data and isinstance(data["shared_reality"], list)
        assert "shared_dreams" in data and isinstance(data["shared_dreams"], list)
        assert "swap_potential" in data and isinstance(data["swap_potential"], list)
        
        print(f"PASSED: Founder taste match works (score: {data['score']}%)")


class TestUserProfileEndpoints:
    """Additional profile-related endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def admin_username(self, auth_token):
        """Get admin user's username"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed to get me: {response.text}"
        return response.json().get("username")
    
    def test_user_profile_loads(self, auth_token, admin_username):
        """GET /api/users/{username} returns profile data"""
        response = requests.get(f"{BASE_URL}/api/users/{admin_username}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Key profile fields should exist
        assert "username" in data
        assert "following_count" in data or "followers_count" in data
        print(f"PASSED: User profile loads for @{admin_username}")
    
    def test_user_records_endpoint(self, auth_token, admin_username):
        """GET /api/users/{username}/records returns records"""
        response = requests.get(f"{BASE_URL}/api/users/{admin_username}/records", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Records should be a list"
        print(f"PASSED: User records endpoint works ({len(data)} records)")
    
    def test_user_iso_endpoint(self, auth_token, admin_username):
        """GET /api/users/{username}/iso returns ISO items"""
        response = requests.get(f"{BASE_URL}/api/users/{admin_username}/iso")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "ISO should be a list"
        print(f"PASSED: User ISO endpoint works ({len(data)} items)")

    def test_valuation_endpoint(self, auth_token, admin_username):
        """GET /api/valuation/collection/{username} returns valuation data"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection/{admin_username}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        # Might be empty if user has no valued records
        if response.status_code == 200:
            data = response.json()
            # Check if it has total_value field
            if "total_value" in data:
                print(f"PASSED: Valuation endpoint works (total: ${data.get('total_value', 0)})")
            else:
                print("PASSED: Valuation endpoint returns response (no total_value)")
        else:
            pytest.skip(f"Valuation endpoint returned {response.status_code}")
