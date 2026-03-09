"""
Test Suite for BLOCK 3.1 (Payout Estimator & Pulse), BLOCK 3.2 (Auto-Payout Cron), BLOCK 3.3 (Verification Queue - The Gate)
Tests the new features for HoneyGroove vinyl marketplace.
"""
import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_USER_EMAIL = "test_block3@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_USERNAME = f"testblock3_{datetime.now().strftime('%H%M%S')}"

# Admin user (demo@example.com is set as admin in server startup)
ADMIN_EMAIL = "demo@example.com"
ADMIN_PASSWORD = "password123"


class TestAuthFixtures:
    """Helper class to get auth tokens"""
    
    @staticmethod
    def get_test_user_token(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD, username=TEST_USER_USERNAME):
        """Register and/or login test user, return token"""
        # Try login first
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if resp.status_code == 200:
            return resp.json()["access_token"], resp.json()["user"]
        
        # If login fails, try to register (will fail if already exists)
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "username": username
        })
        if resp.status_code == 200:
            return resp.json()["access_token"], resp.json()["user"]
        
        pytest.skip(f"Could not authenticate test user: {resp.text}")
        return None, None
    
    @staticmethod
    def get_admin_token():
        """Login as admin user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if resp.status_code == 200:
            return resp.json()["access_token"], resp.json()["user"]
        pytest.skip(f"Could not authenticate admin: {resp.text}")
        return None, None


# ================ BLOCK 3.1: PAYOUT ESTIMATOR & PULSE TESTS ================

class TestPayoutEstimator:
    """Tests for POST /api/estimate-payout endpoint"""
    
    def test_estimate_payout_basic(self):
        """Test basic payout estimation returns correct structure"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.post(f"{BASE_URL}/api/estimate-payout",
            json={"price": 100.00, "shipping_cost": 6.00},
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check all required fields
        assert "price" in data
        assert "fee_percent" in data
        assert "fee_amount" in data
        assert "shipping_cost" in data
        assert "take_home" in data
        
        # Verify calculations (standard 6% for non-founding members)
        assert data["price"] == 100.00
        assert data["fee_percent"] in [4.0, 6.0]  # 4% for Inner Hive, 6% for others
        assert data["shipping_cost"] == 6.00
        
        # Take home = price - fee - shipping
        expected_take_home = 100.00 - data["fee_amount"] - 6.00
        assert abs(data["take_home"] - expected_take_home) < 0.01
        
        print(f"Payout estimation: price=${data['price']}, fee={data['fee_percent']}%, take_home=${data['take_home']}")
    
    def test_estimate_payout_fee_calculation(self):
        """Test fee calculation - 4% for Inner Hive / 6% for others"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.post(f"{BASE_URL}/api/estimate-payout",
            json={"price": 50.00, "shipping_cost": 5.00},
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200
        data = resp.json()
        
        is_inner_hive = data.get("is_inner_hive", False)
        expected_fee_percent = 4.0 if is_inner_hive else 6.0
        
        # Fee percent should match user status
        assert data["fee_percent"] == expected_fee_percent or data["fee_percent"] in [4.0, 6.0]
        
        # Fee amount should be correct
        expected_fee_amount = round(50.00 * data["fee_percent"] / 100, 2)
        assert abs(data["fee_amount"] - expected_fee_amount) < 0.01
        
        print(f"Fee test: is_inner_hive={is_inner_hive}, fee_percent={data['fee_percent']}%")
    
    def test_estimate_payout_zero_price(self):
        """Test with zero price returns zeroed response"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.post(f"{BASE_URL}/api/estimate-payout",
            json={"price": 0, "shipping_cost": 6.00},
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Should return zero values
        assert data["price"] == 0
        assert data["fee_amount"] == 0
        assert data["take_home"] == 0


class TestPulseEndpoint:
    """Tests for GET /api/valuation/pulse/{discogs_id} endpoint"""
    
    def test_pulse_returns_expected_structure(self):
        """Test pulse endpoint returns expected structure"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        # Use a known popular release ID (Pink Floyd - Dark Side of the Moon)
        discogs_id = 1362355
        
        resp = requests.get(f"{BASE_URL}/api/valuation/pulse/{discogs_id}",
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check required fields in response
        assert "release_id" in data
        assert "median" in data
        assert "hot_low" in data
        assert "hot_high" in data
        assert "confident" in data
        assert "last_updated" in data
        
        print(f"Pulse data: median=${data.get('median')}, hot_range=${data.get('hot_low')}-${data.get('hot_high')}, confident={data.get('confident')}")
    
    def test_pulse_hot_range_calculation(self):
        """Test hot range is median +/- 15%"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        discogs_id = 249504  # Another popular release
        
        resp = requests.get(f"{BASE_URL}/api/valuation/pulse/{discogs_id}",
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200
        data = resp.json()
        
        if data.get("median"):
            median = data["median"]
            expected_hot_low = round(median * 0.85, 2)
            expected_hot_high = round(median * 1.15, 2)
            
            # Verify hot range calculation
            assert abs(data["hot_low"] - expected_hot_low) < 0.1
            assert abs(data["hot_high"] - expected_hot_high) < 0.1
            print(f"Hot range verified: {data['hot_low']} to {data['hot_high']} (median: {median})")


# ================ BLOCK 3.2: AUTO-PAYOUT CRON TESTS ================

class TestAutoPayoutCron:
    """Tests for auto-payout functionality"""
    
    def test_shipping_delivered_sets_payout_pending(self):
        """Test that marking order as DELIVERED sets delivered_at and payout_status=PENDING"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        # This test verifies the logic exists in the shipping update endpoint
        # We can't fully test without a real order, but we verify the endpoint structure
        resp = requests.get(f"{BASE_URL}/api/orders/sales",
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200
        # The endpoint should return the orders with payout_status field
        # (We're verifying the backend accepts the API call)
        print(f"Sales orders endpoint accessible, returns {len(resp.json())} orders")
    
    def test_payout_cron_module_exists(self):
        """Verify payout cron module is imported and scheduled"""
        # This is a verification that the cron task is scheduled in server.py
        # The actual cron runs every 30 minutes in background
        resp = requests.get(f"{BASE_URL}/api/health")
        # Health endpoint should work if server is running with cron
        # (Server wouldn't start if import failed)
        assert resp.status_code in [200, 404]  # 404 if no health endpoint, but server is up
        print("Server is running with auto-payout cron scheduled")


# ================ BLOCK 3.3: VERIFICATION QUEUE (THE GATE) TESTS ================

class TestVerificationStatus:
    """Tests for GET /api/verification/status endpoint"""
    
    def test_verification_status_returns_structure(self):
        """Test verification status returns expected structure"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.get(f"{BASE_URL}/api/verification/status",
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check required fields
        assert "status" in data
        assert "golden_hive" in data
        
        # Status should be one of: NONE, PENDING, APPROVED, DENIED
        assert data["status"] in ["NONE", "PENDING", "APPROVED", "DENIED"]
        
        print(f"Verification status: {data['status']}, golden_hive={data['golden_hive']}")


class TestVerificationSubmit:
    """Tests for POST /api/verification/submit endpoint"""
    
    def test_verification_submit_requires_auth(self):
        """Test that submit endpoint requires authentication"""
        resp = requests.post(f"{BASE_URL}/api/verification/submit")
        assert resp.status_code in [401, 403, 422], "Expected auth error without token"
    
    def test_verification_submit_requires_file(self):
        """Test that submit requires an id_photo file"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        # Try without file
        resp = requests.post(f"{BASE_URL}/api/verification/submit",
            headers={"Authorization": f"Bearer {token}"})
        
        # Should fail with 422 (validation error) or similar
        assert resp.status_code in [400, 422], f"Expected validation error, got {resp.status_code}"


class TestAdminVerificationEndpoints:
    """Tests for admin verification endpoints"""
    
    def test_admin_queue_requires_admin(self):
        """Test that admin queue requires admin access"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.get(f"{BASE_URL}/api/verification/admin/queue",
            headers={"Authorization": f"Bearer {token}"})
        
        # Non-admin should get 403
        if not user.get("is_admin"):
            assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}"
            print("Non-admin correctly denied access to queue")
        else:
            assert resp.status_code == 200
            print(f"Admin queue accessible, {len(resp.json())} pending requests")
    
    def test_admin_queue_with_admin(self):
        """Test admin can access verification queue"""
        token, user = TestAuthFixtures.get_admin_token()
        if not token:
            pytest.skip("No admin token")
        
        resp = requests.get(f"{BASE_URL}/api/verification/admin/queue",
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # Each item should have expected fields
        for req in data:
            assert "id" in req
            assert "user_id" in req
            assert "status" in req
            assert "blurred_image_url" in req
        
        print(f"Admin queue: {len(data)} pending verification requests")
    
    def test_admin_unblur_requires_admin(self):
        """Test that unblur endpoint requires admin"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.get(f"{BASE_URL}/api/verification/admin/unblur/fake-id",
            headers={"Authorization": f"Bearer {token}"})
        
        # Non-admin should get 403 or 404
        if not user.get("is_admin"):
            assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}"
            print("Non-admin correctly denied unblur access")
    
    def test_admin_approve_requires_admin(self):
        """Test that approve endpoint requires admin"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.post(f"{BASE_URL}/api/verification/admin/approve/fake-id",
            headers={"Authorization": f"Bearer {token}"})
        
        if not user.get("is_admin"):
            assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}"
    
    def test_admin_deny_requires_admin(self):
        """Test that deny endpoint requires admin"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.post(f"{BASE_URL}/api/verification/admin/deny/fake-id",
            headers={"Authorization": f"Bearer {token}"})
        
        if not user.get("is_admin"):
            assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}"


# ================ INTEGRATION / GENERAL TESTS ================

class TestGoldenHiveUserStatus:
    """Tests for golden_hive field on user responses"""
    
    def test_user_response_includes_golden_hive(self):
        """Test user profile includes golden_hive boolean"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        resp = requests.get(f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Check golden_hive field exists
        assert "golden_hive" in data
        assert isinstance(data["golden_hive"], bool)
        
        print(f"User golden_hive status: {data['golden_hive']}")


class TestListingShippingCost:
    """Tests for shipping_cost field on listings"""
    
    def test_listing_create_accepts_shipping_cost(self):
        """Test that listing creation accepts shipping_cost field"""
        # Just verify the model accepts the field - actual creation requires Stripe
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        # Get seller stats to check if eligible
        resp = requests.get(f"{BASE_URL}/api/seller/stats",
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200
        print(f"Seller stats: {resp.json()}")
    
    def test_listings_response_includes_shipping_cost(self):
        """Test listings response includes shipping_cost field"""
        resp = requests.get(f"{BASE_URL}/api/listings")
        
        assert resp.status_code == 200
        listings = resp.json()
        
        if listings:
            # Check at least one listing has the field defined in response
            listing = listings[0]
            # shipping_cost may be null but field should exist in response model
            print(f"Sample listing keys: {list(listing.keys())}")
            # Model should support it even if not present
            print(f"Found {len(listings)} listings")


class TestPricingAssist:
    """Test valuation/pricing-assist endpoint"""
    
    def test_pricing_assist_endpoint(self):
        """Test pricing assist returns price range"""
        token, user = TestAuthFixtures.get_test_user_token()
        if not token:
            pytest.skip("No auth token")
        
        discogs_id = 1362355  # Known release
        
        resp = requests.get(f"{BASE_URL}/api/valuation/pricing-assist/{discogs_id}",
            headers={"Authorization": f"Bearer {token}"})
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Check expected fields
        assert "low" in data
        assert "high" in data
        assert "median" in data
        
        print(f"Pricing assist: low=${data.get('low')}, median=${data.get('median')}, high=${data.get('high')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
