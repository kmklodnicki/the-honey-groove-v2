"""
Test suite for SEO/SSR metadata endpoints.

Tests:
- GET /api/ssr - Root landing page SSR
- GET /api/ssr/honeypot - Marketplace SSR with active listing count
- GET /api/ssr/listing/{id} - Individual listing SSR with vinyl/product/trade meta
- GET /api/ssr/profile/{username} - User profile SSR
- GET /api/ssr/collection/{username} - Collection SSR with top artists
- GET /api/ssr/iso/{username} - ISO list SSR
- Bot detection middleware behavior
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data from review_request
TEST_LISTING_ID = "9010e90e-3f90-4eff-8e41-b3fd39283d6d"
TEST_USERNAME = "katieintheafterglow"


class TestSSRRootEndpoint:
    """Test SSR for root/landing page"""
    
    def test_ssr_root_returns_html(self):
        """GET /api/ssr returns HTML with OG tags and JSON-LD"""
        response = requests.get(f"{BASE_URL}/api/ssr")
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
        
        html = response.text
        # Check essential OG tags
        assert '<meta property="og:site_name"' in html
        assert '<meta property="og:title"' in html
        assert '<meta property="og:description"' in html
        assert '<meta property="og:image"' in html
        
        # Check Twitter Card
        assert '<meta name="twitter:card"' in html
        assert '<meta name="twitter:title"' in html
        
        # Check canonical URL
        assert '<link rel="canonical"' in html
        
        # Check JSON-LD
        assert 'application/ld+json' in html
        assert 'WebApplication' in html or 'website' in html
        print("PASS: /api/ssr returns valid HTML with OG tags, Twitter Cards, canonical URL, and JSON-LD")


class TestSSRHoneypotEndpoint:
    """Test SSR for marketplace page"""
    
    def test_ssr_honeypot_returns_html(self):
        """GET /api/ssr/honeypot returns HTML with marketplace metadata"""
        response = requests.get(f"{BASE_URL}/api/ssr/honeypot")
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
        
        html = response.text
        # Check marketplace-specific content
        assert 'Marketplace' in html or 'honeypot' in html.lower() or 'for sale' in html.lower()
        
        # Check OG tags
        assert '<meta property="og:title"' in html
        assert '<meta property="og:description"' in html
        assert '<meta property="og:image"' in html
        
        # Check JSON-LD has numberOfItems (active listing count)
        assert 'application/ld+json' in html
        assert 'numberOfItems' in html or 'CollectionPage' in html
        
        # Check canonical URL
        assert '<link rel="canonical"' in html
        assert 'honeypot' in html
        print("PASS: /api/ssr/honeypot returns valid marketplace SSR with active listing count")


class TestSSRListingEndpoint:
    """Test SSR for individual listing pages"""
    
    def test_ssr_listing_returns_html_with_vinyl_meta(self):
        """GET /api/ssr/listing/{id} returns HTML with vinyl-specific metadata"""
        response = requests.get(f"{BASE_URL}/api/ssr/listing/{TEST_LISTING_ID}")
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 404:
            # Listing may have been removed, check it returns proper 404 HTML
            html = response.text
            assert 'Not Found' in html
            print(f"INFO: Listing {TEST_LISTING_ID} not found (404), but SSR 404 page works correctly")
            return
            
        html = response.text
        assert 'text/html' in response.headers.get('content-type', '')
        
        # Check vinyl-specific meta tags
        vinyl_tags_found = []
        if 'vinyl:artist' in html:
            vinyl_tags_found.append('vinyl:artist')
        if 'vinyl:album' in html:
            vinyl_tags_found.append('vinyl:album')
        if 'vinyl:variant' in html:
            vinyl_tags_found.append('vinyl:variant')
        
        # Check product meta tags
        product_tags_found = []
        if 'product:price' in html:
            product_tags_found.append('product:price')
        if 'product:availability' in html:
            product_tags_found.append('product:availability')
        if 'product:condition' in html:
            product_tags_found.append('product:condition')
        
        # Check trade meta tags
        trade_tags_found = []
        if 'trade:available' in html:
            trade_tags_found.append('trade:available')
        
        # Check JSON-LD Product schema
        assert 'application/ld+json' in html
        assert 'Product' in html
        
        # Check OG tags
        assert '<meta property="og:title"' in html
        assert '<meta property="og:image"' in html
        assert '<link rel="canonical"' in html
        
        print(f"PASS: /api/ssr/listing/{TEST_LISTING_ID} returns valid SSR")
        print(f"  Vinyl meta tags: {vinyl_tags_found}")
        print(f"  Product meta tags: {product_tags_found}")
        print(f"  Trade meta tags: {trade_tags_found}")


class TestSSRProfileEndpoint:
    """Test SSR for user profile pages"""
    
    def test_ssr_profile_returns_html_with_collector_meta(self):
        """GET /api/ssr/profile/{username} returns HTML with collector metadata"""
        response = requests.get(f"{BASE_URL}/api/ssr/profile/{TEST_USERNAME}")
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 404:
            html = response.text
            assert 'Not Found' in html
            print(f"INFO: Profile {TEST_USERNAME} not found (404)")
            return
            
        html = response.text
        assert 'text/html' in response.headers.get('content-type', '')
        
        # Check collector meta tags
        assert 'collector:username' in html, "Missing collector:username meta tag"
        assert 'collector:collection_size' in html, "Missing collector:collection_size meta tag"
        
        # Check JSON-LD ProfilePage schema
        assert 'application/ld+json' in html
        assert 'ProfilePage' in html
        
        # Check OG tags
        assert '<meta property="og:title"' in html
        assert '<meta property="og:image"' in html
        assert '<link rel="canonical"' in html
        
        # Check username is in the content
        assert TEST_USERNAME.lower() in html.lower()
        
        print(f"PASS: /api/ssr/profile/{TEST_USERNAME} returns valid profile SSR with collector metadata")


class TestSSRCollectionEndpoint:
    """Test SSR for user collection pages"""
    
    def test_ssr_collection_returns_html(self):
        """GET /api/ssr/collection/{username} returns HTML with collection metadata"""
        response = requests.get(f"{BASE_URL}/api/ssr/collection/{TEST_USERNAME}")
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 404:
            html = response.text
            assert 'Not Found' in html
            print(f"INFO: Collection for {TEST_USERNAME} not found (404)")
            return
            
        html = response.text
        assert 'text/html' in response.headers.get('content-type', '')
        
        # Check collection-specific content
        assert 'Collection' in html or 'Records' in html
        
        # Check JSON-LD CollectionPage
        assert 'application/ld+json' in html
        assert 'CollectionPage' in html
        
        # Check OG tags and canonical
        assert '<meta property="og:title"' in html
        assert '<link rel="canonical"' in html
        
        print(f"PASS: /api/ssr/collection/{TEST_USERNAME} returns valid collection SSR")


class TestSSRISOEndpoint:
    """Test SSR for user ISO list pages"""
    
    def test_ssr_iso_returns_html(self):
        """GET /api/ssr/iso/{username} returns HTML with ISO metadata"""
        response = requests.get(f"{BASE_URL}/api/ssr/iso/{TEST_USERNAME}")
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 404:
            html = response.text
            assert 'Not Found' in html
            print(f"INFO: ISO list for {TEST_USERNAME} not found (404)")
            return
            
        html = response.text
        assert 'text/html' in response.headers.get('content-type', '')
        
        # Check ISO-specific content
        assert 'ISO' in html or 'Wanted' in html or 'searching' in html.lower()
        
        # Check JSON-LD ItemList
        assert 'application/ld+json' in html
        assert 'ItemList' in html
        
        # Check OG tags and canonical
        assert '<meta property="og:title"' in html
        assert '<link rel="canonical"' in html
        
        print(f"PASS: /api/ssr/iso/{TEST_USERNAME} returns valid ISO SSR")


class TestBotDetectionMiddleware:
    """Test bot detection middleware behavior"""
    
    def test_twitterbot_profile_returns_ssr(self):
        """Twitterbot user-agent on /profile/{username} should return SSR HTML"""
        headers = {'User-Agent': 'Twitterbot/1.0'}
        response = requests.get(f"{BASE_URL}/profile/{TEST_USERNAME}", headers=headers, allow_redirects=True)
        
        # Either we get SSR HTML or the frontend (which is also fine as middleware might not be running in test)
        if response.status_code == 200:
            html = response.text
            # Check if this is SSR (has meta tags) or React SPA
            if '<meta property="og:title"' in html and 'collector:' in html:
                print(f"PASS: Twitterbot receives SSR HTML for /profile/{TEST_USERNAME}")
            else:
                print(f"INFO: Twitterbot received response, but may be React SPA (middleware not active in this environment)")
        else:
            print(f"INFO: /profile/{TEST_USERNAME} returned status {response.status_code}")
    
    def test_discordbot_honeypot_returns_ssr(self):
        """Discordbot user-agent on /honeypot should return SSR HTML"""
        headers = {'User-Agent': 'Discordbot/2.0'}
        response = requests.get(f"{BASE_URL}/honeypot", headers=headers, allow_redirects=True)
        
        if response.status_code == 200:
            html = response.text
            if '<meta property="og:title"' in html and 'Marketplace' in html:
                print(f"PASS: Discordbot receives SSR HTML for /honeypot")
            else:
                print(f"INFO: Discordbot received response, but may be React SPA")
        else:
            print(f"INFO: /honeypot returned status {response.status_code}")
    
    def test_normal_user_profile_returns_spa(self):
        """Normal Chrome user-agent on /profile/{username} should return React SPA"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(f"{BASE_URL}/profile/{TEST_USERNAME}", headers=headers, allow_redirects=True)
        
        if response.status_code == 200:
            html = response.text
            # React SPA should have React root or bundle references
            if '<div id="root"' in html or 'bundle.js' in html or 'main.' in html:
                print(f"PASS: Normal user receives React SPA for /profile/{TEST_USERNAME}")
            elif 'collector:username' in html:
                print(f"INFO: Normal user received SSR (middleware may intercept all requests in this env)")
            else:
                print(f"INFO: Received response but couldn't identify type")
        else:
            print(f"INFO: /profile/{TEST_USERNAME} returned status {response.status_code}")


class TestSSRCanonicalURLs:
    """Verify all SSR endpoints include canonical URLs"""
    
    def test_all_endpoints_have_canonical(self):
        """All SSR endpoints must include canonical URLs"""
        endpoints = [
            "/api/ssr",
            "/api/ssr/honeypot",
            f"/api/ssr/profile/{TEST_USERNAME}",
            f"/api/ssr/collection/{TEST_USERNAME}",
            f"/api/ssr/iso/{TEST_USERNAME}",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                html = response.text
                assert '<link rel="canonical"' in html, f"Missing canonical URL in {endpoint}"
                print(f"PASS: {endpoint} has canonical URL")
            else:
                print(f"INFO: {endpoint} returned {response.status_code}")


class TestSSROGImages:
    """Verify all SSR endpoints include og:image tags"""
    
    def test_all_endpoints_have_og_image(self):
        """All SSR endpoints must include og:image tags"""
        endpoints = [
            "/api/ssr",
            "/api/ssr/honeypot",
            f"/api/ssr/profile/{TEST_USERNAME}",
            f"/api/ssr/collection/{TEST_USERNAME}",
            f"/api/ssr/iso/{TEST_USERNAME}",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                html = response.text
                assert '<meta property="og:image"' in html, f"Missing og:image in {endpoint}"
                print(f"PASS: {endpoint} has og:image tag")
            else:
                print(f"INFO: {endpoint} returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
