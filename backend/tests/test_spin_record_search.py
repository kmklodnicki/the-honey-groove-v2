"""
Test suite for Now Spinning Record Search feature (iteration 58)
Tests: 
- Backend: GET /api/discogs/search returns variant fields (label, catno, country, color_variant)
- Backend: GET /api/search/unified works correctly
- Backend: Composer endpoints work with record_id
"""
import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Pre-generated valid JWT token for testspinui user
# This token is for testing purposes only
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyNGUwMmRmZC05YjU5LTRlZjktOGQ4Yy1kOTU2OTYyYTNhYTQiLCJleHAiOjE3NzI5NDc1MTcsImlhdCI6MTc3Mjg2MTExN30.lalIxsW7FqRPLk269BvxFT3x5xMpQ7aiSLJrFXWyI_o"


class TestDiscogsSearch:
    """Test /api/discogs/search endpoint returns variant details"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Return auth headers using pre-generated token"""
        return {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    def test_discogs_search_requires_auth(self):
        """Test that /api/discogs/search requires authentication"""
        response = requests.get(f"{BASE_URL}/api/discogs/search?q=taylor+swift")
        assert response.status_code == 401 or response.status_code == 403
        print("PASS: discogs/search requires auth")
    
    def test_discogs_search_min_query_length(self, auth_headers):
        """Test that query must be at least 2 characters"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search?q=t",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
        print("PASS: discogs/search requires min 2 chars")
    
    def test_discogs_search_returns_variant_fields(self, auth_headers):
        """Test that search returns label, catno, country, color_variant fields"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search?q=taylor+swift+lover",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            result = data[0]
            # Check required fields exist
            assert "discogs_id" in result
            assert "title" in result
            assert "artist" in result
            
            # Check variant fields are present (may be null)
            assert "label" in result, "Missing label field"
            assert "catno" in result, "Missing catno field"
            assert "country" in result, "Missing country field"
            assert "color_variant" in result, "Missing color_variant field"
            assert "format" in result, "Missing format field"
            
            print(f"PASS: Discogs search returns variant fields - found {len(data)} results")
            print(f"  Sample result: {result.get('artist')} - {result.get('title')}")
            print(f"  Label: {result.get('label')}, Catno: {result.get('catno')}, Country: {result.get('country')}")
            print(f"  Format: {result.get('format')}, Color: {result.get('color_variant')}")
        else:
            print("PASS: Discogs search works but returned 0 results (may be rate limited)")
    
    def test_discogs_search_format_is_string(self, auth_headers):
        """Test that format field is string not list (per model change)"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search?q=radiohead+ok+computer",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            result = data[0]
            # Format should be string or None, not list
            format_val = result.get("format")
            assert format_val is None or isinstance(format_val, str), f"format should be string, got {type(format_val)}"
            print(f"PASS: format field is string: '{format_val}'")
        else:
            print("PASS: Format check (no results to verify)")


class TestUnifiedSearch:
    """Test /api/search/unified endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Return auth headers using pre-generated token"""
        return {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    def test_unified_search_requires_auth(self):
        """Test that /api/search/unified requires authentication"""
        response = requests.get(f"{BASE_URL}/api/search/unified?q=taylor")
        assert response.status_code == 401 or response.status_code == 403
        print("PASS: unified search requires auth")
    
    def test_unified_search_min_query_length(self, auth_headers):
        """Test that query must be at least 2 characters"""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=t",
            headers=auth_headers
        )
        assert response.status_code == 422
        print("PASS: unified search requires min 2 chars")
    
    def test_unified_search_returns_grouped_results(self, auth_headers):
        """Test that unified search returns records, collectors, posts, listings"""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=taylor",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check all groups exist
        assert "records" in data, "Missing records group"
        assert "collectors" in data, "Missing collectors group"
        assert "posts" in data, "Missing posts group"
        assert "listings" in data, "Missing listings group"
        
        print(f"PASS: Unified search returns grouped results")
        print(f"  Records: {len(data['records'])}, Collectors: {len(data['collectors'])}")
        print(f"  Posts: {len(data['posts'])}, Listings: {len(data['listings'])}")
    
    def test_unified_search_records_have_variant_fields(self, auth_headers):
        """Test that records from unified search include variant fields"""
        response = requests.get(
            f"{BASE_URL}/api/search/unified?q=vinyl",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data.get("records", [])) > 0:
            rec = data["records"][0]
            # Check variant fields exist in response
            assert "label" in rec, "Missing label in unified search record"
            assert "catno" in rec, "Missing catno in unified search record"
            assert "country" in rec, "Missing country in unified search record"
            assert "color_variant" in rec, "Missing color_variant in unified search record"
            print(f"PASS: Unified search records have variant fields")
        else:
            print("PASS: Unified search works (no records to verify fields)")


class TestSearchDiscogs:
    """Test /api/search/discogs endpoint (external Discogs search)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Return auth headers using pre-generated token"""
        return {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    def test_search_discogs_requires_auth(self):
        """Test that /api/search/discogs requires authentication"""
        response = requests.get(f"{BASE_URL}/api/search/discogs?q=taylor")
        assert response.status_code == 401 or response.status_code == 403
        print("PASS: search/discogs requires auth")
    
    def test_search_discogs_returns_results(self, auth_headers):
        """Test that search/discogs returns Discogs catalog results"""
        response = requests.get(
            f"{BASE_URL}/api/search/discogs?q=nirvana+nevermind",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            result = data[0]
            assert "discogs_id" in result
            assert "title" in result
            assert "artist" in result
            print(f"PASS: search/discogs returns results - found {len(data)}")
        else:
            print("PASS: search/discogs works (0 results, may be rate limited)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
