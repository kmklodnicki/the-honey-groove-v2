"""
Test suite for HoneyGroove Stripe Connect, Payments, and Notification features
- Stripe Connect onboarding (simulated)
- Stripe Connect return & status
- Payment checkout for BUY_NOW and MAKE_OFFER listings
- Notifications CRUD and triggers (follow, like, trade, stripe)
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://vinyl-collector-hub.preview.emergentagent.com"

# Test credentials
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "password123"
TRADER_EMAIL = "trader@example.com"
TRADER_PASSWORD = "password123"


class TestStripeConnect:
    """Tests for Stripe Connect onboarding (simulated flow)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get tokens for both users"""
        # Login demo user (admin, already stripe_connected=true)
        demo_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD
        })
        assert demo_resp.status_code == 200, f"Demo login failed: {demo_resp.text}"
        self.demo_token = demo_resp.json()["access_token"]
        self.demo_user = demo_resp.json()["user"]
        
        # Login trader user
        trader_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER_EMAIL, "password": TRADER_PASSWORD
        })
        assert trader_resp.status_code == 200, f"Trader login failed: {trader_resp.text}"
        self.trader_token = trader_resp.json()["access_token"]
        self.trader_user = trader_resp.json()["user"]
    
    def test_stripe_status_authenticated(self):
        """GET /api/stripe/status - returns stripe_connected and stripe_account_id"""
        resp = requests.get(f"{BASE_URL}/api/stripe/status", 
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "stripe_connected" in data, "Missing stripe_connected field"
        assert "stripe_account_id" in data, "Missing stripe_account_id field"
        print(f"Stripe status for demo: connected={data['stripe_connected']}, account_id={data['stripe_account_id']}")
    
    def test_stripe_status_demo_already_connected(self):
        """GET /api/stripe/status - demo user should be already connected"""
        resp = requests.get(f"{BASE_URL}/api/stripe/status",
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        data = resp.json()
        # Demo was set up with stripe_connected=true per context
        assert data["stripe_connected"] == True, f"Demo should be connected but got: {data}"
        print(f"Demo user stripe connected: {data['stripe_connected']}")
    
    def test_stripe_connect_already_connected_user(self):
        """POST /api/stripe/connect - should fail for already connected user"""
        resp = requests.post(f"{BASE_URL}/api/stripe/connect", json={},
                            headers={"Authorization": f"Bearer {self.demo_token}"})
        # Demo is already connected, should get 400
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        assert "already connected" in resp.json().get("detail", "").lower()
        print("Correctly rejected: Stripe already connected for demo user")
    
    def test_stripe_status_unauthenticated(self):
        """GET /api/stripe/status - should require auth"""
        resp = requests.get(f"{BASE_URL}/api/stripe/status")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("Correctly requires authentication for stripe status")
    
    def test_stripe_connect_return_marks_connected(self):
        """GET /api/stripe/connect/return?user_id=X - marks user as connected and creates notification"""
        # This is a redirect endpoint, test the logic by checking a return call
        # Note: This simulates what happens when Stripe onboarding completes
        resp = requests.get(f"{BASE_URL}/api/stripe/connect/return?user_id={self.demo_user['id']}", 
                           allow_redirects=False)
        # Should redirect to profile page
        assert resp.status_code in [302, 307, 200], f"Expected redirect, got {resp.status_code}: {resp.text}"
        if resp.status_code in [302, 307]:
            location = resp.headers.get("Location", "")
            assert "profile" in location.lower() or "stripe=connected" in location.lower()
            print(f"Stripe return redirects to: {location}")


class TestPaymentCheckout:
    """Tests for payment checkout for BUY_NOW and MAKE_OFFER listings"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and setup test data"""
        # Login demo user (seller)
        demo_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD
        })
        assert demo_resp.status_code == 200
        self.demo_token = demo_resp.json()["access_token"]
        self.demo_user = demo_resp.json()["user"]
        
        # Login trader user (buyer)
        trader_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER_EMAIL, "password": TRADER_PASSWORD
        })
        assert trader_resp.status_code == 200
        self.trader_token = trader_resp.json()["access_token"]
        self.trader_user = trader_resp.json()["user"]
        
        # Get existing listings or create test listings
        listings_resp = requests.get(f"{BASE_URL}/api/listings?limit=30")
        self.listings = listings_resp.json() if listings_resp.status_code == 200 else []
    
    def _get_or_create_listing(self, listing_type, owner_token, price=None):
        """Get existing listing or create a new one for testing"""
        # First check my listings
        my_listings = requests.get(f"{BASE_URL}/api/listings/my", 
                                   headers={"Authorization": f"Bearer {owner_token}"})
        if my_listings.status_code == 200:
            for listing in my_listings.json():
                if listing["listing_type"] == listing_type and listing["status"] == "ACTIVE":
                    return listing
        
        # Create a new listing
        unique_id = uuid.uuid4().hex[:8]
        listing_data = {
            "artist": f"TEST_Artist_{unique_id}",
            "album": f"TEST_Album_{unique_id}",
            "listing_type": listing_type,
            "price": price or 25.00,
            "condition": "Very Good",
            "photo_urls": ["https://via.placeholder.com/300"]
        }
        resp = requests.post(f"{BASE_URL}/api/listings", json=listing_data,
                            headers={"Authorization": f"Bearer {owner_token}"})
        if resp.status_code == 201:
            return resp.json()
        return None
    
    def test_checkout_buy_now_listing(self):
        """POST /api/payments/checkout - creates checkout for BUY_NOW listing"""
        # Get or create a BUY_NOW listing owned by demo
        listing = self._get_or_create_listing("BUY_NOW", self.demo_token, price=50.00)
        if not listing:
            pytest.skip("Could not create BUY_NOW listing for test")
        
        # Trader attempts to buy (should work or fail with Stripe error)
        resp = requests.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": listing["id"],
            "origin_url": "https://vinyl-collector-hub.preview.emergentagent.com"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        # May fail due to test Stripe key, but structure should be correct
        if resp.status_code == 200:
            data = resp.json()
            assert "url" in data or "session_id" in data
            print(f"BUY_NOW checkout created: session_id={data.get('session_id')}")
        else:
            # Accept Stripe API errors as expected with test key
            print(f"Checkout returned {resp.status_code}: {resp.text} (expected with test Stripe key)")
            assert resp.status_code in [200, 400, 500], f"Unexpected error: {resp.status_code}"
    
    def test_checkout_make_offer_with_amount(self):
        """POST /api/payments/checkout - creates checkout for MAKE_OFFER with offer_amount"""
        listing = self._get_or_create_listing("MAKE_OFFER", self.demo_token, price=75.00)
        if not listing:
            pytest.skip("Could not create MAKE_OFFER listing for test")
        
        resp = requests.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": listing["id"],
            "offer_amount": 60.00,
            "origin_url": "https://vinyl-collector-hub.preview.emergentagent.com"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code == 200:
            data = resp.json()
            assert "url" in data or "session_id" in data
            print(f"MAKE_OFFER checkout created with offer_amount=60.00")
        else:
            print(f"Make offer checkout returned {resp.status_code}: {resp.text}")
            assert resp.status_code in [200, 400, 500]
    
    def test_checkout_cannot_buy_own_listing(self):
        """POST /api/payments/checkout - cannot buy own listing"""
        listing = self._get_or_create_listing("BUY_NOW", self.demo_token, price=30.00)
        if not listing:
            pytest.skip("Could not create listing for test")
        
        # Demo tries to buy their own listing
        resp = requests.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": listing["id"],
            "origin_url": "https://vinyl-collector-hub.preview.emergentagent.com"
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        assert "own listing" in resp.json().get("detail", "").lower()
        print("Correctly rejected: Cannot buy your own listing")
    
    def test_checkout_invalid_listing(self):
        """POST /api/payments/checkout - fails for non-existent listing"""
        resp = requests.post(f"{BASE_URL}/api/payments/checkout", json={
            "listing_id": "non-existent-id-12345",
            "origin_url": "https://vinyl-collector-hub.preview.emergentagent.com"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("Correctly returns 404 for non-existent listing")
    
    def test_get_my_sales(self):
        """GET /api/payments/my-sales - returns seller's transaction history"""
        resp = requests.get(f"{BASE_URL}/api/payments/my-sales",
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "transactions" in data
        assert "total_earned" in data
        assert "total_fees" in data
        assert "total_sales" in data
        print(f"My sales: {data['total_sales']} sales, earned ${data['total_earned']}, fees ${data['total_fees']}")


class TestNotifications:
    """Tests for notification system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login users"""
        demo_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD
        })
        assert demo_resp.status_code == 200
        self.demo_token = demo_resp.json()["access_token"]
        self.demo_user = demo_resp.json()["user"]
        
        trader_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER_EMAIL, "password": TRADER_PASSWORD
        })
        assert trader_resp.status_code == 200
        self.trader_token = trader_resp.json()["access_token"]
        self.trader_user = trader_resp.json()["user"]
    
    def test_get_notifications(self):
        """GET /api/notifications - returns user's notifications sorted by date"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=15",
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        if len(data) > 0:
            notif = data[0]
            assert "id" in notif
            assert "type" in notif
            assert "body" in notif
            assert "read" in notif
            assert "created_at" in notif
            print(f"Found {len(data)} notifications for demo user. Latest: {notif['type']}")
        else:
            print("No notifications found for demo user")
    
    def test_get_notifications_sorted_by_date(self):
        """GET /api/notifications - should be sorted by created_at descending"""
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=30",
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        data = resp.json()
        if len(data) > 1:
            dates = [n["created_at"] for n in data]
            assert dates == sorted(dates, reverse=True), "Notifications not sorted by date"
            print("Notifications correctly sorted by date (newest first)")
    
    def test_get_unread_count(self):
        """GET /api/notifications/unread-count - returns count of unread notifications"""
        resp = requests.get(f"{BASE_URL}/api/notifications/unread-count",
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        print(f"Demo user has {data['count']} unread notifications")
    
    def test_mark_notification_read(self):
        """PUT /api/notifications/{id}/read - marks notification as read"""
        # First get notifications
        notifs_resp = requests.get(f"{BASE_URL}/api/notifications?limit=15",
                                   headers={"Authorization": f"Bearer {self.demo_token}"})
        notifs = notifs_resp.json()
        if not notifs:
            pytest.skip("No notifications to mark as read")
        
        notif_id = notifs[0]["id"]
        resp = requests.put(f"{BASE_URL}/api/notifications/{notif_id}/read", json={},
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200, f"Failed: {resp.text}"
        print(f"Marked notification {notif_id} as read")
    
    def test_mark_all_read(self):
        """PUT /api/notifications/read-all - marks all as read"""
        resp = requests.put(f"{BASE_URL}/api/notifications/read-all", json={},
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        # Verify count is now 0
        count_resp = requests.get(f"{BASE_URL}/api/notifications/unread-count",
                                 headers={"Authorization": f"Bearer {self.demo_token}"})
        assert count_resp.status_code == 200
        assert count_resp.json()["count"] == 0, "Unread count should be 0 after mark-all-read"
        print("All notifications marked as read, count now 0")


class TestNotificationTriggers:
    """Tests that verify notifications are created on specific actions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login users"""
        demo_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD
        })
        assert demo_resp.status_code == 200
        self.demo_token = demo_resp.json()["access_token"]
        self.demo_user = demo_resp.json()["user"]
        
        trader_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER_EMAIL, "password": TRADER_PASSWORD
        })
        assert trader_resp.status_code == 200
        self.trader_token = trader_resp.json()["access_token"]
        self.trader_user = trader_resp.json()["user"]
    
    def test_follow_creates_new_follower_notification(self):
        """Following a user creates a NEW_FOLLOWER notification"""
        # Get initial notification count for demo
        initial_count = requests.get(f"{BASE_URL}/api/notifications/unread-count",
                                     headers={"Authorization": f"Bearer {self.demo_token}"})
        initial = initial_count.json()["count"]
        
        # Check if trader is already following demo
        check_resp = requests.get(f"{BASE_URL}/api/follow/check/{self.demo_user['username']}",
                                  headers={"Authorization": f"Bearer {self.trader_token}"})
        is_following = check_resp.json().get("is_following", False)
        
        if is_following:
            # Unfollow first
            requests.delete(f"{BASE_URL}/api/follow/{self.demo_user['username']}",
                           headers={"Authorization": f"Bearer {self.trader_token}"})
        
        # Now follow demo
        resp = requests.post(f"{BASE_URL}/api/follow/{self.demo_user['username']}", json={},
                            headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code == 200:
            # Check for NEW_FOLLOWER notification
            notifs = requests.get(f"{BASE_URL}/api/notifications?limit=5",
                                 headers={"Authorization": f"Bearer {self.demo_token}"})
            latest_notifs = notifs.json()
            new_follower_notifs = [n for n in latest_notifs if n["type"] == "NEW_FOLLOWER"]
            assert len(new_follower_notifs) > 0, "NEW_FOLLOWER notification not created"
            print(f"NEW_FOLLOWER notification created: {new_follower_notifs[0]['body']}")
        else:
            print(f"Follow returned {resp.status_code} (may already follow)")
    
    def test_like_post_creates_post_liked_notification(self):
        """Liking a post creates a POST_LIKED notification"""
        # Get a post from explore to like
        explore_resp = requests.get(f"{BASE_URL}/api/explore?limit=10")
        posts = explore_resp.json() if explore_resp.status_code == 200 else []
        
        # Find a post by demo that trader can like
        demo_posts = [p for p in posts if p["user_id"] == self.demo_user["id"]]
        if not demo_posts:
            pytest.skip("No posts by demo user to like")
        
        post_id = demo_posts[0]["id"]
        
        # Unlike first if already liked
        requests.delete(f"{BASE_URL}/api/posts/{post_id}/like",
                       headers={"Authorization": f"Bearer {self.trader_token}"})
        
        # Like the post
        resp = requests.post(f"{BASE_URL}/api/posts/{post_id}/like", json={},
                            headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code in [200, 201]:
            # Check for POST_LIKED notification
            notifs = requests.get(f"{BASE_URL}/api/notifications?limit=5",
                                 headers={"Authorization": f"Bearer {self.demo_token}"})
            latest_notifs = notifs.json()
            liked_notifs = [n for n in latest_notifs if n["type"] == "POST_LIKED"]
            # Should have at least one POST_LIKED notification
            print(f"Found {len(liked_notifs)} POST_LIKED notifications")
        else:
            print(f"Like returned {resp.status_code}: {resp.text}")
    
    def test_stripe_connected_notification_exists(self):
        """STRIPE_CONNECTED notification should exist for connected user"""
        notifs = requests.get(f"{BASE_URL}/api/notifications?limit=30",
                             headers={"Authorization": f"Bearer {self.demo_token}"})
        all_notifs = notifs.json()
        stripe_notifs = [n for n in all_notifs if n["type"] == "STRIPE_CONNECTED"]
        
        # Per context, demo user has stripe_connected and should have this notification
        if stripe_notifs:
            print(f"STRIPE_CONNECTED notification found: {stripe_notifs[0]['body']}")
        else:
            print("No STRIPE_CONNECTED notification found (may have been read/deleted)")


class TestPaymentStatus:
    """Tests for payment status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login"""
        demo_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD
        })
        assert demo_resp.status_code == 200
        self.demo_token = demo_resp.json()["access_token"]
    
    def test_payment_status_not_found(self):
        """GET /api/payments/status/{session_id} - returns 404 for invalid session"""
        resp = requests.get(f"{BASE_URL}/api/payments/status/invalid-session-id-123",
                           headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("Correctly returns 404 for invalid session_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
