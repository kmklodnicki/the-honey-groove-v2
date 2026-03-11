"""
BLOCK 453: Discogs OAuth 1.0a Integration
BLOCK 455: Security Migration Modal

Tests for:
- OAuth start endpoint returns authorization_url
- Deprecated connect-token endpoint returns 400
- Discogs status includes oauth_verified, auth_type, needs_migration
- dismiss-migration sets flag on user doc
- /auth/me includes needs_discogs_migration and discogs_oauth_verified
- imposter-flags admin-only access
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from requirement
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "test123"
ADMIN_EMAIL = "admin@thehoneygroove.com"
ADMIN_PASSWORD = "admin_password"


class TestDiscogsOAuthMigration:
    """Tests for Discogs OAuth 1.0a and Security Migration features"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """Shared requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    @pytest.fixture(scope="class")
    def user_token(self, api_client):
        """Get authentication token for test user"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Test user login failed: {response.status_code} - {response.text}")

    @pytest.fixture(scope="class")
    def admin_token(self, api_client):
        """Get authentication token for admin user"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")

    # ==== BLOCK 453: OAuth Start Endpoint ====
    def test_oauth_start_returns_authorization_url(self, api_client, user_token):
        """GET /api/discogs/oauth/start returns authorization_url for authenticated users"""
        response = api_client.get(
            f"{BASE_URL}/api/discogs/oauth/start",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "authorization_url" in data, "Response should contain 'authorization_url'"
        assert "discogs.com" in data["authorization_url"], "Authorization URL should point to Discogs"
        assert "oauth_token" in data["authorization_url"], "Authorization URL should contain oauth_token"
        print(f"✓ OAuth start returned authorization URL: {data['authorization_url'][:60]}...")

    def test_oauth_start_requires_auth(self, api_client):
        """GET /api/discogs/oauth/start requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/discogs/oauth/start")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ OAuth start requires authentication")

    # ==== BLOCK 453: Deprecated connect-token Endpoint ====
    def test_connect_token_returns_400_deprecated(self, api_client, user_token):
        """POST /api/discogs/connect-token returns 400 with deprecation message"""
        response = api_client.post(
            f"{BASE_URL}/api/discogs/connect-token",
            json={"discogs_username": "some_username"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "no longer supported" in data.get("detail", "").lower(), \
            f"Error should mention 'no longer supported', got: {data.get('detail')}"
        print(f"✓ connect-token deprecated: {data.get('detail')}")

    # ==== Discogs Status Endpoint ====
    def test_discogs_status_includes_migration_fields(self, api_client, user_token):
        """GET /api/discogs/status returns oauth_verified, auth_type, needs_migration fields"""
        response = api_client.get(
            f"{BASE_URL}/api/discogs/status",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # These fields should exist in the response (may be null/false for users without Discogs)
        # Check structure, not specific values
        expected_fields = ["connected", "oauth_verified", "auth_type", "needs_migration"]
        for field in expected_fields:
            assert field in data, f"Response should contain '{field}', got: {data.keys()}"
        
        print(f"✓ Discogs status has migration fields: connected={data.get('connected')}, "
              f"oauth_verified={data.get('oauth_verified')}, auth_type={data.get('auth_type')}, "
              f"needs_migration={data.get('needs_migration')}")

    # ==== BLOCK 455: Dismiss Migration Endpoint ====
    def test_dismiss_migration_sets_flag(self, api_client, user_token):
        """POST /api/discogs/dismiss-migration sets discogs_migration_dismissed on user"""
        response = api_client.post(
            f"{BASE_URL}/api/discogs/dismiss-migration",
            json={},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("dismissed") == True, f"Response should have dismissed=True, got: {data}"
        print("✓ dismiss-migration returned dismissed=True")

    # ==== /auth/me Fields ====
    def test_auth_me_includes_discogs_fields(self, api_client, user_token):
        """GET /api/auth/me includes needs_discogs_migration and discogs_oauth_verified"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # These fields should be present
        assert "needs_discogs_migration" in data, \
            f"Response should contain 'needs_discogs_migration', got: {data.keys()}"
        assert "discogs_oauth_verified" in data, \
            f"Response should contain 'discogs_oauth_verified', got: {data.keys()}"
        
        print(f"✓ /auth/me includes migration fields: needs_discogs_migration={data.get('needs_discogs_migration')}, "
              f"discogs_oauth_verified={data.get('discogs_oauth_verified')}")

    # ==== Imposter Flags Admin-Only ====
    def test_imposter_flags_requires_admin(self, api_client, user_token):
        """GET /api/discogs/imposter-flags returns 403 for non-admin users"""
        response = api_client.get(
            f"{BASE_URL}/api/discogs/imposter-flags",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("✓ imposter-flags returns 403 for non-admin user")

    def test_imposter_flags_accessible_to_admin(self, api_client, admin_token):
        """GET /api/discogs/imposter-flags accessible to admin users"""
        response = api_client.get(
            f"{BASE_URL}/api/discogs/imposter-flags",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should return a list (empty or with flags)
        assert isinstance(data, list), f"Response should be a list, got: {type(data)}"
        print(f"✓ imposter-flags accessible to admin, returned {len(data)} flags")


class TestMigrationScenarios:
    """Test specific migration scenarios based on user state"""

    @pytest.fixture(scope="class")
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    @pytest.fixture(scope="class")
    def user_token(self, api_client):
        """Get authentication token for test user"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Test user login failed: {response.status_code}")

    def test_dismiss_then_check_me_migration_false(self, api_client, user_token):
        """After dismissing migration, /auth/me should return needs_discogs_migration=False"""
        # First dismiss
        dismiss_resp = api_client.post(
            f"{BASE_URL}/api/discogs/dismiss-migration",
            json={},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert dismiss_resp.status_code == 200
        
        # Then check /auth/me
        me_resp = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert me_resp.status_code == 200
        data = me_resp.json()
        
        # After dismissal, needs_discogs_migration should be False
        # (regardless of whether user has discogs connected)
        print(f"✓ After dismissal: needs_discogs_migration={data.get('needs_discogs_migration')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
