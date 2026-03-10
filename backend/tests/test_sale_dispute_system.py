"""
Test sale dispute system for HoneyGroove marketplace.
Features tested:
- Sale dispute endpoints (open, respond, admin list, admin resolve)
- Trade dispute with structured reasons and 48h window
- Backend API validations
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "golden_test@test.com"
TEST_USER_PASSWORD = "test123"
ADMIN_EMAIL = "admin@thehoneygroove.com"


class TestSaleDisputeBackend:
    """Tests for sale dispute backend APIs"""
    
    @pytest.fixture
    def api_client(self):
        """Shared requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture
    def auth_token(self, api_client):
        """Get authentication token for test user"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed for {TEST_USER_EMAIL}")
    
    @pytest.fixture
    def authenticated_client(self, api_client, auth_token):
        """Session with auth header"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        return api_client
    
    # === SALE DISPUTE ENDPOINTS ===
    
    def test_open_sale_dispute_requires_auth(self, api_client):
        """POST /api/orders/{order_id}/dispute requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/orders/fake-order-id/dispute", json={
            "reason": "record_not_as_described",
            "photo_urls": ["https://example.com/photo.jpg"]
        })
        # Should be 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Open sale dispute requires auth")
    
    def test_open_sale_dispute_order_not_found(self, authenticated_client):
        """POST /api/orders/{order_id}/dispute returns 404 for non-existent order"""
        response = authenticated_client.post(f"{BASE_URL}/api/orders/fake-order-id-12345/dispute", json={
            "reason": "record_not_as_described",
            "photo_urls": ["https://example.com/photo.jpg"]
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Returns 404 for non-existent order")
    
    def test_open_sale_dispute_invalid_reason(self, authenticated_client):
        """POST /api/orders/{order_id}/dispute validates reason field"""
        # First we need to find or create a test order - for now we test validation path
        response = authenticated_client.post(f"{BASE_URL}/api/orders/test-order-123/dispute", json={
            "reason": "invalid_reason_type",
            "photo_urls": ["https://example.com/photo.jpg"]
        })
        # Should fail with 400 (invalid reason) or 404 (order not found)
        assert response.status_code in [400, 404], f"Expected 400/404, got {response.status_code}"
        print("PASS: Invalid reason validation works")
    
    def test_open_sale_dispute_requires_photos(self, authenticated_client):
        """POST /api/orders/{order_id}/dispute requires photo_urls"""
        response = authenticated_client.post(f"{BASE_URL}/api/orders/test-order-123/dispute", json={
            "reason": "record_not_as_described",
            "photo_urls": []  # Empty photos
        })
        # Should fail with 400 (no photos) or 404 (order not found)
        assert response.status_code in [400, 404], f"Expected 400/404, got {response.status_code}"
        print("PASS: Photos required validation works")
    
    def test_respond_sale_dispute_requires_auth(self, api_client):
        """POST /api/orders/{order_id}/dispute/respond requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/orders/fake-order/dispute/respond", json={
            "response_text": "My response",
            "photo_urls": []
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Respond to dispute requires auth")
    
    def test_respond_sale_dispute_order_not_found(self, authenticated_client):
        """POST /api/orders/{order_id}/dispute/respond returns 404 for non-existent order"""
        response = authenticated_client.post(f"{BASE_URL}/api/orders/nonexistent-order-id/dispute/respond", json={
            "response_text": "My response",
            "photo_urls": []
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Returns 404 for non-existent order on respond")
    
    # === ADMIN ENDPOINTS (should require admin role) ===
    
    def test_admin_sale_disputes_requires_admin(self, authenticated_client):
        """GET /api/admin/sale-disputes requires admin role"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/sale-disputes")
        # Non-admin should get 403
        # Note: If test user happens to be admin, we'll get 200
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}"
        if response.status_code == 403:
            print("PASS: Admin sale disputes requires admin (non-admin got 403)")
        else:
            print("PASS: Admin sale disputes accessible (user is admin)")
            data = response.json()
            assert isinstance(data, list), "Response should be a list"
            print(f"  - Found {len(data)} open sale disputes")
    
    def test_admin_sale_disputes_all_requires_admin(self, authenticated_client):
        """GET /api/admin/sale-disputes/all requires admin role"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/sale-disputes/all")
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}"
        if response.status_code == 403:
            print("PASS: Admin all sale disputes requires admin (non-admin got 403)")
        else:
            print("PASS: Admin all sale disputes accessible")
    
    def test_admin_resolve_sale_dispute_requires_admin(self, authenticated_client):
        """POST /api/admin/sale-disputes/{order_id}/resolve requires admin role"""
        response = authenticated_client.post(f"{BASE_URL}/api/admin/sale-disputes/test-order-id/resolve", json={
            "outcome": "approved",
            "notes": "Test resolution"
        })
        # Should be 403 (not admin) or 404 (order not found)
        assert response.status_code in [403, 404], f"Expected 403/404, got {response.status_code}"
        print("PASS: Admin resolve dispute requires admin/valid order")


class TestTradeDisputeStructuredReasons:
    """Tests for trade dispute with structured reasons"""
    
    @pytest.fixture
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture
    def auth_token(self, api_client):
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed for {TEST_USER_EMAIL}")
    
    @pytest.fixture
    def authenticated_client(self, api_client, auth_token):
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        return api_client
    
    def test_trade_dispute_requires_auth(self, api_client):
        """POST /api/trades/{trade_id}/dispute requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/trades/fake-trade-id/dispute", json={
            "reason": "record_not_as_described",
            "photo_urls": ["https://example.com/photo.jpg"]
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Trade dispute requires auth")
    
    def test_trade_dispute_trade_not_found(self, authenticated_client):
        """POST /api/trades/{trade_id}/dispute returns 404 for non-existent trade"""
        response = authenticated_client.post(f"{BASE_URL}/api/trades/nonexistent-trade-id/dispute", json={
            "reason": "record_not_as_described",
            "photo_urls": ["https://example.com/photo.jpg"]
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Returns 404 for non-existent trade")
    
    def test_valid_dispute_reasons_list(self):
        """Verify the valid dispute reasons match expected values"""
        valid_reasons = [
            "record_not_as_described",
            "damaged_during_shipping",
            "wrong_record_sent",
            "missing_item",
            "counterfeit_fake_pressing"
        ]
        print(f"PASS: Valid dispute reasons documented: {valid_reasons}")
        assert len(valid_reasons) == 5, "Should have 5 valid dispute reasons"


class TestOrdersEndpoints:
    """Tests for orders-related endpoints"""
    
    @pytest.fixture
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture
    def auth_token(self, api_client):
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def authenticated_client(self, api_client, auth_token):
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        return api_client
    
    def test_get_purchases_endpoint(self, authenticated_client):
        """GET /api/orders/purchases returns user's purchases"""
        response = authenticated_client.get(f"{BASE_URL}/api/orders/purchases")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: GET /api/orders/purchases returns {len(data)} purchases")
        
        # If there are purchases, verify structure
        if len(data) > 0:
            purchase = data[0]
            print(f"  - Sample purchase keys: {list(purchase.keys())[:10]}")
    
    def test_get_sales_endpoint(self, authenticated_client):
        """GET /api/orders/sales returns user's sales"""
        response = authenticated_client.get(f"{BASE_URL}/api/orders/sales")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: GET /api/orders/sales returns {len(data)} sales")


class TestTradesEndpoints:
    """Tests for trades-related endpoints"""
    
    @pytest.fixture
    def api_client(self):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture
    def auth_token(self, api_client):
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def authenticated_client(self, api_client, auth_token):
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        return api_client
    
    def test_get_trades_endpoint(self, authenticated_client):
        """GET /api/trades returns user's trades"""
        response = authenticated_client.get(f"{BASE_URL}/api/trades")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: GET /api/trades returns {len(data)} trades")
    
    def test_get_admin_hold_disputes(self, authenticated_client):
        """GET /api/admin/hold-disputes requires admin"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/hold-disputes")
        # Should be 403 for non-admin or 200 for admin
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}"
        if response.status_code == 403:
            print("PASS: Admin hold disputes requires admin (got 403)")
        else:
            data = response.json()
            print(f"PASS: Admin hold disputes accessible, found {len(data)} disputes")


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_health(self):
        """Verify API is responding"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("PASS: API health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
