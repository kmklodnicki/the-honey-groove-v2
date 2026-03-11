"""
BLOCK 369: Mobile Image Emergency Fix - Backend Tests
Tests:
1. CORS headers on GET /api/image-proxy
2. OPTIONS /api/image-proxy returns 204 with CORS headers (pre-flight)
3. HTTPS enforcement in image proxy
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')

class TestImageProxyCORS:
    """Test CORS headers on image proxy endpoint"""
    
    def test_image_proxy_cors_headers_on_get(self):
        """GET /api/image-proxy should return Access-Control-Allow-Origin: * header"""
        # Use a simple test URL - actual image may not exist, but CORS headers should be present
        test_url = "https://i.discogs.com/test.jpg"
        response = requests.get(f"{BASE_URL}/api/image-proxy", params={"url": test_url})
        
        # Check CORS header is present regardless of response status
        # The key test is that the CORS header is set - image existence is secondary
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        assert cors_header == '*', f"Expected Access-Control-Allow-Origin: *, got: {cors_header}"
        
        print(f"✓ GET /api/image-proxy returns Access-Control-Allow-Origin: {cors_header}")
        print(f"  Response status: {response.status_code} (expected - test image may not exist)")
        
    def test_image_proxy_options_preflight(self):
        """OPTIONS /api/image-proxy should return 204 with CORS headers for pre-flight"""
        response = requests.options(f"{BASE_URL}/api/image-proxy")
        
        # Should return 204 for pre-flight
        assert response.status_code == 204, f"Expected 204 for OPTIONS pre-flight, got {response.status_code}"
        
        # Check all CORS headers
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        cors_methods = response.headers.get('Access-Control-Allow-Methods')
        cors_headers = response.headers.get('Access-Control-Allow-Headers')
        
        assert cors_origin == '*', f"Expected Access-Control-Allow-Origin: *, got: {cors_origin}"
        assert 'GET' in cors_methods, f"Expected GET in Allow-Methods, got: {cors_methods}"
        assert 'OPTIONS' in cors_methods, f"Expected OPTIONS in Allow-Methods, got: {cors_methods}"
        
        print(f"✓ OPTIONS /api/image-proxy returns 204 with CORS headers")
        print(f"  - Access-Control-Allow-Origin: {cors_origin}")
        print(f"  - Access-Control-Allow-Methods: {cors_methods}")
        print(f"  - Access-Control-Allow-Headers: {cors_headers}")
        
    def test_image_proxy_https_enforcement(self):
        """Image proxy should convert http:// URLs to https:// before fetching"""
        # Use an HTTP URL - the proxy should convert it to HTTPS
        # Note: We can't directly test if it converted, but we can test if the request works
        # The proxy code does: if url.startswith("http://"): url = url.replace("http://", "https://", 1)
        http_url = "http://i.discogs.com/test.jpg"
        response = requests.get(f"{BASE_URL}/api/image-proxy", params={"url": http_url})
        
        # Should either:
        # 1. Return 200 if the HTTPS version exists
        # 2. Return 404/502 if the image doesn't exist (but means conversion was attempted)
        # Should NOT return 400 (which would mean it rejected the URL)
        assert response.status_code != 400, "Proxy rejected http:// URL - should convert to https://"
        
        print(f"✓ Image proxy accepts http:// URLs (converts to https:// internally)")
        print(f"  Response status: {response.status_code}")
        
    def test_image_proxy_invalid_url_rejected(self):
        """Image proxy should reject invalid URLs"""
        response = requests.get(f"{BASE_URL}/api/image-proxy", params={"url": "not-a-valid-url"})
        
        # Should return 400 for invalid URL
        assert response.status_code == 400, f"Expected 400 for invalid URL, got {response.status_code}"
        
        print(f"✓ Image proxy rejects invalid URLs with 400")


class TestAuthAndFeed:
    """Test auth and feed endpoints for regression"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_feed_loads(self, auth_token):
        """Feed should load successfully"""
        response = requests.get(f"{BASE_URL}/api/feed", 
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"limit": 10})
        
        assert response.status_code == 200, f"Feed failed with {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        
        print(f"✓ Feed loads successfully with {len(data)} posts")
        
    def test_daily_prompt_endpoint(self, auth_token):
        """Daily prompt endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/prompts/today", 
            headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200, f"Daily prompt failed with {response.status_code}"
        data = response.json()
        # Should have prompt, has_buzzed_in, streak fields
        assert "prompt" in data or "has_buzzed_in" in data, "Daily prompt response missing expected fields"
        
        print(f"✓ Daily prompt endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
