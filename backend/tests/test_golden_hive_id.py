"""
Test suite for Golden Hive ID verification feature.
Tests:
- GET /api/golden-hive/status - returns verification status
- POST /api/golden-hive/checkout - creates Stripe checkout session ($9.99)
- POST /api/golden-hive/checkout - returns 400 if user already verified
- GET /api/golden-hive/verify-payment - handles post-payment verification
- GET /api/admin/golden-hive/pending - returns list of pending verifications (admin only)
- POST /api/admin/golden-hive/{user_id}/approve - updates user to verified status
- POST /api/admin/golden-hive/{user_id}/reject - updates user to rejected status
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestGoldenHiveStatus:
    """Test Golden Hive status endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for demo user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Could not authenticate demo user")
        
    @pytest.fixture(scope="class")
    def user_info(self, auth_token):
        """Get current user info"""
        resp = requests.get(f"{BASE_URL}/api/users/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        if resp.status_code == 200:
            return resp.json()
        return {}

    def test_golden_hive_status_returns_200(self, auth_token):
        """GET /api/golden-hive/status returns 200 for authenticated user"""
        resp = requests.get(f"{BASE_URL}/api/golden-hive/status", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
    def test_golden_hive_status_returns_required_fields(self, auth_token):
        """GET /api/golden-hive/status returns golden_hive_verified, golden_hive_status"""
        resp = requests.get(f"{BASE_URL}/api/golden-hive/status", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Required fields
        assert "golden_hive_verified" in data, "Missing golden_hive_verified field"
        assert "golden_hive_status" in data, "Missing golden_hive_status field"
        assert "golden_hive_verified_at" in data, "Missing golden_hive_verified_at field"
        
        # golden_hive_verified should be a boolean
        assert isinstance(data["golden_hive_verified"], bool), f"golden_hive_verified should be bool, got {type(data['golden_hive_verified'])}"
        
    def test_golden_hive_status_requires_auth(self):
        """GET /api/golden-hive/status requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/golden-hive/status")
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"


class TestGoldenHiveCheckout:
    """Test Golden Hive checkout endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for demo user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Could not authenticate demo user")
        
    def test_checkout_creates_session_or_returns_400(self, auth_token):
        """POST /api/golden-hive/checkout creates Stripe checkout session with url and session_id OR returns 400 if already verified/pending"""
        resp = requests.post(f"{BASE_URL}/api/golden-hive/checkout", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        # If user is already verified or pending, should get 400
        if resp.status_code == 400:
            data = resp.json()
            assert "detail" in data
            assert "verified" in data["detail"].lower() or "pending" in data["detail"].lower(), \
                f"Expected error about verified/pending, got: {data['detail']}"
            print(f"User already verified or pending: {data['detail']}")
        else:
            # Otherwise should create checkout session
            assert resp.status_code == 200, f"Expected 200 or 400, got {resp.status_code}: {resp.text}"
            data = resp.json()
            
            # Should have url and session_id
            assert "url" in data, "Missing 'url' in checkout response"
            assert "session_id" in data, "Missing 'session_id' in checkout response"
            
            # URL should be a valid Stripe checkout URL
            assert data["url"].startswith("https://checkout.stripe.com"), \
                f"URL should be Stripe checkout URL, got: {data['url']}"
            
            # session_id should be non-empty
            assert len(data["session_id"]) > 0, "session_id should not be empty"
            print(f"Checkout session created: {data['session_id']}")
            
    def test_checkout_requires_auth(self):
        """POST /api/golden-hive/checkout requires authentication"""
        resp = requests.post(f"{BASE_URL}/api/golden-hive/checkout")
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"


class TestGoldenHiveVerifyPayment:
    """Test Golden Hive verify payment endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for demo user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Could not authenticate demo user")
        
    def test_verify_payment_with_invalid_session(self, auth_token):
        """GET /api/golden-hive/verify-payment returns error for invalid session"""
        resp = requests.get(f"{BASE_URL}/api/golden-hive/verify-payment", params={
            "session_id": "cs_invalid_test_session_id"
        }, headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        # Should return 400 for invalid session
        assert resp.status_code == 400, f"Expected 400 for invalid session, got {resp.status_code}: {resp.text}"
        
    def test_verify_payment_requires_auth(self):
        """GET /api/golden-hive/verify-payment requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/golden-hive/verify-payment", params={
            "session_id": "cs_test_session"
        })
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"


class TestGoldenHiveAdmin:
    """Test Golden Hive admin endpoints"""
    
    @pytest.fixture(scope="class")
    def demo_token(self):
        """Get auth token for demo user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Could not authenticate demo user")
        
    @pytest.fixture(scope="class")
    def is_admin(self, demo_token):
        """Check if demo user is admin"""
        resp = requests.get(f"{BASE_URL}/api/users/me", headers={
            "Authorization": f"Bearer {demo_token}"
        })
        if resp.status_code == 200:
            return resp.json().get("is_admin", False)
        return False
        
    def test_admin_pending_endpoint_exists(self, demo_token, is_admin):
        """GET /api/admin/golden-hive/pending returns list or 403 for non-admin"""
        resp = requests.get(f"{BASE_URL}/api/admin/golden-hive/pending", headers={
            "Authorization": f"Bearer {demo_token}"
        })
        
        if is_admin:
            assert resp.status_code == 200, f"Expected 200 for admin, got {resp.status_code}: {resp.text}"
            data = resp.json()
            
            # Should return a list
            assert isinstance(data, list), f"Expected list, got {type(data)}"
            
            # Each item should have user fields if not empty
            if data:
                assert "id" in data[0], "Pending user should have 'id'"
                assert "username" in data[0] or "email" in data[0], "Pending user should have 'username' or 'email'"
                print(f"Found {len(data)} pending verifications")
        else:
            # Non-admin should get 403
            assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}"
            print("Demo user is not admin, got expected 403")
            
    def test_admin_approve_endpoint_exists(self, demo_token, is_admin):
        """POST /api/admin/golden-hive/{user_id}/approve returns 403 for non-admin or 404 for non-existent user"""
        fake_user_id = "test_fake_user_id_12345"
        resp = requests.post(f"{BASE_URL}/api/admin/golden-hive/{fake_user_id}/approve", headers={
            "Authorization": f"Bearer {demo_token}"
        })
        
        if is_admin:
            # Admin should get 404 for non-existent user or 400 for user not pending
            assert resp.status_code in [404, 400], f"Expected 404/400 for fake user, got {resp.status_code}: {resp.text}"
        else:
            # Non-admin should get 403
            assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}"
            
    def test_admin_reject_endpoint_exists(self, demo_token, is_admin):
        """POST /api/admin/golden-hive/{user_id}/reject returns 403 for non-admin or 404 for non-existent user"""
        fake_user_id = "test_fake_user_id_12345"
        resp = requests.post(f"{BASE_URL}/api/admin/golden-hive/{fake_user_id}/reject", headers={
            "Authorization": f"Bearer {demo_token}"
        })
        
        if is_admin:
            # Admin should get 404 for non-existent user
            assert resp.status_code == 404, f"Expected 404 for fake user, got {resp.status_code}: {resp.text}"
        else:
            # Non-admin should get 403
            assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}"


class TestGoldenHiveInUserData:
    """Test that golden_hive_verified is included in user data across the platform"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for demo user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Could not authenticate demo user")
        
    @pytest.fixture(scope="class")
    def demo_username(self, auth_token):
        """Get demo user's username"""
        resp = requests.get(f"{BASE_URL}/api/users/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        if resp.status_code == 200:
            return resp.json().get("username", "demo")
        return "demo"
        
    def test_user_profile_includes_golden_hive_verified(self, auth_token, demo_username):
        """User profile endpoint includes golden_hive_verified field"""
        resp = requests.get(f"{BASE_URL}/api/users/{demo_username}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        # Should have golden_hive_verified field (may be True, False, or None)
        assert "golden_hive_verified" in data or "golden_hive_status" in data, \
            "User profile should include golden_hive_verified or golden_hive_status"
            
    def test_hive_posts_include_golden_hive_in_user_data(self, auth_token):
        """Hive feed posts include golden_hive_verified in user data"""
        resp = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                post = data[0]
                if "user" in post and post["user"]:
                    # User data in posts should include golden_hive_verified
                    assert "golden_hive_verified" in post["user"], \
                        "Post user data should include golden_hive_verified"
                    print(f"First post user golden_hive_verified: {post['user'].get('golden_hive_verified')}")
            else:
                print("No posts in feed to check")
        else:
            pytest.skip(f"Could not fetch feed: {resp.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
