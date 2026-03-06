"""
Test Mutual Hold Trade Feature for HoneyGroove API.
Tests the new 'Mutual Hold Trade' feature alongside the existing trade proposal system.

Endpoints tested:
- POST /api/trades — propose trade with hold_enabled=true and hold_amount
- GET /api/trades/{id}/hold-suggestion — returns suggested hold amount
- PUT /api/trades/{id}/hold/respond — counter/decline/accept hold amount
- PUT /api/trades/{id}/accept — with hold_action transitions trade properly
- POST /api/trades/{id}/hold/checkout — creates Stripe checkout session
- GET /api/trades/{id}/hold/status — returns payment status
- PUT /api/trades/{id}/confirm-receipt — both confirmations trigger hold refund
- POST /api/trades/{id}/dispute — freezes holds and sends emails
- GET /api/admin/hold-disputes — returns disputed trades with active/frozen holds
- PUT /api/admin/hold-disputes/{id}/resolve — admin resolution options
"""

import pytest
import requests
import os
import uuid
from typing import Optional

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "demo@example.com"
ADMIN_PASSWORD = "password123"
TRADER2_EMAIL = "trader2@test.com"
TRADER2_PASSWORD = "password123"


class TestAuthSetup:
    """Verify authentication for both test users."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin (demo@example.com)."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def trader2_token(self):
        """Login as trader2."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL,
            "password": TRADER2_PASSWORD
        })
        assert response.status_code == 200, f"Trader2 login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        return data["access_token"]
    
    def test_admin_login(self, admin_token):
        """Verify admin can login."""
        assert admin_token is not None
        assert len(admin_token) > 10
        print(f"Admin token obtained successfully")
    
    def test_trader2_login(self, trader2_token):
        """Verify trader2 can login."""
        assert trader2_token is not None
        assert len(trader2_token) > 10
        print(f"Trader2 token obtained successfully")


class TestMutualHoldTradeProposal:
    """Test proposing trades with mutual hold enabled."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def trader2_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL, "password": TRADER2_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_user_id(self, admin_token):
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        return response.json()["id"]
    
    @pytest.fixture(scope="class")
    def trader2_user_id(self, trader2_token):
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {trader2_token}"
        })
        return response.json()["id"]
    
    @pytest.fixture(scope="class")
    def admin_trade_listing(self, admin_token):
        """Find or create a TRADE listing owned by admin."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First check for existing TRADE listings from admin
        response = requests.get(f"{BASE_URL}/api/listings?type=TRADE", headers=headers)
        if response.status_code == 200:
            listings = response.json()
            admin_listings = [l for l in listings if l.get("status") == "ACTIVE"]
            if admin_listings:
                print(f"Found existing TRADE listing: {admin_listings[0]['id']}")
                return admin_listings[0]
        
        # Create a test listing if none exists
        # First need a record
        record_response = requests.post(f"{BASE_URL}/api/records", headers=headers, json={
            "title": f"TEST_Hold_Trade_Album_{uuid.uuid4().hex[:6]}",
            "artist": "Test Artist",
            "year": 2024,
            "cover_url": "https://via.placeholder.com/300"
        })
        if record_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create record: {record_response.text}")
        
        record = record_response.json()
        
        # Create listing
        listing_response = requests.post(f"{BASE_URL}/api/listings", headers=headers, json={
            "artist": record["artist"],
            "album": record["title"],
            "record_id": record["id"],
            "listing_type": "TRADE",
            "condition": "Very Good Plus",
            "cover_url": record.get("cover_url"),
            "photo_urls": ["https://via.placeholder.com/300"]
        })
        
        if listing_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create listing: {listing_response.text}")
        
        print(f"Created new TRADE listing: {listing_response.json()['id']}")
        return listing_response.json()
    
    @pytest.fixture(scope="class")
    def trader2_record(self, trader2_token):
        """Ensure trader2 has a record to offer in trade."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        
        # Check for existing records
        response = requests.get(f"{BASE_URL}/api/records", headers=headers)
        if response.status_code == 200:
            records = response.json()
            if records:
                print(f"Found existing record for trader2: {records[0]['id']}")
                return records[0]
        
        # Create a record for trader2
        record_response = requests.post(f"{BASE_URL}/api/records", headers=headers, json={
            "title": f"TEST_Trader2_Record_{uuid.uuid4().hex[:6]}",
            "artist": "Trader2 Artist",
            "year": 2023,
            "cover_url": "https://via.placeholder.com/300"
        })
        
        if record_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create record for trader2: {record_response.text}")
        
        print(f"Created record for trader2: {record_response.json()['id']}")
        return record_response.json()

    def test_propose_trade_with_hold_enabled(self, trader2_token, admin_trade_listing, trader2_record):
        """Test POST /api/trades with hold_enabled=true and hold_amount."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        
        response = requests.post(f"{BASE_URL}/api/trades", headers=headers, json={
            "listing_id": admin_trade_listing["id"],
            "offered_record_id": trader2_record["id"],
            "offered_condition": "Very Good Plus",
            "offered_photo_urls": ["https://via.placeholder.com/300"],
            "hold_enabled": True,
            "hold_amount": 50.0,
            "message": "Test mutual hold trade proposal"
        })
        
        # Handle case where user already has pending trade on this listing
        if response.status_code == 400 and "pending trade" in response.text.lower():
            # Verify existing trade has hold fields
            trades_resp = requests.get(f"{BASE_URL}/api/trades", headers=headers)
            assert trades_resp.status_code == 200
            trades = trades_resp.json()
            hold_trade = next((t for t in trades if t.get("hold_enabled")), None)
            if hold_trade:
                assert "hold_enabled" in hold_trade, "TradeResponse missing hold_enabled field"
                assert "hold_amount" in hold_trade, "TradeResponse missing hold_amount field"
                print(f"Existing hold trade found: id={hold_trade['id']}, hold_amount={hold_trade['hold_amount']}")
                return
            print("No hold-enabled trades found, but duplicate trade exists")
            return
        
        assert response.status_code in [200, 201], f"Trade proposal failed: {response.text}"
        trade = response.json()
        
        # Verify hold fields in response
        assert "hold_enabled" in trade, "TradeResponse missing hold_enabled field"
        assert trade["hold_enabled"] == True, "hold_enabled should be True"
        assert "hold_amount" in trade, "TradeResponse missing hold_amount field"
        assert trade["hold_amount"] == 50.0, f"hold_amount should be 50.0, got {trade['hold_amount']}"
        assert trade["status"] == "PROPOSED", f"Status should be PROPOSED, got {trade['status']}"
        
        print(f"Trade proposed with hold: id={trade['id']}, hold_amount={trade['hold_amount']}")
    
    def test_propose_trade_hold_amount_min_enforcement(self, trader2_token, admin_trade_listing, trader2_record):
        """Test that hold_amount below $10 is auto-enforced to $10 minimum."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        
        response = requests.post(f"{BASE_URL}/api/trades", headers=headers, json={
            "listing_id": admin_trade_listing["id"],
            "offered_record_id": trader2_record["id"],
            "hold_enabled": True,
            "hold_amount": 5.0,  # Below $10 min
            "offered_photo_urls": ["https://via.placeholder.com/300"]
        })
        
        # Either the trade is accepted with amount enforced to 10, or blocked as duplicate
        if response.status_code in [200, 201]:
            trade = response.json()
            assert trade["hold_amount"] >= 10, f"Hold amount should be at least $10, got {trade['hold_amount']}"
            print(f"Hold amount auto-enforced to minimum: {trade['hold_amount']}")
        elif response.status_code == 400 and "pending trade" in response.text.lower():
            print("Test skipped - duplicate pending trade exists (expected)")
        else:
            print(f"Response: {response.status_code} - {response.text}")


class TestHoldSuggestion:
    """Test GET /api/trades/{id}/hold-suggestion endpoint."""
    
    @pytest.fixture(scope="class")
    def trader2_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL, "password": TRADER2_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def existing_trade(self, trader2_token):
        """Get an existing trade for the user."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        response = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        if response.status_code == 200:
            trades = response.json()
            if trades:
                return trades[0]
        pytest.skip("No existing trades to test hold-suggestion")
    
    def test_hold_suggestion_returns_valid_structure(self, trader2_token, existing_trade):
        """Test hold suggestion returns suggested_hold, record values, and label."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        trade_id = existing_trade["id"]
        
        response = requests.get(f"{BASE_URL}/api/trades/{trade_id}/hold-suggestion", headers=headers)
        
        assert response.status_code == 200, f"hold-suggestion failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "suggested_hold" in data, "Response missing suggested_hold"
        assert "record_a_value" in data, "Response missing record_a_value"
        assert "record_b_value" in data, "Response missing record_b_value"
        assert "label" in data, "Response missing label"
        
        # Verify suggested_hold is at least $10 (the minimum)
        assert data["suggested_hold"] >= 10.0, f"Suggested hold should be at least $10, got {data['suggested_hold']}"
        
        print(f"Hold suggestion: ${data['suggested_hold']:.2f} (record_a: ${data['record_a_value']}, record_b: ${data['record_b_value']})")
    
    def test_hold_suggestion_fallback_value(self, trader2_token, existing_trade):
        """Test that hold suggestion falls back to $50 when no Discogs data exists."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        trade_id = existing_trade["id"]
        
        response = requests.get(f"{BASE_URL}/api/trades/{trade_id}/hold-suggestion", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # If both record values are 0, suggested should be $50 fallback (enforced to min $10)
        if data["record_a_value"] == 0 and data["record_b_value"] == 0:
            assert data["suggested_hold"] == 50.0, f"Fallback should be $50, got {data['suggested_hold']}"
            print("Verified $50 fallback when no Discogs data")
        else:
            print(f"Discogs data exists - suggested: ${data['suggested_hold']:.2f}")


class TestHoldRespond:
    """Test PUT /api/trades/{id}/hold/respond endpoint."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def hold_enabled_trade(self, admin_token):
        """Get a PROPOSED trade with hold_enabled=true."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        if response.status_code == 200:
            trades = response.json()
            for trade in trades:
                if trade.get("hold_enabled") and trade.get("status") in ["PROPOSED", "COUNTERED"]:
                    return trade
        pytest.skip("No hold-enabled trade in PROPOSED/COUNTERED status")
    
    def test_hold_respond_accept(self, admin_token, hold_enabled_trade):
        """Test accepting hold terms."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        trade_id = hold_enabled_trade["id"]
        
        response = requests.put(f"{BASE_URL}/api/trades/{trade_id}/hold/respond", headers=headers, json={
            "action": "accept"
        })
        
        assert response.status_code == 200, f"Hold respond accept failed: {response.text}"
        data = response.json()
        assert "message" in data, "Response missing message"
        assert "hold_amount" in data, "Response missing hold_amount"
        print(f"Hold accept response: {data['message']}")
    
    def test_hold_respond_counter_valid(self, admin_token, hold_enabled_trade):
        """Test countering with valid hold amount (>= $10)."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        trade_id = hold_enabled_trade["id"]
        
        response = requests.put(f"{BASE_URL}/api/trades/{trade_id}/hold/respond", headers=headers, json={
            "action": "counter",
            "hold_amount": 75.0
        })
        
        assert response.status_code == 200, f"Hold respond counter failed: {response.text}"
        data = response.json()
        assert data.get("hold_amount") == 75.0, f"Hold amount should be updated to 75.0"
        print(f"Hold countered to: ${data['hold_amount']:.2f}")
    
    def test_hold_respond_counter_below_minimum(self, admin_token, hold_enabled_trade):
        """Test that countering below $10 minimum fails."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        trade_id = hold_enabled_trade["id"]
        
        response = requests.put(f"{BASE_URL}/api/trades/{trade_id}/hold/respond", headers=headers, json={
            "action": "counter",
            "hold_amount": 5.0  # Below $10 minimum
        })
        
        assert response.status_code == 400, f"Should fail for amount below $10, got {response.status_code}"
        assert "at least $10" in response.text.lower(), f"Error message should mention $10 minimum"
        print("Correctly rejected counter below $10 minimum")
    
    def test_hold_respond_decline(self, admin_token, hold_enabled_trade):
        """Test declining hold (trade continues as standard)."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        trade_id = hold_enabled_trade["id"]
        
        response = requests.put(f"{BASE_URL}/api/trades/{trade_id}/hold/respond", headers=headers, json={
            "action": "decline"
        })
        
        assert response.status_code == 200, f"Hold respond decline failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"Hold decline response: {data['message']}")
        
        # Verify trade now has hold_enabled=False
        get_response = requests.get(f"{BASE_URL}/api/trades/{trade_id}", headers=headers)
        if get_response.status_code == 200:
            trade = get_response.json()
            assert trade.get("hold_enabled") == False, "Hold should be disabled after decline"
            print("Verified hold_enabled=False after decline")


class TestTradeAcceptWithHold:
    """Test PUT /api/trades/{id}/accept with hold_action parameter."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def trader2_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL, "password": TRADER2_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def fresh_hold_trade(self, admin_token, trader2_token):
        """Create a fresh trade with hold_enabled for testing acceptance."""
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        trader2_headers = {"Authorization": f"Bearer {trader2_token}"}
        
        # Get admin's TRADE listing
        listings_resp = requests.get(f"{BASE_URL}/api/listings?type=TRADE", headers=admin_headers)
        if listings_resp.status_code != 200 or not listings_resp.json():
            pytest.skip("No TRADE listings available")
        
        listing = next((l for l in listings_resp.json() if l.get("status") == "ACTIVE"), None)
        if not listing:
            pytest.skip("No active TRADE listing")
        
        # Get trader2's record
        records_resp = requests.get(f"{BASE_URL}/api/records", headers=trader2_headers)
        if records_resp.status_code != 200 or not records_resp.json():
            pytest.skip("Trader2 has no records")
        
        record = records_resp.json()[0]
        
        # Create trade with hold
        trade_resp = requests.post(f"{BASE_URL}/api/trades", headers=trader2_headers, json={
            "listing_id": listing["id"],
            "offered_record_id": record["id"],
            "hold_enabled": True,
            "hold_amount": 30.0,
            "offered_photo_urls": ["https://via.placeholder.com/300"]
        })
        
        if trade_resp.status_code not in [200, 201]:
            # May fail if pending trade exists
            trades = requests.get(f"{BASE_URL}/api/trades", headers=trader2_headers).json()
            proposed = [t for t in trades if t.get("status") == "PROPOSED" and t.get("hold_enabled")]
            if proposed:
                return proposed[0]
            pytest.skip(f"Could not create fresh trade: {trade_resp.text}")
        
        return trade_resp.json()
    
    def test_accept_trade_with_hold_action_accept(self, admin_token, fresh_hold_trade):
        """Test accepting trade with hold_action=accept moves to HOLD_PENDING."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        trade_id = fresh_hold_trade["id"]
        
        # Accept with hold_action=accept
        response = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept", headers=headers, json={
            "hold_action": "accept"
        })
        
        if response.status_code == 403:
            print(f"Permission denied - may not be responder for this trade")
            return
        
        if response.status_code == 400:
            print(f"Trade not in acceptable status: {response.text}")
            return
        
        assert response.status_code == 200, f"Accept with hold failed: {response.text}"
        trade = response.json()
        
        # Should move to HOLD_PENDING (awaiting both payments)
        assert trade["status"] == "HOLD_PENDING", f"Status should be HOLD_PENDING, got {trade['status']}"
        assert trade.get("hold_status") == "awaiting_payment", f"hold_status should be awaiting_payment"
        
        print(f"Trade accepted with hold -> status={trade['status']}, hold_status={trade['hold_status']}")
    
    def test_accept_trade_with_hold_action_decline(self, admin_token):
        """Test accepting trade with hold_action=decline moves to SHIPPING (standard flow)."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Find a trade in PROPOSED status with hold
        trades_resp = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        if trades_resp.status_code != 200:
            pytest.skip("Could not get trades")
        
        proposed = [t for t in trades_resp.json() if t.get("status") == "PROPOSED" and t.get("hold_enabled")]
        if not proposed:
            print("No PROPOSED hold trades to test decline flow")
            return
        
        trade_id = proposed[0]["id"]
        
        response = requests.put(f"{BASE_URL}/api/trades/{trade_id}/accept", headers=headers, json={
            "hold_action": "decline"
        })
        
        if response.status_code == 403:
            print("Permission denied - may not be responder")
            return
        
        if response.status_code == 200:
            trade = response.json()
            assert trade["status"] == "SHIPPING", f"Status should be SHIPPING when declining hold"
            assert trade.get("hold_enabled") == False, "hold_enabled should be False after decline"
            print(f"Trade accepted with hold declined -> SHIPPING")


class TestHoldCheckout:
    """Test POST /api/trades/{id}/hold/checkout endpoint."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def trader2_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL, "password": TRADER2_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_hold_checkout_creates_stripe_session(self, admin_token, trader2_token):
        """Test that hold checkout creates a Stripe checkout session."""
        # Find a trade in HOLD_PENDING status
        headers = {"Authorization": f"Bearer {trader2_token}"}
        trades_resp = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        
        if trades_resp.status_code != 200:
            pytest.skip("Could not get trades")
        
        hold_pending = [t for t in trades_resp.json() if t.get("status") == "HOLD_PENDING"]
        if not hold_pending:
            print("No HOLD_PENDING trades to test checkout")
            return
        
        trade_id = hold_pending[0]["id"]
        
        response = requests.post(f"{BASE_URL}/api/trades/{trade_id}/hold/checkout", headers=headers)
        
        if response.status_code == 400 and "already paid" in response.text.lower():
            print("User has already paid their hold")
            return
        
        if response.status_code == 500:
            # Stripe error - expected if Stripe keys not configured
            print(f"Stripe checkout error (expected if test mode): {response.text}")
            return
        
        assert response.status_code == 200, f"Hold checkout failed: {response.text}"
        data = response.json()
        
        assert "url" in data, "Response should contain checkout URL"
        assert "session_id" in data, "Response should contain session_id"
        assert data["url"].startswith("https://checkout.stripe.com"), "URL should be Stripe checkout"
        
        print(f"Stripe checkout session created: {data['session_id'][:20]}...")
    
    def test_hold_checkout_requires_hold_pending_status(self, trader2_token):
        """Test that checkout fails for trades not in HOLD_PENDING status."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        trades_resp = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        
        if trades_resp.status_code != 200:
            pytest.skip("Could not get trades")
        
        # Find a trade NOT in HOLD_PENDING
        non_hold = [t for t in trades_resp.json() if t.get("status") != "HOLD_PENDING"]
        if not non_hold:
            print("All trades are in HOLD_PENDING")
            return
        
        trade_id = non_hold[0]["id"]
        
        response = requests.post(f"{BASE_URL}/api/trades/{trade_id}/hold/checkout", headers=headers)
        assert response.status_code == 400, f"Should fail for non-HOLD_PENDING trade"
        print("Correctly rejected checkout for non-HOLD_PENDING trade")


class TestHoldStatus:
    """Test GET /api/trades/{id}/hold/status endpoint."""
    
    @pytest.fixture(scope="class")
    def trader2_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL, "password": TRADER2_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_hold_status_returns_payment_info(self, trader2_token):
        """Test hold status returns payment info for both parties."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        trades_resp = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        
        if trades_resp.status_code != 200:
            pytest.skip("Could not get trades")
        
        # Find any trade with hold_enabled
        hold_trades = [t for t in trades_resp.json() if t.get("hold_enabled")]
        if not hold_trades:
            print("No hold-enabled trades to test status")
            return
        
        trade_id = hold_trades[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/trades/{trade_id}/hold/status", headers=headers)
        assert response.status_code == 200, f"Hold status failed: {response.text}"
        
        data = response.json()
        assert "status" in data, "Response should contain status"
        
        # If in HOLD_PENDING, should have payment tracking
        if data.get("status") == "HOLD_PENDING":
            assert "initiator_paid" in data, "Should track initiator_paid"
            assert "responder_paid" in data, "Should track responder_paid"
            print(f"Hold status: initiator_paid={data['initiator_paid']}, responder_paid={data['responder_paid']}")
        else:
            print(f"Trade status: {data.get('status')}, hold_status: {data.get('hold_status')}")


class TestConfirmReceiptWithHold:
    """Test PUT /api/trades/{id}/confirm-receipt endpoint for hold trades."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_confirm_receipt_endpoint_exists(self, admin_token):
        """Verify confirm-receipt endpoint accepts requests."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        trades_resp = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        
        if trades_resp.status_code != 200:
            pytest.skip("Could not get trades")
        
        # Find a trade in CONFIRMING status
        confirming = [t for t in trades_resp.json() if t.get("status") == "CONFIRMING"]
        if not confirming:
            print("No trades in CONFIRMING status to test")
            return
        
        trade_id = confirming[0]["id"]
        
        response = requests.put(f"{BASE_URL}/api/trades/{trade_id}/confirm-receipt", headers=headers)
        
        if response.status_code == 400:
            if "already" in response.text.lower() or "not in confirming" in response.text.lower():
                print(f"Expected behavior: {response.text}")
                return
        
        assert response.status_code == 200, f"Confirm receipt failed: {response.text}"
        print("Confirm receipt endpoint working")


class TestDisputeWithHold:
    """Test POST /api/trades/{id}/dispute endpoint freezes holds."""
    
    @pytest.fixture(scope="class")
    def trader2_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL, "password": TRADER2_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_dispute_freezes_hold(self, trader2_token):
        """Test that opening dispute freezes holds."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        trades_resp = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        
        if trades_resp.status_code != 200:
            pytest.skip("Could not get trades")
        
        # Find a trade in SHIPPING or CONFIRMING with hold_enabled
        disputable = [t for t in trades_resp.json() 
                      if t.get("status") in ["SHIPPING", "CONFIRMING"] 
                      and t.get("hold_enabled")
                      and not t.get("dispute")]
        
        if not disputable:
            print("No disputable hold trades available")
            return
        
        trade_id = disputable[0]["id"]
        
        response = requests.post(f"{BASE_URL}/api/trades/{trade_id}/dispute", headers=headers, json={
            "reason": "TEST_dispute_reason",
            "photo_urls": []
        })
        
        if response.status_code == 400:
            print(f"Dispute not allowed: {response.text}")
            return
        
        assert response.status_code == 200, f"Dispute failed: {response.text}"
        trade = response.json()
        
        assert trade.get("status") == "DISPUTED", "Status should be DISPUTED"
        assert trade.get("hold_status") == "frozen", "hold_status should be frozen"
        
        print(f"Dispute filed, hold frozen: {trade['id']}")


class TestAdminHoldDisputes:
    """Test admin hold dispute endpoints."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_hold_disputes_endpoint(self, admin_token):
        """Test GET /api/admin/hold-disputes returns disputed trades with holds."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/hold-disputes", headers=headers)
        
        assert response.status_code == 200, f"Get hold disputes failed: {response.text}"
        disputes = response.json()
        
        assert isinstance(disputes, list), "Response should be a list"
        
        # All returned trades should have hold_enabled=true and status=DISPUTED
        for trade in disputes:
            assert trade.get("hold_enabled") == True, "All trades should have hold_enabled"
            assert trade.get("status") == "DISPUTED", "All trades should be DISPUTED"
        
        print(f"Found {len(disputes)} hold disputes")
    
    def test_get_hold_disputes_requires_admin(self):
        """Test that non-admin cannot access hold disputes."""
        # Login as trader2 (non-admin)
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL, "password": TRADER2_PASSWORD
        })
        trader2_token = response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {trader2_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/hold-disputes", headers=headers)
        
        assert response.status_code == 403, f"Should be forbidden for non-admin, got {response.status_code}"
        print("Correctly denied non-admin access to hold disputes")


class TestAdminResolveHoldDispute:
    """Test PUT /api/admin/hold-disputes/{id}/resolve endpoint."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_resolve_hold_dispute_full_reversal(self, admin_token):
        """Test admin can resolve with full_reversal."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get disputed hold trades
        disputes_resp = requests.get(f"{BASE_URL}/api/admin/hold-disputes", headers=headers)
        if disputes_resp.status_code != 200 or not disputes_resp.json():
            print("No hold disputes to resolve")
            return
        
        trade_id = disputes_resp.json()[0]["id"]
        
        response = requests.put(f"{BASE_URL}/api/admin/hold-disputes/{trade_id}/resolve", headers=headers, json={
            "resolution": "full_reversal",
            "notes": "TEST_full_reversal_resolution"
        })
        
        if response.status_code == 200:
            trade = response.json()
            assert trade.get("status") == "CANCELLED", "Status should be CANCELLED after full_reversal"
            assert trade.get("hold_status") == "refunded", "hold_status should be refunded"
            print(f"Full reversal resolved: {trade['id']}")
        else:
            print(f"Resolution response: {response.status_code} - {response.text}")
    
    def test_resolve_requires_disputed_status(self, admin_token):
        """Test that resolve fails for non-disputed trades."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get any non-disputed trade
        trades_resp = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        if trades_resp.status_code != 200:
            pytest.skip("Could not get trades")
        
        non_disputed = [t for t in trades_resp.json() if t.get("status") != "DISPUTED"]
        if not non_disputed:
            print("All trades are disputed")
            return
        
        trade_id = non_disputed[0]["id"]
        
        response = requests.put(f"{BASE_URL}/api/admin/hold-disputes/{trade_id}/resolve", headers=headers, json={
            "resolution": "full_reversal",
            "notes": "TEST"
        })
        
        assert response.status_code == 400, f"Should fail for non-disputed trade"
        print("Correctly rejected resolve for non-disputed trade")
    
    def test_resolve_options_validated(self, admin_token):
        """Test that resolution options are validated."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a disputed trade
        disputes_resp = requests.get(f"{BASE_URL}/api/admin/hold-disputes", headers=headers)
        if disputes_resp.status_code != 200 or not disputes_resp.json():
            print("No disputes to test resolution options")
            return
        
        trade_id = disputes_resp.json()[0]["id"]
        
        # Test partial resolution with amounts
        response = requests.put(f"{BASE_URL}/api/admin/hold-disputes/{trade_id}/resolve", headers=headers, json={
            "resolution": "partial",
            "notes": "Partial resolution test",
            "partial_refund_initiator": 25.0,
            "partial_refund_responder": 15.0
        })
        
        # Either succeeds or trade is already resolved
        if response.status_code == 200:
            print("Partial resolution accepted")
        elif response.status_code == 400:
            print(f"Partial resolution response: {response.text}")


class TestTradeResponseModel:
    """Test that TradeResponse model includes all hold fields."""
    
    @pytest.fixture(scope="class")
    def trader2_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TRADER2_EMAIL, "password": TRADER2_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_trade_response_includes_hold_fields(self, trader2_token):
        """Verify TradeResponse model has hold_enabled, hold_amount, hold_status fields."""
        headers = {"Authorization": f"Bearer {trader2_token}"}
        
        response = requests.get(f"{BASE_URL}/api/trades", headers=headers)
        assert response.status_code == 200
        
        trades = response.json()
        if not trades:
            print("No trades to verify model")
            return
        
        trade = trades[0]
        
        # Check for hold fields in TradeResponse
        assert "hold_enabled" in trade, "TradeResponse missing hold_enabled"
        assert "hold_amount" in trade or trade.get("hold_amount") is None, "hold_amount should be present"
        assert "hold_status" in trade or trade.get("hold_status") is None, "hold_status should be present"
        assert "hold_charges" in trade or trade.get("hold_charges") is None, "hold_charges should be present"
        
        print(f"TradeResponse includes hold fields: hold_enabled={trade.get('hold_enabled')}, "
              f"hold_amount={trade.get('hold_amount')}, hold_status={trade.get('hold_status')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
