"""
Test suite for Variant Action Buttons on Vinyl Variant Pages

Features tested:
- GET /api/vinyl/ownership/{discogs_id} - Returns ownership status (owned, iso_status, record_id, iso_id)
- POST /api/records - Add variant to collection
- POST /api/iso - Add to wishlist (status=WISHLIST) or actively seeking (status=OPEN)
- Ownership check after adding to collection shows owned=true with record_id
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_DISCOGS_ID = 30984958  # Charli XCX - Brat - Black Translucent
NONEXISTENT_DISCOGS_ID = 99999999


class TestOwnershipEndpointUnauthenticated:
    """Test /api/vinyl/ownership without authentication"""
    
    def test_ownership_without_auth_returns_not_owned(self):
        """GET /api/vinyl/ownership/{discogs_id} without auth returns owned=false"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ownership/{TEST_DISCOGS_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["owned"] == False
        assert data["iso_status"] is None
        assert data["record_id"] is None
        assert data["iso_id"] is None
    
    def test_ownership_nonexistent_id_without_auth(self):
        """GET /api/vinyl/ownership/99999999 returns owned=false without error"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ownership/{NONEXISTENT_DISCOGS_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["owned"] == False
        assert "error" not in data  # No error for nonexistent release


class TestVariantActionsAuthenticated:
    """Test variant action flows with authentication"""
    
    @pytest.fixture(autouse=True)
    def setup_user(self):
        """Create a test user for authenticated tests"""
        self.unique_email = f"test_variant_actions_{uuid.uuid4().hex[:8]}@test.com"
        self.unique_username = f"testvar_{uuid.uuid4().hex[:8]}"
        
        # Register user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": self.unique_username,
            "email": self.unique_email,
            "password": "Test123!"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.user_id = data["user"]["id"]
            self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        else:
            pytest.skip(f"Failed to create test user: {response.text}")
        
        yield
        
        # Cleanup: Delete test records and ISO items created during tests
        try:
            # Get and delete records
            records_resp = requests.get(f"{BASE_URL}/api/records", headers=self.headers)
            if records_resp.status_code == 200:
                for record in records_resp.json():
                    if record.get("discogs_id") == TEST_DISCOGS_ID:
                        requests.delete(f"{BASE_URL}/api/records/{record['id']}", headers=self.headers)
            
            # Get and delete ISO items
            iso_resp = requests.get(f"{BASE_URL}/api/iso", headers=self.headers)
            if iso_resp.status_code == 200:
                for iso in iso_resp.json():
                    if iso.get("discogs_id") == TEST_DISCOGS_ID:
                        requests.delete(f"{BASE_URL}/api/iso/{iso['id']}", headers=self.headers)
        except Exception:
            pass  # Cleanup failures are not test failures
    
    def test_ownership_with_auth_not_owned(self):
        """GET /api/vinyl/ownership/{discogs_id} with auth for non-owned variant"""
        response = requests.get(
            f"{BASE_URL}/api/vinyl/ownership/{TEST_DISCOGS_ID}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["owned"] == False
        assert data["record_id"] is None
    
    def test_add_to_wishlist(self):
        """POST /api/iso with status=WISHLIST creates wishlist item"""
        response = requests.post(f"{BASE_URL}/api/iso", headers=self.headers, json={
            "artist": "Charli XCX",
            "album": "Brat",
            "discogs_id": TEST_DISCOGS_ID,
            "cover_url": "https://example.com/cover.jpg",
            "year": 2024,
            "color_variant": "Black Translucent",
            "status": "WISHLIST"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "WISHLIST"
        assert data["discogs_id"] == TEST_DISCOGS_ID
        assert data["artist"] == "Charli XCX"
        assert data["album"] == "Brat"
        
        # Verify ownership shows iso_status=WISHLIST
        ownership = requests.get(
            f"{BASE_URL}/api/vinyl/ownership/{TEST_DISCOGS_ID}",
            headers=self.headers
        ).json()
        
        assert ownership["owned"] == False
        assert ownership["iso_status"] == "WISHLIST"
        assert ownership["iso_id"] == data["id"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/iso/{data['id']}", headers=self.headers)
    
    def test_add_to_actively_seeking(self):
        """POST /api/iso with status=OPEN creates actively seeking item"""
        response = requests.post(f"{BASE_URL}/api/iso", headers=self.headers, json={
            "artist": "Charli XCX",
            "album": "Brat",
            "discogs_id": TEST_DISCOGS_ID,
            "status": "OPEN",
            "priority": "HIGH"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OPEN"
        assert data["priority"] == "HIGH"
        
        # Verify ownership shows iso_status=OPEN
        ownership = requests.get(
            f"{BASE_URL}/api/vinyl/ownership/{TEST_DISCOGS_ID}",
            headers=self.headers
        ).json()
        
        assert ownership["owned"] == False
        assert ownership["iso_status"] == "OPEN"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/iso/{data['id']}", headers=self.headers)
    
    def test_add_to_collection(self):
        """POST /api/records creates collection record and ownership shows owned=true"""
        response = requests.post(f"{BASE_URL}/api/records", headers=self.headers, json={
            "discogs_id": TEST_DISCOGS_ID,
            "title": "Brat",
            "artist": "Charli XCX",
            "cover_url": "https://example.com/cover.jpg",
            "year": 2024,
            "color_variant": "Black Translucent",
            "format": "Vinyl"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["discogs_id"] == TEST_DISCOGS_ID
        assert data["title"] == "Brat"
        assert data["artist"] == "Charli XCX"
        assert "id" in data
        
        # Verify ownership shows owned=true
        ownership = requests.get(
            f"{BASE_URL}/api/vinyl/ownership/{TEST_DISCOGS_ID}",
            headers=self.headers
        ).json()
        
        assert ownership["owned"] == True
        assert ownership["record_id"] == data["id"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{data['id']}", headers=self.headers)
    
    def test_ownership_shows_both_record_and_iso(self):
        """When user has both record and ISO for same discogs_id, ownership shows both"""
        # Add to collection
        record_resp = requests.post(f"{BASE_URL}/api/records", headers=self.headers, json={
            "discogs_id": TEST_DISCOGS_ID,
            "title": "Brat",
            "artist": "Charli XCX",
            "format": "Vinyl"
        })
        assert record_resp.status_code == 200
        record_id = record_resp.json()["id"]
        
        # Also add to ISO/wishlist
        iso_resp = requests.post(f"{BASE_URL}/api/iso", headers=self.headers, json={
            "artist": "Charli XCX",
            "album": "Brat",
            "discogs_id": TEST_DISCOGS_ID,
            "status": "WISHLIST"
        })
        assert iso_resp.status_code == 200
        iso_id = iso_resp.json()["id"]
        
        # Check ownership
        ownership = requests.get(
            f"{BASE_URL}/api/vinyl/ownership/{TEST_DISCOGS_ID}",
            headers=self.headers
        ).json()
        
        assert ownership["owned"] == True
        assert ownership["record_id"] == record_id
        assert ownership["iso_status"] == "WISHLIST"
        assert ownership["iso_id"] == iso_id
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=self.headers)
        requests.delete(f"{BASE_URL}/api/iso/{iso_id}", headers=self.headers)


class TestVariantPageData:
    """Test variant page data includes discogs_id for action buttons"""
    
    def test_variant_page_includes_discogs_id(self):
        """GET /api/vinyl/{artist}/{album}/{variant} includes discogs_id in variant_overview"""
        response = requests.get(f"{BASE_URL}/api/vinyl/charli-xcx/brat/black-translucent")
        assert response.status_code == 200
        
        data = response.json()
        assert "variant_overview" in data
        
        overview = data["variant_overview"]
        assert overview["discogs_id"] == TEST_DISCOGS_ID
        assert overview["artist"] == "Charli XCX"
        assert overview["album"] == "Brat"
        assert "variant" in overview
        assert "cover_url" in overview
        assert "year" in overview


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
