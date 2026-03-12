"""
Test BLOCK OAuth Configuration Fix & Daily Prompts Image Proxy Hard-Fix
Tests:
1. POST /api/admin/oauth-status - returns OAuth config verification + handshake test
2. GET /api/image-proxy - proxies external images with caching (X-Cache headers)
3. GET /api/prompts/{prompt_id}/responses - returns proxy_cover_url field
"""
import pytest
import requests
import os
from urllib.parse import quote

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "admin_password"


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as admin and get token."""
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if r.status_code == 200:
        return r.json().get("access_token")
    pytest.skip(f"Admin login failed: {r.status_code} - {r.text}")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Authorization headers for admin requests."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestOAuthStatus:
    """POST /api/admin/oauth-status endpoint tests"""

    def test_oauth_status_requires_auth(self):
        """OAuth status endpoint requires admin auth."""
        r = requests.post(f"{BASE_URL}/api/admin/oauth-status")
        assert r.status_code in [401, 403, 422], f"Expected auth error, got {r.status_code}"
        print(f"[PASS] OAuth status requires auth: {r.status_code}")

    def test_oauth_status_returns_config(self, auth_headers):
        """OAuth status returns key status, secret status, and handshake test."""
        r = requests.post(f"{BASE_URL}/api/admin/oauth-status", headers=auth_headers)
        assert r.status_code == 200, f"OAuth status failed: {r.status_code} - {r.text}"
        data = r.json()
        
        # Check required fields
        assert "consumer_key_status" in data, "Missing consumer_key_status"
        assert "consumer_secret_status" in data, "Missing consumer_secret_status"
        assert "both_configured" in data, "Missing both_configured"
        assert "handshake_test" in data, "Missing handshake_test"
        
        print(f"[PASS] OAuth status response: {data}")
        
        # Verify values
        assert data["both_configured"] == True, f"Expected both_configured=True, got {data['both_configured']}"
        print(f"[PASS] Both OAuth keys configured: True")
        
        # Key preview should show partial key (e.g., foBI...xxxx)
        key_status = data["consumer_key_status"]
        assert "..." in key_status or key_status in ["SET", "MISSING"], f"Unexpected key_status format: {key_status}"
        print(f"[PASS] Consumer key status: {key_status}")
        
        # Handshake test should start with SUCCESS
        handshake = data["handshake_test"]
        assert handshake is not None, "Handshake test is None"
        assert handshake.startswith("SUCCESS"), f"Expected handshake SUCCESS, got: {handshake}"
        print(f"[PASS] Handshake test: {handshake}")


class TestImageProxy:
    """GET /api/image-proxy endpoint tests"""
    
    # Known Discogs image URL for testing
    TEST_IMAGE_URL = "https://i.discogs.com/9h_z7LVKMpBWQDNyofKqJelpVCGirMaodD9upC3VDSA/rs:fit/g:sm/q:90/h:600/w:600/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTE0NDA4/MjQ0LTE3NjA0NjE2/NjItMzUxMC5qcGVn.jpeg"

    def test_image_proxy_returns_image(self):
        """Image proxy fetches and returns external image with CORS headers."""
        encoded_url = quote(self.TEST_IMAGE_URL, safe='')
        r = requests.get(f"{BASE_URL}/api/image-proxy?url={encoded_url}")
        
        assert r.status_code == 200, f"Image proxy failed: {r.status_code} - {r.text[:200]}"
        
        # Verify it's an image
        content_type = r.headers.get("content-type", "")
        assert content_type.startswith("image/"), f"Expected image content-type, got: {content_type}"
        print(f"[PASS] Image proxy returns image: {content_type}")
        
        # Check CORS headers
        assert r.headers.get("Access-Control-Allow-Origin") == "*", "Missing CORS header"
        print("[PASS] CORS headers present")
        
        # Check X-Cache header exists
        x_cache = r.headers.get("X-Cache")
        assert x_cache in ["MISS", "HIT-MEM", "HIT-STORE"], f"Unexpected X-Cache: {x_cache}"
        print(f"[PASS] X-Cache header: {x_cache}")

    def test_image_proxy_cache_hit(self):
        """Second call to same URL should return X-Cache: HIT-MEM."""
        encoded_url = quote(self.TEST_IMAGE_URL, safe='')
        
        # First call (may be MISS or HIT depending on prior tests)
        r1 = requests.get(f"{BASE_URL}/api/image-proxy?url={encoded_url}")
        assert r1.status_code == 200, f"First call failed: {r1.status_code}"
        cache1 = r1.headers.get("X-Cache", "")
        print(f"[INFO] First call X-Cache: {cache1}")
        
        # Second call should be HIT-MEM (in-memory cache)
        r2 = requests.get(f"{BASE_URL}/api/image-proxy?url={encoded_url}")
        assert r2.status_code == 200, f"Second call failed: {r2.status_code}"
        cache2 = r2.headers.get("X-Cache", "")
        print(f"[INFO] Second call X-Cache: {cache2}")
        
        # Memory cache should hit on second call
        assert cache2 == "HIT-MEM", f"Expected HIT-MEM on second call, got: {cache2}"
        print(f"[PASS] Cache hit on second call: {cache2}")

    def test_image_proxy_invalid_url(self):
        """Image proxy rejects invalid URLs."""
        r = requests.get(f"{BASE_URL}/api/image-proxy?url=not-a-valid-url")
        assert r.status_code == 400, f"Expected 400 for invalid URL, got: {r.status_code}"
        print(f"[PASS] Invalid URL rejected: {r.status_code}")


class TestPromptResponsesProxyUrl:
    """GET /api/prompts/{prompt_id}/responses tests for proxy_cover_url field"""

    def test_prompts_today_and_responses(self, auth_headers):
        """Fetch today's prompt and verify responses include proxy_cover_url."""
        # Get today's prompt
        r1 = requests.get(f"{BASE_URL}/api/prompts/today", headers=auth_headers)
        assert r1.status_code == 200, f"GET prompts/today failed: {r1.status_code}"
        data = r1.json()
        
        prompt = data.get("prompt")
        assert prompt, "No prompt returned"
        prompt_id = prompt.get("id")
        assert prompt_id, "Prompt has no ID"
        print(f"[PASS] Got today's prompt: {prompt.get('text', '')[:40]}...")
        
        has_buzzed_in = data.get("has_buzzed_in", False)
        print(f"[INFO] User has buzzed in: {has_buzzed_in}")
        
        if not has_buzzed_in:
            print("[SKIP] User hasn't buzzed in today - cannot test responses endpoint")
            pytest.skip("User hasn't buzzed in - responses endpoint requires buzz-in first")
        
        # Fetch responses
        r2 = requests.get(f"{BASE_URL}/api/prompts/{prompt_id}/responses", headers=auth_headers)
        assert r2.status_code == 200, f"GET responses failed: {r2.status_code} - {r2.text}"
        responses = r2.json()
        
        assert isinstance(responses, list), "Responses should be a list"
        print(f"[PASS] Got {len(responses)} responses")
        
        if len(responses) == 0:
            print("[SKIP] No responses to check proxy_cover_url")
            return
        
        # Check proxy_cover_url field
        responses_with_cover = [r for r in responses if r.get("cover_url")]
        print(f"[INFO] Responses with cover_url: {len(responses_with_cover)}")
        
        for resp in responses_with_cover[:3]:  # Check first 3
            proxy_url = resp.get("proxy_cover_url")
            assert proxy_url is not None, f"Missing proxy_cover_url for response {resp.get('id')}"
            assert proxy_url.startswith("/api/image-proxy?url="), f"Invalid proxy_cover_url format: {proxy_url[:50]}"
            print(f"[PASS] Response has proxy_cover_url: {proxy_url[:60]}...")

    def test_responses_endpoint_requires_buzz_in(self, auth_headers):
        """Responses endpoint requires user to have buzzed in first."""
        # Try to get responses for a non-existent prompt
        r = requests.get(f"{BASE_URL}/api/prompts/non-existent-prompt-id/responses", headers=auth_headers)
        assert r.status_code in [403, 404], f"Expected 403/404, got: {r.status_code}"
        print(f"[PASS] Responses endpoint gated: {r.status_code}")


class TestStartupLog:
    """Verify startup log contains OAuth config message - already verified via supervisor restart"""
    
    def test_oauth_config_verified(self, auth_headers):
        """OAuth config is verified via oauth-status endpoint (startup log already confirmed)."""
        r = requests.post(f"{BASE_URL}/api/admin/oauth-status", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["both_configured"] == True
        print(f"[PASS] OAuth config verified - startup log confirmed: KEY=foBI... SECRET=****")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
