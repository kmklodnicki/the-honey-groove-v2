"""
BLOCK 434/627: Stripe Express Checkout Integration Tests
Tests for PaymentIntent creation, status polling with pi_/cs_ handling, and webhook events.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestExpressCheckoutBackend:
    """Tests for Express Checkout PaymentIntent flow."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as test user
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Could not authenticate test user")
    
    # --- PaymentIntent Creation Tests ---
    
    def test_create_intent_endpoint_exists(self):
        """POST /api/payments/create-intent exists and requires auth."""
        # Test without auth
        resp = requests.post(f"{BASE_URL}/api/payments/create-intent", json={})
        assert resp.status_code in [401, 403], "Should require authentication"
    
    def test_create_intent_requires_listing_id(self):
        """POST /api/payments/create-intent requires listing_id."""
        resp = self.session.post(f"{BASE_URL}/api/payments/create-intent", json={})
        # Should fail with 400/409/404 because listing_id is missing or not found
        assert resp.status_code in [400, 404, 409, 422], f"Expected 400/404/409, got {resp.status_code}"
    
    def test_create_intent_invalid_listing(self):
        """POST /api/payments/create-intent with invalid listing returns error."""
        resp = self.session.post(f"{BASE_URL}/api/payments/create-intent", json={
            "listing_id": "non-existent-listing-id"
        })
        # Should return 404 or 409 for non-existent/already-claimed listing
        assert resp.status_code in [404, 409], f"Expected 404/409, got {resp.status_code}"
    
    # --- Payment Status Tests ---
    
    def test_payment_status_endpoint_exists(self):
        """GET /api/payments/status/{session_id} exists."""
        # Test with a fake pi_ ID (will return 404 since no transaction)
        resp = self.session.get(f"{BASE_URL}/api/payments/status/pi_fake_test_intent")
        # Should return 404 for unknown session
        assert resp.status_code == 404, f"Expected 404 for unknown pi_, got {resp.status_code}"
    
    def test_payment_status_handles_pi_prefix(self):
        """GET /api/payments/status handles PaymentIntent IDs (pi_*)."""
        resp = self.session.get(f"{BASE_URL}/api/payments/status/pi_test_unknown_intent")
        # Should return 404 since this PI doesn't exist in our DB
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
    
    def test_payment_status_handles_cs_prefix(self):
        """GET /api/payments/status handles Checkout Session IDs (cs_*)."""
        resp = self.session.get(f"{BASE_URL}/api/payments/status/cs_test_unknown_session")
        # Should return 404 since this session doesn't exist in our DB
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
    
    def test_payment_status_requires_auth(self):
        """GET /api/payments/status/{id} requires authentication."""
        resp = requests.get(f"{BASE_URL}/api/payments/status/pi_test")
        assert resp.status_code in [401, 403], "Should require authentication"
    
    # --- Webhook Tests ---
    
    def test_webhook_endpoint_exists(self):
        """POST /api/webhook/stripe exists."""
        # Webhook endpoint should exist and accept POST
        # Without valid signature, it should still return 200 (received: true) or signature error
        resp = requests.post(f"{BASE_URL}/api/webhook/stripe", json={
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test"}}
        })
        # Even without valid signature, endpoint should exist (returns {"received": true} or error)
        assert resp.status_code in [200, 400], f"Webhook endpoint should exist, got {resp.status_code}"
    
    def test_webhook_handles_payment_intent_succeeded(self):
        """Webhook handles payment_intent.succeeded event type (at endpoint level)."""
        # Without valid Stripe signature, just verify the endpoint accepts the event type
        # The actual signature validation will reject it, but endpoint structure is tested
        resp = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            json={
                "type": "payment_intent.succeeded",
                "data": {"object": {"id": "pi_test_fake"}}
            },
            headers={"Content-Type": "application/json"}
        )
        # Returns 200 with {"received": true} even for invalid signature in our implementation
        assert resp.status_code == 200
        assert resp.json().get("received") == True
    
    def test_webhook_handles_checkout_session_completed(self):
        """Webhook handles checkout.session.completed event type (legacy flow)."""
        resp = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            json={
                "type": "checkout.session.completed",
                "data": {"object": {"id": "cs_test_fake", "payment_status": "paid"}}
            },
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 200
        assert resp.json().get("received") == True


class TestLegacyCheckoutEndpoint:
    """Tests for legacy checkout (redirect flow) alongside express checkout."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Could not authenticate test user")
    
    def test_checkout_endpoint_exists(self):
        """POST /api/payments/checkout exists (legacy redirect flow)."""
        resp = requests.post(f"{BASE_URL}/api/payments/checkout", json={})
        assert resp.status_code in [401, 403], "Should require authentication"
    
    def test_checkout_requires_listing_id(self):
        """POST /api/payments/checkout requires listing_id."""
        resp = self.session.post(f"{BASE_URL}/api/payments/checkout", json={})
        assert resp.status_code in [400, 404, 409, 422]


class TestPlatformFee:
    """Tests for platform fee endpoint (used by checkout)."""
    
    def test_platform_fee_endpoint(self):
        """GET /api/platform-fee returns fee percentage."""
        resp = requests.get(f"{BASE_URL}/api/platform-fee")
        assert resp.status_code == 200
        data = resp.json()
        assert "platform_fee_percent" in data
        assert isinstance(data["platform_fee_percent"], (int, float))
        assert data["platform_fee_percent"] >= 0


class TestStripeConnectStatus:
    """Tests for Stripe Connect status (required for sellers)."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Could not authenticate test user")
    
    def test_stripe_status_endpoint(self):
        """GET /api/stripe/status returns connect status."""
        resp = self.session.get(f"{BASE_URL}/api/stripe/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "stripe_connected" in data
        assert isinstance(data["stripe_connected"], bool)
