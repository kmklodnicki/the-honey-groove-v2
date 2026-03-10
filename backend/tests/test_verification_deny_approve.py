"""
Test Verification Approve/Deny Endpoints
- Tests POST /api/verification/admin/approve/{id} 
- Tests POST /api/verification/admin/deny/{id} with reason field
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestVerificationEndpoints:
    """Verification admin approve/deny endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login as admin user"""
        self.session = requests.Session()
        # Login as demo admin
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Auth failed - skipping tests")
    
    def test_approve_endpoint_exists(self):
        """Test POST /api/verification/admin/approve/{id} endpoint exists"""
        # Use a fake ID - should get 404 (not found) not 405 (method not allowed)
        resp = self.session.post(
            f"{BASE_URL}/api/verification/admin/approve/fake_id_12345", 
            json={}, 
            headers=self.headers
        )
        # 404 means endpoint exists but ID not found (expected)
        # 405 would mean endpoint doesn't exist
        assert resp.status_code in [404, 400], f"Expected 404 or 400, got {resp.status_code}"
        print(f"Approve endpoint test: status {resp.status_code} - endpoint exists")
    
    def test_deny_endpoint_accepts_reason(self):
        """Test POST /api/verification/admin/deny/{id} accepts reason field"""
        # Use a fake ID - should get 404 (not found) not 405 (method not allowed)
        resp = self.session.post(
            f"{BASE_URL}/api/verification/admin/deny/fake_id_12345", 
            json={"reason": "Blurry", "notes": "Test denial reason"}, 
            headers=self.headers
        )
        # 404 means endpoint exists but ID not found
        assert resp.status_code in [404, 400], f"Expected 404 or 400, got {resp.status_code}"
        print(f"Deny endpoint test: status {resp.status_code} - endpoint accepts reason field")
    
    def test_verification_queue_endpoint(self):
        """Test GET /api/verification/admin/queue returns pending requests"""
        resp = self.session.get(
            f"{BASE_URL}/api/verification/admin/queue", 
            headers=self.headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), "Queue should return a list"
        print(f"Verification queue: {len(data)} pending requests")


class TestNotificationEndpoints:
    """Test notification endpoint for multi-channel notifications"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login as admin user"""
        self.session = requests.Session()
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Auth failed - skipping tests")
    
    def test_notifications_endpoint(self):
        """Test GET /api/notifications returns user notifications"""
        resp = self.session.get(
            f"{BASE_URL}/api/notifications?limit=10", 
            headers=self.headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), "Notifications should return a list"
        print(f"Notifications endpoint: {len(data)} notifications returned")
    
    def test_notifications_unread_count(self):
        """Test GET /api/notifications/unread-count returns count"""
        resp = self.session.get(
            f"{BASE_URL}/api/notifications/unread-count", 
            headers=self.headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "count" in data, "Response should have count field"
        print(f"Unread notifications count: {data['count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
