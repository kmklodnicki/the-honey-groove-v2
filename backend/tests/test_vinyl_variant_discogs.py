"""
Test Vinyl Variant & Value Pages - Discogs API Integration
Tests the /api/vinyl/{artist}/{album}/{variant} endpoint with real Discogs data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestVinylVariantAPIChappellRoan:
    """Tests for Chappell Roan - Pink Pony Club (Baby Pink) variant page"""
    
    def test_chappell_roan_variant_overview(self):
        """Test variant_overview contains all required Discogs-sourced data"""
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        ov = data.get("variant_overview", {})
        
        # Verify all required fields
        assert ov.get("artist") == "Chappell Roan", f"Artist mismatch: {ov.get('artist')}"
        assert ov.get("album") == "Pink Pony Club", f"Album mismatch: {ov.get('album')}"
        assert ov.get("variant") == "Baby Pink", f"Variant mismatch: {ov.get('variant')}"
        assert ov.get("year") == 2024, f"Year mismatch: {ov.get('year')}"
        assert ov.get("cover_url") is not None, "cover_url is missing"
        assert "discogs.com" in ov.get("cover_url", ""), "cover_url should be from Discogs"
        assert ov.get("label") is not None, "label is missing"
        assert ov.get("catalog_number") is not None, "catalog_number is missing"
        assert ov.get("pressing_country") == "US", f"pressing_country mismatch: {ov.get('pressing_country')}"
        assert ov.get("discogs_id") == 31785674, f"discogs_id mismatch: {ov.get('discogs_id')}"
        assert ov.get("format") is not None, "format is missing"
    
    def test_chappell_roan_data_source(self):
        """Test data_source confirms Discogs data was fetched"""
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        ds = data.get("data_source", {})
        
        assert ds.get("discogs_release_id") == 31785674
        assert ds.get("discogs_fetched") is True, "discogs_fetched should be true"
        assert ds.get("discogs_market_fetched") is True, "discogs_market_fetched should be true"
    
    def test_chappell_roan_discogs_value(self):
        """Test value field contains Discogs market data"""
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        val = data.get("value", {})
        
        # Should have Discogs market data
        assert val.get("discogs_median") is not None, "discogs_median is missing"
        assert isinstance(val.get("discogs_median"), (int, float)), "discogs_median should be a number"
        assert val.get("discogs_low") is not None, "discogs_low is missing"
        assert val.get("discogs_high") is not None, "discogs_high is missing"
        
        # Verify pricing makes sense (low <= median <= high)
        assert val.get("discogs_low") <= val.get("discogs_median") <= val.get("discogs_high")
    
    def test_chappell_roan_seo_fields(self):
        """Test seo field has proper title, description, canonical, image"""
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        seo = data.get("seo", {})
        
        assert "Chappell Roan" in seo.get("title", ""), "SEO title should contain artist"
        assert "Pink Pony Club" in seo.get("title", ""), "SEO title should contain album"
        assert "Baby Pink" in seo.get("title", ""), "SEO title should contain variant"
        assert seo.get("description") is not None and len(seo.get("description", "")) > 20
        assert seo.get("canonical") == "/vinyl/chappell-roan/pink-pony-club/baby-pink"
        assert seo.get("image") is not None, "SEO image is missing"
    
    def test_chappell_roan_collector_owner(self):
        """Test activity.owners contains the expected collector"""
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        owners = data.get("activity", {}).get("owners", [])
        
        # Verify owner @katieintheafterglow is present
        usernames = [o.get("username") for o in owners]
        assert "katieintheafterglow" in usernames, f"Expected owner not found. Found: {usernames}"


class TestVinylVariantAPICharliXCX:
    """Tests for Charli XCX - Brat (Black Translucent) variant page"""
    
    def test_charli_xcx_variant_overview(self):
        """Test variant_overview for Charli XCX - Brat (Black Translucent)"""
        response = requests.get(f"{BASE_URL}/api/vinyl/charli-xcx/brat/black-translucent")
        assert response.status_code == 200
        
        data = response.json()
        ov = data.get("variant_overview", {})
        
        assert ov.get("artist") == "Charli XCX", f"Artist mismatch: {ov.get('artist')}"
        assert ov.get("album") == "Brat", f"Album mismatch: {ov.get('album')}"
        assert ov.get("variant") == "Black Translucent", f"Variant mismatch: {ov.get('variant')}"
        assert ov.get("year") == 2024
        assert ov.get("discogs_id") == 30984958
        assert ov.get("cover_url") is not None
    
    def test_charli_xcx_data_source(self):
        """Test data_source for Charli XCX variant"""
        response = requests.get(f"{BASE_URL}/api/vinyl/charli-xcx/brat/black-translucent")
        assert response.status_code == 200
        
        data = response.json()
        ds = data.get("data_source", {})
        
        assert ds.get("discogs_release_id") == 30984958
        assert ds.get("discogs_fetched") is True
        assert ds.get("discogs_market_fetched") is True
    
    def test_charli_xcx_discogs_value(self):
        """Test Discogs market data for Charli XCX variant"""
        response = requests.get(f"{BASE_URL}/api/vinyl/charli-xcx/brat/black-translucent")
        assert response.status_code == 200
        
        data = response.json()
        val = data.get("value", {})
        
        assert val.get("discogs_median") is not None
        assert val.get("discogs_low") is not None
        assert val.get("discogs_high") is not None


class TestVinylVariantAPIGracefulHandling:
    """Tests for graceful handling of nonexistent variants"""
    
    def test_nonexistent_variant_returns_200(self):
        """Test nonexistent variant returns 200 with graceful empty data"""
        response = requests.get(f"{BASE_URL}/api/vinyl/nonexistent/nonexistent/nonexistent")
        assert response.status_code == 200, f"Should return 200, got {response.status_code}"
        
        data = response.json()
        assert "variant_overview" in data
        assert "value" in data
        assert "seo" in data
    
    def test_nonexistent_variant_no_discogs_data(self):
        """Test nonexistent variant has no Discogs data"""
        response = requests.get(f"{BASE_URL}/api/vinyl/nonexistent/nonexistent/nonexistent")
        assert response.status_code == 200
        
        data = response.json()
        ds = data.get("data_source", {})
        
        assert ds.get("discogs_release_id") is None
        assert ds.get("discogs_fetched") is False
        assert ds.get("discogs_market_fetched") is False
    
    def test_nonexistent_variant_empty_values(self):
        """Test nonexistent variant has null market values"""
        response = requests.get(f"{BASE_URL}/api/vinyl/nonexistent/nonexistent/nonexistent")
        assert response.status_code == 200
        
        data = response.json()
        val = data.get("value", {})
        
        assert val.get("discogs_median") is None
        assert val.get("discogs_low") is None
        assert val.get("discogs_high") is None
        assert val.get("average_value") is None


class TestVinylSSREndpoint:
    """Tests for the SSR endpoint /api/vinyl/ssr/{artist}/{album}/{variant}"""
    
    def test_ssr_returns_html(self):
        """Test SSR endpoint returns HTML"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, f"Expected HTML, got {content_type}"
    
    def test_ssr_og_tags(self):
        """Test SSR HTML contains Open Graph tags"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        html = response.text
        
        assert 'og:title' in html, "Missing og:title meta tag"
        assert 'og:image' in html, "Missing og:image meta tag"
        assert 'og:description' in html, "Missing og:description meta tag"
    
    def test_ssr_twitter_card(self):
        """Test SSR HTML contains Twitter card tags"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        html = response.text
        
        assert 'twitter:card' in html, "Missing twitter:card meta tag"
        assert 'summary_large_image' in html, "Twitter card should be summary_large_image"
    
    def test_ssr_json_ld(self):
        """Test SSR HTML contains JSON-LD structured data"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        html = response.text
        
        assert 'application/ld+json' in html, "Missing JSON-LD script"
        assert 'schema.org' in html, "JSON-LD should reference schema.org"
        assert '"@type": "Product"' in html, "JSON-LD should have Product type"
    
    def test_ssr_vinyl_meta_tags(self):
        """Test SSR HTML contains vinyl-specific meta tags"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        html = response.text
        
        assert 'vinyl:artist' in html, "Missing vinyl:artist meta tag"
        assert 'vinyl:album' in html, "Missing vinyl:album meta tag"
        assert 'vinyl:variant' in html, "Missing vinyl:variant meta tag"
        assert 'vinyl:format' in html, "Missing vinyl:format meta tag"
        assert 'vinyl:label' in html, "Missing vinyl:label meta tag"
        assert 'vinyl:catalog_number' in html, "Missing vinyl:catalog_number meta tag"
        assert 'vinyl:discogs_id' in html, "Missing vinyl:discogs_id meta tag"
        assert 'vinyl:pressing_country' in html, "Missing vinyl:pressing_country meta tag"
        assert 'vinyl:release_year' in html, "Missing vinyl:release_year meta tag"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
