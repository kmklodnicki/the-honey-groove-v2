"""
Tests for HoneyGroove v2.8.3 Emergency Directive
- API Metadata Enrichment: is_unofficial field in variant_overview
- Admin scrub-unofficial-metadata endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://honeypot-hotfix.preview.emergentagent.com')

# Admin credentials
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "admin_password"

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin authentication failed with status {response.status_code}")


class TestVariantAPIIsUnofficial:
    """Tests for is_unofficial field in variant API responses"""
    
    def test_merry_swiftmas_is_unofficial_true(self, api_client):
        """GET /api/vinyl/release/32442177 should return variant_overview.is_unofficial=true (Merry Swiftmas - unofficial)"""
        response = api_client.get(f"{BASE_URL}/api/vinyl/release/32442177")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "variant_overview" in data, "Response should contain variant_overview"
        
        variant_overview = data["variant_overview"]
        assert "is_unofficial" in variant_overview, "variant_overview should contain is_unofficial field"
        assert variant_overview["is_unofficial"] == True, f"Merry Swiftmas should be unofficial, got {variant_overview['is_unofficial']}"
        
        # Verify it's the correct record
        assert "Merry Swiftmas" in variant_overview.get("album", ""), f"Expected Merry Swiftmas album, got {variant_overview.get('album')}"
        assert "Taylor Swift" in variant_overview.get("artist", ""), f"Expected Taylor Swift artist, got {variant_overview.get('artist')}"
        
        print(f"✓ Merry Swiftmas (32442177) correctly marked as unofficial: is_unofficial={variant_overview['is_unofficial']}")

    def test_pink_pony_club_is_unofficial_false(self, api_client):
        """GET /api/vinyl/release/31785674 should return variant_overview.is_unofficial=false (Pink Pony Club - official)"""
        response = api_client.get(f"{BASE_URL}/api/vinyl/release/31785674")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "variant_overview" in data, "Response should contain variant_overview"
        
        variant_overview = data["variant_overview"]
        assert "is_unofficial" in variant_overview, "variant_overview should contain is_unofficial field"
        assert variant_overview["is_unofficial"] == False, f"Pink Pony Club should be official, got {variant_overview['is_unofficial']}"
        
        # Verify it's the correct record
        assert "Pink Pony Club" in variant_overview.get("album", ""), f"Expected Pink Pony Club album, got {variant_overview.get('album')}"
        assert "Chappell Roan" in variant_overview.get("artist", ""), f"Expected Chappell Roan artist, got {variant_overview.get('artist')}"
        
        print(f"✓ Pink Pony Club (31785674) correctly marked as official: is_unofficial={variant_overview['is_unofficial']}")


class TestAdminScrubUnofficialMetadata:
    """Tests for admin scrub-unofficial-metadata endpoint"""
    
    def test_scrub_unofficial_metadata_returns_expected_counts(self, api_client, admin_token):
        """POST /api/admin/scrub-unofficial-metadata should return total_scanned=168 with total_updated=0"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/scrub-unofficial-metadata",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=120  # This endpoint may take time to scan all records
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_scanned" in data, f"Response should contain total_scanned: {data}"
        assert "total_updated" in data, f"Response should contain total_updated: {data}"
        
        # According to task, all records should already be correctly flagged
        # so total_updated should be 0
        assert data["total_scanned"] == 168, f"Expected 168 total_scanned, got {data['total_scanned']}"
        assert data["total_updated"] == 0, f"Expected 0 total_updated (all already correct), got {data['total_updated']}"
        
        print(f"✓ Scrub endpoint returned: total_scanned={data['total_scanned']}, total_updated={data['total_updated']}")

    def test_scrub_unauthorized_without_admin(self, api_client):
        """POST /api/admin/scrub-unofficial-metadata without admin token should fail"""
        response = api_client.post(f"{BASE_URL}/api/admin/scrub-unofficial-metadata")
        
        # Should be 401 or 403
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
        print(f"✓ Scrub endpoint correctly requires admin auth (status: {response.status_code})")


class TestVariantAPIsResponse:
    """Additional tests for variant API response structure"""
    
    def test_variant_release_contains_required_fields(self, api_client):
        """Verify variant API returns all required fields"""
        response = api_client.get(f"{BASE_URL}/api/vinyl/release/32442177")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check variant_overview has essential fields
        vo = data.get("variant_overview", {})
        required_fields = ["artist", "album", "is_unofficial"]
        
        for field in required_fields:
            assert field in vo, f"variant_overview missing required field: {field}"
        
        print(f"✓ variant_overview contains all required fields: {required_fields}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
