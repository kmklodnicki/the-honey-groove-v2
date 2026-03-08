"""
Tests for Instagram and TikTok username fields in user profile.
Features tested:
- PUT /api/auth/me accepts instagram_username and tiktok_username fields
- GET /api/auth/me returns instagram_username and tiktok_username
- Fields are properly saved and retrieved
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestSocialUsernames:
    """Tests for Instagram and TikTok username fields."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "vinylcollector@honey.io",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_me_returns_social_fields(self):
        """GET /api/auth/me should return instagram_username and tiktok_username fields."""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify fields exist in response (may be null initially)
        assert "instagram_username" in data, "instagram_username field missing from response"
        assert "tiktok_username" in data, "tiktok_username field missing from response"
    
    def test_update_instagram_username(self):
        """PUT /api/auth/me should accept and persist instagram_username."""
        test_username = "test_insta_user_82"
        
        # Update
        response = requests.put(f"{BASE_URL}/api/auth/me", headers=self.headers, json={
            "instagram_username": test_username
        })
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        assert data.get("instagram_username") == test_username, f"Expected {test_username}, got {data.get('instagram_username')}"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data.get("instagram_username") == test_username, "Instagram username not persisted"
    
    def test_update_tiktok_username(self):
        """PUT /api/auth/me should accept and persist tiktok_username."""
        test_username = "test_tiktok_user_82"
        
        # Update
        response = requests.put(f"{BASE_URL}/api/auth/me", headers=self.headers, json={
            "tiktok_username": test_username
        })
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        assert data.get("tiktok_username") == test_username, f"Expected {test_username}, got {data.get('tiktok_username')}"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data.get("tiktok_username") == test_username, "TikTok username not persisted"
    
    def test_update_both_social_usernames(self):
        """PUT /api/auth/me should accept both social usernames together."""
        insta_username = "both_insta_82"
        tiktok_username = "both_tiktok_82"
        
        # Update both
        response = requests.put(f"{BASE_URL}/api/auth/me", headers=self.headers, json={
            "instagram_username": insta_username,
            "tiktok_username": tiktok_username
        })
        assert response.status_code == 200, f"Update failed: {response.text}"
        data = response.json()
        assert data.get("instagram_username") == insta_username
        assert data.get("tiktok_username") == tiktok_username
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data.get("instagram_username") == insta_username
        assert get_data.get("tiktok_username") == tiktok_username
    
    def test_clear_social_usernames(self):
        """Setting social usernames to empty string should clear them."""
        # First set them
        requests.put(f"{BASE_URL}/api/auth/me", headers=self.headers, json={
            "instagram_username": "temp_insta",
            "tiktok_username": "temp_tiktok"
        })
        
        # Then clear them
        response = requests.put(f"{BASE_URL}/api/auth/me", headers=self.headers, json={
            "instagram_username": "",
            "tiktok_username": ""
        })
        assert response.status_code == 200
        data = response.json()
        # Empty string should be stored as is
        assert data.get("instagram_username") == ""
        assert data.get("tiktok_username") == ""
    
    def test_profile_endpoint_shows_social_usernames(self):
        """GET /api/users/{username} should return social username fields."""
        # First set them
        set_response = requests.put(f"{BASE_URL}/api/auth/me", headers=self.headers, json={
            "instagram_username": "profile_test_insta",
            "tiktok_username": "profile_test_tiktok"
        })
        assert set_response.status_code == 200
        
        # Get own username
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        username = me_response.json().get("username")
        
        # Fetch profile
        profile_response = requests.get(f"{BASE_URL}/api/users/{username}", headers=self.headers)
        assert profile_response.status_code == 200, f"Profile fetch failed: {profile_response.text}"
        profile_data = profile_response.json()
        
        # Verify social fields are in profile
        assert profile_data.get("instagram_username") == "profile_test_insta"
        assert profile_data.get("tiktok_username") == "profile_test_tiktok"
