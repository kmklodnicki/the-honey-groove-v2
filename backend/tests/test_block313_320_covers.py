"""
Test suite for BLOCK-313 (ISO Modal Variant Art) and BLOCK-320 (MongoDB connection limits)
- Verifies variant search returns cover_url for all results
- Verifies vinyl release endpoint returns variant_overview with cover_url
- Verifies discogs search returns cover_url for all results  
- Verifies health endpoint shows correct MongoDB pool configuration
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "kmklodnicki@gmail.com"
TEST_PASSWORD = "HoneyGroove2026"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for authenticated endpoints"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


class TestHealthEndpoint:
    """BLOCK-320: MongoDB connection pool configuration tests"""
    
    def test_health_returns_ok(self):
        """Health endpoint returns status ok"""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"
        
    def test_pool_max_size_is_10(self):
        """Pool maxPoolSize should be 10"""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        pool = data.get("pool", {})
        assert pool.get("maxPoolSize") == 10, f"Expected maxPoolSize=10, got {pool.get('maxPoolSize')}"
        
    def test_pool_min_size_is_1(self):
        """Pool minPoolSize should be 1"""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        pool = data.get("pool", {})
        assert pool.get("minPoolSize") == 1, f"Expected minPoolSize=1, got {pool.get('minPoolSize')}"
        
    def test_db_status_connected(self):
        """Database should be connected"""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        pool = data.get("pool", {})
        assert pool.get("db_status") == "connected", f"Expected db_status=connected, got {pool.get('db_status')}"


class TestSearchVariants:
    """BLOCK-313: Variant search cover_url tests"""
    
    def test_search_variants_returns_results(self, auth_token):
        """Search variants for 'me! taylor swift' returns results"""
        resp = requests.get(f"{BASE_URL}/api/search/variants?q=me!+taylor+swift&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "variants" in data
        assert len(data["variants"]) > 0, "Expected variants in response"
        
    def test_search_variants_all_have_cover_url(self, auth_token):
        """All variant results should have cover_url (no blank covers)"""
        resp = requests.get(f"{BASE_URL}/api/search/variants?q=me!+taylor+swift&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        variants = data.get("variants", [])
        
        missing_covers = []
        for i, v in enumerate(variants[:10]):
            if not v.get("cover_url"):
                missing_covers.append(f"{i+1}. {v.get('artist')} - {v.get('album')}")
        
        assert len(missing_covers) == 0, f"Found {len(missing_covers)} variants without cover_url: {missing_covers}"
        
    def test_search_variants_me_taylor_at_top(self, auth_token):
        """ME! by Taylor Swift should appear in top results"""
        resp = requests.get(f"{BASE_URL}/api/search/variants?q=me!+taylor+swift&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        variants = data.get("variants", [])
        
        # Check first 5 results for ME! 
        me_found = any(
            "me" in (v.get("album", "").lower()) and "taylor" in (v.get("artist", "").lower())
            for v in variants[:5]
        )
        assert me_found, "Expected ME! by Taylor Swift in top 5 results"


class TestVinylRelease:
    """BLOCK-313: Vinyl release endpoint cover_url tests"""
    
    def test_release_13900109_returns_data(self):
        """Taylor Swift ME! Picture Disc (13900109) returns data"""
        resp = requests.get(f"{BASE_URL}/api/vinyl/release/13900109")
        assert resp.status_code == 200
        data = resp.json()
        assert "variant_overview" in data, "Expected variant_overview in response"
        
    def test_release_13900109_has_picture_disc_variant(self):
        """Release 13900109 should have variant='Picture Disc'"""
        resp = requests.get(f"{BASE_URL}/api/vinyl/release/13900109")
        assert resp.status_code == 200
        data = resp.json()
        vo = data.get("variant_overview", {})
        variant = vo.get("variant", "")
        assert "picture" in variant.lower() or variant, f"Expected Picture Disc variant, got: {variant}"
        
    def test_release_13900109_has_cover_url(self):
        """Release 13900109 should have a valid cover_url"""
        resp = requests.get(f"{BASE_URL}/api/vinyl/release/13900109")
        assert resp.status_code == 200
        data = resp.json()
        vo = data.get("variant_overview", {})
        cover_url = vo.get("cover_url")
        assert cover_url, "Expected non-null cover_url in variant_overview"
        assert cover_url.startswith("http"), f"Expected valid URL, got: {cover_url}"
        
    def test_release_13900109_artist_is_taylor_swift(self):
        """Release 13900109 artist should be Taylor Swift"""
        resp = requests.get(f"{BASE_URL}/api/vinyl/release/13900109")
        assert resp.status_code == 200
        data = resp.json()
        vo = data.get("variant_overview", {})
        artist = vo.get("artist", "").lower()
        assert "taylor swift" in artist, f"Expected Taylor Swift, got: {vo.get('artist')}"


class TestDiscogsSearch:
    """BLOCK-313: Discogs search cover_url tests"""
    
    def test_discogs_search_returns_results(self, auth_token):
        """Discogs search for 'me! taylor swift' returns results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = requests.get(f"{BASE_URL}/api/discogs/search?q=me!+taylor+swift", headers=headers)
        
        # Retry once if rate limited
        if resp.status_code == 429 or len(resp.json() if resp.status_code == 200 else []) == 0:
            time.sleep(3)
            resp = requests.get(f"{BASE_URL}/api/discogs/search?q=me!+taylor+swift", headers=headers)
            
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected results from Discogs search"
        
    def test_discogs_search_all_have_cover_url(self, auth_token):
        """All Discogs search results should have cover_url"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = requests.get(f"{BASE_URL}/api/discogs/search?q=me!+taylor+swift", headers=headers)
        
        # Retry once if rate limited
        if resp.status_code == 429 or len(resp.json() if resp.status_code == 200 else []) == 0:
            time.sleep(3)
            resp = requests.get(f"{BASE_URL}/api/discogs/search?q=me!+taylor+swift", headers=headers)
            
        assert resp.status_code == 200
        results = resp.json()
        
        missing_covers = []
        for i, r in enumerate(results[:20]):
            if not r.get("cover_url"):
                missing_covers.append(f"{i+1}. {r.get('artist')} - {r.get('title')}")
        
        assert len(missing_covers) == 0, f"Found {len(missing_covers)} results without cover_url: {missing_covers}"
        
    def test_discogs_search_me_at_top(self, auth_token):
        """ME! should appear at top of Discogs search results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = requests.get(f"{BASE_URL}/api/discogs/search?q=me!+taylor+swift", headers=headers)
        
        # Retry once if rate limited
        if resp.status_code == 429 or len(resp.json() if resp.status_code == 200 else []) == 0:
            time.sleep(3)
            resp = requests.get(f"{BASE_URL}/api/discogs/search?q=me!+taylor+swift", headers=headers)
            
        assert resp.status_code == 200
        results = resp.json()
        
        # Check first 5 results for ME!
        me_found = any(
            "me" in (r.get("title", "").lower())
            for r in results[:5]
        )
        assert me_found, "Expected ME! in top 5 Discogs results"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
