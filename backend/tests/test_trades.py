"""
Test suite for Trade System Phase 1
Tests trade status machine: PROPOSED → COUNTERED → ACCEPTED → DECLINED
Tests all trade endpoints and edge cases
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTradeSystem:
    """Trade System Phase 1 Tests"""
    
    demo_token = None
    trader_token = None
    demo_user = None
    trader_user = None
    demo_records = None
    trader_records = None
    trade_listing_id = None
    test_trade_id = None
    
    @classmethod
    def setup_class(cls):
        """Login both test users and get their records"""
        # Login demo user
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        assert resp.status_code == 200, f"Demo login failed: {resp.text}"
        data = resp.json()
        cls.demo_token = data["access_token"]
        cls.demo_user = data["user"]
        
        # Login trader user
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@example.com",
            "password": "password123"
        })
        assert resp.status_code == 200, f"Trader login failed: {resp.text}"
        data = resp.json()
        cls.trader_token = data["access_token"]
        cls.trader_user = data["user"]
        
        # Get demo's records
        resp = requests.get(f"{BASE_URL}/api/users/{cls.demo_user['username']}/records")
        assert resp.status_code == 200
        cls.demo_records = resp.json()
        print(f"Demo user has {len(cls.demo_records)} records")
        
        # Get trader's records
        resp = requests.get(f"{BASE_URL}/api/users/{cls.trader_user['username']}/records")
        assert resp.status_code == 200
        cls.trader_records = resp.json()
        print(f"Trader user has {len(cls.trader_records)} records")
        
        # Find or create a TRADE listing by demo user
        resp = requests.get(f"{BASE_URL}/api/listings/my", headers={
            "Authorization": f"Bearer {cls.demo_token}"
        })
        if resp.status_code == 200:
            demo_listings = resp.json()
            trade_listings = [l for l in demo_listings if l["listing_type"] == "TRADE" and l["status"] == "ACTIVE"]
            if trade_listings:
                cls.trade_listing_id = trade_listings[0]["id"]
                print(f"Found existing TRADE listing: {cls.trade_listing_id}")
                return
        
        # Create a new TRADE listing if none exists
        if cls.demo_records:
            resp = requests.post(f"{BASE_URL}/api/listings", json={
                "artist": "Test Trade Artist",
                "album": "Test Trade Album",
                "listing_type": "TRADE",
                "photo_urls": ["https://example.com/photo.jpg"],
                "condition": "Very Good Plus",
                "description": "Test trade listing"
            }, headers={"Authorization": f"Bearer {cls.demo_token}"})
            if resp.status_code == 200:
                cls.trade_listing_id = resp.json()["id"]
                print(f"Created TRADE listing: {cls.trade_listing_id}")
    
    # ----- POST /api/trades Tests -----
    
    def test_01_propose_trade_requires_listing_id(self):
        """POST /api/trades - requires listing_id"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing trader data")
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        # Should fail validation - missing listing_id
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
        print("PASSED: POST /api/trades requires listing_id")
    
    def test_02_propose_trade_requires_offered_record(self):
        """POST /api/trades - requires offered_record_id"""
        if not self.trader_token or not self.trade_listing_id:
            pytest.skip("Missing test data")
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": self.trade_listing_id
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        # Should fail validation - missing offered_record_id
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
        print("PASSED: POST /api/trades requires offered_record_id")
    
    def test_03_cannot_trade_with_yourself(self):
        """POST /api/trades - cannot trade with yourself"""
        if not self.demo_token or not self.trade_listing_id or not self.demo_records:
            pytest.skip("Missing test data")
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": self.trade_listing_id,
            "offered_record_id": self.demo_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        assert "yourself" in resp.json().get("detail", "").lower()
        print("PASSED: Cannot trade with yourself")
    
    def test_04_cannot_trade_on_non_trade_listing(self):
        """POST /api/trades - cannot trade on non-TRADE listings"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing test data")
        
        # Create a BUY_NOW listing by demo
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "BuyNow Artist",
            "album": "BuyNow Album",
            "listing_type": "BUY_NOW",
            "price": 25.0,
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create BUY_NOW listing")
        
        buy_now_listing_id = resp.json()["id"]
        
        # Try to propose trade on BUY_NOW listing
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": buy_now_listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        assert "not open for trades" in resp.json().get("detail", "").lower()
        print("PASSED: Cannot trade on non-TRADE listing")
    
    def test_05_propose_trade_success(self):
        """POST /api/trades - successfully propose a trade"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing test data")
        
        # Create a new TRADE listing specifically for this test
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Test Propose Artist",
            "album": "Test Propose Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create listing")
        
        new_listing_id = resp.json()["id"]
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": new_listing_id,
            "offered_record_id": self.trader_records[0]["id"],
            "boot_amount": 10.0,
            "boot_direction": "TO_SELLER",
            "message": "Interested in trading!"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        trade = resp.json()
        
        assert trade["status"] == "PROPOSED"
        assert trade["initiator_id"] == self.trader_user["id"]
        assert trade["responder_id"] == self.demo_user["id"]
        assert trade["offered_record_id"] == self.trader_records[0]["id"]
        assert trade["boot_amount"] == 10.0
        assert trade["boot_direction"] == "TO_SELLER"
        assert len(trade.get("messages", [])) == 1
        assert trade["initiator"] is not None
        assert trade["responder"] is not None
        assert trade["offered_record"] is not None
        
        TestTradeSystem.test_trade_id = trade["id"]
        print(f"PASSED: Trade proposed successfully, id={trade['id']}")
    
    def test_06_cannot_have_duplicate_pending_trade(self):
        """POST /api/trades - cannot have duplicate pending trade"""
        if not self.trader_token or not self.trader_records or not self.test_trade_id:
            pytest.skip("Missing test data")
        
        # First get the trade we just created to find the listing ID
        resp = requests.get(f"{BASE_URL}/api/trades/{self.test_trade_id}", headers={
            "Authorization": f"Bearer {self.trader_token}"
        })
        if resp.status_code != 200:
            pytest.skip("Could not get trade details")
        
        listing_id = resp.json()["listing_id"]
        
        # Try to propose another trade on the same listing by the same user
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        assert "pending trade" in resp.json().get("detail", "").lower()
        print("PASSED: Cannot have duplicate pending trade on same listing")
    
    # ----- GET /api/trades Tests -----
    
    def test_07_get_my_trades(self):
        """GET /api/trades - returns user's trades"""
        if not self.trader_token:
            pytest.skip("Missing trader token")
        
        resp = requests.get(f"{BASE_URL}/api/trades", headers={
            "Authorization": f"Bearer {self.trader_token}"
        })
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        trades = resp.json()
        assert isinstance(trades, list)
        
        # Should find the trade we just created
        if self.test_trade_id:
            found = any(t["id"] == self.test_trade_id for t in trades)
            assert found, "Created trade not found in my trades"
        
        print(f"PASSED: GET /api/trades returns {len(trades)} trades for trader")
        
        # Also check demo user can see it as responder
        resp = requests.get(f"{BASE_URL}/api/trades", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })
        assert resp.status_code == 200
        demo_trades = resp.json()
        if self.test_trade_id:
            found = any(t["id"] == self.test_trade_id for t in demo_trades)
            assert found, "Trade not found in demo's trades (as responder)"
        print(f"PASSED: Demo user sees {len(demo_trades)} trades as responder")
    
    def test_08_get_trade_detail(self):
        """GET /api/trades/{id} - returns trade detail with populated data"""
        if not self.test_trade_id or not self.demo_token:
            pytest.skip("Missing test data")
        
        resp = requests.get(f"{BASE_URL}/api/trades/{self.test_trade_id}", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        trade = resp.json()
        
        assert trade["id"] == self.test_trade_id
        assert trade["initiator"] is not None and "username" in trade["initiator"]
        assert trade["responder"] is not None and "username" in trade["responder"]
        assert trade["offered_record"] is not None
        assert trade["listing_record"] is not None or trade["listing"] is not None
        
        print("PASSED: GET /api/trades/{id} returns detailed trade with populated records/users")
    
    # ----- PUT /api/trades/{id}/counter Tests -----
    
    def test_09_counter_trade(self):
        """PUT /api/trades/{id}/counter - responder counters with boot"""
        if not self.test_trade_id or not self.demo_token:
            pytest.skip("Missing test data")
        
        resp = requests.put(f"{BASE_URL}/api/trades/{self.test_trade_id}/counter", json={
            "boot_amount": 20.0,
            "boot_direction": "TO_BUYER",
            "message": "I'd want a little more boot"
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        trade = resp.json()
        
        assert trade["status"] == "COUNTERED"
        assert trade["counter"] is not None
        assert trade["counter"]["boot_amount"] == 20.0
        assert trade["counter"]["boot_direction"] == "TO_BUYER"
        assert len(trade.get("messages", [])) >= 2  # Original + counter message
        
        print("PASSED: Counter trade works - status changed to COUNTERED")
    
    def test_10_counter_with_different_record(self):
        """PUT /api/trades/{id}/counter - counter can request different record"""
        # Create a new trade to test record counter
        if not self.trader_token or not self.trader_records or not self.trade_listing_id:
            pytest.skip("Missing test data")
        
        # First need to decline the existing trade to make room
        if self.test_trade_id:
            requests.put(f"{BASE_URL}/api/trades/{self.test_trade_id}/decline", headers={
                "Authorization": f"Bearer {self.demo_token}"
            })
        
        # Create new TRADE listing
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Counter Test Artist",
            "album": "Counter Test Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create listing")
        
        listing_id = resp.json()["id"]
        
        # Trader proposes
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not propose trade")
        
        trade_id = resp.json()["id"]
        
        # Demo counters requesting a different record from trader's collection
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/counter", json={
            "requested_record_id": self.trader_records[0]["id"],  # Request specific record
            "message": "I want that specific record"
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        trade = resp.json()
        assert trade["status"] == "COUNTERED"
        assert trade["counter"]["record_id"] == self.trader_records[0]["id"]
        
        print("PASSED: Counter with different record works")
        
        # Clean up - decline the trade
        requests.put(f"{BASE_URL}/api/trades/{trade_id}/decline", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })
    
    # ----- PUT /api/trades/{id}/accept Tests -----
    
    def test_11_accept_proposed_trade(self):
        """PUT /api/trades/{id}/accept - responder accepts PROPOSED trade"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing test data")
        
        # Create new listing and trade for accept test
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Accept Test Artist",
            "album": "Accept Test Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create listing")
        
        listing_id = resp.json()["id"]
        
        # Trader proposes
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not propose trade")
        
        trade_id = resp.json()["id"]
        
        # Demo (responder) accepts
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        trade = resp.json()
        assert trade["status"] == "ACCEPTED"
        
        print("PASSED: Responder can accept PROPOSED trade")
        
        # Verify listing status changed to IN_TRADE
        resp = requests.get(f"{BASE_URL}/api/listings/{listing_id}")
        if resp.status_code == 200:
            listing = resp.json()
            assert listing.get("status") == "IN_TRADE", f"Expected IN_TRADE, got {listing.get('status')}"
            print("PASSED: Listing status changed to IN_TRADE after accept")
    
    def test_12_accept_countered_trade(self):
        """PUT /api/trades/{id}/accept - initiator accepts COUNTERED trade"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing test data")
        
        # Create new listing
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Counter Accept Test",
            "album": "Counter Accept Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create listing")
        
        listing_id = resp.json()["id"]
        
        # Trader proposes
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not propose trade")
        
        trade_id = resp.json()["id"]
        
        # Demo counters
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/counter", json={
            "boot_amount": 15.0,
            "boot_direction": "TO_SELLER"
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        assert resp.status_code == 200
        
        # Trader (initiator) accepts the counter
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept", headers={
            "Authorization": f"Bearer {self.trader_token}"
        })
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        trade = resp.json()
        assert trade["status"] == "ACCEPTED"
        # Counter terms should be applied
        assert trade["boot_amount"] == 15.0
        assert trade["boot_direction"] == "TO_SELLER"
        
        print("PASSED: Initiator can accept COUNTERED trade, counter terms applied")
    
    # ----- PUT /api/trades/{id}/decline Tests -----
    
    def test_13_decline_trade_by_either_party(self):
        """PUT /api/trades/{id}/decline - either party can decline"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing test data")
        
        # Create listing
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Decline Test",
            "album": "Decline Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create listing")
        
        listing_id = resp.json()["id"]
        
        # Trader proposes
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not propose trade")
        
        trade_id = resp.json()["id"]
        
        # Demo (responder) declines
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/decline", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASSED: Responder can decline trade")
        
        # Create another trade to test initiator decline
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Decline Test 2",
            "album": "Decline Album 2",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        listing_id2 = resp.json()["id"]
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id2,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        trade_id2 = resp.json()["id"]
        
        # Trader (initiator) declines
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id2}/decline", headers={
            "Authorization": f"Bearer {self.trader_token}"
        })
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASSED: Initiator can decline trade")
    
    # ----- GET /api/users/{username}/trades Tests -----
    
    def test_14_profile_trades(self):
        """GET /api/users/{username}/trades - returns ACCEPTED/COMPLETED trades"""
        if not self.demo_user:
            pytest.skip("Missing demo user")
        
        resp = requests.get(f"{BASE_URL}/api/users/{self.demo_user['username']}/trades")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        trades = resp.json()
        assert isinstance(trades, list)
        
        # All returned trades should be in accepted/completed states
        for trade in trades:
            assert trade["status"] in ["ACCEPTED", "COMPLETED", "SHIPPING", "CONFIRMING"], \
                f"Unexpected status {trade['status']} in profile trades"
            # Should have record info
            assert trade.get("offered_record") is not None or trade.get("listing_record") is not None
        
        print(f"PASSED: Profile trades returns {len(trades)} ACCEPTED/COMPLETED trades")
    
    # ----- POST /api/trades/{id}/message Tests -----
    
    def test_15_add_message_to_trade(self):
        """POST /api/trades/{id}/message - add message to trade"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing test data")
        
        # Create a trade to test messaging
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Message Test",
            "album": "Message Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create listing")
        
        listing_id = resp.json()["id"]
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not propose trade")
        
        trade_id = resp.json()["id"]
        initial_messages = len(resp.json().get("messages", []))
        
        # Add message from demo
        resp = requests.post(f"{BASE_URL}/api/trades/{trade_id}/message", json={
            "text": "Hey, great offer!"
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        # Verify message was added
        resp = requests.get(f"{BASE_URL}/api/trades/{trade_id}", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })
        trade = resp.json()
        assert len(trade.get("messages", [])) > initial_messages
        
        # Add message from trader
        resp = requests.post(f"{BASE_URL}/api/trades/{trade_id}/message", json={
            "text": "Thanks for considering!"
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        assert resp.status_code == 200
        print("PASSED: Both parties can add messages to trade")
        
        # Clean up
        requests.put(f"{BASE_URL}/api/trades/{trade_id}/decline", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })


class TestTradePermissions:
    """Test trade action permissions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login users
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        self.demo_token = resp.json()["access_token"] if resp.status_code == 200 else None
        self.demo_user = resp.json()["user"] if resp.status_code == 200 else None
        
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@example.com",
            "password": "password123"
        })
        self.trader_token = resp.json()["access_token"] if resp.status_code == 200 else None
        self.trader_user = resp.json()["user"] if resp.status_code == 200 else None
        
        # Get records
        if self.trader_user:
            resp = requests.get(f"{BASE_URL}/api/users/{self.trader_user['username']}/records")
            self.trader_records = resp.json() if resp.status_code == 200 else []
    
    def test_initiator_cannot_accept_own_proposal(self):
        """Initiator cannot accept their own PROPOSED trade"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing test data")
        
        # Create listing and trade
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Perm Test",
            "album": "Perm Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create listing")
        
        listing_id = resp.json()["id"]
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not propose trade")
        
        trade_id = resp.json()["id"]
        
        # Initiator tries to accept (should fail)
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept", headers={
            "Authorization": f"Bearer {self.trader_token}"
        })
        
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("PASSED: Initiator cannot accept own proposal")
        
        # Clean up
        requests.put(f"{BASE_URL}/api/trades/{trade_id}/decline", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })
    
    def test_responder_cannot_accept_own_counter(self):
        """Responder cannot accept their own counter"""
        if not self.trader_token or not self.trader_records:
            pytest.skip("Missing test data")
        
        # Create listing and trade
        resp = requests.post(f"{BASE_URL}/api/listings", json={
            "artist": "Counter Perm Test",
            "album": "Counter Perm Album",
            "listing_type": "TRADE",
            "photo_urls": ["https://example.com/photo.jpg"]
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not create listing")
        
        listing_id = resp.json()["id"]
        
        resp = requests.post(f"{BASE_URL}/api/trades", json={
            "listing_id": listing_id,
            "offered_record_id": self.trader_records[0]["id"]
        }, headers={"Authorization": f"Bearer {self.trader_token}"})
        
        if resp.status_code != 200:
            pytest.skip("Could not propose trade")
        
        trade_id = resp.json()["id"]
        
        # Demo counters
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/counter", json={
            "boot_amount": 25.0
        }, headers={"Authorization": f"Bearer {self.demo_token}"})
        
        assert resp.status_code == 200
        
        # Demo (responder, who countered) tries to accept own counter (should fail)
        resp = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept", headers={
            "Authorization": f"Bearer {self.demo_token}"
        })
        
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print("PASSED: Responder cannot accept own counter")
        
        # Clean up
        requests.put(f"{BASE_URL}/api/trades/{trade_id}/decline", headers={
            "Authorization": f"Bearer {self.trader_token}"
        })


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
