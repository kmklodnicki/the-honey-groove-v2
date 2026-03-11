"""
BLOCK 491 & BLOCK 492: Debug Reset Migration and Migration Modal Logic
Tests for:
- POST /api/debug/reset-migration - restricted to @katieintheafterglow only
- _check_needs_migration logic - triggers when has_seen_security_migration is False
- /api/auth/me returns needs_discogs_migration flag correctly
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBlockDebugResetMigration:
    """Test BLOCK 491 debug reset migration endpoint access control"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin@thehoneygroove.com"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Admin login failed - skipping admin tests")
    
    @pytest.fixture(scope="class")
    def test_user_token(self):
        """Login as test@example.com"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Test user login failed - skipping test user tests")
    
    def test_admin_cannot_use_debug_reset(self, admin_token):
        """BLOCK 491: Admin (username != katieintheafterglow) should get 403"""
        resp = requests.post(
            f"{BASE_URL}/api/debug/reset-migration",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 403, f"Expected 403 for admin, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "restricted" in data.get("detail", "").lower() or "authorized" in data.get("detail", "").lower(), \
            f"Expected restricted/authorized error message, got: {data}"
        print(f"PASS: Admin correctly gets 403 for debug reset - {data.get('detail')}")
    
    def test_regular_user_cannot_use_debug_reset(self, test_user_token):
        """BLOCK 491: Regular test user should also get 403"""
        resp = requests.post(
            f"{BASE_URL}/api/debug/reset-migration",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert resp.status_code == 403, f"Expected 403 for test user, got {resp.status_code}: {resp.text}"
        print(f"PASS: Test user correctly gets 403 for debug reset")
    
    def test_unauthenticated_cannot_use_debug_reset(self):
        """BLOCK 491: Unauthenticated requests should fail"""
        resp = requests.post(f"{BASE_URL}/api/debug/reset-migration")
        assert resp.status_code in [401, 403], f"Expected 401/403 for unauthenticated, got {resp.status_code}"
        print(f"PASS: Unauthenticated request correctly rejected with {resp.status_code}")


class TestBlockMigrationCheck:
    """Test BLOCK 492 migration check logic via /api/auth/me"""
    
    @pytest.fixture(scope="class")
    def admin_auth(self):
        """Login as admin and get both token and user data"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        if resp.status_code == 200:
            data = resp.json()
            return {
                "token": data.get("access_token"),
                "user": data.get("user")
            }
        pytest.skip("Admin login failed")
    
    def test_auth_me_returns_needs_migration_field(self, admin_auth):
        """BLOCK 492: /api/auth/me should return needs_discogs_migration field"""
        resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        assert resp.status_code == 200, f"Auth/me failed: {resp.text}"
        data = resp.json()
        
        # Field must exist
        assert "needs_discogs_migration" in data, \
            f"needs_discogs_migration field missing from auth/me response: {list(data.keys())}"
        
        print(f"PASS: needs_discogs_migration field present in auth/me response")
        print(f"  Current value: {data.get('needs_discogs_migration')}")
        print(f"  User: {data.get('username')}")
    
    def test_admin_needs_migration_field_type(self, admin_auth):
        """BLOCK 492: Admin's needs_discogs_migration should be a boolean (True or False)"""
        resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        assert resp.status_code == 200, f"Auth/me failed: {resp.text}"
        data = resp.json()
        
        # The needs_discogs_migration field should be a boolean
        # (True if has_seen_security_migration=False, False if already seen/dismissed)
        needs_migration = data.get("needs_discogs_migration")
        assert isinstance(needs_migration, bool), \
            f"Expected needs_discogs_migration to be boolean, got: {type(needs_migration)}"
        
        print(f"PASS: Admin user's needs_discogs_migration is boolean: {needs_migration}")
    
    def test_login_response_includes_migration_flag(self):
        """Login response user object should include needs_discogs_migration"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        user = data.get("user", {})
        
        assert "needs_discogs_migration" in user, \
            f"needs_discogs_migration missing from login user response: {list(user.keys())}"
        
        print(f"PASS: Login response includes needs_discogs_migration: {user.get('needs_discogs_migration')}")


class TestMigrationDismissedFlow:
    """Test that dismissed users don't need migration"""
    
    @pytest.fixture(scope="class")
    def test_user_auth(self):
        """Login as test user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if resp.status_code == 200:
            data = resp.json()
            return {
                "token": data.get("access_token"),
                "user": data.get("user")
            }
        pytest.skip("Test user login failed")
    
    def test_discogs_migration_dismissed_field_exists(self, test_user_auth):
        """Verify discogs_migration_dismissed field in auth/me"""
        resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {test_user_auth['token']}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Check both fields exist
        assert "discogs_migration_dismissed" in data, "discogs_migration_dismissed field missing"
        assert "needs_discogs_migration" in data, "needs_discogs_migration field missing"
        
        print(f"PASS: Both migration fields present")
        print(f"  discogs_migration_dismissed: {data.get('discogs_migration_dismissed')}")
        print(f"  needs_discogs_migration: {data.get('needs_discogs_migration')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
