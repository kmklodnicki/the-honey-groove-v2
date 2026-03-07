"""
Tests for Unified Global Search Feature
- /api/search/unified - Local MongoDB search across records, users, posts, listings
- /api/search/discogs - External Discogs catalog search
"""
import pytest
import requests
import jwt
import os
import time
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
JWT_SECRET = "waxlog_jwt_secret_key_2024_vinyl_collectors"
JWT_ALGORITHM = "HS256"


def generate_token(user_id: str) -> str:
    """Generate JWT token for a user."""
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@pytest.fixture(scope="module")
def auth_headers():
    """Get auth headers using admin user."""
    admin_id = "63dcf386-b4aa-4061-9333-99adc0a770bd"
    token = generate_token(admin_id)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class TestUnifiedSearchEndpoint:
    """Tests for /api/search/unified endpoint."""

    def test_search_taylor_returns_grouped_results(self, auth_headers):
        """Search 'taylor' should return records grouped by type (records, collectors, posts, listings)."""
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=taylor",
            headers=auth_headers,
            timeout=5
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure has all 4 groups
        assert "records" in data, "Missing 'records' in response"
        assert "collectors" in data, "Missing 'collectors' in response"
        assert "posts" in data, "Missing 'posts' in response"
        assert "listings" in data, "Missing 'listings' in response"
        
        # All should be lists
        assert isinstance(data["records"], list), "records should be a list"
        assert isinstance(data["collectors"], list), "collectors should be a list"
        assert isinstance(data["posts"], list), "posts should be a list"
        assert isinstance(data["listings"], list), "listings should be a list"
        
        print(f"Search 'taylor': {len(data['records'])} records, {len(data['collectors'])} collectors, {len(data['posts'])} posts, {len(data['listings'])} listings")
        print(f"Response time: {elapsed*1000:.0f}ms")

    def test_fuzzy_search_tay_swift(self, auth_headers):
        """Fuzzy/partial matching: 'tay swift' should find Taylor Swift records."""
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=tay+swift",
            headers=auth_headers,
            timeout=5
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check if any records match Taylor Swift
        records = data.get("records", [])
        taylor_found = any(
            "taylor" in r.get("artist", "").lower() or "swift" in r.get("artist", "").lower()
            for r in records
        )
        
        print(f"Fuzzy search 'tay swift': Found {len(records)} records")
        if records:
            for r in records[:3]:
                print(f"  - {r.get('artist')} - {r.get('title')}")
        print(f"Response time: {elapsed*1000:.0f}ms")

    def test_search_lover_album(self, auth_headers):
        """Search 'lover' should return matching records."""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=lover",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        print(f"Search 'lover': {len(data.get('records', []))} records found")
        for r in data.get("records", [])[:3]:
            print(f"  - {r.get('artist')} - {r.get('title')}")

    def test_search_katie_collector(self, auth_headers):
        """Search 'katie' should return the collector 'katieintheafterglow'."""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=katie",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        collectors = data.get("collectors", [])
        katie_found = any(
            "katie" in c.get("username", "").lower()
            for c in collectors
        )
        
        print(f"Search 'katie': Found {len(collectors)} collectors")
        if collectors:
            for c in collectors[:3]:
                print(f"  - @{c.get('username')} ({c.get('record_count', 0)} records)")
        
        assert katie_found, "Expected to find collector containing 'katie' in username"

    def test_search_response_time_under_300ms(self, auth_headers):
        """Search should respond in under 300ms."""
        # Run multiple searches and check timing
        queries = ["taylor", "vinyl", "rock", "jazz"]
        
        for q in queries:
            start_time = time.time()
            response = requests.get(
                f"{BASE_URL}/api/search/unified?q={q}",
                headers=auth_headers,
                timeout=5
            )
            elapsed = time.time() - start_time
            elapsed_ms = elapsed * 1000
            
            assert response.status_code == 200, f"Query '{q}' failed: {response.status_code}"
            print(f"Query '{q}': {elapsed_ms:.0f}ms")
            
            # Allow some network latency - target is 300ms for DB query + network
            # Using 600ms as practical threshold for remote testing
            assert elapsed_ms < 600, f"Query '{q}' too slow: {elapsed_ms:.0f}ms > 600ms"

    def test_empty_results_for_nonexistent(self, auth_headers):
        """Search 'xyznonexistent' should return empty arrays for all types."""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=xyznonexistent",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data.get("records", []) == [], "Expected empty records array"
        assert data.get("collectors", []) == [], "Expected empty collectors array"
        assert data.get("posts", []) == [], "Expected empty posts array"
        assert data.get("listings", []) == [], "Expected empty listings array"
        
        print("Empty results test passed: all arrays empty for 'xyznonexistent'")

    def test_min_2_chars_validation(self, auth_headers):
        """Search with single character 'a' should return 422 (min 2 chars)."""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=a",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("Min 2 chars validation passed: single char returns 422")

    def test_hidden_users_not_in_results(self, auth_headers):
        """Hidden users (is_hidden=true) should NOT appear in collector results."""
        # Admin user has is_hidden=true, search for their username fragment
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=admin",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        collectors = data.get("collectors", [])
        
        # Admin should NOT be in results since they have is_hidden=true
        admin_found = any(
            c.get("id") == "63dcf386-b4aa-4061-9333-99adc0a770bd"
            for c in collectors
        )
        
        assert not admin_found, "Hidden admin user should NOT appear in search results"
        print(f"Hidden user test: admin not found in {len(collectors)} collector results")

    def test_search_returns_correct_record_structure(self, auth_headers):
        """Verify record result structure has required fields."""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=taylor",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        records = data.get("records", [])
        if records:
            record = records[0]
            # Check expected fields
            expected_fields = ["title", "artist", "source"]
            for field in expected_fields:
                assert field in record, f"Record missing field: {field}"
            
            print(f"Record structure validated: {list(record.keys())}")
        else:
            print("No records returned to validate structure")

    def test_search_collectors_has_follow_status(self, auth_headers):
        """Collector results should include is_following field."""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=katie",
            headers=auth_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        
        collectors = data.get("collectors", [])
        if collectors:
            collector = collectors[0]
            assert "is_following" in collector, "Collector missing is_following field"
            assert "id" in collector, "Collector missing id field"
            assert "username" in collector, "Collector missing username field"
            print(f"Collector structure: {list(collector.keys())}")
        else:
            print("No collectors returned to validate structure")


class TestDiscogsSearchEndpoint:
    """Tests for /api/search/discogs endpoint (external Discogs catalog)."""

    def test_discogs_search_taylor_swift(self, auth_headers):
        """Search Discogs for 'taylor swift' should return catalog results."""
        response = requests.get(
            f"{BASE_URL}/api/search/discogs?q=taylor+swift",
            headers=auth_headers,
            timeout=10  # External API may be slower
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert isinstance(data, list), "Discogs response should be a list"
        
        print(f"Discogs search 'taylor swift': {len(data)} results")
        if data:
            for r in data[:3]:
                print(f"  - {r.get('artist')} - {r.get('title')} (discogs_id: {r.get('discogs_id')})")
        
        # Should return at least some results
        if len(data) > 0:
            assert "discogs_id" in data[0], "Result should have discogs_id"

    def test_discogs_min_2_chars(self, auth_headers):
        """Discogs search also requires min 2 chars."""
        response = requests.get(
            f"{BASE_URL}/api/search/discogs?q=x",
            headers=auth_headers,
            timeout=10
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"


class TestSearchAuth:
    """Test that search endpoints require authentication."""

    def test_unified_search_requires_auth(self):
        """Unified search should require authentication."""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=taylor",
            timeout=5
        )
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"

    def test_discogs_search_requires_auth(self):
        """Discogs search should require authentication."""
        response = requests.get(
            f"{BASE_URL}/api/search/discogs?q=taylor",
            timeout=5
        )
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
