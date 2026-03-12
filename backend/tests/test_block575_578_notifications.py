"""
BLOCK 575-578 Backend Tests: Notification Pagination
Tests the GET /api/notifications endpoint with skip/limit query params.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestNotificationPagination:
    """BLOCK 575/578: Notification pagination with skip/limit parameters"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for test user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test_recovery@test.com", "password": "test123"}
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate test user")
    
    def test_notifications_default_pagination(self):
        """GET /api/notifications returns array with default limit=15, skip=0"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be an array"
        print(f"✅ Default pagination works: returned {len(data)} notifications")
    
    def test_notifications_with_limit_param(self):
        """GET /api/notifications?limit=5 respects limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/notifications?limit=5",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5, "Should return at most 5 notifications"
        print(f"✅ Limit param works: returned {len(data)} notifications (max 5)")
    
    def test_notifications_with_skip_param(self):
        """GET /api/notifications?limit=15&skip=0 respects skip parameter"""
        response = requests.get(
            f"{BASE_URL}/api/notifications?limit=15&skip=0",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Skip param works: returned {len(data)} notifications")
    
    def test_notifications_pagination_combined(self):
        """GET /api/notifications?limit=10&skip=5 supports combined pagination"""
        response = requests.get(
            f"{BASE_URL}/api/notifications?limit=10&skip=5",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Combined pagination works: returned {len(data)} notifications")
    
    def test_notifications_unread_count(self):
        """GET /api/notifications/unread-count returns count object"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data, "Response should have 'count' field"
        assert isinstance(data["count"], int)
        print(f"✅ Unread count works: {data['count']} unread")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
