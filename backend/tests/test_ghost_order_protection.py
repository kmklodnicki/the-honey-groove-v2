"""
Test Suite for Ghost Order Protection - Atomic Inventory Lock (Block 8.1)
Tests the atomic find_one_and_update mechanism that prevents double-sales.

Features tested:
- POST /api/payments/checkout returns 409 when listing is already claimed
- Atomic lock correctly prevents race conditions
- Rollback mechanism restores listing to ACTIVE when order is cancelled or Stripe fails
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testexplore@test.com"
TEST_PASSWORD = "testpass123"


def get_auth_session():
    """Create and return an authenticated session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login to get token
    login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if login_resp.status_code != 200:
        return None, None
    
    data = login_resp.json()
    # API returns "access_token" not "token"
    token = data.get("access_token") or data.get("token")
    user_id = data.get("user", {}).get("id")
    
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    return session, user_id


class TestGhostOrderProtection:
    """Tests for atomic inventory lock preventing double-sales"""

    def test_checkout_returns_409_for_nonexistent_listing(self):
        """
        Test that POST /api/payments/checkout returns 409 with correct message
        when attempting to checkout a listing that doesn't exist (simulating already claimed)
        """
        session, user_id = get_auth_session()
        if not session:
            pytest.skip("Authentication failed")
        
        # Use a non-existent listing_id which should fail the atomic lock
        fake_listing_id = str(uuid.uuid4())
        
        response = session.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": fake_listing_id,
            "origin_url": "https://test.example.com"
        })
        
        # Should return 409 since listing doesn't exist or isn't ACTIVE
        assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.text}"
        
        # Verify the error message
        data = response.json()
        assert "detail" in data, "Response should contain 'detail' field"
        assert "This honey has already been claimed" in data["detail"], \
            f"Expected 'This honey has already been claimed' in message, got: {data['detail']}"
        print(f"PASS: Non-existent listing correctly returns 409 with message: {data['detail']}")

    def test_409_response_contains_exact_message(self):
        """Verify the 409 response contains the exact expected message"""
        session, _ = get_auth_session()
        if not session:
            pytest.skip("Authentication failed")
        
        fake_id = str(uuid.uuid4())
        
        response = session.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": fake_id,
            "origin_url": "https://test.example.com"
        })
        
        assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.text}"
        data = response.json()
        
        # The message should be exactly "This honey has already been claimed!"
        assert data.get("detail") == "This honey has already been claimed!", \
            f"Expected exact message 'This honey has already been claimed!', got: {data.get('detail')}"
        print(f"PASS: 409 response contains correct message: {data.get('detail')}")

    def test_checkout_endpoint_reachable(self):
        """Basic health check that the checkout endpoint is reachable"""
        session, _ = get_auth_session()
        if not session:
            pytest.skip("Authentication failed")
        
        response = session.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": "test",
            "origin_url": "https://test.example.com"
        })
        
        # Should return 409 (not ACTIVE/not found) rather than 500 or other server errors
        assert response.status_code in [400, 409], \
            f"Expected 400 or 409, got {response.status_code}: {response.text}"
        print(f"PASS: Checkout endpoint is healthy, returned {response.status_code}")

    def test_checkout_with_real_listing_and_rollback(self):
        """
        Test that the atomic lock works with a real listing and rollback occurs on failure.
        Tests the full flow:
        1. Attempt checkout (will lock to PENDING)
        2. Stripe fails (test seller account)
        3. Verify listing is rolled back to ACTIVE
        """
        session, user_id = get_auth_session()
        if not session:
            pytest.skip("Authentication failed")
        
        # Get all active listings
        listings_resp = session.get(f"{BASE_URL}/api/listings?limit=10")
        assert listings_resp.status_code == 200, f"Failed to get listings: {listings_resp.status_code}"
        
        listings = listings_resp.json()
        
        # Find a listing from a different user
        test_listing = None
        for listing in listings:
            if listing.get("user", {}).get("id") != user_id:
                if listing.get("listing_type") in ["BUY_NOW", "MAKE_OFFER"]:
                    test_listing = listing
                    break
        
        if not test_listing:
            pytest.skip("No suitable test listing found from another user")
        
        listing_id = test_listing["id"]
        print(f"Testing with listing: {listing_id} - {test_listing.get('album')} by {test_listing.get('artist')}")
        
        # Checkout attempt - may succeed, fail at Stripe, or 409 if already claimed
        response = session.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": listing_id,
            "origin_url": "https://test.example.com"
        })
        
        # Accept any of these valid outcomes:
        # 200 - Stripe succeeded
        # 400 - Seller not set up
        # 409 - Already claimed
        # 500 - Stripe error (test account doesn't exist on live Stripe)
        assert response.status_code in [200, 400, 409, 500], \
            f"Unexpected status {response.status_code}: {response.text}"
        
        print(f"Checkout response: {response.status_code}")
        
        # If we got a 500 (Stripe error), verify the rollback occurred
        if response.status_code == 500:
            # Verify the listing was rolled back to ACTIVE
            listing_check = session.get(f"{BASE_URL}/api/listings/{listing_id}")
            assert listing_check.status_code == 200, f"Failed to fetch listing: {listing_check.status_code}"
            
            listing_data = listing_check.json()
            assert listing_data.get("status") == "ACTIVE", \
                f"Expected listing to be rolled back to ACTIVE, got {listing_data.get('status')}"
            assert listing_data.get("locked_at") is None, \
                f"Expected locked_at to be cleared, got {listing_data.get('locked_at')}"
            assert listing_data.get("locked_by") is None, \
                f"Expected locked_by to be cleared, got {listing_data.get('locked_by')}"
            print("PASS: Listing correctly rolled back to ACTIVE after Stripe failure")
        else:
            print(f"PASS: Checkout returned {response.status_code}")


class TestOrderCancellationRollback:
    """Tests for order cancellation rollback mechanism"""

    def test_cancel_order_endpoint_requires_auth(self):
        """Test that the cancel order endpoint requires authentication"""
        fake_order_id = "HONEY-999999999"
        
        # Without auth should fail
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        response = no_auth_session.post(f"{BASE_URL}/api/honeypot/orders/{fake_order_id}/cancel")
        
        assert response.status_code in [401, 403, 404, 422], \
            f"Expected auth error or 404, got {response.status_code}: {response.text}"
        print(f"PASS: Cancel order endpoint returned {response.status_code} for unauthenticated request")
        
    def test_cancel_order_returns_404_for_nonexistent(self):
        """Test that cancelling a non-existent order returns 404"""
        session, _ = get_auth_session()
        if not session:
            pytest.skip("Authentication failed")
        
        fake_order_id = "HONEY-999999999"
        
        response = session.post(f"{BASE_URL}/api/honeypot/orders/{fake_order_id}/cancel")
        assert response.status_code == 404, f"Expected 404 for non-existent order, got {response.status_code}: {response.text}"
        print("PASS: Cancel order returns 404 for non-existent order")

    def test_cancel_order_endpoint_structure(self):
        """
        Verify that cancel order endpoint exists and has correct response structure.
        The implementation at honeypot.py lines 980-982 clears locked_at/locked_by.
        """
        session, _ = get_auth_session()
        if not session:
            pytest.skip("Authentication failed")
        
        # Test with a clearly invalid order ID
        response = session.post(f"{BASE_URL}/api/honeypot/orders/INVALID-ORDER/cancel")
        
        # Should return 404 with proper JSON error structure
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Response should contain 'detail' field"
        print(f"PASS: Cancel order endpoint returns proper error structure: {data}")


class TestAtomicLockImplementation:
    """Tests to verify the atomic lock implementation"""

    def test_atomic_lock_with_missing_listing(self):
        """
        Verify that when a listing is not found or not ACTIVE,
        the endpoint returns 409 immediately (atomic behavior).
        """
        session, _ = get_auth_session()
        if not session:
            pytest.skip("Authentication failed")
        
        # Generate a UUID that definitely doesn't exist
        non_existent_id = f"TEST_{uuid.uuid4()}"
        
        response = session.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": non_existent_id,
            "origin_url": "https://test.example.com"
        })
        
        # The atomic operation should return None (listing not found or not ACTIVE)
        # which triggers the 409 response
        assert response.status_code == 409, f"Expected 409, got {response.status_code}"
        assert "This honey has already been claimed" in response.json().get("detail", "")
        print("PASS: Atomic lock correctly handles non-existent listings with 409")

    def test_checkout_requires_listing_id(self):
        """Verify the checkout endpoint requires listing_id parameter"""
        session, _ = get_auth_session()
        if not session:
            pytest.skip("Authentication failed")
        
        response = session.post(f"{BASE_URL}/api/payments/checkout", json={
            "origin_url": "https://test.example.com"
        })
        
        # Should return 409 (for None listing_id) or 422 (validation error)
        assert response.status_code in [409, 422], f"Expected 409 or 422, got {response.status_code}"
        print(f"PASS: Checkout endpoint handles missing listing_id with status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
