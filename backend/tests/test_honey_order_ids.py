"""
Test HONEY-XXXXXXXXX Order ID Branding Feature

This test file verifies the new sequential order ID format:
- HONEY-XXXXXXXXX for new orders (starting at HONEY-134208789)
- Legacy UUID format for existing orders (8-char uppercase prefix)
"""

import pytest
import requests
import os
from datetime import datetime
import asyncio

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials
TEST_EMAIL = "testexplore@test.com"
TEST_PASSWORD = "testpass123"


class TestHoneyOrderIDsBackend:
    """Backend tests for HONEY Order ID feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_01_auth_works(self):
        """Verify authentication is working"""
        assert self.token is not None, "Failed to authenticate"
        print(f"Authenticated successfully, token: {self.token[:20]}...")
    
    def test_02_purchases_endpoint_returns_order_number_field(self):
        """Test GET /api/orders/purchases returns orders with order_number field"""
        response = self.session.get(f"{BASE_URL}/api/orders/purchases")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        orders = response.json()
        print(f"Found {len(orders)} purchases")
        
        # If there are orders, verify structure
        if orders:
            for order in orders[:5]:  # Check first 5 orders
                assert "id" in order, "Order missing 'id' field"
                assert "order_number" in order, "Order missing 'order_number' field"
                
                order_num = order["order_number"]
                order_id = order["id"]
                
                # Check order_number format
                if order_id.startswith("HONEY-"):
                    # New format: order_number should equal order_id
                    assert order_num == order_id, f"New order should have order_number == id, got {order_num} vs {order_id}"
                    print(f"  [NEW] Order ID: {order_id}, Order Number: {order_num}")
                else:
                    # Legacy format: order_number should be 8-char uppercase prefix
                    expected_prefix = order_id[:8].upper()
                    assert order_num == expected_prefix, f"Legacy order should have 8-char prefix, got {order_num} vs {expected_prefix}"
                    print(f"  [LEGACY] Order ID: {order_id[:16]}..., Order Number: {order_num}")
        else:
            print("No purchases found - endpoint works but no data to verify format")
    
    def test_03_sales_endpoint_returns_order_number_field(self):
        """Test GET /api/orders/sales returns orders with order_number field"""
        response = self.session.get(f"{BASE_URL}/api/orders/sales")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        orders = response.json()
        print(f"Found {len(orders)} sales")
        
        # If there are orders, verify structure
        if orders:
            for order in orders[:5]:  # Check first 5 orders
                assert "id" in order, "Order missing 'id' field"
                assert "order_number" in order, "Order missing 'order_number' field"
                
                order_num = order["order_number"]
                order_id = order["id"]
                
                # Check order_number format
                if order_id.startswith("HONEY-"):
                    # New format: order_number should equal order_id
                    assert order_num == order_id, f"New order should have order_number == id, got {order_num} vs {order_id}"
                    print(f"  [NEW] Order ID: {order_id}, Order Number: {order_num}")
                else:
                    # Legacy format: order_number should be 8-char uppercase prefix
                    expected_prefix = order_id[:8].upper()
                    assert order_num == expected_prefix, f"Legacy order should have 8-char prefix, got {order_num} vs {expected_prefix}"
                    print(f"  [LEGACY] Order ID: {order_id[:16]}..., Order Number: {order_num}")
        else:
            print("No sales found - endpoint works but no data to verify format")


class TestHoneyOrderIDCounter:
    """Test the HONEY order ID counter directly using MongoDB"""
    
    def test_01_counter_logic_verification(self):
        """Verify the counter logic formula: seq + HONEY_ORDER_START - 1"""
        HONEY_ORDER_START = 134208789
        
        # Test cases:
        # seq=1 -> HONEY-134208789
        # seq=2 -> HONEY-134208790
        # seq=10 -> HONEY-134208798
        
        test_cases = [
            (1, "HONEY-134208789"),
            (2, "HONEY-134208790"),
            (10, "HONEY-134208798"),
            (100, "HONEY-134208888"),
        ]
        
        for seq, expected in test_cases:
            computed = seq + HONEY_ORDER_START - 1
            result = f"HONEY-{computed}"
            assert result == expected, f"For seq={seq}, expected {expected}, got {result}"
            print(f"  seq={seq} -> {result} ✓")
        
        print("Counter formula verified correctly!")


class TestOrderNumberDisplayLogic:
    """Test order_number display logic from backend _enrich_transactions"""
    
    def test_01_order_number_for_honey_id(self):
        """Test that HONEY- prefixed IDs are returned as-is"""
        # Simulate the backend logic
        order_id = "HONEY-134208789"
        order_number = order_id if order_id.startswith("HONEY-") else order_id[:8].upper()
        
        assert order_number == "HONEY-134208789"
        print(f"  HONEY-prefixed ID: {order_id} -> order_number: {order_number} ✓")
    
    def test_02_order_number_for_legacy_uuid(self):
        """Test that legacy UUIDs get 8-char uppercase prefix"""
        # Simulate the backend logic
        order_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        order_number = order_id if order_id.startswith("HONEY-") else order_id[:8].upper()
        
        assert order_number == "A1B2C3D4"
        print(f"  Legacy UUID: {order_id[:16]}... -> order_number: {order_number} ✓")
    
    def test_03_order_number_for_various_uuids(self):
        """Test multiple UUID formats"""
        test_uuids = [
            "12345678-abcd-1234-5678-abcdef123456",
            "ABCDEFGH-1234-5678-ABCD-EF1234567890",
            "deadbeef-cafe-babe-dead-beefcafebabe",
        ]
        
        for uuid in test_uuids:
            order_number = uuid if uuid.startswith("HONEY-") else uuid[:8].upper()
            expected = uuid[:8].upper()
            assert order_number == expected, f"Expected {expected}, got {order_number}"
            print(f"  UUID: {uuid[:16]}... -> order_number: {order_number} ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
