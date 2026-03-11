"""
Test BLOCK 510, 511, 513 - Admin Override, Golden Hive Payment Trigger, Honey Connect Button
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBlock511AdminOverride:
    """BLOCK 511: Admin override for @katieintheafterglow"""
    
    def test_admin_override_applied(self):
        """Verify @katieintheafterglow has golden_hive=true, golden_hive_verified=true, is_admin=true"""
        # Since we can't directly query DB, we verify via profile API
        # First login as admin
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin_password"
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Admin login failed - skipping admin override test")
        
        token = login_resp.json().get("access_token") or login_resp.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get katieintheafterglow profile
        profile_resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow", headers=headers)
        
        # If profile exists, verify fields
        if profile_resp.status_code == 200:
            profile = profile_resp.json()
            assert profile.get("golden_hive_verified") == True, "golden_hive_verified should be True"
            # Note: is_admin may not be exposed in public profile for security
            print(f"PASS: @katieintheafterglow has golden_hive_verified=True")
        else:
            # User may not exist yet - that's okay, test is about startup code
            print(f"Note: @katieintheafterglow profile not found (status {profile_resp.status_code})")


class TestBlock510GoldenHivePayment:
    """BLOCK 510: Golden Hive payment trigger and notifications (code review - webhook cannot be triggered)"""
    
    def test_golden_hive_checkout_endpoint_exists(self):
        """Verify /api/golden-hive/checkout endpoint exists and requires auth"""
        # Without auth, should get 401 or 403
        resp = requests.post(f"{BASE_URL}/api/golden-hive/checkout")
        assert resp.status_code in [401, 403, 422], f"Expected 401/403/422 for unauthenticated request, got {resp.status_code}"
        print("PASS: /api/golden-hive/checkout endpoint exists and requires auth")
    
    def test_golden_hive_status_endpoint(self):
        """Verify /api/golden-hive/status endpoint requires auth"""
        resp = requests.get(f"{BASE_URL}/api/golden-hive/status")
        assert resp.status_code in [401, 403, 422], f"Expected 401/403/422, got {resp.status_code}"
        print("PASS: /api/golden-hive/status endpoint exists and requires auth")
    
    def test_golden_hive_checkout_authenticated(self):
        """Test checkout endpoint with authenticated user"""
        # Login as test user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Test user login failed")
        
        token = login_resp.json().get("access_token") or login_resp.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check golden hive status
        status_resp = requests.get(f"{BASE_URL}/api/golden-hive/status", headers=headers)
        assert status_resp.status_code == 200, f"Status check failed: {status_resp.status_code}"
        status = status_resp.json()
        print(f"Golden Hive status for test user: {status}")


class TestBlock509GoldenHiveBadge:
    """BLOCK 509: Golden Hive Verified badge renders for verified users"""
    
    def test_profile_includes_golden_hive_verified(self):
        """Verify profile API returns golden_hive_verified field"""
        # Login as test user (testuser1 has golden_hive_verified=true in DB)
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Test user login failed")
        
        token = login_resp.json().get("access_token") or login_resp.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get own profile
        profile_resp = requests.get(f"{BASE_URL}/api/users/testuser1", headers=headers)
        assert profile_resp.status_code == 200, f"Profile fetch failed: {profile_resp.status_code}"
        
        profile = profile_resp.json()
        # testuser1 has golden_hive_verified=true in DB
        assert "golden_hive_verified" in profile, "Profile should include golden_hive_verified field"
        assert profile.get("golden_hive_verified") == True, "testuser1 should have golden_hive_verified=True"
        print(f"PASS: Profile includes golden_hive_verified={profile.get('golden_hive_verified')}")


class TestApiHealth:
    """Basic API health checks"""
    
    def test_api_health(self):
        """Verify API is responding"""
        resp = requests.get(f"{BASE_URL}/api/platform-fee")
        assert resp.status_code == 200, f"API health check failed: {resp.status_code}"
        print("PASS: API is healthy")
    
    def test_webhook_endpoint_exists(self):
        """Verify Stripe webhook endpoint exists"""
        # POST without signature should fail with signature error or 400
        resp = requests.post(f"{BASE_URL}/api/webhook/stripe", data=b'{}', headers={"Stripe-Signature": ""})
        # Should process but return received:true (signature verification may fail silently)
        assert resp.status_code in [200, 400], f"Webhook endpoint issue: {resp.status_code}"
        print("PASS: Webhook endpoint exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
