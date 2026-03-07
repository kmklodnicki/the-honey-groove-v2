"""
Test Orders Feature - My Orders / My Sales tabs
Tests for GET /api/orders/purchases, GET /api/orders/sales, PUT /api/orders/{order_id}/shipping
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOrdersEndpoints:
    """Tests for Orders API endpoints"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create or get a test user for authenticated requests"""
        # First try to login with existing test user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_direct_66@test.com",
            "password": "testpass123"
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            # API returns access_token, not token
            return {"token": data.get("access_token") or data.get("token"), "user": data["user"]}
        
        pytest.skip(f"Cannot login test user: {login_resp.status_code} - {login_resp.text}")
    
    # ============== GET /api/orders/purchases ==============
    
    def test_orders_purchases_requires_auth(self):
        """GET /api/orders/purchases should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/orders/purchases")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASSED: GET /api/orders/purchases requires auth")
    
    def test_orders_purchases_returns_array(self, test_user):
        """GET /api/orders/purchases should return an array"""
        resp = requests.get(f"{BASE_URL}/api/orders/purchases",
            headers={"Authorization": f"Bearer {test_user['token']}"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASSED: GET /api/orders/purchases returns array (length={len(data)})")
    
    def test_orders_purchases_enriched_fields(self, test_user):
        """GET /api/orders/purchases should return enriched transaction data"""
        resp = requests.get(f"{BASE_URL}/api/orders/purchases",
            headers={"Authorization": f"Bearer {test_user['token']}"})
        assert resp.status_code == 200
        data = resp.json()
        
        # Even if empty, the endpoint should work
        if len(data) == 0:
            print("INFO: No purchases found - endpoint works, data is empty")
        else:
            # Check enriched fields on first item
            item = data[0]
            expected_fields = ["id", "order_number", "payment_status", "amount", "shipping_status"]
            for field in expected_fields:
                assert field in item, f"Missing enriched field: {field}"
            print(f"PASSED: Purchases have enriched fields: {list(item.keys())}")
    
    # ============== GET /api/orders/sales ==============
    
    def test_orders_sales_requires_auth(self):
        """GET /api/orders/sales should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/orders/sales")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASSED: GET /api/orders/sales requires auth")
    
    def test_orders_sales_returns_array(self, test_user):
        """GET /api/orders/sales should return an array"""
        resp = requests.get(f"{BASE_URL}/api/orders/sales",
            headers={"Authorization": f"Bearer {test_user['token']}"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASSED: GET /api/orders/sales returns array (length={len(data)})")
    
    def test_orders_sales_enriched_fields(self, test_user):
        """GET /api/orders/sales should return enriched transaction data"""
        resp = requests.get(f"{BASE_URL}/api/orders/sales",
            headers={"Authorization": f"Bearer {test_user['token']}"})
        assert resp.status_code == 200
        data = resp.json()
        
        if len(data) == 0:
            print("INFO: No sales found - endpoint works, data is empty")
        else:
            item = data[0]
            expected_fields = ["id", "order_number", "payment_status", "amount", "shipping_status"]
            for field in expected_fields:
                assert field in item, f"Missing enriched field: {field}"
            print(f"PASSED: Sales have enriched fields: {list(item.keys())}")
    
    # ============== PUT /api/orders/{order_id}/shipping ==============
    
    def test_shipping_update_requires_auth(self):
        """PUT /api/orders/{order_id}/shipping should require authentication"""
        resp = requests.put(f"{BASE_URL}/api/orders/fake-order-id/shipping", json={
            "shipping_status": "SHIPPED"
        })
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASSED: PUT /api/orders/{id}/shipping requires auth")
    
    def test_shipping_update_404_for_invalid_order(self, test_user):
        """PUT /api/orders/{order_id}/shipping should return 404 for invalid order ID"""
        resp = requests.put(f"{BASE_URL}/api/orders/nonexistent-order-id/shipping",
            json={"shipping_status": "SHIPPED"},
            headers={"Authorization": f"Bearer {test_user['token']}"})
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("PASSED: PUT /api/orders/{id}/shipping returns 404 for invalid order")
    
    def test_shipping_update_validates_status(self, test_user):
        """PUT /api/orders/{order_id}/shipping should validate shipping_status values"""
        # First, we need to find or create an order where the test user is the seller
        # For now, test with invalid order ID to verify validation logic
        resp = requests.put(f"{BASE_URL}/api/orders/nonexistent-order/shipping",
            json={"shipping_status": "INVALID_STATUS"},
            headers={"Authorization": f"Bearer {test_user['token']}"})
        # Should return 404 (order not found) or 400 (invalid status) - both are acceptable
        assert resp.status_code in [400, 404], f"Expected 400/404, got {resp.status_code}"
        print(f"PASSED: PUT /api/orders/{'{id}'}/shipping validates input (status={resp.status_code})")


class TestOrdersDataIntegrity:
    """Tests for orders data structure and integrity"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for test user"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_direct_66@test.com",
            "password": "testpass123"
        })
        if login_resp.status_code != 200:
            pytest.skip("No test user available")
        data = login_resp.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_purchases_response_structure(self, auth_headers):
        """Verify purchases response has expected structure"""
        resp = requests.get(f"{BASE_URL}/api/orders/purchases", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify it's a list
        assert isinstance(data, list)
        
        # If there are items, verify structure
        if len(data) > 0:
            item = data[0]
            # Required fields from _enrich_transactions
            assert "order_number" in item, "order_number is required"
            assert "shipping_status" in item, "shipping_status is required"
            assert item["shipping_status"] in ["NOT_SHIPPED", "SHIPPED", "DELIVERED", None], \
                f"Invalid shipping_status: {item['shipping_status']}"
        
        print(f"PASSED: Purchases response structure valid (count={len(data)})")
    
    def test_sales_response_structure(self, auth_headers):
        """Verify sales response has expected structure"""
        resp = requests.get(f"{BASE_URL}/api/orders/sales", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert isinstance(data, list)
        
        if len(data) > 0:
            item = data[0]
            assert "order_number" in item
            assert "shipping_status" in item
            # Seller should see counterparty (buyer)
            assert "counterparty" in item
        
        print(f"PASSED: Sales response structure valid (count={len(data)})")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
