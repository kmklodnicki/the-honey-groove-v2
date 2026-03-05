"""
Beta Signup, Invite Codes, and Auth Lockdown Tests
Tests for closed beta system with invite-only registration
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBetaSignup:
    """Beta signup endpoint tests (public, no auth)"""
    
    def test_beta_signup_success(self):
        """Test successful beta signup"""
        unique_email = f"test_beta_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/beta/signup", json={
            "first_name": "Test",
            "email": unique_email,
            "instagram_handle": "testhandle",
            "feature_interest": "Tracking my collection"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "on the list" in data["message"].lower()
    
    def test_beta_signup_duplicate_email(self):
        """Test duplicate beta signup returns error"""
        unique_email = f"test_beta_dup_{uuid.uuid4().hex[:8]}@example.com"
        # First signup
        requests.post(f"{BASE_URL}/api/beta/signup", json={
            "first_name": "Test",
            "email": unique_email,
            "instagram_handle": "testhandle",
            "feature_interest": "Tracking my collection"
        })
        # Duplicate signup
        response = requests.post(f"{BASE_URL}/api/beta/signup", json={
            "first_name": "Test2",
            "email": unique_email,
            "instagram_handle": "testhandle2",
            "feature_interest": "Trading with other collectors"
        })
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestInviteCodeRegistration:
    """Invite code registration tests (public endpoint)"""
    
    def test_register_with_invalid_code(self):
        """Test registration with invalid invite code"""
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "INVALID-CODE-123",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "test1234",
            "username": f"testuser_{uuid.uuid4().hex[:8]}"
        })
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower() or "used" in response.json()["detail"].lower()
    
    def test_register_with_used_code(self):
        """Test registration with already used invite code"""
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "HG-5RGLCH78",  # Known used code from testing
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "test1234",
            "username": f"testuser_{uuid.uuid4().hex[:8]}"
        })
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower() or "used" in response.json()["detail"].lower()


class TestAdminAccess:
    """Admin-only endpoint tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def non_admin_token(self):
        """Get non-admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "newuser@test.com",
            "password": "test1234"
        })
        if response.status_code != 200:
            pytest.skip("Non-admin login failed")
        return response.json()["access_token"]
    
    def test_admin_can_list_beta_signups(self, admin_token):
        """Test admin can list beta signups"""
        response = requests.get(
            f"{BASE_URL}/api/admin/beta-signups",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_admin_can_list_invite_codes(self, admin_token):
        """Test admin can list invite codes"""
        response = requests.get(
            f"{BASE_URL}/api/admin/invite-codes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify structure
        if len(data) > 0:
            code = data[0]
            assert "code" in code
            assert "status" in code
            assert "created_at" in code
    
    def test_admin_can_generate_invite_codes(self, admin_token):
        """Test admin can generate invite codes"""
        response = requests.post(
            f"{BASE_URL}/api/admin/invite-codes/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"count": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["code"].startswith("HG-")
        assert data[0]["status"] == "unused"
    
    def test_non_admin_cannot_list_beta_signups(self, non_admin_token):
        """Test non-admin cannot access beta signups"""
        response = requests.get(
            f"{BASE_URL}/api/admin/beta-signups",
            headers={"Authorization": f"Bearer {non_admin_token}"}
        )
        assert response.status_code == 403
    
    def test_non_admin_cannot_list_invite_codes(self, non_admin_token):
        """Test non-admin cannot access invite codes"""
        response = requests.get(
            f"{BASE_URL}/api/admin/invite-codes",
            headers={"Authorization": f"Bearer {non_admin_token}"}
        )
        assert response.status_code == 403
    
    def test_non_admin_cannot_generate_invite_codes(self, non_admin_token):
        """Test non-admin cannot generate invite codes"""
        response = requests.post(
            f"{BASE_URL}/api/admin/invite-codes/generate",
            headers={"Authorization": f"Bearer {non_admin_token}"},
            json={"count": 1}
        )
        assert response.status_code == 403
    
    def test_unauthenticated_cannot_access_admin(self):
        """Test unauthenticated users cannot access admin endpoints"""
        response = requests.get(f"{BASE_URL}/api/admin/beta-signups")
        assert response.status_code == 401


class TestInviteCodeRegistrationWithValidCode:
    """Test full invite code flow with valid code generation and usage"""
    
    def test_full_invite_registration_flow(self):
        """Test complete flow: generate code -> register -> verify founding member"""
        # Step 1: Admin login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        if login_resp.status_code != 200:
            pytest.skip("Admin login failed")
        admin_token = login_resp.json()["access_token"]
        
        # Step 2: Generate invite code
        gen_resp = requests.post(
            f"{BASE_URL}/api/admin/invite-codes/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"count": 1}
        )
        assert gen_resp.status_code == 200
        new_code = gen_resp.json()[0]["code"]
        
        # Step 3: Register with invite code
        unique_suffix = uuid.uuid4().hex[:8]
        register_resp = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": new_code,
            "email": f"founding_{unique_suffix}@example.com",
            "password": "test1234",
            "username": f"founding_{unique_suffix}"
        })
        assert register_resp.status_code == 200
        data = register_resp.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["founding_member"] == True
        
        # Step 4: Verify code is marked as used
        codes_resp = requests.get(
            f"{BASE_URL}/api/admin/invite-codes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        codes = codes_resp.json()
        used_code = next((c for c in codes if c["code"] == new_code), None)
        assert used_code is not None
        assert used_code["status"] == "used"


class TestPublicPageAccess:
    """Test that public pages are accessible without auth"""
    
    def test_beta_page_accessible(self):
        """Test /beta page is publicly accessible"""
        response = requests.get(f"{BASE_URL.replace('/api', '')}/beta", allow_redirects=False)
        # Should return 200 or serve HTML
        assert response.status_code in [200, 304]
    
    def test_join_page_accessible(self):
        """Test /join page is publicly accessible"""
        response = requests.get(f"{BASE_URL.replace('/api', '')}/join", allow_redirects=False)
        # Should return 200 or serve HTML
        assert response.status_code in [200, 304]
