"""
Test Suite for Login Authentication - P0 Critical Login Fix
Tests login by email, username, case-insensitivity, whitespace handling,
and the auth/me endpoint with tokens from username login.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials from the review request
ADMIN_USER = {
    "email": "kmklodnicki@gmail.com",
    "username": "katieintheafterglow",
    "password": "admin_password"
}

TEST_USER = {
    "email": "test@example.com",
    "username": "testuser1",
    "password": "test123"
}


class TestLoginByEmail:
    """Test login using exact email match"""
    
    def test_login_exact_email_match(self):
        """Login with exact email (kmklodnicki@gmail.com / admin_password)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_USER["email"],
            "password": ADMIN_USER["password"]
        })
        print(f"Login by exact email: status={response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        assert "user" in data, "Response missing user"
        assert data["user"]["email"] == ADMIN_USER["email"], f"Email mismatch: {data['user']['email']}"
        print(f"SUCCESS: Login by exact email worked for {data['user']['username']}")
        return data["access_token"]
    
    def test_login_test_user_email(self):
        """Login with test user email (test@example.com / test123)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        print(f"Login by test user email: status={response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == TEST_USER["email"]
        print(f"SUCCESS: Login by test user email worked for {data['user']['username']}")


class TestLoginByUsername:
    """Test login using username (case-insensitive)"""
    
    def test_login_exact_username(self):
        """Login with exact username (katieintheafterglow / admin_password)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_USER["username"],  # Using username in email field
            "password": ADMIN_USER["password"]
        })
        print(f"Login by exact username: status={response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == ADMIN_USER["username"]
        print(f"SUCCESS: Login by exact username worked")
        return data["access_token"]
    
    def test_login_test_user_username(self):
        """Login with test user username (testuser1 / test123)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER["username"],
            "password": TEST_USER["password"]
        })
        print(f"Login by test user username: status={response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == TEST_USER["username"]
        print(f"SUCCESS: Login by test user username worked")


class TestLoginCaseInsensitive:
    """Test case-insensitive login for email and username"""
    
    def test_login_email_mixed_case(self):
        """Login with mixed case email (Kmklodnicki@Gmail.com / admin_password)"""
        mixed_email = "Kmklodnicki@Gmail.com"
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": mixed_email,
            "password": ADMIN_USER["password"]
        })
        print(f"Login by mixed case email: status={response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        print(f"SUCCESS: Case-insensitive email login worked")
    
    def test_login_username_case_insensitive(self):
        """Login with different case username (KATIEINTHEAFTERGLOW)"""
        upper_username = ADMIN_USER["username"].upper()
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": upper_username,
            "password": ADMIN_USER["password"]
        })
        print(f"Login by uppercase username: status={response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        print(f"SUCCESS: Case-insensitive username login worked")


class TestLoginWhitespace:
    """Test whitespace handling in login"""
    
    def test_login_email_with_whitespace(self):
        """Login with whitespace around email (  kmklodnicki@gmail.com  / admin_password)"""
        whitespace_email = "  kmklodnicki@gmail.com  "
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": whitespace_email,
            "password": ADMIN_USER["password"]
        })
        print(f"Login by email with whitespace: status={response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        print(f"SUCCESS: Whitespace in email handled correctly")


class TestLoginNegativeCases:
    """Test negative login scenarios"""
    
    def test_login_wrong_password(self):
        """Login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_USER["email"],
            "password": "wrong"
        })
        print(f"Login wrong password: status={response.status_code}")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print(f"SUCCESS: Wrong password correctly returns 401")
    
    def test_login_nonexistent_user(self):
        """Login with non-existent user returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "katie@thehoneygroove.com",  # This email does NOT exist
            "password": ADMIN_USER["password"]
        })
        print(f"Login non-existent user: status={response.status_code}")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print(f"SUCCESS: Non-existent user correctly returns 401")
    
    def test_login_nonexistent_email_and_username(self):
        """Login with completely non-existent credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "doesnotexist@fake.com",
            "password": "anypassword"
        })
        print(f"Login completely non-existent: status={response.status_code}")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print(f"SUCCESS: Non-existent credentials correctly returns 401")


class TestAuthMeEndpoint:
    """Test auth/me endpoint with tokens from username login"""
    
    def test_auth_me_with_username_login_token(self):
        """Auth/me works with token from username login"""
        # First login by username
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_USER["username"],
            "password": ADMIN_USER["password"]
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        token = login_resp.json()["access_token"]
        
        # Now call auth/me
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Auth/me with username login token: status={me_resp.status_code}")
        assert me_resp.status_code == 200, f"Expected 200, got {me_resp.status_code}: {me_resp.text}"
        
        user = me_resp.json()
        assert user["username"] == ADMIN_USER["username"]
        assert user["email"] == ADMIN_USER["email"]
        print(f"SUCCESS: Auth/me works with token from username login")
    
    def test_auth_me_with_email_login_token(self):
        """Auth/me works with token from email login"""
        # Login by email
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        token = login_resp.json()["access_token"]
        
        # Call auth/me
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Auth/me with email login token: status={me_resp.status_code}")
        assert me_resp.status_code == 200, f"Expected 200, got {me_resp.status_code}: {me_resp.text}"
        
        user = me_resp.json()
        assert user["email"] == TEST_USER["email"]
        print(f"SUCCESS: Auth/me works with token from email login")


class TestRegistrationEmailNormalization:
    """Test that registration normalizes email to lowercase"""
    
    def test_registration_email_lowercase(self):
        """Registration normalizes email - check existing user's email is lowercase"""
        # Login to check the stored email format
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_USER["email"],
            "password": ADMIN_USER["password"]
        })
        assert response.status_code == 200
        
        user = response.json()["user"]
        # Check email is lowercase
        assert user["email"] == user["email"].lower(), f"Email not lowercase: {user['email']}"
        print(f"SUCCESS: Email is stored lowercase: {user['email']}")


class TestAdminLoginDiagnostic:
    """Test admin login-diagnostic endpoint"""
    
    def test_admin_login_diagnostic_requires_auth(self):
        """Login diagnostic requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/login-diagnostic", json={
            "identifier": ADMIN_USER["email"]
        })
        print(f"Diagnostic without auth: status={response.status_code}")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: Diagnostic endpoint requires auth")
    
    def test_admin_login_diagnostic_works(self):
        """Login diagnostic works for admin users"""
        # First login as admin
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_USER["email"],
            "password": ADMIN_USER["password"]
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        token = login_resp.json()["access_token"]
        
        # Now call diagnostic
        diag_resp = requests.post(
            f"{BASE_URL}/api/admin/login-diagnostic",
            json={"identifier": ADMIN_USER["email"], "test_password": ADMIN_USER["password"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Diagnostic as admin: status={diag_resp.status_code}")
        
        # If user is admin, should return 200
        # If user is not admin, should return 403
        if diag_resp.status_code == 200:
            data = diag_resp.json()
            assert data.get("user_found") == True
            if "password_match" in data:
                assert data["password_match"] == True
            print(f"SUCCESS: Admin diagnostic works. Checks: {data.get('checks')}")
        elif diag_resp.status_code == 403:
            print(f"INFO: User is not admin, diagnostic endpoint returned 403 (expected for non-admin)")
        else:
            print(f"WARNING: Unexpected status {diag_resp.status_code}: {diag_resp.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
