"""
Test suite for HoneyGroove Landing Page, Payments, Admin Disputes, and Notifications
Tests the new features: Landing page redesign, Stripe payment execution, Admin dispute dashboard, and Browser push notifications
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "password123"

@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def demo_token(api_client):
    """Login as demo (admin) user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]

@pytest.fixture(scope="module")
def demo_user(api_client):
    """Get demo user data"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD
    })
    assert response.status_code == 200
    return response.json()["user"]


# ============== NOTIFICATION API TESTS ==============
class TestNotificationsAPI:
    """Tests for /api/notifications endpoints"""

    def test_get_notifications(self, api_client, demo_token):
        """GET /api/notifications returns user notifications"""
        response = api_client.get(
            f"{BASE_URL}/api/notifications",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200, f"Get notifications failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Notifications should be a list"
        print(f"GET /api/notifications - returned {len(data)} notifications - PASSED")

    def test_get_notifications_requires_auth(self, api_client):
        """GET /api/notifications requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 401, "Should require auth"
        print("GET /api/notifications requires auth - PASSED")

    def test_get_unread_count(self, api_client, demo_token):
        """GET /api/notifications/unread-count returns count"""
        response = api_client.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200, f"Get unread count failed: {response.text}"
        data = response.json()
        assert "count" in data, "Response should have count field"
        assert isinstance(data["count"], int), "Count should be an integer"
        print(f"GET /api/notifications/unread-count - count: {data['count']} - PASSED")


# ============== PAYMENT API TESTS ==============
class TestPaymentsAPI:
    """Tests for /api/payments endpoints"""

    def test_checkout_requires_auth(self, api_client):
        """POST /api/payments/checkout requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": "test",
            "origin_url": "https://example.com"
        })
        assert response.status_code == 401, "Should require auth"
        print("POST /api/payments/checkout requires auth - PASSED")

    def test_checkout_invalid_listing(self, api_client, demo_token):
        """POST /api/payments/checkout returns 404 for invalid listing"""
        response = api_client.post(
            f"{BASE_URL}/api/payments/checkout",
            headers={"Authorization": f"Bearer {demo_token}"},
            json={"listing_id": "invalid-listing-id", "origin_url": "https://example.com"}
        )
        # Should return 404 for invalid listing
        assert response.status_code == 404, f"Expected 404 for invalid listing, got {response.status_code}"
        print("POST /api/payments/checkout - 404 for invalid listing - PASSED")

    def test_payment_status_invalid_session(self, api_client, demo_token):
        """GET /api/payments/status/{session_id} returns 404 for invalid session"""
        response = api_client.get(
            f"{BASE_URL}/api/payments/status/invalid_session_123",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 404, f"Expected 404 for invalid session, got {response.status_code}"
        print("GET /api/payments/status/{session_id} - 404 for invalid session - PASSED")


# ============== ADMIN DISPUTES API TESTS ==============
class TestAdminDisputesAPI:
    """Tests for /api/admin/disputes endpoints (admin only)"""

    def test_get_disputes_as_admin(self, api_client, demo_token):
        """GET /api/admin/disputes returns disputes for admin user"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/disputes",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        # demo user should be admin
        assert response.status_code == 200, f"Get disputes failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Disputes should be a list"
        print(f"GET /api/admin/disputes - returned {len(data)} open disputes - PASSED")

    def test_get_all_disputes_as_admin(self, api_client, demo_token):
        """GET /api/admin/disputes/all returns all disputes for admin"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/disputes/all",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200, f"Get all disputes failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "All disputes should be a list"
        print(f"GET /api/admin/disputes/all - returned {len(data)} total disputes - PASSED")

    def test_get_disputes_requires_auth(self, api_client):
        """GET /api/admin/disputes requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/admin/disputes")
        assert response.status_code == 401, "Should require auth"
        print("GET /api/admin/disputes requires auth - PASSED")


# ============== EXISTING LISTING API FOR PAYMENT FLOW ==============
class TestListingsForPaymentFlow:
    """Verify listing endpoints work for payment flow"""

    def test_get_all_listings(self, api_client):
        """GET /api/listings returns marketplace listings"""
        response = api_client.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200, f"Get listings failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Listings should be a list"
        print(f"GET /api/listings - returned {len(data)} listings - PASSED")
        
        # Check for BUY_NOW listings which can be used for payment flow
        buy_now = [l for l in data if l.get("listing_type") == "BUY_NOW"]
        make_offer = [l for l in data if l.get("listing_type") == "MAKE_OFFER"]
        trade = [l for l in data if l.get("listing_type") == "TRADE"]
        print(f"  - BUY_NOW: {len(buy_now)}, MAKE_OFFER: {len(make_offer)}, TRADE: {len(trade)}")

    def test_get_iso_matches(self, api_client, demo_token):
        """GET /api/listings/iso-matches returns ISO matches"""
        response = api_client.get(
            f"{BASE_URL}/api/listings/iso-matches",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200, f"Get ISO matches failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "ISO matches should be a list"
        print(f"GET /api/listings/iso-matches - returned {len(data)} matches - PASSED")


# ============== CHECKOUT FLOW VALIDATION ==============
class TestCheckoutFlowValidation:
    """Test the validation logic in the checkout flow"""
    
    def test_cannot_buy_own_listing(self, api_client, demo_token, demo_user):
        """User cannot buy their own listing"""
        # First get listings to find one owned by demo user
        response = api_client.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200
        listings = response.json()
        
        # Find a listing owned by demo user
        own_listing = None
        for l in listings:
            if l.get("user_id") == demo_user["id"] or (l.get("user") and l["user"].get("id") == demo_user["id"]):
                own_listing = l
                break
        
        if own_listing:
            # Try to buy own listing - should fail
            response = api_client.post(
                f"{BASE_URL}/api/payments/checkout",
                headers={"Authorization": f"Bearer {demo_token}"},
                json={"listing_id": own_listing["id"], "origin_url": "https://example.com"}
            )
            assert response.status_code == 400, f"Should not allow buying own listing, got {response.status_code}"
            print("POST /api/payments/checkout - cannot buy own listing (400) - PASSED")
        else:
            print("POST /api/payments/checkout - no own listing found to test - SKIPPED")


# ============== STRIPE STATUS ENDPOINT ==============
class TestStripeStatus:
    """Test Stripe Connect status endpoint"""
    
    def test_stripe_status(self, api_client, demo_token):
        """GET /api/stripe/status returns Stripe connection status"""
        response = api_client.get(
            f"{BASE_URL}/api/stripe/status",
            headers={"Authorization": f"Bearer {demo_token}"}
        )
        assert response.status_code == 200, f"Get Stripe status failed: {response.text}"
        data = response.json()
        assert "stripe_connected" in data, "Should have stripe_connected field"
        print(f"GET /api/stripe/status - connected: {data.get('stripe_connected')} - PASSED")


# ============== LANDING PAGE ENDPOINTS ==============
class TestLandingPageAPIs:
    """Test APIs that landing page relies on"""
    
    def test_explore_feed_public(self, api_client):
        """GET /api/explore is accessible without auth (for landing page)"""
        response = api_client.get(f"{BASE_URL}/api/explore")
        assert response.status_code == 200, f"Explore feed failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Explore feed should be a list"
        print(f"GET /api/explore (public) - returned {len(data)} posts - PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
