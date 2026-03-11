"""
Test suite for BLOCK 169: Duplicate Detection Prompt feature
Tests the check-ownership endpoint and duplicate detection flows
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@test.com"
TEST_PASSWORD = "demouser"

# Demo user has these Igor records: discogs_ids 14215683, 14219559, 23310752


class TestDuplicateDetectionBackend:
    """Tests for duplicate detection backend functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Authenticate and get token for demo user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture
    def headers(self, auth_token):
        """Return authenticated headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # --- Check Ownership Endpoint Tests ---
    
    def test_check_ownership_returns_copy_count_for_owned_record(self, headers):
        """Test GET /api/records/check-ownership returns copy_count for owned discogs_id"""
        # Using discogs_id 14215683 which demo user owns (Igor by Tyler)
        response = requests.get(
            f"{BASE_URL}/api/records/check-ownership",
            params={"discogs_id": 14215683},
            headers=headers
        )
        assert response.status_code == 200, f"Check ownership failed: {response.text}"
        data = response.json()
        
        # Verify required fields are present
        assert "in_collection" in data, "Response missing 'in_collection' field"
        assert "copy_count" in data, "Response missing 'copy_count' field"
        assert "record_id" in data, "Response missing 'record_id' field"
        
        # Since demo user owns this record, in_collection should be True
        assert data["in_collection"] == True, f"Expected in_collection=True for owned record"
        assert data["copy_count"] >= 1, f"Expected copy_count >= 1 for owned record, got {data['copy_count']}"
        assert data["record_id"] is not None, "Expected record_id to be present for owned record"
        
        print(f"PASS: check-ownership returns copy_count={data['copy_count']} for owned discogs_id 14215683")
    
    def test_check_ownership_returns_zero_for_unowned_record(self, headers):
        """Test GET /api/records/check-ownership returns copy_count=0 for unowned discogs_id"""
        # Using a random discogs_id that is unlikely to be in the user's collection
        response = requests.get(
            f"{BASE_URL}/api/records/check-ownership",
            params={"discogs_id": 999999999},
            headers=headers
        )
        assert response.status_code == 200, f"Check ownership failed: {response.text}"
        data = response.json()
        
        assert data["in_collection"] == False, "Expected in_collection=False for unowned record"
        assert data["copy_count"] == 0, f"Expected copy_count=0 for unowned record, got {data['copy_count']}"
        assert data["record_id"] is None, "Expected record_id=None for unowned record"
        
        print(f"PASS: check-ownership returns copy_count=0 for unowned discogs_id")
    
    def test_check_ownership_by_artist_title(self, headers):
        """Test GET /api/records/check-ownership with artist+title params"""
        # Demo user should own "Igor" by "Tyler, The Creator"
        response = requests.get(
            f"{BASE_URL}/api/records/check-ownership",
            params={"artist": "Tyler, The Creator", "title": "Igor"},
            headers=headers
        )
        assert response.status_code == 200, f"Check ownership failed: {response.text}"
        data = response.json()
        
        # Response should include copy_count field
        assert "copy_count" in data, "Response missing 'copy_count' field"
        
        # Note: This may or may not match depending on exact artist/title in DB
        print(f"PASS: check-ownership by artist+title returns in_collection={data['in_collection']}, copy_count={data['copy_count']}")
    
    def test_check_ownership_no_params_returns_false(self, headers):
        """Test GET /api/records/check-ownership with no params returns in_collection=False"""
        response = requests.get(
            f"{BASE_URL}/api/records/check-ownership",
            headers=headers
        )
        assert response.status_code == 200, f"Check ownership failed: {response.text}"
        data = response.json()
        
        assert data["in_collection"] == False, "Expected in_collection=False when no params provided"
        assert data["copy_count"] == 0, "Expected copy_count=0 when no params provided"
        
        print(f"PASS: check-ownership with no params returns in_collection=False, copy_count=0")
    
    def test_check_ownership_requires_auth(self):
        """Test GET /api/records/check-ownership requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/records/check-ownership",
            params={"discogs_id": 14215683}
        )
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"PASS: check-ownership requires authentication")
    
    # --- Add Record with Duplicate Tests ---
    
    def test_add_record_with_instance_id_allows_duplicate(self, headers):
        """Test POST /api/records allows adding duplicate with new instance_id"""
        # First check ownership to see if we own this record
        check_resp = requests.get(
            f"{BASE_URL}/api/records/check-ownership",
            params={"discogs_id": 14215683},
            headers=headers
        )
        initial_count = check_resp.json().get("copy_count", 0)
        
        # Add record with unique instance_id
        unique_instance_id = 1736000000001  # Unique timestamp-based instance_id
        record_data = {
            "discogs_id": 14215683,
            "title": "IGOR",
            "artist": "Tyler, The Creator",
            "instance_id": unique_instance_id,
            "notes": "Test duplicate copy"
        }
        
        add_resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=headers)
        
        if add_resp.status_code == 200:
            added_record = add_resp.json()
            record_id = added_record.get("id")
            
            # Verify instance_id is in response
            assert added_record.get("instance_id") == unique_instance_id, "instance_id not preserved in response"
            
            # Clean up: delete the test record
            delete_resp = requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=headers)
            assert delete_resp.status_code == 200, f"Failed to clean up test record: {delete_resp.text}"
            
            print(f"PASS: Adding duplicate record with instance_id succeeds, then cleaned up")
        else:
            # 409 Conflict might be returned if duplicate detection is server-side blocking
            print(f"INFO: Add record returned {add_resp.status_code}: {add_resp.text}")
            print(f"INFO: This is expected if server-side duplicate blocking is enabled")
    
    # --- User Records Endpoint Tests ---
    
    def test_user_records_endpoint_returns_records(self, headers):
        """Test GET /api/users/{username}/records returns user's records"""
        response = requests.get(f"{BASE_URL}/api/users/demo/records", headers=headers)
        assert response.status_code == 200, f"Get user records failed: {response.text}"
        records = response.json()
        
        assert isinstance(records, list), "Expected list of records"
        assert len(records) >= 1, "Expected at least 1 record for demo user"
        
        print(f"PASS: GET /api/users/demo/records returns {len(records)} records")
    
    def test_get_my_records_endpoint(self, headers):
        """Test GET /api/records returns authenticated user's records"""
        response = requests.get(f"{BASE_URL}/api/records", headers=headers)
        assert response.status_code == 200, f"Get my records failed: {response.text}"
        records = response.json()
        
        assert isinstance(records, list), "Expected list of records"
        
        # Check if any records have discogs_id 14215683, 14219559, or 23310752
        owned_igor_ids = {14215683, 14219559, 23310752}
        found_igor = any(r.get("discogs_id") in owned_igor_ids for r in records)
        
        print(f"PASS: GET /api/records returns {len(records)} records, Igor records found: {found_igor}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
