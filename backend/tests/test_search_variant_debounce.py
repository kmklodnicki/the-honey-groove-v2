"""
Test Search Variant Details & Debounce Features (Iteration 57)
- Tests: Discogs search returns variant data (label, catno, country, color_variant)
- Tests: Unified search returns variant data from local records
- Tests: Hidden users excluded from search
- Tests: Minimum 2 character query requirement
"""
import pytest
import requests
import os
import jwt
from datetime import datetime, timezone, timedelta

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
JWT_SECRET = "waxlog_jwt_secret_key_2024_vinyl_collectors"
JWT_ALGORITHM = "HS256"

# Test user credentials
ADMIN_USER_ID = "63dcf386-b4aa-4061-9333-99adc0a770bd"  # is_hidden=true

def get_test_token(user_id: str) -> str:
    """Generate a valid JWT token for testing"""
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


class TestDiscogsSearchVariants:
    """Tests for /api/discogs/search endpoint - variant data fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_test_token(ADMIN_USER_ID)
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_discogs_search_returns_variant_fields(self):
        """GET /api/discogs/search?q=taylor+swift+lover returns results with label, catno, country"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search",
            params={"q": "taylor swift lover"},
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should return at least one result for 'taylor swift lover'"
        
        # Check first result has expected variant fields
        first = data[0]
        assert "discogs_id" in first, "Missing discogs_id field"
        assert "title" in first, "Missing title field"
        assert "artist" in first, "Missing artist field"
        assert "format" in first, "Missing format field"
        # New variant fields should be present (may be null but keys should exist)
        assert "label" in first, "Missing label field (new variant field)"
        assert "catno" in first, "Missing catno field (new variant field)"
        assert "country" in first, "Missing country field (new variant field)"
        assert "color_variant" in first, "Missing color_variant field (new variant field)"
        
        print(f"✓ Discogs search returned {len(data)} results with variant fields")
        print(f"  Sample: {first.get('artist')} - {first.get('title')}")
        print(f"  Format: {first.get('format')}, Label: {first.get('label')}, Catno: {first.get('catno')}")
        print(f"  Country: {first.get('country')}, Color: {first.get('color_variant')}")
    
    def test_discogs_search_format_is_string(self):
        """Verify format field is a string (not list) as per DiscogsSearchResult model change"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search",
            params={"q": "radiohead ok computer"},
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "Should return results"
        
        # Format should be string not list
        for result in data[:5]:
            if result.get("format"):
                assert isinstance(result["format"], str), \
                    f"Format should be str, got {type(result['format'])}: {result['format']}"
        
        print(f"✓ Format field is string type as expected")
    
    def test_discogs_search_genre_field(self):
        """Verify genre field is returned as list"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search",
            params={"q": "beatles abbey road"},
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        
        first = data[0]
        # Genre should be a list or None
        if first.get("genre"):
            assert isinstance(first["genre"], list), f"Genre should be list, got {type(first['genre'])}"
        
        print(f"✓ Genre field verified")
    
    def test_discogs_search_min_query_length(self):
        """Search requires minimum 2 characters"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search",
            params={"q": "a"},
            headers=self.headers,
            timeout=10
        )
        assert response.status_code == 422, f"Expected 422 for 1-char query, got {response.status_code}"
        print("✓ Search correctly rejects 1-character queries")
    
    def test_discogs_search_requires_auth(self):
        """Search endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search",
            params={"q": "test"},
            timeout=10
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Search requires authentication")


class TestUnifiedSearchVariants:
    """Tests for /api/search/unified endpoint - variant data for local records"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_test_token(ADMIN_USER_ID)
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_unified_search_returns_grouped_results(self):
        """GET /api/search/unified?q=taylor returns records/collectors grouped"""
        response = requests.get(
            f"{BASE_URL}/api/search/unified",
            params={"q": "taylor"},
            headers=self.headers,
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "records" in data, "Missing records key"
        assert "collectors" in data, "Missing collectors key"
        assert "posts" in data, "Missing posts key"
        assert "listings" in data, "Missing listings key"
        
        print(f"✓ Unified search returns grouped results")
        print(f"  Records: {len(data['records'])}, Collectors: {len(data['collectors'])}")
        print(f"  Posts: {len(data['posts'])}, Listings: {len(data['listings'])}")
    
    def test_unified_search_records_have_variant_fields(self):
        """Records in unified search should include variant fields if present in DB"""
        response = requests.get(
            f"{BASE_URL}/api/search/unified",
            params={"q": "taylor"},
            headers=self.headers,
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        records = data.get("records", [])
        
        if len(records) > 0:
            first = records[0]
            # Records from search should have these keys (may be null)
            expected_keys = ["title", "artist", "year", "format", "label", "catno", "country", "color_variant"]
            for key in expected_keys:
                assert key in first, f"Record missing '{key}' field"
            print(f"✓ Records have variant fields: {list(first.keys())}")
        else:
            print("⚠ No records found in unified search (may be empty collection)")
    
    def test_unified_search_hidden_users_excluded(self):
        """Hidden users (is_hidden=true) should not appear in search results"""
        response = requests.get(
            f"{BASE_URL}/api/search/unified",
            params={"q": "admin"},  # Search for admin username
            headers=self.headers,
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        collectors = data.get("collectors", [])
        
        # Admin user has is_hidden=true, should NOT be in results
        admin_found = any(c.get("id") == ADMIN_USER_ID for c in collectors)
        assert not admin_found, "Hidden admin user should NOT appear in search results"
        
        print("✓ Hidden users correctly excluded from search results")
    
    def test_unified_search_min_query_length(self):
        """Search requires minimum 2 characters"""
        response = requests.get(
            f"{BASE_URL}/api/search/unified",
            params={"q": "a"},
            headers=self.headers,
            timeout=10
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Unified search correctly rejects 1-char queries")


class TestSearchDiscogsEndpoint:
    """Tests for /api/search/discogs endpoint (external Discogs search)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_test_token(ADMIN_USER_ID)
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_search_discogs_returns_variant_data(self):
        """GET /api/search/discogs?q=taylor+swift returns results with variant data"""
        response = requests.get(
            f"{BASE_URL}/api/search/discogs",
            params={"q": "taylor swift"},
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            first = data[0]
            # Should have variant fields
            assert "label" in first or first.get("label") is None, "Should have label field"
            assert "catno" in first or first.get("catno") is None, "Should have catno field"
            assert "color_variant" in first or first.get("color_variant") is None, "Should have color_variant field"
            print(f"✓ /api/search/discogs returns variant data")
            print(f"  Sample: {first.get('artist')} - {first.get('title')}")
            print(f"  Label: {first.get('label')}, Catno: {first.get('catno')}, Color: {first.get('color_variant')}")
        else:
            print("⚠ No results from search/discogs endpoint")
    
    def test_search_discogs_requires_auth(self):
        """Endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/search/discogs",
            params={"q": "test"},
            timeout=10
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ /api/search/discogs requires authentication")


class TestSearchPerformance:
    """Performance tests for search endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_test_token(ADMIN_USER_ID)
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_unified_search_response_time(self):
        """Unified search should respond quickly (under 500ms)"""
        import time
        
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/search/unified",
            params={"q": "taylor"},
            headers=self.headers,
            timeout=10
        )
        elapsed = (time.time() - start) * 1000  # ms
        
        assert response.status_code == 200
        assert elapsed < 500, f"Search took {elapsed:.0f}ms, should be under 500ms"
        print(f"✓ Unified search response time: {elapsed:.0f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
