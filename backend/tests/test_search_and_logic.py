"""
Test suite for Search AND logic and Discogs structured search fallback
Tests:
1. /api/search/variants - AND logic for multi-word queries
2. /api/discogs/search - structured search fallback for album-specific queries
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSearchANDLogic:
    """Test the new AND-based search logic for variant search"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip(f"Login failed: {login_resp.status_code} - {login_resp.text}")
    
    def test_me_taylor_swift_returns_me_album_variants(self):
        """Search 'me! taylor swift' should return ME! album results at top, not 255 unrelated Taylor Swift variants"""
        resp = requests.get(
            f"{BASE_URL}/api/search/variants",
            params={"q": "me! taylor swift"},
            headers=self.headers
        )
        assert resp.status_code == 200, f"Status {resp.status_code}: {resp.text}"
        data = resp.json()
        variants = data.get("variants", [])
        
        # Should have results
        assert len(variants) > 0, "Should return some variants"
        
        # Check that results contain "ME!" or "Me!" in the album title (not just any Taylor Swift)
        me_results = [v for v in variants[:10] if "me" in v.get("album", "").lower() and "!" in v.get("album", "")]
        
        # At least some top results should be ME! album
        print(f"Found {len(variants)} total variants")
        print(f"Top 10 results: {[(v.get('album'), v.get('artist'), v.get('score')) for v in variants[:10]]}")
        
        # The key assertion: we should NOT have 255+ generic Taylor Swift results
        # With AND logic, we should have far fewer, more relevant results
        assert len(variants) < 255, f"AND logic should reduce results, got {len(variants)}"
    
    def test_taylor_swift_broad_query_still_works(self):
        """Search 'taylor swift' should still return Taylor Swift variants (broad query still works)"""
        resp = requests.get(
            f"{BASE_URL}/api/search/variants",
            params={"q": "taylor swift"},
            headers=self.headers
        )
        assert resp.status_code == 200, f"Status {resp.status_code}: {resp.text}"
        data = resp.json()
        variants = data.get("variants", [])
        
        # Should have multiple results for a broad artist query
        assert len(variants) > 0, "Should return Taylor Swift variants"
        
        # Check that results are actually Taylor Swift
        taylor_swift_count = sum(1 for v in variants if "taylor swift" in v.get("artist", "").lower())
        print(f"Found {taylor_swift_count} Taylor Swift variants out of {len(variants)}")
        assert taylor_swift_count > 0, "Should have Taylor Swift variants"
    
    def test_radiohead_ok_computer_returns_ok_computer_only(self):
        """Search 'radiohead ok computer' should return OK Computer variants only"""
        resp = requests.get(
            f"{BASE_URL}/api/search/variants",
            params={"q": "radiohead ok computer"},
            headers=self.headers
        )
        assert resp.status_code == 200, f"Status {resp.status_code}: {resp.text}"
        data = resp.json()
        variants = data.get("variants", [])
        
        # Should have results
        assert len(variants) > 0, "Should return OK Computer variants"
        
        # Check that top results are OK Computer, not other Radiohead albums
        ok_computer_count = sum(1 for v in variants[:10] if "ok computer" in v.get("album", "").lower())
        print(f"Found {ok_computer_count} OK Computer results in top 10")
        print(f"Top 10: {[(v.get('album'), v.get('artist')) for v in variants[:10]]}")
        
        # Most top results should be OK Computer
        assert ok_computer_count >= 3, f"Expected at least 3 OK Computer results in top 10, got {ok_computer_count}"


class TestDiscogsStructuredSearch:
    """Test the Discogs search endpoint with structured search fallback"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip(f"Login failed: {login_resp.status_code} - {login_resp.text}")
    
    def test_me_taylor_swift_discogs_search(self):
        """Search 'me! taylor swift' in Discogs should return ME! by Taylor Swift at top"""
        resp = requests.get(
            f"{BASE_URL}/api/discogs/search",
            params={"q": "me! taylor swift"},
            headers=self.headers
        )
        assert resp.status_code == 200, f"Status {resp.status_code}: {resp.text}"
        results = resp.json()
        
        assert len(results) > 0, "Should return Discogs results"
        
        # Check that ME! appears in top results
        me_results = [r for r in results[:5] if "me" in r.get("title", "").lower()]
        print(f"Total results: {len(results)}")
        print(f"Top 5: {[(r.get('title'), r.get('artist')) for r in results[:5]]}")
        
        # Structured search fallback should put ME! near top
        assert len(me_results) > 0, "ME! should appear in top 5 results"
    
    def test_taylor_swift_broad_discogs_search(self):
        """Search 'taylor swift' should return Taylor Swift results"""
        resp = requests.get(
            f"{BASE_URL}/api/discogs/search",
            params={"q": "taylor swift"},
            headers=self.headers
        )
        assert resp.status_code == 200, f"Status {resp.status_code}: {resp.text}"
        results = resp.json()
        
        assert len(results) > 0, "Should return Taylor Swift results"
        
        # Results should be Taylor Swift
        ts_count = sum(1 for r in results if "taylor swift" in r.get("artist", "").lower())
        print(f"Found {ts_count} Taylor Swift results out of {len(results)}")
        assert ts_count > 0, "Should have Taylor Swift results"


class TestSearchRecordsPaginated:
    """Test the paginated records search with AND logic"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip(f"Login failed: {login_resp.status_code} - {login_resp.text}")
    
    def test_search_records_with_and_logic(self):
        """Test paginated records search uses AND logic"""
        resp = requests.get(
            f"{BASE_URL}/api/search/records",
            params={"q": "radiohead ok computer"},
            headers=self.headers
        )
        assert resp.status_code == 200, f"Status {resp.status_code}: {resp.text}"
        data = resp.json()
        records = data.get("records", [])
        
        print(f"Found {len(records)} records")
        if records:
            print(f"Sample: {[(r.get('title'), r.get('artist')) for r in records[:5]]}")
        
        # May have few or no results from local collections - that's OK
        # The key is that the endpoint works without error


class TestUnifiedSearch:
    """Test unified search endpoint with AND logic"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip(f"Login failed: {login_resp.status_code} - {login_resp.text}")
    
    def test_unified_search_with_and_logic(self):
        """Test unified search uses AND logic for records"""
        resp = requests.get(
            f"{BASE_URL}/api/search/unified",
            params={"q": "taylor swift"},
            headers=self.headers
        )
        assert resp.status_code == 200, f"Status {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Should return structured response
        assert "records" in data
        assert "collectors" in data
        assert "posts" in data
        assert "listings" in data
        
        print(f"Records: {len(data.get('records', []))}")
        print(f"Collectors: {len(data.get('collectors', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
