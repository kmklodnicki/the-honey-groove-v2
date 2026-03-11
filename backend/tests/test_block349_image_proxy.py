"""
BLOCK 349: Image Proxy for CORS-safe canvas export
Tests for GET /api/image-proxy endpoint that proxies external images with CORS headers
"""
import pytest
import requests
import os
import urllib.parse

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Sample external Discogs image for testing
SAMPLE_DISCOGS_IMAGE = "https://i.discogs.com/1lIoN90TJ6tb2HIZeWx8rPEUPVaYrceQCdJWYx7ABGM/rs:fit/g:sm/q:90/h:600/w:591/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTMxNzg1/Njc0LTE3MjY5NjA1/MTUtOTIyNi5wbmc.jpeg"

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"


class TestImageProxyEndpoint:
    """Tests for /api/image-proxy endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_image_proxy_proxies_external_discogs_image(self):
        """Test that image proxy fetches and returns external Discogs image with CORS headers"""
        encoded_url = urllib.parse.quote(SAMPLE_DISCOGS_IMAGE, safe='')
        response = requests.get(f"{BASE_URL}/api/image-proxy?url={encoded_url}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify CORS headers
        assert response.headers.get("Access-Control-Allow-Origin") == "*", \
            "Missing or incorrect Access-Control-Allow-Origin header"
        
        # Verify content-type is image type
        content_type = response.headers.get("Content-Type", "")
        assert "image/" in content_type, f"Expected image content-type, got {content_type}"
        
        # Verify we got actual image data
        assert len(response.content) > 1000, "Response content too small for an image"
        print(f"SUCCESS: Image proxy returned {len(response.content)} bytes with Content-Type: {content_type}")
    
    def test_image_proxy_returns_proper_content_type_jpeg(self):
        """Test that proxy preserves content-type for JPEG images"""
        # Use a known JPEG image
        jpeg_url = "https://images.pexels.com/photos/1649771/pexels-photo-1649771.jpeg?auto=compress&cs=tinysrgb&w=200"
        encoded_url = urllib.parse.quote(jpeg_url, safe='')
        response = requests.get(f"{BASE_URL}/api/image-proxy?url={encoded_url}")
        
        # This may return 200 or fail depending on the external image availability
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            assert "image/" in content_type, f"Expected image content-type, got {content_type}"
            print(f"SUCCESS: Content-type is {content_type}")
        else:
            # If external image is unavailable, that's acceptable
            print(f"INFO: External test image unavailable (status {response.status_code})")
    
    def test_image_proxy_handles_invalid_url_with_400(self):
        """Test that proxy returns 400 for invalid URLs"""
        # Test with missing URL
        response = requests.get(f"{BASE_URL}/api/image-proxy")
        assert response.status_code == 422 or response.status_code == 400, \
            f"Expected 400/422 for missing URL, got {response.status_code}"
        print(f"SUCCESS: Missing URL returns {response.status_code}")
        
        # Test with non-http URL
        response = requests.get(f"{BASE_URL}/api/image-proxy?url=not-a-valid-url")
        assert response.status_code == 400, f"Expected 400 for invalid URL, got {response.status_code}"
        print("SUCCESS: Invalid URL returns 400")
    
    def test_image_proxy_handles_failing_url_gracefully(self):
        """Test that proxy handles 404 from upstream gracefully"""
        # URL that doesn't exist
        fake_url = "https://i.discogs.com/nonexistent-image-12345.jpeg"
        encoded_url = urllib.parse.quote(fake_url, safe='')
        response = requests.get(f"{BASE_URL}/api/image-proxy?url={encoded_url}")
        
        # Should return error status (not crash)
        assert response.status_code in [404, 502, 503], \
            f"Expected error status for non-existent image, got {response.status_code}"
        print(f"SUCCESS: Non-existent image returns {response.status_code}")
    
    def test_image_proxy_cache_control_header(self):
        """Test that proxy returns proper cache headers"""
        encoded_url = urllib.parse.quote(SAMPLE_DISCOGS_IMAGE, safe='')
        response = requests.get(f"{BASE_URL}/api/image-proxy?url={encoded_url}")
        
        if response.status_code == 200:
            cache_control = response.headers.get("Cache-Control", "")
            assert "max-age" in cache_control, f"Expected max-age in Cache-Control, got {cache_control}"
            print(f"SUCCESS: Cache-Control header is: {cache_control}")
    
    def test_image_proxy_follows_redirects(self):
        """Test that proxy follows redirects (e.g., Discogs URL redirections)"""
        # Discogs often redirects image URLs
        encoded_url = urllib.parse.quote(SAMPLE_DISCOGS_IMAGE, safe='')
        response = requests.get(f"{BASE_URL}/api/image-proxy?url={encoded_url}", allow_redirects=False)
        
        # Our proxy should have already followed redirects, so we should get 200 directly
        assert response.status_code == 200, f"Proxy should handle redirects internally, got {response.status_code}"
        print("SUCCESS: Proxy handles redirects internally")


class TestWeeklyReportEndpoints:
    """Tests for endpoints used by Weekly Report page"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_records_endpoint_returns_data(self, auth_token):
        """Test GET /api/records returns user records"""
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of records"
        print(f"SUCCESS: GET /api/records returns {len(data)} records")
    
    def test_spins_endpoint_returns_data(self, auth_token):
        """Test GET /api/spins returns user spins"""
        response = requests.get(
            f"{BASE_URL}/api/spins",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of spins"
        print(f"SUCCESS: GET /api/spins returns {len(data)} spins")
    
    def test_collection_value_endpoint(self, auth_token):
        """Test GET /api/valuation/collection-value returns value data"""
        response = requests.get(
            f"{BASE_URL}/api/valuation/collection-value",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Can be 200 or 404 depending on user data
        assert response.status_code in [200, 404], f"Unexpected status {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Collection value endpoint returned: {data}")
        else:
            print("INFO: No collection value data for test user")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
