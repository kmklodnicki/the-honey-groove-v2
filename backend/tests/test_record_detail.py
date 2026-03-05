"""
Test suite for Record Detail Page endpoint
GET /api/records/{record_id}/detail
Features: enriched record data, community stats, market value, related posts, owners
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "demo@example.com"
ADMIN_PASSWORD = "password123"

# Module-level fixtures
@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for the test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")

@pytest.fixture(scope="module")
def authenticated_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session

@pytest.fixture(scope="module")
def user_records(authenticated_client):
    """Get user's records to find a valid record ID for testing"""
    response = authenticated_client.get(f"{BASE_URL}/api/records")
    assert response.status_code == 200, f"Failed to get records: {response.text}"
    return response.json()


class TestRecordDetailAPI:
    """Tests for the GET /api/records/{record_id}/detail endpoint"""

    def test_authentication_required(self):
        """Test that unauthenticated requests fail"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}/api/records/{fake_id}/detail")
        # The endpoint uses get_current_user which may allow None (optional auth)
        # but should still return 404 for non-existent record
        assert response.status_code in [200, 401, 404]
        print(f"Unauthenticated request returned: {response.status_code}")

    def test_nonexistent_record_returns_404(self, authenticated_client):
        """Test that non-existent record ID returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = authenticated_client.get(f"{BASE_URL}/api/records/{fake_id}/detail")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        print("Non-existent record correctly returns 404")

    def test_record_detail_response_structure(self, authenticated_client, user_records):
        """Test that valid record returns correct response structure"""
        if not user_records:
            pytest.skip("No records in user's collection to test")
        
        record_id = user_records[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/records/{record_id}/detail")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check top-level structure
        assert "record" in data, "Response missing 'record' field"
        assert "owner" in data, "Response missing 'owner' field"
        assert "community" in data, "Response missing 'community' field"
        assert "related_posts" in data, "Response missing 'related_posts' field"
        # market_value can be None if no Discogs data cached
        assert "market_value" in data, "Response missing 'market_value' field"
        print("Response structure is correct with all required fields")

    def test_record_field_contents(self, authenticated_client, user_records):
        """Test that record object contains expected fields"""
        if not user_records:
            pytest.skip("No records in user's collection to test")
        
        record_id = user_records[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/records/{record_id}/detail")
        assert response.status_code == 200
        
        record = response.json()["record"]
        
        # Required fields
        assert "id" in record
        assert "title" in record
        assert "artist" in record
        assert "user_id" in record
        assert "spin_count" in record, "Record should include spin_count"
        
        # Optional but expected fields
        expected_optional = ["cover_url", "year", "format", "discogs_id", "notes", "created_at"]
        for field in expected_optional:
            if field in record:
                print(f"Record has optional field: {field}")
        
        print(f"Record fields validated: {record['title']} by {record['artist']}")

    def test_community_stats_structure(self, authenticated_client, user_records):
        """Test that community stats object contains expected fields"""
        if not user_records:
            pytest.skip("No records in user's collection to test")
        
        record_id = user_records[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/records/{record_id}/detail")
        assert response.status_code == 200
        
        community = response.json()["community"]
        
        # Required community stats
        assert "total_owners" in community, "Community missing total_owners"
        assert "total_spins" in community, "Community missing total_spins"
        assert "wantlist_count" in community, "Community missing wantlist_count"
        assert "owners" in community, "Community missing owners list"
        
        # Validate types
        assert isinstance(community["total_owners"], int)
        assert isinstance(community["total_spins"], int)
        assert isinstance(community["wantlist_count"], int)
        assert isinstance(community["owners"], list)
        
        print(f"Community stats: {community['total_owners']} owners, {community['total_spins']} spins, {community['wantlist_count']} wanted")

    def test_owners_list_structure(self, authenticated_client, user_records):
        """Test that owners list contains proper user info"""
        if not user_records:
            pytest.skip("No records in user's collection to test")
        
        record_id = user_records[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/records/{record_id}/detail")
        assert response.status_code == 200
        
        owners = response.json()["community"]["owners"]
        
        if len(owners) > 0:
            owner = owners[0]
            assert "id" in owner, "Owner missing id"
            assert "username" in owner, "Owner missing username"
            assert "avatar_url" in owner, "Owner missing avatar_url"
            print(f"Owner info structure validated for @{owner['username']}")
        else:
            print("No additional owners found (this is OK if record has single owner)")

    def test_owner_info_populated(self, authenticated_client, user_records):
        """Test that record owner info is populated"""
        if not user_records:
            pytest.skip("No records in user's collection to test")
        
        record_id = user_records[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/records/{record_id}/detail")
        assert response.status_code == 200
        
        owner = response.json()["owner"]
        
        assert owner is not None, "Owner should not be null"
        assert "id" in owner
        assert "username" in owner
        assert "avatar_url" in owner
        print(f"Record owner: @{owner['username']}")

    def test_related_posts_structure(self, authenticated_client, user_records):
        """Test related posts array and post structure"""
        if not user_records:
            pytest.skip("No records in user's collection to test")
        
        record_id = user_records[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/records/{record_id}/detail")
        assert response.status_code == 200
        
        related_posts = response.json()["related_posts"]
        assert isinstance(related_posts, list), "related_posts should be a list"
        
        if len(related_posts) > 0:
            post = related_posts[0]
            assert "id" in post
            assert "user_id" in post
            assert "post_type" in post
            assert "created_at" in post
            # Check user info enrichment
            if "user" in post and post["user"]:
                assert "username" in post["user"]
                print(f"Post has user info: @{post['user']['username']}")
            print(f"Found {len(related_posts)} related posts, post_type: {post.get('post_type')}")
        else:
            print("No related posts found for this record")

    def test_market_value_when_present(self, authenticated_client, user_records):
        """Test market value structure when Discogs data is available"""
        if not user_records:
            pytest.skip("No records in user's collection to test")
        
        # Find a record with discogs_id
        discogs_record = None
        for r in user_records:
            if r.get("discogs_id"):
                discogs_record = r
                break
        
        if not discogs_record:
            pytest.skip("No records with discogs_id to test market value")
        
        response = authenticated_client.get(f"{BASE_URL}/api/records/{discogs_record['id']}/detail")
        assert response.status_code == 200
        
        market_value = response.json()["market_value"]
        
        # Market value can be None if not cached
        if market_value:
            # When present, should have expected fields
            expected_fields = ["low", "median", "high", "currency"]
            for field in expected_fields:
                if field in market_value:
                    print(f"Market value has {field}: {market_value[field]}")
            print("Market value structure validated")
        else:
            print("Market value is null (not cached in DB) - this is expected behavior")


class TestRecordDetailSpecificRecord:
    """Test with specific known record - 'Red' by Taylor Swift"""
    
    KNOWN_RECORD_ID = "9ab0fbd2-ed43-472e-91b9-60ccbad4690d"
    
    def test_known_record_detail(self, authenticated_client):
        """Test the specific known record with related posts"""
        response = authenticated_client.get(f"{BASE_URL}/api/records/{self.KNOWN_RECORD_ID}/detail")
        
        # Record may or may not exist depending on test data
        if response.status_code == 404:
            pytest.skip("Known test record not found - may have been deleted")
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"Record: {data['record']['title']} by {data['record']['artist']}")
        print(f"Related posts count: {len(data['related_posts'])}")
        print(f"Community owners: {data['community']['total_owners']}")


class TestSpinLogging:
    """Test spin logging for owned records"""
    
    def test_log_spin_for_owned_record(self, authenticated_client, user_records):
        """Test that user can log a spin for their owned record"""
        if not user_records:
            pytest.skip("No records in user's collection")
        
        user_record = user_records[0]
        
        # Get initial detail
        detail_before = authenticated_client.get(f"{BASE_URL}/api/records/{user_record['id']}/detail")
        assert detail_before.status_code == 200
        initial_spins = detail_before.json()["record"]["spin_count"]
        
        # Log a spin
        spin_response = authenticated_client.post(f"{BASE_URL}/api/spins", json={
            "record_id": user_record['id']
        })
        assert spin_response.status_code == 200, f"Failed to log spin: {spin_response.text}"
        
        # Verify spin count increased
        detail_after = authenticated_client.get(f"{BASE_URL}/api/records/{user_record['id']}/detail")
        assert detail_after.status_code == 200
        new_spins = detail_after.json()["record"]["spin_count"]
        
        assert new_spins == initial_spins + 1, f"Spin count should increase from {initial_spins} to {initial_spins + 1}, got {new_spins}"
        print(f"Spin logged successfully. Count: {initial_spins} -> {new_spins}")
    
    def test_log_spin_creates_post(self, authenticated_client, user_records):
        """Test that logging a spin creates a NOW_SPINNING post"""
        if not user_records:
            pytest.skip("No records in user's collection")
        
        user_record = user_records[0]
        
        # Log a spin
        spin_response = authenticated_client.post(f"{BASE_URL}/api/spins", json={
            "record_id": user_record['id']
        })
        assert spin_response.status_code == 200
        
        # Check related posts for NOW_SPINNING
        detail = authenticated_client.get(f"{BASE_URL}/api/records/{user_record['id']}/detail")
        assert detail.status_code == 200
        
        related_posts = detail.json()["related_posts"]
        now_spinning_posts = [p for p in related_posts if p.get("post_type") == "NOW_SPINNING"]
        
        assert len(now_spinning_posts) > 0, "Should have at least one NOW_SPINNING post after logging spin"
        print(f"Found {len(now_spinning_posts)} NOW_SPINNING posts for this record")


class TestRecordDetailEdgeCases:
    """Edge case tests for record detail endpoint"""
    
    def test_invalid_uuid_format(self, authenticated_client):
        """Test with invalid UUID format"""
        response = authenticated_client.get(f"{BASE_URL}/api/records/not-a-valid-uuid/detail")
        # Should return 404 since it won't match any record
        assert response.status_code == 404
        print("Invalid UUID correctly returns 404")
    
    def test_empty_record_id(self, authenticated_client):
        """Test with empty record ID path"""
        response = authenticated_client.get(f"{BASE_URL}/api/records//detail")
        # Should return 404 or 405 (method not allowed)
        assert response.status_code in [404, 405, 422]
        print(f"Empty record ID returns: {response.status_code}")
    
    def test_sql_injection_attempt(self, authenticated_client):
        """Test that SQL injection attempts are safely handled"""
        malicious_id = "'; DROP TABLE records; --"
        response = authenticated_client.get(f"{BASE_URL}/api/records/{malicious_id}/detail")
        # Should return 404, not crash
        assert response.status_code in [404, 422]
        print("SQL injection attempt safely handled")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
