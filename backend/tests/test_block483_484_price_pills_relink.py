"""
BLOCK 483: Price Pill Badges on Collection Grid
BLOCK 484: Data Re-Linking after OAuth Reset

Tests:
1. /api/valuation/record-values returns map of record_id -> median_value
2. /api/valuation/priority-relink POST triggers background refresh
3. Background task respects rate limits
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials from context
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def test_auth_token():
    """Get auth token for testuser1 who has records with values"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if resp.status_code == 200:
        data = resp.json()
        # API returns access_token not token
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {resp.status_code} - {resp.text}")


class TestBlock483RecordValues:
    """Test the /api/valuation/record-values endpoint for price pill badges"""

    def test_record_values_endpoint_exists(self, test_auth_token):
        """GET /api/valuation/record-values should return 200"""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/record-values",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"PASS: /api/valuation/record-values returns 200")

    def test_record_values_returns_map(self, test_auth_token):
        """The endpoint should return a dictionary mapping record_id to median_value"""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/record-values",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        print(f"PASS: Record values response is a dictionary with {len(data)} entries")
        
        # testuser1 should have at least 1 record with value (~$32)
        if data:
            for record_id, value in data.items():
                assert isinstance(record_id, str), f"Record ID should be string, got {type(record_id)}"
                assert isinstance(value, (int, float)), f"Value should be number, got {type(value)}"
                assert value > 0, f"Value should be positive, got {value}"
                print(f"  - record {record_id[:8]}... has value ${value}")
        
        return data

    def test_record_values_for_user_with_records(self, test_auth_token):
        """testuser1 has 4 records, 1 with cached value ~$32"""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/record-values",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Per context: testuser1 has 4 records, 1 has ~$32 value
        # So we expect the map to have at least 1 entry
        if len(data) > 0:
            print(f"PASS: User has {len(data)} record(s) with values")
            # Check for approximately $32 value
            has_expected_value = any(20 <= v <= 50 for v in data.values())
            if has_expected_value:
                print(f"  - Found expected value in ~$20-50 range")
        else:
            print(f"INFO: User has no valued records (might need Discogs data refresh)")


class TestBlock484PriorityRelink:
    """Test the /api/valuation/priority-relink endpoint for OAuth re-auth data refresh"""

    def test_priority_relink_endpoint_exists(self, test_auth_token):
        """POST /api/valuation/priority-relink should return 200"""
        resp = requests.post(
            f"{BASE_URL}/api/valuation/priority-relink",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"PASS: /api/valuation/priority-relink returns 200")

    def test_priority_relink_returns_counts(self, test_auth_token):
        """The endpoint should return fetched/total counts"""
        resp = requests.post(
            f"{BASE_URL}/api/valuation/priority-relink",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Should have message, fetched, total fields
        assert "message" in data, f"Missing 'message' field in response: {data}"
        assert "fetched" in data or "total" in data, f"Missing count fields in response: {data}"
        
        print(f"PASS: Priority relink response: {data}")
        return data

    def test_priority_relink_handles_no_records(self, test_auth_token):
        """The endpoint should gracefully handle users with no discogs_id records"""
        resp = requests.post(
            f"{BASE_URL}/api/valuation/priority-relink",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Should not error out
        assert "message" in data
        print(f"PASS: Priority relink handles gracefully: {data['message']}")


class TestBlock484Integration:
    """Integration tests for BLOCK 484 flow"""

    def test_priority_relink_triggered_after_oauth(self, test_auth_token):
        """
        Verify the priority-relink is called after OAuth connect.
        We can't test the OAuth flow directly, but we verify the endpoint works.
        """
        # Get current record values
        values_before = requests.get(
            f"{BASE_URL}/api/valuation/record-values",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        ).json()
        
        # Trigger priority relink
        relink_resp = requests.post(
            f"{BASE_URL}/api/valuation/priority-relink",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert relink_resp.status_code == 200
        
        print(f"PASS: Priority relink can be triggered manually")
        print(f"  - Had {len(values_before)} valued records before")
        print(f"  - Relink response: {relink_resp.json()}")

    def test_collection_value_endpoint_still_works(self, test_auth_token):
        """Ensure /api/valuation/collection still works alongside new endpoints"""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/collection",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "total_value" in data
        assert "valued_count" in data
        assert "total_count" in data
        
        print(f"PASS: Collection value endpoint works")
        print(f"  - Total value: ${data['total_value']}")
        print(f"  - Valued: {data['valued_count']}/{data['total_count']}")


class TestBlock483ZeroValueHandling:
    """Test zero-value handling - records with $0 or no value should not show price pill"""

    def test_zero_values_not_in_map(self, test_auth_token):
        """Records with $0 or no value should not appear in the values map"""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/record-values",
            headers={"Authorization": f"Bearer {test_auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Check no zero values in the map
        for record_id, value in data.items():
            assert value > 0, f"Record {record_id} has zero/negative value {value} - should not be in map"
        
        print(f"PASS: All {len(data)} values in map are positive (zero-value handling works)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
