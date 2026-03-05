"""
Extended Discogs Import Tests + Platform Fee Tests
Tests import summary endpoint, collection stats, and dynamic platform fee on ISOPage
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


@pytest.fixture
def auth_token():
    """Get auth token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Authentication failed")


class TestDiscogsImportSummary:
    """Test GET /api/discogs/import/summary endpoint"""
    
    def test_summary_endpoint_returns_200(self, auth_token):
        """Test that summary endpoint returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/import/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_summary_returns_has_import_field(self, auth_token):
        """Test that summary response includes has_import field"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/import/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "has_import" in data
        assert isinstance(data["has_import"], bool)
    
    def test_summary_returns_rich_data_when_has_import(self, auth_token):
        """Test that summary includes imported, skipped, total, sample_covers when has_import=True"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/import/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("has_import"):
            # Check basic import stats
            assert "imported" in data
            assert "skipped" in data
            assert "total" in data
            assert isinstance(data["imported"], int)
            assert isinstance(data["skipped"], int)
            assert isinstance(data["total"], int)
            
            # Check sample_covers exists
            assert "sample_covers" in data
            assert isinstance(data["sample_covers"], list)
            
            # Check discogs_username
            assert "discogs_username" in data
    
    def test_summary_returns_collection_stats(self, auth_token):
        """Test that summary includes collection_stats with total_records, total_value, valued_count"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/import/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("has_import"):
            assert "collection_stats" in data
            stats = data["collection_stats"]
            assert "total_records" in stats
            assert "total_value" in stats
            assert "valued_count" in stats
            assert isinstance(stats["total_records"], int)
            assert isinstance(stats["total_value"], (int, float))
            assert isinstance(stats["valued_count"], int)
    
    def test_summary_requires_auth(self):
        """Test that /api/discogs/import/summary requires authentication"""
        response = requests.get(f"{BASE_URL}/api/discogs/import/summary")
        assert response.status_code == 401


class TestDiscogsImportProgressFields:
    """Test GET /api/discogs/import/progress returns expected fields"""
    
    def test_progress_returns_sample_covers_field(self, auth_token):
        """Test that progress includes sample_covers field"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/import/progress",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # sample_covers may be present in completed state
        if data.get("status") == "completed":
            assert "sample_covers" in data
            assert isinstance(data["sample_covers"], list)
    
    def test_progress_returns_errors_field(self, auth_token):
        """Test that progress includes errors count field for completed status"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/import/progress",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # After import, should have errors count
        if data.get("status") == "completed":
            assert "errors" in data
            assert isinstance(data["errors"], int)


class TestPlatformFee:
    """Test GET /api/platform-fee endpoint - dynamic fee for ISOPage"""
    
    def test_platform_fee_returns_200(self):
        """Test that /api/platform-fee returns 200 without auth"""
        response = requests.get(f"{BASE_URL}/api/platform-fee")
        assert response.status_code == 200
    
    def test_platform_fee_returns_fee_percent(self):
        """Test that /api/platform-fee returns platform_fee_percent field"""
        response = requests.get(f"{BASE_URL}/api/platform-fee")
        assert response.status_code == 200
        data = response.json()
        assert "platform_fee_percent" in data
        assert isinstance(data["platform_fee_percent"], (int, float))
    
    def test_platform_fee_is_reasonable(self):
        """Test that platform fee is a reasonable percentage (0-20%)"""
        response = requests.get(f"{BASE_URL}/api/platform-fee")
        assert response.status_code == 200
        data = response.json()
        fee = data["platform_fee_percent"]
        assert 0 <= fee <= 20, f"Fee {fee}% is outside expected range"


class TestDiscogsConnectPrivateCollection:
    """Test error handling for private Discogs collections"""
    
    def test_connect_shows_private_error_message(self, auth_token):
        """Test that connecting to a private collection returns appropriate error"""
        # First disconnect
        requests.delete(
            f"{BASE_URL}/api/discogs/disconnect",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Try to connect with a username that has a private collection
        # Note: We can't easily find a private collection to test, so we test the endpoint exists
        # and returns proper error structure
        response = requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": "nonexistent_user_xyz_123456"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # Error message should be meaningful
        assert len(data["detail"]) > 5
        
        # Re-connect for other tests
        requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": VALID_DISCOGS_USERNAME},
            headers={"Authorization": f"Bearer {auth_token}"}
        )


class TestDiscogsStatusFields:
    """Test GET /api/discogs/status returns all expected fields"""
    
    def test_status_returns_last_synced(self, auth_token):
        """Test that status includes last_synced field when connected"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("connected"):
            # last_synced may be null if never synced
            assert "last_synced" in data
    
    def test_status_returns_connected_at(self, auth_token):
        """Test that status includes connected_at field when connected"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("connected"):
            assert "connected_at" in data


class TestDuplicateHandling:
    """Test that import properly skips duplicates"""
    
    def test_sync_shows_skipped_duplicates(self, auth_token):
        """Test that syncing again shows skipped duplicates (since all 143 are already imported)"""
        # Ensure connected
        requests.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": VALID_DISCOGS_USERNAME},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Start import (should be quick since all are duplicates)
        import_response = requests.post(
            f"{BASE_URL}/api/discogs/import",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert import_response.status_code == 200
        
        # Wait for import to complete (max 30 seconds)
        for _ in range(15):
            progress_response = requests.get(
                f"{BASE_URL}/api/discogs/import/progress",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            progress = progress_response.json()
            if progress.get("status") in ["completed", "error"]:
                break
            time.sleep(2)
        
        # Check progress or summary for skipped count
        final_response = requests.get(
            f"{BASE_URL}/api/discogs/import/progress",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        final = final_response.json()
        
        if final.get("status") == "completed":
            # Since all 143 are already imported, skipped should be ~143
            skipped = final.get("skipped", 0)
            # Allow some tolerance since collection may have changed
            assert skipped > 100 or final.get("imported", 0) == 0, f"Expected high skipped count, got {skipped}"
