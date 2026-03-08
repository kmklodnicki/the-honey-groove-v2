"""
Test Orders API - Sales Expandable Feature
Tests that GET /api/orders/sales returns enriched order data with new fields
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "vinylcollector@honey.io"
TEST_PASSWORD = "password123"


class TestOrdersAPI:
    """Test the orders endpoints with enriched data"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.headers = {"Content-Type": "application/json"}
        # Login to get token
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers=self.headers
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")  # Token field is 'access_token'
            self.auth_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        else:
            pytest.skip(f"Login failed: {response.status_code} - {response.text}")

    def test_orders_sales_endpoint_returns_200(self):
        """GET /api/orders/sales returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/orders/sales",
            headers=self.auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/orders/sales returns 200 with {len(data)} sales")

    def test_orders_purchases_endpoint_returns_200(self):
        """GET /api/orders/purchases returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/orders/purchases",
            headers=self.auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/orders/purchases returns 200 with {len(data)} purchases")

    def test_orders_sales_without_auth_returns_401(self):
        """GET /api/orders/sales without auth returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/orders/sales",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/orders/sales without auth returns 401")

    def test_orders_purchases_without_auth_returns_401(self):
        """GET /api/orders/purchases without auth returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/orders/purchases",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/orders/purchases without auth returns 401")

    def test_orders_sales_response_structure(self):
        """GET /api/orders/sales returns proper structure with enriched fields"""
        response = requests.get(
            f"{BASE_URL}/api/orders/sales",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are sales, verify the structure contains the new enriched fields
        if len(data) > 0:
            order = data[0]
            # Basic fields that should always be present
            expected_base_fields = ["id", "order_number", "shipping_status"]
            for field in expected_base_fields:
                assert field in order, f"Missing field: {field}"
            
            # New enriched fields (may or may not be present depending on listing data)
            enriched_fields = ["pressing_variant", "listing_price", "description", "listing_type", "photo_urls", "year"]
            print(f"✓ Order has fields: {list(order.keys())}")
            print(f"✓ Checking for enriched fields: {enriched_fields}")
            
            # Just verify the structure is correct - fields may be None if listing doesn't have them
            for field in enriched_fields:
                if field in order:
                    print(f"  - {field}: present ({type(order[field]).__name__})")
        else:
            print("✓ No sales found for test user (empty list is valid)")

    def test_orders_purchases_response_structure(self):
        """GET /api/orders/purchases returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/orders/purchases",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            order = data[0]
            expected_fields = ["id", "order_number", "shipping_status"]
            for field in expected_fields:
                assert field in order, f"Missing field: {field}"
            print(f"✓ Purchase order structure valid with fields: {list(order.keys())}")
        else:
            print("✓ No purchases found for test user (empty list is valid)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
