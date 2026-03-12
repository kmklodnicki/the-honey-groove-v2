"""
Tests for BLOCK 592 Phase 2: Unofficial Pill Position & Global Metadata Scrub
- Tests the /api/admin/scrub-unofficial-metadata endpoint
- Verifies unofficial records in database
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "http://localhost:8001"

ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "admin_password"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    # Note: Response uses 'access_token' not 'token'
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Auth headers for admin endpoints"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestScrubUnofficialMetadataEndpoint:
    """Tests for POST /api/admin/scrub-unofficial-metadata"""
    
    def test_scrub_endpoint_requires_auth(self):
        """Endpoint should return 401/403 without auth"""
        response = requests.post(f"{BASE_URL}/api/admin/scrub-unofficial-metadata")
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ Scrub endpoint requires authentication")
    
    def test_scrub_endpoint_returns_correct_structure(self, auth_headers):
        """Endpoint should return proper JSON structure with stats"""
        response = requests.post(
            f"{BASE_URL}/api/admin/scrub-unofficial-metadata",
            headers=auth_headers,
            timeout=120  # Long timeout due to Discogs rate limiting
        )
        assert response.status_code == 200, f"Scrub failed: {response.text}"
        
        data = response.json()
        
        # Verify required fields in response
        assert "total_scanned" in data, "Missing total_scanned"
        assert "total_updated" in data, "Missing total_updated"
        assert "newly_flagged_unofficial" in data, "Missing newly_flagged_unofficial"
        assert "newly_unflagged" in data, "Missing newly_unflagged"
        assert "errors" in data, "Missing errors"
        
        # Verify data types
        assert isinstance(data["total_scanned"], int)
        assert isinstance(data["total_updated"], int)
        assert isinstance(data["newly_flagged_unofficial"], list)
        assert isinstance(data["newly_unflagged"], list)
        assert isinstance(data["errors"], list)
        
        print(f"✓ Scrub completed: {data['total_scanned']} scanned, {data['total_updated']} updated")
        print(f"  Newly flagged: {len(data['newly_flagged_unofficial'])}, Unflagged: {len(data['newly_unflagged'])}")
        print(f"  Errors: {len(data['errors'])}")
    
    def test_scrub_idempotent(self, auth_headers):
        """Running scrub twice should return 0 updates on second run (already processed)"""
        # First run
        response1 = requests.post(
            f"{BASE_URL}/api/admin/scrub-unofficial-metadata",
            headers=auth_headers,
            timeout=120
        )
        assert response1.status_code == 200
        
        # Second run should have 0 updates since data already correct
        response2 = requests.post(
            f"{BASE_URL}/api/admin/scrub-unofficial-metadata",
            headers=auth_headers,
            timeout=120
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # total_updated should be 0 on second run
        assert data2["total_updated"] == 0, f"Expected 0 updates, got {data2['total_updated']}"
        print("✓ Scrub is idempotent (0 updates on re-run)")


class TestUnofficialRecordsInDatabase:
    """Verify specific records have correct is_unofficial flags"""
    
    def test_merry_swiftmas_is_unofficial(self, auth_headers):
        """Merry Swiftmas by Taylor Swift should be marked unofficial"""
        # Search for records with title containing 'Merry Swiftmas'
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers=auth_headers,
            params={"search": "Merry Swiftmas"}
        )
        assert response.status_code == 200
        
        records = response.json()
        merry_records = [r for r in records if "Merry" in r.get("title", "")]
        
        assert len(merry_records) > 0, "No Merry Swiftmas records found"
        for record in merry_records:
            assert record.get("is_unofficial") == True, \
                f"Merry Swiftmas should be unofficial: {record.get('title')}"
        
        print(f"✓ Found {len(merry_records)} 'Merry Swiftmas' records, all marked unofficial")
    
    def test_beautiful_eyes_is_unofficial(self, auth_headers):
        """Beautiful Eyes by Taylor Swift should be marked unofficial"""
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers=auth_headers,
            params={"search": "Beautiful Eyes"}
        )
        assert response.status_code == 200
        
        records = response.json()
        beautiful_records = [r for r in records if "Beautiful Eyes" in r.get("title", "")]
        
        assert len(beautiful_records) > 0, "No Beautiful Eyes records found"
        for record in beautiful_records:
            assert record.get("is_unofficial") == True, \
                f"Beautiful Eyes should be unofficial: {record.get('title')}"
        
        print(f"✓ Found {len(beautiful_records)} 'Beautiful Eyes' records, all marked unofficial")
    
    def test_shiny_things_is_unofficial(self, auth_headers):
        """Shiny Things by Taylor Swift should be marked unofficial"""
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers=auth_headers,
            params={"search": "Shiny Things"}
        )
        assert response.status_code == 200
        
        records = response.json()
        shiny_records = [r for r in records if "Shiny Things" in r.get("title", "")]
        
        assert len(shiny_records) > 0, "No Shiny Things records found"
        for record in shiny_records:
            assert record.get("is_unofficial") == True, \
                f"Shiny Things should be unofficial: {record.get('title')}"
        
        print(f"✓ Found {len(shiny_records)} 'Shiny Things' records, all marked unofficial")


class TestOfficialRecordsNotFlagged:
    """Verify official records are NOT marked as unofficial"""
    
    def test_red_album_not_unofficial(self, auth_headers):
        """Red by Taylor Swift (official album) should NOT be marked unofficial"""
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers=auth_headers,
            params={"search": "Red Taylor Swift"}
        )
        assert response.status_code == 200
        
        records = response.json()
        # Look for "Red" album (the specific album, not 'Red w/ White Splatter')
        red_albums = [r for r in records if r.get("title") == "Red" and r.get("artist") == "Taylor Swift"]
        
        if red_albums:
            for record in red_albums:
                # Should NOT be unofficial (either False or not set)
                is_unofficial = record.get("is_unofficial", False)
                assert is_unofficial == False, \
                    f"Red (official album) should not be unofficial"
            print(f"✓ Found {len(red_albums)} 'Red' albums, correctly NOT marked unofficial")
        else:
            print("ℹ No exact 'Red' album found in search results (may not be in collection)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
