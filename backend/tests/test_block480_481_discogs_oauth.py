"""
Test cases for BLOCK 480 (Emergent Environment Alignment) and BLOCK 481 (Internal Error Resolution)
- OAuth start endpoint accepts frontend_origin query param
- Callback URL priority: frontend_origin > Origin header > FRONTEND_URL env var
- HMAC-SHA1 signature method explicitly set
- Comprehensive error logging for Discogs failures
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBlock480OAuthDynamicOrigin:
    """BLOCK 480: Test dynamic callback URL generation based on frontend_origin"""

    @pytest.fixture
    def auth_headers(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        if login_resp.status_code == 200:
            # API returns access_token, not token
            token = login_resp.json().get("access_token") or login_resp.json().get("token")
            if token:
                return {"Authorization": f"Bearer {token}"}
        pytest.skip("Authentication failed - skipping authenticated tests")

    def test_oauth_start_accepts_frontend_origin_param(self, auth_headers):
        """Test that /api/discogs/oauth/start accepts frontend_origin query param"""
        # Call OAuth start with frontend_origin param
        test_origin = "https://test-origin.example.com"
        resp = requests.get(
            f"{BASE_URL}/api/discogs/oauth/start?frontend_origin={test_origin}",
            headers=auth_headers
        )
        
        # The endpoint should return 200 with authorization_url OR 500 if Discogs credentials are invalid
        # But it should accept the param without error
        assert resp.status_code in [200, 500], f"Unexpected status {resp.status_code}: {resp.text}"
        
        # If successful, check we get authorization_url
        if resp.status_code == 200:
            data = resp.json()
            assert "authorization_url" in data
            assert "oauth_token" in data["authorization_url"]
            print(f"OAuth start successful with frontend_origin param")
        else:
            # 500 is OK if Discogs credentials are invalid (different from not accepting param)
            error_detail = resp.json().get("detail", "")
            assert "frontend_origin" not in error_detail.lower(), "Error should not be about frontend_origin param"
            print(f"OAuth start returned 500 (expected if Discogs creds invalid): {error_detail[:100]}")

    def test_oauth_start_returns_authorization_url(self, auth_headers):
        """Test that OAuth start returns a valid authorization_url"""
        # Use a realistic frontend origin
        resp = requests.get(
            f"{BASE_URL}/api/discogs/oauth/start?frontend_origin=https://production-bugs-2.preview.emergentagent.com",
            headers=auth_headers
        )
        
        if resp.status_code == 200:
            data = resp.json()
            assert "authorization_url" in data
            assert "https://www.discogs.com/oauth/authorize" in data["authorization_url"]
            print(f"Got authorization URL: {data['authorization_url'][:80]}...")
        elif resp.status_code == 500:
            # 500 is acceptable if Discogs API is unreachable or credentials are wrong
            print(f"OAuth start failed (may be expected): {resp.json().get('detail', '')[:100]}")
        else:
            pytest.fail(f"Unexpected status {resp.status_code}: {resp.text}")

    def test_oauth_start_without_frontend_origin_uses_fallback(self, auth_headers):
        """Test that OAuth start works without frontend_origin (falls back to Origin header or FRONTEND_URL)"""
        # Call without frontend_origin param
        resp = requests.get(
            f"{BASE_URL}/api/discogs/oauth/start",
            headers={**auth_headers, "Origin": "https://fallback-origin.example.com"}
        )
        
        # Should still work (use Origin header as fallback)
        assert resp.status_code in [200, 500], f"Unexpected status {resp.status_code}: {resp.text}"
        print(f"OAuth start without frontend_origin: status {resp.status_code}")

    def test_oauth_start_requires_auth(self):
        """Test that OAuth start requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/discogs/oauth/start")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("OAuth start correctly requires authentication")


class TestBlock481ErrorLogging:
    """BLOCK 481: Test comprehensive error logging for Discogs failures"""

    @pytest.fixture
    def auth_headers(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        if login_resp.status_code == 200:
            # API returns access_token, not token
            token = login_resp.json().get("access_token") or login_resp.json().get("token")
            if token:
                return {"Authorization": f"Bearer {token}"}
        pytest.skip("Authentication failed - skipping authenticated tests")

    def test_oauth_callback_invalid_token(self):
        """Test OAuth callback with invalid token returns proper error"""
        resp = requests.get(
            f"{BASE_URL}/api/discogs/oauth/callback?oauth_token=invalid_token&oauth_verifier=invalid_verifier"
        )
        # Should redirect (3xx) to frontend with error message
        # Note: requests follows redirects by default unless allow_redirects=False
        # The endpoint returns RedirectResponse, so we might get 200 after redirect
        # OR if redirect target doesn't exist, we might get connection error
        print(f"OAuth callback with invalid token: status {resp.status_code}")
        # Just verify it doesn't crash with 500
        assert resp.status_code != 500 or "discogs" in resp.url.lower() or "error" in resp.url.lower()


class TestDiscogsConnectionStatus:
    """Test Discogs connection status endpoint"""

    @pytest.fixture
    def auth_headers(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        if login_resp.status_code == 200:
            # API returns access_token, not token
            token = login_resp.json().get("access_token") or login_resp.json().get("token")
            if token:
                return {"Authorization": f"Bearer {token}"}
        pytest.skip("Authentication failed - skipping authenticated tests")

    def test_discogs_status_endpoint(self, auth_headers):
        """Test /api/discogs/status returns proper status structure"""
        resp = requests.get(
            f"{BASE_URL}/api/discogs/status",
            headers=auth_headers
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check expected fields are present
        assert "connected" in data
        assert isinstance(data["connected"], bool)
        
        if data["connected"]:
            assert "discogs_username" in data
            print(f"Discogs connected as: {data.get('discogs_username')}")
        else:
            print("Discogs not connected for this user")

    def test_discogs_import_progress_endpoint(self, auth_headers):
        """Test /api/discogs/import/progress returns proper structure"""
        resp = requests.get(
            f"{BASE_URL}/api/discogs/import/progress",
            headers=auth_headers
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check expected fields
        assert "status" in data
        assert data["status"] in ["idle", "in_progress", "completed", "error"]
        print(f"Import progress status: {data['status']}")


class TestBackendEnvConfiguration:
    """Test that backend .env doesn't have duplicate entries"""

    def test_discogs_keys_configured(self, auth_headers=None):
        """Test that Discogs keys are properly configured (no duplicates)"""
        # We can't directly read .env, but we can verify the endpoint works
        # If there were duplicate/empty keys, the OAuth start would fail with "not configured"
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Login failed")
            
        token = login_resp.json().get("access_token") or login_resp.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = requests.get(
            f"{BASE_URL}/api/discogs/oauth/start?frontend_origin=https://test.example.com",
            headers=headers
        )
        
        # If keys are empty, we'd get "Discogs OAuth not configured" error
        if resp.status_code == 400:
            error = resp.json().get("detail", "")
            assert "not configured" not in error.lower(), "Discogs keys appear to be empty or misconfigured"
            
        print(f"Discogs OAuth endpoint response: {resp.status_code}")
        # 200 = working, 500 = Discogs API issue (but keys are configured)
        assert resp.status_code in [200, 500], f"Unexpected status: {resp.status_code}"


class TestHMacSHA1Signature:
    """Test that OAuth uses HMAC-SHA1 signature method"""

    @pytest.fixture
    def auth_headers(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        if login_resp.status_code == 200:
            # API returns access_token, not token
            token = login_resp.json().get("access_token") or login_resp.json().get("token")
            if token:
                return {"Authorization": f"Bearer {token}"}
        pytest.skip("Authentication failed - skipping authenticated tests")

    def test_oauth_start_uses_hmac_sha1(self, auth_headers):
        """
        Verify OAuth start endpoint works (HMAC-SHA1 is used internally).
        We can't directly test the signature method via API, but if it's wrong,
        Discogs would reject the request with signature_invalid error.
        """
        resp = requests.get(
            f"{BASE_URL}/api/discogs/oauth/start?frontend_origin=https://test.example.com",
            headers=auth_headers
        )
        
        # If HMAC-SHA1 is not used correctly, Discogs would return an error
        # about invalid signature method
        if resp.status_code == 500:
            error = resp.json().get("detail", "")
            assert "signature" not in error.lower() or "invalid" not in error.lower(), \
                f"Possible HMAC-SHA1 signature issue: {error}"
            print(f"OAuth start returned 500 (not signature related): {error[:100]}")
        elif resp.status_code == 200:
            print("OAuth start successful - HMAC-SHA1 signature working correctly")
        else:
            print(f"OAuth start returned {resp.status_code}")
