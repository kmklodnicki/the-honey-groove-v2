"""
Test vinyl variant pages API endpoints and SSR for SEO optimization.
Tests:
- GET /api/vinyl/{artist}/{album}/{variant} returns JSON with variant_overview, marketplace, value, demand, activity, seo
- GET /api/vinyl/ssr/{artist}/{album}/{variant} returns SSR HTML with OG tags, Twitter cards, vinyl meta, canonical, JSON-LD
"""
import pytest
import requests
import os
import re
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')


class TestVinylVariantAPI:
    """Test vinyl variant JSON API endpoint"""
    
    def test_vinyl_variant_endpoint_returns_200(self):
        """Test that GET /api/vinyl/{artist}/{album}/{variant} returns 200"""
        response = requests.get(f"{BASE_URL}/api/vinyl/taylor-swift/fearless/sunshine-yellow")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: Vinyl variant endpoint returns 200")
    
    def test_vinyl_variant_returns_variant_overview(self):
        """Test JSON response contains variant_overview section"""
        response = requests.get(f"{BASE_URL}/api/vinyl/taylor-swift/fearless/sunshine-yellow")
        data = response.json()
        
        assert "variant_overview" in data, "Missing variant_overview section"
        overview = data["variant_overview"]
        
        # Verify variant_overview fields
        assert "artist" in overview, "Missing artist in variant_overview"
        assert "album" in overview, "Missing album in variant_overview"
        assert "variant" in overview, "Missing variant in variant_overview"
        assert "year" in overview, "Missing year in variant_overview"
        assert "cover_url" in overview, "Missing cover_url in variant_overview"
        assert "format" in overview, "Missing format in variant_overview"
        assert "label" in overview, "Missing label in variant_overview"
        assert "catalog_number" in overview, "Missing catalog_number in variant_overview"
        assert "discogs_id" in overview, "Missing discogs_id in variant_overview"
        
        # Verify fallback values from URL slugs
        assert overview["artist"] == "Taylor Swift", f"Expected 'Taylor Swift', got {overview['artist']}"
        assert overview["album"] == "Fearless", f"Expected 'Fearless', got {overview['album']}"
        assert overview["variant"] == "Sunshine Yellow", f"Expected 'Sunshine Yellow', got {overview['variant']}"
        print("PASS: variant_overview section present with correct fields")
    
    def test_vinyl_variant_returns_marketplace(self):
        """Test JSON response contains marketplace section"""
        response = requests.get(f"{BASE_URL}/api/vinyl/taylor-swift/fearless/sunshine-yellow")
        data = response.json()
        
        assert "marketplace" in data, "Missing marketplace section"
        marketplace = data["marketplace"]
        
        assert "active_listings" in marketplace, "Missing active_listings in marketplace"
        assert "listing_count" in marketplace, "Missing listing_count in marketplace"
        assert isinstance(marketplace["active_listings"], list), "active_listings should be a list"
        assert isinstance(marketplace["listing_count"], int), "listing_count should be an int"
        print("PASS: marketplace section present with correct fields")
    
    def test_vinyl_variant_returns_value(self):
        """Test JSON response contains value section"""
        response = requests.get(f"{BASE_URL}/api/vinyl/taylor-swift/fearless/sunshine-yellow")
        data = response.json()
        
        assert "value" in data, "Missing value section"
        value = data["value"]
        
        assert "recent_sales_count" in value, "Missing recent_sales_count in value"
        assert "average_value" in value, "Missing average_value in value"
        assert "highest_sale" in value, "Missing highest_sale in value"
        assert "lowest_sale" in value, "Missing lowest_sale in value"
        print("PASS: value section present with correct fields")
    
    def test_vinyl_variant_returns_demand(self):
        """Test JSON response contains demand section"""
        response = requests.get(f"{BASE_URL}/api/vinyl/taylor-swift/fearless/sunshine-yellow")
        data = response.json()
        
        assert "demand" in data, "Missing demand section"
        demand = data["demand"]
        
        assert "owners_count" in demand, "Missing owners_count in demand"
        assert "iso_count" in demand, "Missing iso_count in demand"
        assert "post_count" in demand, "Missing post_count in demand"
        print("PASS: demand section present with correct fields")
    
    def test_vinyl_variant_returns_activity(self):
        """Test JSON response contains activity section"""
        response = requests.get(f"{BASE_URL}/api/vinyl/taylor-swift/fearless/sunshine-yellow")
        data = response.json()
        
        assert "activity" in data, "Missing activity section"
        activity = data["activity"]
        
        assert "owners" in activity, "Missing owners in activity"
        assert "recent_posts" in activity, "Missing recent_posts in activity"
        assert isinstance(activity["owners"], list), "owners should be a list"
        assert isinstance(activity["recent_posts"], list), "recent_posts should be a list"
        print("PASS: activity section present with correct fields")
    
    def test_vinyl_variant_returns_seo(self):
        """Test JSON response contains seo section"""
        response = requests.get(f"{BASE_URL}/api/vinyl/taylor-swift/fearless/sunshine-yellow")
        data = response.json()
        
        assert "seo" in data, "Missing seo section"
        seo = data["seo"]
        
        assert "title" in seo, "Missing title in seo"
        assert "description" in seo, "Missing description in seo"
        assert "canonical" in seo, "Missing canonical in seo"
        assert "image" in seo, "Missing image in seo"
        
        # Verify canonical URL format
        assert seo["canonical"] == "/vinyl/taylor-swift/fearless/sunshine-yellow", \
            f"Expected '/vinyl/taylor-swift/fearless/sunshine-yellow', got {seo['canonical']}"
        
        # Verify title contains key info
        assert "Taylor Swift" in seo["title"], "Title should contain artist name"
        assert "Fearless" in seo["title"], "Title should contain album name"
        assert "Sunshine Yellow" in seo["title"], "Title should contain variant name"
        print("PASS: seo section present with correct fields")


class TestVinylVariantSSR:
    """Test vinyl variant SSR HTML endpoint for social bots"""
    
    def test_ssr_endpoint_returns_html(self):
        """Test GET /api/vinyl/ssr/{artist}/{album}/{variant} returns HTML"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/taylor-swift/fearless/sunshine-yellow")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content_type = response.headers.get('content-type', '')
        assert 'text/html' in content_type, f"Expected text/html content type, got {content_type}"
        print("PASS: SSR endpoint returns 200 with HTML content type")
    
    def test_ssr_contains_og_tags(self):
        """Test SSR HTML contains Open Graph meta tags"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/taylor-swift/fearless/sunshine-yellow")
        html = response.text
        
        assert '<meta property="og:title"' in html, "Missing og:title meta tag"
        assert '<meta property="og:description"' in html, "Missing og:description meta tag"
        assert '<meta property="og:image"' in html, "Missing og:image meta tag"
        assert '<meta property="og:url"' in html, "Missing og:url meta tag"
        assert '<meta property="og:type"' in html, "Missing og:type meta tag"
        assert '<meta property="og:site_name"' in html, "Missing og:site_name meta tag"
        print("PASS: SSR HTML contains OG meta tags")
    
    def test_ssr_contains_twitter_cards(self):
        """Test SSR HTML contains Twitter Card meta tags"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/taylor-swift/fearless/sunshine-yellow")
        html = response.text
        
        assert '<meta name="twitter:card"' in html, "Missing twitter:card meta tag"
        assert '<meta name="twitter:title"' in html, "Missing twitter:title meta tag"
        assert '<meta name="twitter:description"' in html, "Missing twitter:description meta tag"
        assert '<meta name="twitter:image"' in html, "Missing twitter:image meta tag"
        print("PASS: SSR HTML contains Twitter Card meta tags")
    
    def test_ssr_contains_vinyl_meta_tags(self):
        """Test SSR HTML contains vinyl-specific meta tags"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/taylor-swift/fearless/sunshine-yellow")
        html = response.text
        
        assert '<meta name="vinyl:artist"' in html, "Missing vinyl:artist meta tag"
        assert '<meta name="vinyl:album"' in html, "Missing vinyl:album meta tag"
        assert '<meta name="vinyl:variant"' in html, "Missing vinyl:variant meta tag"
        assert '<meta name="vinyl:format"' in html, "Missing vinyl:format meta tag"
        
        # Verify values
        assert 'content="Taylor Swift"' in html, "vinyl:artist should have correct value"
        assert 'content="Fearless"' in html, "vinyl:album should have correct value"
        assert 'content="Sunshine Yellow"' in html, "vinyl:variant should have correct value"
        print("PASS: SSR HTML contains vinyl-specific meta tags")
    
    def test_ssr_contains_canonical_url(self):
        """Test SSR HTML contains canonical URL"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/taylor-swift/fearless/sunshine-yellow")
        html = response.text
        
        assert '<link rel="canonical"' in html, "Missing canonical link"
        assert '/vinyl/taylor-swift/fearless/sunshine-yellow' in html, "Canonical URL should match vinyl variant path"
        print("PASS: SSR HTML contains canonical URL")
    
    def test_ssr_contains_json_ld_schema(self):
        """Test SSR HTML contains JSON-LD Product schema"""
        response = requests.get(f"{BASE_URL}/api/vinyl/ssr/taylor-swift/fearless/sunshine-yellow")
        html = response.text
        
        assert '<script type="application/ld+json">' in html, "Missing JSON-LD script tag"
        
        # Extract JSON-LD content
        json_ld_match = re.search(r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL)
        assert json_ld_match, "Could not extract JSON-LD content"
        
        json_ld = json.loads(json_ld_match.group(1))
        
        assert json_ld.get("@context") == "https://schema.org", "JSON-LD should use schema.org context"
        assert json_ld.get("@type") == "Product", "JSON-LD type should be Product"
        assert "Taylor Swift" in json_ld.get("name", ""), "JSON-LD name should contain artist"
        assert json_ld.get("category") == "Vinyl Record", "JSON-LD category should be Vinyl Record"
        
        # Verify brand/artist info
        brand = json_ld.get("brand", {})
        assert brand.get("@type") == "MusicGroup", "Brand type should be MusicGroup"
        assert brand.get("name") == "Taylor Swift", "Brand name should be the artist"
        
        # Verify additionalProperty for variant
        props = json_ld.get("additionalProperty", [])
        variant_prop = next((p for p in props if p.get("name") == "Variant"), None)
        assert variant_prop, "JSON-LD should have Variant property"
        assert variant_prop.get("value") == "Sunshine Yellow", "Variant value should be correct"
        print("PASS: SSR HTML contains valid JSON-LD Product schema")


class TestVinylBotMiddleware:
    """Test bot middleware returns SSR HTML for bots vs React SPA for users"""
    
    def test_twitterbot_gets_ssr_html(self):
        """Test Twitterbot user-agent receives SSR HTML"""
        headers = {'User-Agent': 'Twitterbot/1.0'}
        response = requests.get(f"{BASE_URL.replace('/api', '')}/vinyl/taylor-swift/fearless/sunshine-yellow", headers=headers)
        
        # Should return SSR HTML with meta tags
        html = response.text
        assert '<meta property="og:title"' in html, "Twitterbot should receive SSR HTML with OG tags"
        assert '<meta name="twitter:card"' in html, "Twitterbot should receive SSR HTML with Twitter cards"
        print("PASS: Twitterbot receives SSR HTML")
    
    def test_facebookbot_gets_ssr_html(self):
        """Test Facebook bot user-agent receives SSR HTML"""
        headers = {'User-Agent': 'facebookexternalhit/1.1'}
        response = requests.get(f"{BASE_URL.replace('/api', '')}/vinyl/taylor-swift/fearless/sunshine-yellow", headers=headers)
        
        html = response.text
        assert '<meta property="og:title"' in html, "Facebook bot should receive SSR HTML with OG tags"
        print("PASS: Facebook bot receives SSR HTML")
    
    def test_normal_user_gets_react_spa(self):
        """Test normal browser user-agent receives React SPA (not raw SSR)"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(f"{BASE_URL.replace('/api', '')}/vinyl/taylor-swift/fearless/sunshine-yellow", headers=headers)
        
        html = response.text
        # React SPA will have the root div and React script tags
        # SSR HTML will NOT have these
        is_react_spa = '<div id="root">' in html or 'react' in html.lower()
        assert is_react_spa, "Normal user should receive React SPA, not SSR HTML"
        print("PASS: Normal user receives React SPA")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
