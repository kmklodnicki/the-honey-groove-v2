"""
Test cases for Welcome to the Hive Dashboard (Block 5.1)
Tests the /welcome-hive-data and /mark-welcome-seen endpoints
Test user: testexplore@test.com (5 seeded records worth $370, 4 artists, top artist Radiohead)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestWelcomeHiveDashboardAPI:
    """Tests for Welcome Hive Dashboard backend endpoints"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testexplore@test.com",
            "password": "testpass123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns access_token, not token
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in login response: {data.keys()}"
        return token

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}

    def test_welcome_hive_data_endpoint_returns_200(self, auth_headers):
        """GET /api/welcome-hive-data should return 200 for authenticated user"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_welcome_hive_data_returns_collection_value(self, auth_headers):
        """GET /api/welcome-hive-data should return total_collection_value field"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_collection_value" in data, "Missing total_collection_value field"
        assert isinstance(data["total_collection_value"], (int, float)), "Collection value should be a number"

    def test_welcome_hive_data_returns_record_count(self, auth_headers):
        """GET /api/welcome-hive-data should return total_records_imported field"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_records_imported" in data, "Missing total_records_imported field"
        assert isinstance(data["total_records_imported"], int), "Record count should be an integer"
        assert data["total_records_imported"] >= 0, "Record count should not be negative"

    def test_welcome_hive_data_returns_artist_count(self, auth_headers):
        """GET /api/welcome-hive-data should return total_unique_artists field"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_unique_artists" in data, "Missing total_unique_artists field"
        assert isinstance(data["total_unique_artists"], int), "Artist count should be an integer"

    def test_welcome_hive_data_returns_top_artist(self, auth_headers):
        """GET /api/welcome-hive-data should return top_artist_by_count field"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "top_artist_by_count" in data, "Missing top_artist_by_count field"
        # Can be None if no records or Unknown Artist

    def test_welcome_hive_data_returns_has_seen_flag(self, auth_headers):
        """GET /api/welcome-hive-data should return has_seen field"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "has_seen" in data, "Missing has_seen field"
        assert isinstance(data["has_seen"], bool), "has_seen should be a boolean"

    def test_welcome_hive_data_requires_auth(self):
        """GET /api/welcome-hive-data should return 401/403 without auth"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"

    def test_mark_welcome_seen_endpoint_returns_200(self, auth_headers):
        """POST /api/mark-welcome-seen should return 200 for authenticated user"""
        response = requests.post(f"{BASE_URL}/api/mark-welcome-seen", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_mark_welcome_seen_returns_ok(self, auth_headers):
        """POST /api/mark-welcome-seen should return ok: true"""
        response = requests.post(f"{BASE_URL}/api/mark-welcome-seen", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True, f"Expected ok: true, got {data}"

    def test_mark_welcome_seen_requires_auth(self):
        """POST /api/mark-welcome-seen should return 401/403 without auth"""
        response = requests.post(f"{BASE_URL}/api/mark-welcome-seen")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"

    def test_mark_welcome_seen_updates_flag(self, auth_headers):
        """POST /api/mark-welcome-seen should set has_seen to true"""
        # Call mark-welcome-seen
        mark_response = requests.post(f"{BASE_URL}/api/mark-welcome-seen", headers=auth_headers)
        assert mark_response.status_code == 200
        
        # Verify the flag was updated
        get_response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert get_response.status_code == 200
        data = get_response.json()
        assert data.get("has_seen") == True, "has_seen should be True after marking as seen"


class TestWelcomeHiveDataValues:
    """Test expected values for test user's collection"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testexplore@test.com",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        return data.get("access_token") or data.get("token")

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}

    def test_user_has_records(self, auth_headers):
        """Test user should have records imported"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Test user has 5 seeded records per context
        assert data["total_records_imported"] >= 1, "Test user should have at least 1 record"
        print(f"User has {data['total_records_imported']} records")

    def test_user_has_artists(self, auth_headers):
        """Test user should have artists collected"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Test user has 4 unique artists per context
        assert data["total_unique_artists"] >= 1, "Test user should have at least 1 artist"
        print(f"User has {data['total_unique_artists']} artists")

    def test_user_collection_value_non_negative(self, auth_headers):
        """Collection value should be non-negative"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_collection_value"] >= 0, "Collection value should be non-negative"
        print(f"Collection value: ${data['total_collection_value']}")

    def test_data_structure_complete(self, auth_headers):
        """All required fields should be present in response"""
        response = requests.get(f"{BASE_URL}/api/welcome-hive-data", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "total_collection_value",
            "total_records_imported", 
            "total_unique_artists",
            "top_artist_by_count",
            "has_seen"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"All fields present: {list(data.keys())}")
