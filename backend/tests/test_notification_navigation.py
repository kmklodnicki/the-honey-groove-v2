"""
Test suite for notification navigation feature
Tests that clicking notifications navigates to correct routes
- GET /api/notifications - list notifications
- PUT /api/notifications/{id}/read - mark single notification as read  
- PUT /api/notifications/read-all - mark all notifications as read
- Verify notification data structure for each type
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://vinyl-hive-feed.preview.emergentagent.com"

# Test user credentials
TEST_EMAIL = "testnotif73@test.com"
TEST_PASSWORD = "testpass123"


class TestNotificationAPI:
    """Tests for notification API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, 
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        self.token = resp.json()["access_token"]
        self.user = resp.json()["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_notifications_returns_list(self):
        """GET /api/notifications - returns list of notifications"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=15", headers=self.headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Got {len(data)} notifications")
    
    def test_notification_structure(self):
        """Notifications have correct structure with id, type, body, data, read fields"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=15", headers=self.headers)
        assert resp.status_code == 200
        notifications = resp.json()
        
        if len(notifications) == 0:
            pytest.skip("No notifications to verify structure")
        
        notif = notifications[0]
        required_fields = ["id", "type", "body", "data", "read", "created_at"]
        for field in required_fields:
            assert field in notif, f"Missing field: {field}"
        
        print(f"Notification structure verified: {notif.keys()}")
    
    def test_notifications_sorted_newest_first(self):
        """Notifications are sorted by created_at descending"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=15", headers=self.headers)
        assert resp.status_code == 200
        notifications = resp.json()
        
        if len(notifications) < 2:
            pytest.skip("Need at least 2 notifications to verify sorting")
        
        dates = [n["created_at"] for n in notifications]
        assert dates == sorted(dates, reverse=True), "Notifications not sorted by date"
        print("Notifications correctly sorted (newest first)")
    
    def test_get_unread_count(self):
        """GET /api/notifications/unread-count - returns count"""
        resp = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=self.headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "count" in data, "Missing count field"
        assert isinstance(data["count"], int), "Count should be integer"
        print(f"Unread count: {data['count']}")
    
    def test_mark_notification_read(self):
        """PUT /api/notifications/{id}/read - marks as read"""
        # Get notifications
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=15", headers=self.headers)
        notifications = resp.json()
        
        # Find unread notification
        unread = [n for n in notifications if not n.get("read", True)]
        if not unread:
            pytest.skip("No unread notifications to mark")
        
        notif_id = unread[0]["id"]
        
        # Mark as read
        mark_resp = requests.put(f"{BASE_URL}/api/notifications/{notif_id}/read", 
                                 json={}, headers=self.headers)
        assert mark_resp.status_code == 200, f"Failed: {mark_resp.text}"
        print(f"Marked notification {notif_id} as read")
    
    def test_mark_all_read(self):
        """PUT /api/notifications/read-all - marks all as read and count becomes 0"""
        # Get initial unread count
        count_resp = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=self.headers)
        initial_count = count_resp.json()["count"]
        print(f"Initial unread count: {initial_count}")
        
        # Mark all as read
        resp = requests.put(f"{BASE_URL}/api/notifications/read-all", json={}, headers=self.headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        # Verify count is now 0
        count_resp = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=self.headers)
        new_count = count_resp.json()["count"]
        assert new_count == 0, f"Expected 0 unread after mark-all, got {new_count}"
        print("All notifications marked as read, count is now 0")
    
    def test_notifications_require_auth(self):
        """Notification endpoints require authentication"""
        # No auth header
        resp = requests.get(f"{BASE_URL}/api/notifications")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("Correctly requires authentication")


class TestNotificationDataTypes:
    """Tests that verify notification data structure for each type needed for navigation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, 
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_new_follower_notification_has_follower_username(self):
        """NEW_FOLLOWER notification has follower_username in data"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=30", headers=self.headers)
        notifications = resp.json()
        
        follower_notifs = [n for n in notifications if n["type"] == "NEW_FOLLOWER"]
        if not follower_notifs:
            pytest.skip("No NEW_FOLLOWER notifications found")
        
        notif = follower_notifs[0]
        assert "data" in notif, "Missing data field"
        assert "follower_username" in notif["data"], "NEW_FOLLOWER missing follower_username"
        print(f"NEW_FOLLOWER has follower_username: {notif['data']['follower_username']}")
    
    def test_post_liked_notification_has_post_id(self):
        """POST_LIKED notification has post_id in data"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=30", headers=self.headers)
        notifications = resp.json()
        
        liked_notifs = [n for n in notifications if n["type"] == "POST_LIKED"]
        if not liked_notifs:
            pytest.skip("No POST_LIKED notifications found")
        
        notif = liked_notifs[0]
        assert "data" in notif, "Missing data field"
        assert "post_id" in notif["data"], "POST_LIKED missing post_id"
        print(f"POST_LIKED has post_id: {notif['data']['post_id']}")
    
    def test_trade_proposed_notification_has_trade_id(self):
        """TRADE_PROPOSED notification has trade_id in data"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=30", headers=self.headers)
        notifications = resp.json()
        
        trade_notifs = [n for n in notifications if n["type"] == "TRADE_PROPOSED"]
        if not trade_notifs:
            pytest.skip("No TRADE_PROPOSED notifications found")
        
        notif = trade_notifs[0]
        assert "data" in notif, "Missing data field"
        assert "trade_id" in notif["data"], "TRADE_PROPOSED missing trade_id"
        print(f"TRADE_PROPOSED has trade_id: {notif['data']['trade_id']}")
    
    def test_stripe_connected_notification_structure(self):
        """STRIPE_CONNECTED notification exists with proper structure"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=30", headers=self.headers)
        notifications = resp.json()
        
        stripe_notifs = [n for n in notifications if n["type"] == "STRIPE_CONNECTED"]
        if not stripe_notifs:
            pytest.skip("No STRIPE_CONNECTED notifications found")
        
        notif = stripe_notifs[0]
        assert "id" in notif, "Missing id"
        assert "type" in notif, "Missing type"
        print(f"STRIPE_CONNECTED notification found: {notif['body']}")
    
    def test_order_shipped_notification_has_order_id(self):
        """ORDER_SHIPPED notification has order_id in data"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=30", headers=self.headers)
        notifications = resp.json()
        
        order_notifs = [n for n in notifications if n["type"] == "ORDER_SHIPPED"]
        if not order_notifs:
            pytest.skip("No ORDER_SHIPPED notifications found")
        
        notif = order_notifs[0]
        assert "data" in notif, "Missing data field"
        assert "order_id" in notif["data"], "ORDER_SHIPPED missing order_id"
        print(f"ORDER_SHIPPED has order_id: {notif['data']['order_id']}")
    
    def test_wax_report_notification_structure(self):
        """WAX_REPORT notification has correct structure"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=30", headers=self.headers)
        notifications = resp.json()
        
        wax_notifs = [n for n in notifications if n["type"] == "WAX_REPORT"]
        if not wax_notifs:
            pytest.skip("No WAX_REPORT notifications found")
        
        notif = wax_notifs[0]
        assert "id" in notif, "Missing id"
        assert "type" in notif, "Missing type"
        assert notif["type"] == "WAX_REPORT"
        print(f"WAX_REPORT notification found: {notif['body']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
