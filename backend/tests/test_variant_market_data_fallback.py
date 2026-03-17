"""
Tests for variant pages showing blank squares and $0 market data issue.
Tests three fallback strategies:
1) Market data: variant → sibling discogs_releases with same master_id → master release's main_release → master's lowest_price estimate
2) Community stats: variant → aggregation pipeline across sibling releases → master API main release
3) Cover art: variant → records collection siblings → discogs_releases siblings → Discogs API (max 3 calls)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://record-search-ui.preview.emergentagent.com')
DEFAULT_TIMEOUT = 30  # Increased timeout for Discogs API rate limiting


def request_with_retry(url, params=None, max_retries=3, timeout=DEFAULT_TIMEOUT):
    """Make GET request with retry logic for rate limiting and timeouts."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code == 200:
                return response
            time.sleep(2)  # Wait before retry
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            raise
    return response


class TestHealthEndpoint:
    """Health endpoint - verify MongoDB pool configuration."""
    
    def test_health_pool_config(self):
        """GET /api/health should return pool info with maxPoolSize=10, db_status='connected'."""
        response = request_with_retry(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health endpoint returned {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "ok", f"Expected status='ok', got {data.get('status')}"
        
        pool = data.get("pool", {})
        assert pool.get("db_status") == "connected", f"Expected db_status='connected', got {pool.get('db_status')}"
        assert pool.get("maxPoolSize") == 10, f"Expected maxPoolSize=10, got {pool.get('maxPoolSize')}"
        assert pool.get("minPoolSize") == 1, f"Expected minPoolSize=1, got {pool.get('minPoolSize')}"
        print(f"PASS: Health endpoint - pool maxPoolSize=10, minPoolSize=1, db_status='connected'")


class TestOpaliteChrisLakeVariant:
    """Tests for Taylor Swift - Opalite (Chris Lake Remix) variant (release 36527356)."""
    
    def test_release_has_cover_url(self):
        """GET /api/vinyl/release/36527356 should return cover_url."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/36527356")
        assert response.status_code == 200, f"Opalite release returned {response.status_code}"
        
        data = response.json()
        variant = data.get("variant_overview", {})
        cover_url = variant.get("cover_url")
        
        assert cover_url is not None, "cover_url is None - blank square issue"
        assert cover_url != "", "cover_url is empty string - blank square issue"
        assert cover_url.startswith("http"), f"cover_url doesn't look like a URL: {cover_url}"
        print(f"PASS: Opalite Chris Lake has cover_url: {cover_url[:60]}...")
    
    def test_release_has_community_stats(self):
        """GET /api/vinyl/release/36527356 should have community stats > 0."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/36527356")
        assert response.status_code == 200
        
        data = response.json()
        scarcity = data.get("scarcity", {})
        discogs_have = scarcity.get("discogs_have", 0)
        
        assert discogs_have > 0, f"discogs_have is {discogs_have}, expected > 0"
        print(f"PASS: Opalite Chris Lake has community stats: have={discogs_have}, want={scarcity.get('discogs_want')}")
    
    def test_release_has_market_value(self):
        """GET /api/vinyl/release/36527356 should have market value > 0."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/36527356")
        assert response.status_code == 200
        
        data = response.json()
        value = data.get("value", {})
        discogs_median = value.get("discogs_median")
        
        assert discogs_median is not None, "discogs_median is None - $0 market data issue"
        assert discogs_median > 0, f"discogs_median is {discogs_median}, expected > 0"
        print(f"PASS: Opalite Chris Lake has market value: median=${discogs_median}")


class TestSpeakNowOrchidVariant:
    """Tests for Taylor Swift - Speak Now Orchid variant (release 27597354)."""
    
    def test_release_has_cover_url(self):
        """GET /api/vinyl/release/27597354 should return cover_url."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/27597354")
        assert response.status_code == 200, f"Speak Now Orchid returned {response.status_code}"
        
        data = response.json()
        variant = data.get("variant_overview", {})
        cover_url = variant.get("cover_url")
        
        assert cover_url is not None, "cover_url is None - blank square issue"
        assert cover_url != "", "cover_url is empty string - blank square issue"
        assert cover_url.startswith("http"), f"cover_url doesn't look like a URL: {cover_url}"
        print(f"PASS: Speak Now Orchid has cover_url: {cover_url[:60]}...")
    
    def test_release_has_community_stats(self):
        """GET /api/vinyl/release/27597354 should have community stats > 0."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/27597354")
        assert response.status_code == 200
        
        data = response.json()
        scarcity = data.get("scarcity", {})
        discogs_have = scarcity.get("discogs_have", 0)
        
        assert discogs_have > 0, f"discogs_have is {discogs_have}, expected > 0"
        print(f"PASS: Speak Now Orchid has community stats: have={discogs_have}, want={scarcity.get('discogs_want')}")
    
    def test_release_has_market_value(self):
        """GET /api/vinyl/release/27597354 should have market value > 0."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/27597354")
        assert response.status_code == 200
        
        data = response.json()
        value = data.get("value", {})
        discogs_median = value.get("discogs_median")
        
        assert discogs_median is not None, "discogs_median is None - $0 market data issue"
        assert discogs_median > 0, f"discogs_median is {discogs_median}, expected > 0"
        print(f"PASS: Speak Now Orchid has market value: median=${discogs_median}")


class TestHilaryDuffMatureEditionFallback:
    """Tests for Hilary Duff - Mature Edition variant (release 36739498) - tests master sibling aggregation."""
    
    def test_release_uses_master_fallback(self):
        """GET /api/vinyl/release/36739498 should aggregate stats from master siblings."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/36739498")
        assert response.status_code == 200, f"Hilary Duff Mature returned {response.status_code}"
        
        data = response.json()
        scarcity = data.get("scarcity", {})
        stats_source = scarcity.get("stats_source")
        discogs_have = scarcity.get("discogs_have", 0)
        
        # This release has sparse variant data, should fallback to 'master' aggregation
        assert stats_source == "master", f"Expected stats_source='master', got '{stats_source}'"
        assert discogs_have > 0, f"discogs_have is {discogs_have}, expected > 0 after master fallback"
        print(f"PASS: Hilary Duff Mature uses master fallback: stats_source='{stats_source}', have={discogs_have}")
    
    def test_release_has_cover_url(self):
        """GET /api/vinyl/release/36739498 should return cover_url."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/36739498")
        assert response.status_code == 200
        
        data = response.json()
        variant = data.get("variant_overview", {})
        cover_url = variant.get("cover_url")
        
        assert cover_url is not None, "cover_url is None - blank square issue"
        assert cover_url != "", "cover_url is empty string - blank square issue"
        print(f"PASS: Hilary Duff Mature has cover_url: {cover_url[:60]}...")
    
    def test_release_has_market_value(self):
        """GET /api/vinyl/release/36739498 should have market value (possibly from fallback)."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/36739498")
        assert response.status_code == 200
        
        data = response.json()
        value = data.get("value", {})
        discogs_median = value.get("discogs_median")
        
        # Market data may come from sibling releases or master's lowest_price estimate
        assert discogs_median is not None, "discogs_median is None - market data fallback not working"
        print(f"PASS: Hilary Duff Mature has market value: median=${discogs_median}")


class TestSearchVariantsCoverResolution:
    """Tests for batch cover resolution in variant search results."""
    
    def test_opalite_search_has_covers(self):
        """GET /api/search/variants?q=opalite+chris+lake+taylor+swift - all results should have cover_url."""
        # Add retry for rate limiting
        for attempt in range(3):
            response = requests.get(
                f"{BASE_URL}/api/search/variants",
                params={"q": "opalite chris lake taylor swift"},
                timeout=20
            )
            if response.status_code == 200:
                break
            time.sleep(2)
        
        assert response.status_code == 200, f"Search returned {response.status_code}"
        
        data = response.json()
        variants = data.get("variants", [])
        
        assert len(variants) > 0, "No variants returned for opalite chris lake taylor swift search"
        
        missing_covers = [v for v in variants if not v.get("cover_url")]
        assert len(missing_covers) == 0, f"Found {len(missing_covers)} variants with missing cover_url: {[v.get('variant') for v in missing_covers]}"
        print(f"PASS: Opalite search returned {len(variants)} variants, all have cover_url")
    
    def test_speak_now_orchid_search_has_covers(self):
        """GET /api/search/variants?q=speak+now+orchid - results should have cover_url."""
        # Add retry for rate limiting
        for attempt in range(3):
            response = requests.get(
                f"{BASE_URL}/api/search/variants",
                params={"q": "speak now orchid"},
                timeout=20
            )
            if response.status_code == 200:
                break
            time.sleep(2)
        
        assert response.status_code == 200, f"Search returned {response.status_code}"
        
        data = response.json()
        variants = data.get("variants", [])
        
        assert len(variants) > 0, "No variants returned for speak now orchid search"
        
        missing_covers = [v for v in variants if not v.get("cover_url")]
        assert len(missing_covers) == 0, f"Found {len(missing_covers)} variants with missing cover_url: {[v.get('variant') for v in missing_covers]}"
        print(f"PASS: Speak Now Orchid search returned {len(variants)} variants, all have cover_url")


class TestDataIntegrity:
    """Tests for data integrity across variant detail endpoints."""
    
    def test_opalite_variant_data_structure(self):
        """Verify all expected fields are present in Opalite variant response."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/36527356")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check top-level structure
        assert "variant_overview" in data
        assert "scarcity" in data
        assert "value" in data
        assert "community" in data
        
        # Check variant_overview fields
        overview = data["variant_overview"]
        assert "artist" in overview
        assert "album" in overview
        assert "cover_url" in overview
        assert "discogs_id" in overview
        
        # Check scarcity fields
        scarcity = data["scarcity"]
        assert "discogs_have" in scarcity
        assert "discogs_want" in scarcity
        assert "stats_source" in scarcity
        assert "master_id" in scarcity
        
        # Check value fields
        value = data["value"]
        assert "discogs_median" in value
        
        print(f"PASS: Opalite variant has all expected data structure fields")
    
    def test_speak_now_orchid_has_internal_owners(self):
        """Speak Now Orchid is popular - verify internal_owners_count > 0."""
        response = request_with_retry(f"{BASE_URL}/api/vinyl/release/27597354")
        assert response.status_code == 200
        
        data = response.json()
        community = data.get("community", {})
        internal_owners = community.get("internal_owners_count", 0)
        
        assert internal_owners > 0, f"Expected internal_owners_count > 0 for popular variant, got {internal_owners}"
        print(f"PASS: Speak Now Orchid has {internal_owners} internal owners")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
