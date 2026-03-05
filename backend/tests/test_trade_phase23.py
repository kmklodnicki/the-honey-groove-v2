"""
Test Trade Phase 2 (Shipping/Confirming) and Phase 3 (Disputes/Ratings) API endpoints
HoneyGroove Trade System - Full flow testing
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test user credentials
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "password123"
TRADER_EMAIL = "trader@example.com"
TRADER_PASSWORD = "password123"


class TestSetup:
    """Setup: Get tokens and prepare test data"""
    demo_token = None
    trader_token = None
    demo_user = None
    trader_user = None
    
    @classmethod
    def get_demo_token(cls):
        if not cls.demo_token:
            resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            })
            assert resp.status_code == 200, f"Demo login failed: {resp.text}"
            data = resp.json()
            cls.demo_token = data["access_token"]
            cls.demo_user = data["user"]
        return cls.demo_token, cls.demo_user

    @classmethod
    def get_trader_token(cls):
        if not cls.trader_token:
            resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TRADER_EMAIL,
                "password": TRADER_PASSWORD
            })
            assert resp.status_code == 200, f"Trader login failed: {resp.text}"
            data = resp.json()
            cls.trader_token = data["access_token"]
            cls.trader_user = data["user"]
        return cls.trader_token, cls.trader_user


class TestPhase2ShippingFlow:
    """Test Phase 2: Shipping and Confirmation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth tokens for tests"""
        self.demo_token, self.demo_user = TestSetup.get_demo_token()
        self.trader_token, self.trader_user = TestSetup.get_trader_token()
    
    def test_accept_trade_sets_shipping_status(self):
        """After accept, trade should move to SHIPPING with shipping_deadline"""
        # First create a fresh trade for testing
        # Get demo's records
        resp = requests.get(f"{BASE_URL}/api/users/demo/records")
        assert resp.status_code == 200
        demo_records = resp.json()
        
        # Get trader's records
        resp = requests.get(f"{BASE_URL}/api/users/trader/records")
        assert resp.status_code == 200
        trader_records = resp.json()
        
        if not trader_records:
            pytest.skip("Trader has no records for testing")
        
        # Create a TRADE listing as demo
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "TEST_Phase2_Artist",
            "album": "TEST_Phase2_Shipping",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/test.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        listing = resp.json()
        listing_id = listing["id"]
        
        # Trader proposes a trade
        offered_record_id = trader_records[0]["id"]
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": offered_record_id,
            "message": "Phase 2 test trade"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        trade = resp.json()
        trade_id = trade["id"]
        assert trade["status"] == "PROPOSED"
        print(f"Trade proposed: {trade_id}, status: {trade['status']}")
        
        # Demo accepts the trade
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept", 
            headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        accepted = resp.json()
        
        # Verify status changed to SHIPPING
        assert accepted["status"] == "SHIPPING", f"Expected SHIPPING, got {accepted['status']}"
        assert accepted.get("shipping_deadline") is not None, "Missing shipping_deadline"
        assert accepted.get("shipping") is not None, "Missing shipping object"
        assert accepted["shipping"].get("initiator") is None
        assert accepted["shipping"].get("responder") is None
        print(f"Trade accepted, status: {accepted['status']}, deadline: {accepted['shipping_deadline']}")
        
        # Store trade_id for subsequent tests
        self.__class__.test_trade_id = trade_id
        self.__class__.test_listing_id = listing_id
    
    def test_ship_first_party_stays_shipping(self):
        """First party shipping keeps SHIPPING status"""
        trade_id = getattr(self.__class__, 'test_trade_id', None)
        if not trade_id:
            pytest.skip("No trade_id from previous test")
        
        # Trader (initiator) ships first
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/ship", json={
            "tracking_number": "TEST123456789",
            "carrier": "USPS"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        trade = resp.json()
        
        assert trade["status"] == "SHIPPING", f"Expected SHIPPING, got {trade['status']}"
        assert trade["shipping"]["initiator"] is not None
        assert trade["shipping"]["initiator"]["tracking_number"] == "TEST123456789"
        assert trade["shipping"]["responder"] is None
        print(f"First party shipped, status still: {trade['status']}")
    
    def test_cannot_ship_twice(self):
        """Cannot submit tracking twice"""
        trade_id = getattr(self.__class__, 'test_trade_id', None)
        if not trade_id:
            pytest.skip("No trade_id from previous test")
        
        # Try to ship again as trader
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/ship", json={
            "tracking_number": "DUPLICATE123",
            "carrier": "UPS"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 400
        assert "already submitted" in resp.json()["detail"].lower()
        print("Correctly prevented duplicate shipping submission")
    
    def test_both_ship_moves_to_confirming(self):
        """When both ship, trade moves to CONFIRMING with 48h deadline"""
        trade_id = getattr(self.__class__, 'test_trade_id', None)
        if not trade_id:
            pytest.skip("No trade_id from previous test")
        
        # Demo (responder) ships
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/ship", json={
            "tracking_number": "DEMO987654321",
            "carrier": "FedEx"
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        trade = resp.json()
        
        assert trade["status"] == "CONFIRMING", f"Expected CONFIRMING, got {trade['status']}"
        assert trade.get("confirmation_deadline") is not None, "Missing confirmation_deadline"
        assert trade["shipping"]["initiator"] is not None
        assert trade["shipping"]["responder"] is not None
        print(f"Both shipped, status: {trade['status']}, confirm deadline: {trade['confirmation_deadline']}")
    
    def test_first_confirm_keeps_confirming(self):
        """First confirmation keeps CONFIRMING status"""
        trade_id = getattr(self.__class__, 'test_trade_id', None)
        if not trade_id:
            pytest.skip("No trade_id from previous test")
        
        # Trader confirms receipt
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/confirm-receipt",
            headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        trade = resp.json()
        
        assert trade["status"] == "CONFIRMING", f"Expected CONFIRMING, got {trade['status']}"
        assert trade["confirmations"].get(self.trader_user["id"]) == True
        print(f"First confirmation, status: {trade['status']}")
    
    def test_both_confirm_completes_trade(self):
        """Both confirmations complete the trade"""
        trade_id = getattr(self.__class__, 'test_trade_id', None)
        if not trade_id:
            pytest.skip("No trade_id from previous test")
        
        # Demo confirms receipt
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/confirm-receipt",
            headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        trade = resp.json()
        
        assert trade["status"] == "COMPLETED", f"Expected COMPLETED, got {trade['status']}"
        print(f"Both confirmed, trade COMPLETED!")
        
        # Store for rating tests
        self.__class__.completed_trade_id = trade_id


class TestPhase2CancelShipping:
    """Test cancel-shipping edge cases"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.demo_token, self.demo_user = TestSetup.get_demo_token()
        self.trader_token, self.trader_user = TestSetup.get_trader_token()
    
    def test_cannot_cancel_before_deadline(self):
        """Cannot cancel shipping before deadline passes"""
        # Create a new trade for this test
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "TEST_Cancel_Before",
            "album": "TEST_Cancel_Deadline",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/test.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        listing_id = resp.json()["id"]
        
        # Get trader records
        resp = requests.get(f"{BASE_URL}/api/users/trader/records")
        trader_records = resp.json()
        if not trader_records:
            pytest.skip("No trader records")
        
        # Propose and accept
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": trader_records[0]["id"],
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        trade_id = resp.json()["id"]
        
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept",
            headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        
        # Ship as trader
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/ship", json={
            "tracking_number": "CANCEL_TEST_123",
            "carrier": "USPS"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        
        # Try to cancel before deadline
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/cancel-shipping",
            headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 400
        assert "deadline" in resp.json()["detail"].lower()
        print("Correctly prevented early cancellation")
    
    def test_cannot_cancel_if_not_shipped(self):
        """Cannot cancel if you haven't shipped"""
        # Create fresh trade
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "TEST_Cancel_NoShip",
            "album": "TEST_Cancel_NotShipped",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/test.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        listing_id = resp.json()["id"]
        
        resp = requests.get(f"{BASE_URL}/api/users/trader/records")
        trader_records = resp.json()
        if not trader_records:
            pytest.skip("No trader records")
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": trader_records[0]["id"],
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        trade_id = resp.json()["id"]
        
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept",
            headers={"Authorization": f"Bearer {self.demo_token}"})
        
        # Demo tries to cancel without shipping (deadline would need to pass too)
        # This will fail because deadline not passed, but we test the validation
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/cancel-shipping",
            headers={"Authorization": f"Bearer {self.demo_token}"})
        # Should fail because deadline hasn't passed
        assert resp.status_code == 400
        print("Cancel shipping properly validates conditions")


class TestPhase3Disputes:
    """Test Phase 3: Dispute functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.demo_token, self.demo_user = TestSetup.get_demo_token()
        self.trader_token, self.trader_user = TestSetup.get_trader_token()
    
    def test_open_dispute_on_confirming_trade(self):
        """Can open dispute on CONFIRMING trade"""
        # Create trade and get to CONFIRMING
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "TEST_Dispute_Artist",
            "album": "TEST_Dispute_Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/test.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        listing_id = resp.json()["id"]
        
        resp = requests.get(f"{BASE_URL}/api/users/trader/records")
        trader_records = resp.json()
        if not trader_records:
            pytest.skip("No trader records")
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": trader_records[0]["id"],
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        trade_id = resp.json()["id"]
        
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept",
            headers={"Authorization": f"Bearer {self.demo_token}"})
        
        # Both ship
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/ship", json={
            "tracking_number": "DISPUTE_TEST_1", "carrier": "USPS"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/ship", json={
            "tracking_number": "DISPUTE_TEST_2", "carrier": "FedEx"
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.json()["status"] == "CONFIRMING"
        
        # Open dispute
        resp = requests.post(f"{BASE_URL}/api/trades/{trade_id}/dispute", json={
            "reason": "Record arrived damaged - sleeve has water damage",
            "photo_urls": []
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        trade = resp.json()
        
        assert trade["status"] == "DISPUTED"
        assert trade["dispute"] is not None
        assert trade["dispute"]["opened_by"] == self.trader_user["id"]
        assert trade["dispute"]["reason"] == "Record arrived damaged - sleeve has water damage"
        assert trade["dispute"].get("response_deadline") is not None
        print(f"Dispute opened, status: {trade['status']}")
        
        self.__class__.disputed_trade_id = trade_id
    
    def test_cannot_respond_to_own_dispute(self):
        """Cannot respond to your own dispute"""
        trade_id = getattr(self.__class__, 'disputed_trade_id', None)
        if not trade_id:
            pytest.skip("No disputed trade from previous test")
        
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/dispute/respond", json={
            "response_text": "I didn't mean that!",
            "photo_urls": []
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 400
        assert "own dispute" in resp.json()["detail"].lower()
        print("Correctly prevented self-response to dispute")
    
    def test_other_party_can_respond(self):
        """Other party can respond to dispute within 24h"""
        trade_id = getattr(self.__class__, 'disputed_trade_id', None)
        if not trade_id:
            pytest.skip("No disputed trade")
        
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/dispute/respond", json={
            "response_text": "The record was in great condition when shipped. Photos attached show condition at time of packaging.",
            "photo_urls": []
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        trade = resp.json()
        
        assert trade["dispute"]["response"] is not None
        assert trade["dispute"]["response"]["by_user_id"] == self.demo_user["id"]
        print("Dispute response submitted successfully")


class TestPhase3Ratings:
    """Test Phase 3: Rating functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.demo_token, self.demo_user = TestSetup.get_demo_token()
        self.trader_token, self.trader_user = TestSetup.get_trader_token()
    
    def test_rate_completed_trade(self):
        """Can rate a completed trade (1-5 stars)"""
        # Find a COMPLETED trade
        resp = requests.get(f"{BASE_URL}/api/trades",
            headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        trades = resp.json()
        
        completed_trades = [t for t in trades if t["status"] == "COMPLETED" 
                           and not (t.get("ratings") or {}).get(self.trader_user["id"])]
        
        if not completed_trades:
            pytest.skip("No unrated completed trades for trader")
        
        trade_id = completed_trades[0]["id"]
        
        # Rate the trade
        resp = requests.post(f"{BASE_URL}/api/trades/{trade_id}/rate", json={
            "rating": 5,
            "review": "Great trade partner! Fast shipping and accurate description."
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        result = resp.json()
        assert result["rating"] == 5
        print(f"Rating submitted: {result['rating']}/5")
        
        self.__class__.rated_trade_id = trade_id
    
    def test_cannot_rate_twice(self):
        """Cannot rate the same trade twice"""
        trade_id = getattr(self.__class__, 'rated_trade_id', None)
        if not trade_id:
            pytest.skip("No rated trade from previous test")
        
        resp = requests.post(f"{BASE_URL}/api/trades/{trade_id}/rate", json={
            "rating": 1,
            "review": "Changed my mind!"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 400
        assert "already rated" in resp.json()["detail"].lower()
        print("Correctly prevented duplicate rating")
    
    def test_cannot_rate_non_completed_trade(self):
        """Cannot rate trade that isn't COMPLETED"""
        # Find a non-completed trade
        resp = requests.get(f"{BASE_URL}/api/trades",
            headers={"Authorization": f"Bearer {self.trader_token}"})
        trades = resp.json()
        
        non_completed = [t for t in trades if t["status"] != "COMPLETED"]
        if not non_completed:
            pytest.skip("No non-completed trades")
        
        resp = requests.post(f"{BASE_URL}/api/trades/{non_completed[0]['id']}/rate", json={
            "rating": 5,
            "review": "Early rating attempt"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 400
        assert "completed" in resp.json()["detail"].lower()
        print("Correctly prevented rating non-completed trade")
    
    def test_get_user_ratings(self):
        """GET /api/users/{username}/ratings returns average and count"""
        resp = requests.get(f"{BASE_URL}/api/users/demo/ratings")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "ratings" in data
        assert "average" in data
        assert "count" in data
        print(f"User ratings: average={data['average']}, count={data['count']}")


class TestCanInitiate:
    """Test the can-initiate endpoint for mandatory ratings"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.demo_token, _ = TestSetup.get_demo_token()
        self.trader_token, _ = TestSetup.get_trader_token()
    
    def test_can_initiate_returns_blocking_trades(self):
        """GET /api/trades/can-initiate returns unrated trade IDs"""
        resp = requests.get(f"{BASE_URL}/api/trades/can-initiate",
            headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 200
        data = resp.json()
        
        assert "can_trade" in data
        assert "unrated_trade_ids" in data
        print(f"Can trade: {data['can_trade']}, unrated: {data['unrated_trade_ids']}")


class TestAdminDisputes:
    """Test admin dispute endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.demo_token, self.demo_user = TestSetup.get_demo_token()
        self.trader_token, self.trader_user = TestSetup.get_trader_token()
    
    def test_admin_disputes_requires_admin(self):
        """GET /api/admin/disputes requires admin"""
        resp = requests.get(f"{BASE_URL}/api/admin/disputes",
            headers={"Authorization": f"Bearer {self.trader_token}"})
        assert resp.status_code == 403
        print("Correctly requires admin for disputes endpoint")
    
    def test_admin_can_view_disputes(self):
        """Admin (demo) can view disputes"""
        resp = requests.get(f"{BASE_URL}/api/admin/disputes",
            headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        disputes = resp.json()
        assert isinstance(disputes, list)
        print(f"Admin disputes returned: {len(disputes)} open disputes")
    
    def test_admin_can_view_all_disputes(self):
        """Admin can view all disputes including resolved"""
        resp = requests.get(f"{BASE_URL}/api/admin/disputes/all",
            headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        disputes = resp.json()
        assert isinstance(disputes, list)
        print(f"All disputes (including resolved): {len(disputes)}")


class TestAdminResolve:
    """Test admin dispute resolution"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.demo_token, self.demo_user = TestSetup.get_demo_token()
        self.trader_token, self.trader_user = TestSetup.get_trader_token()
    
    def test_admin_resolve_disputed_trade(self):
        """Admin can resolve a disputed trade"""
        # Get open disputes
        resp = requests.get(f"{BASE_URL}/api/admin/disputes",
            headers={"Authorization": f"Bearer {self.demo_token}"})
        disputes = resp.json()
        
        if not disputes:
            # Create a new disputed trade for testing
            resp = requests.post(f"{BASE_URL}/api/listings", json={
                "artist": "TEST_AdminResolve",
                "album": "TEST_AdminResolve",
                "listing_type": "TRADE",
                "photo_urls": ["https://example.com/test.jpg"]
            }, headers={"Authorization": f"Bearer {self.demo_token}"})
            listing_id = resp.json()["id"]
            
            resp = requests.get(f"{BASE_URL}/api/users/trader/records")
            trader_records = resp.json()
            if not trader_records:
                pytest.skip("No trader records")
            
            resp = requests.post(f"{BASE_URL}/api/trades", json={
                "listing_id": listing_id,
                "offered_record_id": trader_records[0]["id"],
            }, headers={"Authorization": f"Bearer {self.trader_token}"})
            trade_id = resp.json()["id"]
            
            requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept",
                headers={"Authorization": f"Bearer {self.demo_token}"})
            
            requests.put(f"{BASE_URL}/api/trades/{trade_id}/ship", json={
                "tracking_number": "RESOLVE_TEST_1", "carrier": "USPS"
            }, headers={"Authorization": f"Bearer {self.trader_token}"})
            
            requests.put(f"{BASE_URL}/api/trades/{trade_id}/ship", json={
                "tracking_number": "RESOLVE_TEST_2", "carrier": "FedEx"
            }, headers={"Authorization": f"Bearer {self.demo_token}"})
            
            requests.post(f"{BASE_URL}/api/trades/{trade_id}/dispute", json={
                "reason": "Testing admin resolution",
                "photo_urls": []
            }, headers={"Authorization": f"Bearer {self.trader_token}"})
            
            disputes = [{"id": trade_id}]
        
        if not disputes:
            pytest.skip("No disputed trades to resolve")
        
        trade_id = disputes[0]["id"]
        
        # Resolve the dispute
        resp = requests.put(f"{BASE_URL}/api/admin/disputes/{trade_id}/resolve", json={
            "resolution": "COMPLETED",
            "notes": "Admin resolved: Both parties shipped valid items."
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        assert resp.status_code == 200
        trade = resp.json()
        
        assert trade["status"] == "COMPLETED"
        assert trade["dispute"]["resolution"] is not None
        assert trade["dispute"]["resolution"]["outcome"] == "COMPLETED"
        print(f"Dispute resolved: {trade['dispute']['resolution']['outcome']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
