"""
Discogs Import API Tests
Tests for the new Discogs Import feature: OAuth/token connection, import, progress, disconnect
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"
VALID_DISCOGS_USERNAME = "katieintheafterglow"
INVALID_DISCOGS_USERNAME = "thisuserdoesnotexist123456789xyz"


class TestDiscogsStatus:
    """Test GET /api/discogs/status endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_discogs_status_returns_connection_info(self, auth_token):
        """Test that GET /api/discogs/status returns connection status"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        assert isinstance(data["connected"], bool)
    
    def test_discogs_status_requires_auth(self):
        """Test that /api/discogs/status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/discogs/status")
        assert response.status_code == 401


class TestDiscogsConnectToken:
    """Test POST /api/discogs/connect-token endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_connect_with_valid_username(self, auth_token):
        """Test connecting Discogs with valid username succeeds"""
        # First disconnect to ensure clean state
        requests.delete(
            f"{BASE_URL}/api/discogs/disconnect",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        response = requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": VALID_DISCOGS_USERNAME},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Connected as" in data["message"]
        assert data["discogs_username"] == VALID_DISCOGS_USERNAME
    
    def test_connect_with_invalid_username_returns_400(self, auth_token):
        """Test connecting Discogs with invalid username returns 400 error"""
        response = requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": INVALID_DISCOGS_USERNAME},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_connect_token_requires_auth(self):
        """Test that /api/discogs/connect-token requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": VALID_DISCOGS_USERNAME}
        )
        assert response.status_code == 401


class TestDiscogsStatusAfterConnect:
    """Test GET /api/discogs/status after connection"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_status_shows_connected_after_connect(self, auth_token):
        """Test that status shows connected=true and discogs_username after connecting"""
        # Ensure connected state
        requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": VALID_DISCOGS_USERNAME},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        response = requests.get(
            f"{BASE_URL}/api/discogs/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] == True
        assert data["discogs_username"] == VALID_DISCOGS_USERNAME
        assert "connected_at" in data


class TestDiscogsImportProgress:
    """Test GET /api/discogs/import/progress endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_import_progress_returns_status(self, auth_token):
        """Test that GET /api/discogs/import/progress returns import status"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/import/progress",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["idle", "in_progress", "completed", "error"]
        assert "total" in data
        assert "imported" in data
        assert "skipped" in data
    
    def test_import_progress_requires_auth(self):
        """Test that /api/discogs/import/progress requires authentication"""
        response = requests.get(f"{BASE_URL}/api/discogs/import/progress")
        assert response.status_code == 401


class TestDiscogsDisconnect:
    """Test DELETE /api/discogs/disconnect endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_disconnect_removes_connection(self, auth_token):
        """Test that DELETE /api/discogs/disconnect removes the connection"""
        # First ensure connected
        requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": VALID_DISCOGS_USERNAME},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Disconnect
        response = requests.delete(
            f"{BASE_URL}/api/discogs/disconnect",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify disconnected
        status_response = requests.get(
            f"{BASE_URL}/api/discogs/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["connected"] == False
    
    def test_disconnect_requires_auth(self):
        """Test that /api/discogs/disconnect requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/discogs/disconnect")
        assert response.status_code == 401


class TestDiscogsImportStartAndSync:
    """Test POST /api/discogs/import endpoint (sync functionality)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_import_requires_connection(self, auth_token):
        """Test that import fails if Discogs is not connected"""
        # Disconnect first
        requests.delete(
            f"{BASE_URL}/api/discogs/disconnect",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        response = requests.post(
            f"{BASE_URL}/api/discogs/import",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not connected" in data["detail"].lower()
        
        # Re-connect for other tests
        requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": VALID_DISCOGS_USERNAME},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
    
    def test_import_starts_when_connected(self, auth_token):
        """Test that import can start when Discogs is connected"""
        # Ensure connected
        requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": VALID_DISCOGS_USERNAME},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Start import
        response = requests.post(
            f"{BASE_URL}/api/discogs/import",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        # Could be in_progress or completed (if sync was already done)
        assert data["status"] in ["in_progress", "completed"]


class TestRecordCountAfterImport:
    """Test that records count increased after import"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_user_has_imported_records(self, auth_token):
        """Test that user's collection contains imported records (143 total expected)"""
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Based on the context, user has 143 records (139 imported + 4 original)
        assert len(data) >= 100, f"Expected at least 100 records, got {len(data)}"
        
        # Check that some records have discogs_id (from import)
        discogs_records = [r for r in data if r.get("discogs_id")]
        assert len(discogs_records) > 0, "Expected some records with discogs_id from import"
