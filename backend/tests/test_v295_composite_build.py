"""
Test Suite for Composite Build Directive v2.9.5
Features:
- Smart De-Duplication: GET /api/records/duplicates returns is_hydrated, total_spins, spin_count per record (NO needs_review field)
- DELETE /api/records/duplicates/clean returns removed_count AND spins_merged fields
- POST /api/records/hard-refresh-images endpoint for authenticated users
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def auth_headers():
    """Authenticate as admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@thehoneygroove.com",
        "password": "admin_password"
    })
    if response.status_code != 200:
        pytest.skip("Authentication failed - cannot proceed with tests")
    data = response.json()
    return {"Authorization": f"Bearer {data.get('access_token')}"}


class TestDuplicateDetection:
    """Test GET /api/records/duplicates endpoint"""
    
    def test_duplicates_requires_auth(self):
        """GET /api/records/duplicates requires authentication"""
        response = requests.get(f"{BASE_URL}/api/records/duplicates")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ GET /api/records/duplicates requires auth (401)")
    
    def test_duplicates_returns_correct_structure(self, auth_headers):
        """GET /api/records/duplicates returns proper response structure with is_hydrated, total_spins, spin_count"""
        response = requests.get(f"{BASE_URL}/api/records/duplicates", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "duplicate_groups" in data, "Missing duplicate_groups field"
        assert "total_duplicates" in data, "Missing total_duplicates field"
        assert isinstance(data["duplicate_groups"], list), "duplicate_groups should be a list"
        
        print(f"✅ GET /api/records/duplicates - {len(data['duplicate_groups'])} groups, {data['total_duplicates']} total duplicates")
        
        # If there are duplicate groups, verify structure
        if data["duplicate_groups"]:
            group = data["duplicate_groups"][0]
            
            # Check group-level fields
            assert "discogs_id" in group, "Missing discogs_id in group"
            assert "count" in group, "Missing count in group"
            assert "total_spins" in group, "Missing total_spins in group (Smart De-Duplication feature)"
            assert "records" in group, "Missing records in group"
            
            # CRITICAL: Verify needs_review field is NOT present
            assert "needs_review" not in group, "needs_review field should be REMOVED (per v2.9.5 directive)"
            
            # Check record-level fields
            record = group["records"][0]
            assert "is_hydrated" in record, "Missing is_hydrated in record (Smart De-Duplication feature)"
            assert "spin_count" in record, "Missing spin_count in record (Smart De-Duplication feature)"
            
            # Verify needs_review is not in records either
            assert "needs_review" not in record, "needs_review should be REMOVED from records"
            
            print(f"  ✅ Group has total_spins={group['total_spins']}")
            print(f"  ✅ Record has is_hydrated={record['is_hydrated']}, spin_count={record['spin_count']}")
            print(f"  ✅ NO needs_review field present (verified)")
        else:
            print("  ℹ️ No duplicate groups found - structure verification skipped")


class TestDuplicateClean:
    """Test DELETE /api/records/duplicates/clean endpoint"""
    
    def test_clean_duplicates_requires_auth(self):
        """DELETE /api/records/duplicates/clean requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/records/duplicates/clean")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ DELETE /api/records/duplicates/clean requires auth (401)")
    
    def test_clean_duplicates_returns_correct_structure(self, auth_headers):
        """DELETE /api/records/duplicates/clean returns removed_count AND spins_merged fields"""
        response = requests.delete(f"{BASE_URL}/api/records/duplicates/clean", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "removed_count" in data, "Missing removed_count field"
        assert "spins_merged" in data, "Missing spins_merged field (Smart De-Duplication feature)"
        
        assert isinstance(data["removed_count"], int), "removed_count should be an integer"
        assert isinstance(data["spins_merged"], int), "spins_merged should be an integer"
        
        print(f"✅ DELETE /api/records/duplicates/clean - removed {data['removed_count']} duplicates, merged {data['spins_merged']} spins")


class TestHardRefreshImages:
    """Test POST /api/records/hard-refresh-images endpoint"""
    
    def test_hard_refresh_requires_auth(self):
        """POST /api/records/hard-refresh-images requires authentication"""
        response = requests.post(f"{BASE_URL}/api/records/hard-refresh-images")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ POST /api/records/hard-refresh-images requires auth (401)")
    
    def test_hard_refresh_returns_correct_structure(self, auth_headers):
        """POST /api/records/hard-refresh-images returns total_placeholders, fixed, failed fields"""
        response = requests.post(f"{BASE_URL}/api/records/hard-refresh-images", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_placeholders" in data, "Missing total_placeholders field"
        assert "fixed" in data, "Missing fixed field"
        assert "failed" in data, "Missing failed field"
        
        assert isinstance(data["total_placeholders"], int), "total_placeholders should be an integer"
        assert isinstance(data["fixed"], int), "fixed should be an integer"
        assert isinstance(data["failed"], int), "failed should be an integer"
        
        print(f"✅ POST /api/records/hard-refresh-images - {data['total_placeholders']} placeholders, {data['fixed']} fixed, {data['failed']} failed")


class TestTestUserAuth:
    """Test with test user credentials"""
    
    @pytest.fixture(scope="class")
    def test_user_headers(self):
        """Authenticate as test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if response.status_code != 200:
            pytest.skip("Test user authentication failed")
        data = response.json()
        return {"Authorization": f"Bearer {data.get('access_token')}"}
    
    def test_hard_refresh_works_for_regular_user(self, test_user_headers):
        """POST /api/records/hard-refresh-images works for authenticated non-admin user"""
        response = requests.post(f"{BASE_URL}/api/records/hard-refresh-images", headers=test_user_headers)
        assert response.status_code == 200, f"Expected 200 (user-scoped, not admin-only), got {response.status_code}"
        print("✅ POST /api/records/hard-refresh-images works for regular user (user-scoped)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
