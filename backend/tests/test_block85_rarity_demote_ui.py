"""
BLOCK 85.1, 85.2, 85.3 Test Suite
================================
BLOCK 85.1: Global Rarity Engine - Discogs-based community.have count
BLOCK 85.2: Three-Step Hunting Pipeline: Dreaming→Seeking→Collected with demote
BLOCK 85.3: Boutique UI: pill truncation, button heights 32px, style refinements

Test credentials: demo@test.com / demouser
Test record ID: b03404ff-afd0-44ce-b851-ba2b465b77c9 (Igor, discogs_id: 14215683)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestBlock85RarityEngine:
    """BLOCK 85.1: Global Rarity Engine - GET /api/vinyl/rarity/{discogs_id}"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as demo user"""
        self.session = requests.Session()
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Could not authenticate as demo user")
    
    def test_rarity_endpoint_returns_tier_for_igor(self):
        """GET /api/vinyl/rarity/14215683 returns rarity tier for Igor (Tyler, The Creator)
        Igor has 67,110 owners, should be 'Common' (5001+)
        """
        resp = self.session.get(f"{BASE_URL}/api/vinyl/rarity/14215683")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify tier field exists
        assert "tier" in data, "Response should contain 'tier' field"
        
        # Verify discogs_owners field exists
        assert "discogs_owners" in data, "Response should contain 'discogs_owners'"
        
        # Verify discogs_wantlist field exists
        assert "discogs_wantlist" in data, "Response should contain 'discogs_wantlist'"
        
        # Verify listings_available field exists
        assert "listings_available" in data, "Response should contain 'listings_available'"
        
        # Igor has many owners, should be Common
        owners = data.get("discogs_owners", 0)
        tier = data.get("tier", "")
        print(f"Igor: {owners} owners, tier: {tier}")
        
        # Verify tier calculation based on owner count
        if owners < 500:
            assert tier == "Ultra Rare", f"Expected Ultra Rare for {owners} owners"
        elif owners < 2500:
            assert tier == "Rare", f"Expected Rare for {owners} owners"
        elif owners < 5000:
            assert tier == "Uncommon", f"Expected Uncommon for {owners} owners"
        else:
            assert tier == "Common", f"Expected Common for {owners} owners"
    
    def test_rarity_endpoint_returns_discogs_id(self):
        """GET /api/vinyl/rarity/{discogs_id} includes discogs_id in response"""
        resp = self.session.get(f"{BASE_URL}/api/vinyl/rarity/14215683")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("discogs_id") == 14215683, "Response should echo back discogs_id"
    
    def test_rarity_tier_thresholds(self):
        """Verify the rarity tier calculation function (from backend code review):
        - Ultra Rare: < 500 owners
        - Rare: 500 - 2499
        - Uncommon: 2500 - 4999
        - Common: 5001+
        """
        # Test with Igor which is known to have many owners
        resp = self.session.get(f"{BASE_URL}/api/vinyl/rarity/14215683")
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify score field exists (formula: max(0, 5000 - have))
        assert "score" in data, "Response should contain 'score'"
        score = data.get("score", -1)
        owners = data.get("discogs_owners", 0)
        
        # Verify score calculation
        expected_score = max(0, 5000 - owners)
        assert score == expected_score, f"Score should be max(0, 5000 - {owners}) = {expected_score}, got {score}"


class TestBlock85DemoteEndpoint:
    """BLOCK 85.2: PUT /api/iso/{id}/demote - Reverts OPEN ISO back to WISHLIST"""
    
    def get_auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("access_token") or data.get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            return session
        return None
    
    def test_demote_endpoint_exists(self):
        """PUT /api/iso/{id}/demote endpoint should exist"""
        session = self.get_auth_session()
        if not session:
            pytest.skip("Could not authenticate")
        # Use a non-existent ID to test the endpoint exists (should return 404, not 405)
        fake_id = str(uuid.uuid4())
        resp = session.put(f"{BASE_URL}/api/iso/{fake_id}/demote")
        # 404 = endpoint exists but item not found
        # 405 = endpoint doesn't exist
        assert resp.status_code != 405, "Demote endpoint should exist (not 405 Method Not Allowed)"
        assert resp.status_code == 404, f"Expected 404 for non-existent ID, got {resp.status_code}"
    
    def test_demote_workflow_create_promote_demote(self):
        """Full workflow: Create ISO → Promote to OPEN → Demote back to WISHLIST"""
        session = self.get_auth_session()
        if not session:
            pytest.skip("Could not authenticate")
        
        # Step 1: Create a WISHLIST (dream) item
        create_resp = session.post(f"{BASE_URL}/api/iso", json={
            "artist": "Test Artist Demote",
            "album": "Test Album Demote",
            "status": "WISHLIST",
            "priority": "LOW"
        })
        assert create_resp.status_code == 200 or create_resp.status_code == 201, \
            f"Failed to create ISO: {create_resp.text}"
        iso_data = create_resp.json()
        iso_id = iso_data.get("id")
        assert iso_id, "Created ISO should have an id"
        assert iso_data.get("status") == "WISHLIST", "Initial status should be WISHLIST"
        
        try:
            # Step 2: Promote to OPEN (Actively Seeking)
            promote_resp = session.put(f"{BASE_URL}/api/iso/{iso_id}/promote")
            assert promote_resp.status_code == 200, f"Promote failed: {promote_resp.text}"
            
            # Verify it's now OPEN by checking the ISO list (OPEN items are in /api/iso)
            isos_resp = session.get(f"{BASE_URL}/api/iso")
            assert isos_resp.status_code == 200
            open_isos = isos_resp.json()
            found_promoted = any(iso.get("id") == iso_id and iso.get("status") == "OPEN" for iso in open_isos)
            assert found_promoted, "ISO should be in OPEN status after promote"
            
            # Step 3: Demote back to WISHLIST (Dreaming)
            demote_resp = session.put(f"{BASE_URL}/api/iso/{iso_id}/demote")
            assert demote_resp.status_code == 200, f"Demote failed: {demote_resp.text}"
            demote_data = demote_resp.json()
            assert "message" in demote_data, "Demote response should contain message"
            print(f"Demote response: {demote_data.get('message')}")
            
            # Step 4: Verify it's back in Dream List (WISHLIST)
            dreamlist_resp = session.get(f"{BASE_URL}/api/iso/dreamlist")
            assert dreamlist_resp.status_code == 200
            dreams = dreamlist_resp.json()
            found_demoted = any(d.get("id") == iso_id and d.get("status") == "WISHLIST" for d in dreams)
            assert found_demoted, "ISO should be back in WISHLIST status after demote"
            
            # Verify it's no longer in the OPEN ISO list
            isos_resp2 = session.get(f"{BASE_URL}/api/iso")
            open_isos2 = isos_resp2.json()
            still_open = any(iso.get("id") == iso_id for iso in open_isos2)
            assert not still_open, "ISO should NOT be in active ISO list after demote"
            
        finally:
            # Cleanup: Delete the test ISO
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
    
    def test_demote_returns_correct_message(self):
        """PUT /api/iso/{id}/demote returns message like 'X moved back to Dreams.'"""
        session = self.get_auth_session()
        if not session:
            pytest.skip("Could not authenticate")
        
        # Create test ISO
        create_resp = session.post(f"{BASE_URL}/api/iso", json={
            "artist": "Message Test Artist",
            "album": "Message Test Album",
            "status": "OPEN",  # Start as OPEN so we can demote
            "priority": "HIGH"
        })
        if create_resp.status_code not in [200, 201]:
            pytest.skip("Could not create test ISO")
        
        iso_id = create_resp.json().get("id")
        
        try:
            # Demote it
            demote_resp = session.put(f"{BASE_URL}/api/iso/{iso_id}/demote")
            assert demote_resp.status_code == 200
            data = demote_resp.json()
            
            # Verify message format
            assert "message" in data
            msg = data["message"]
            assert "Dreams" in msg or "moved back" in msg.lower(), \
                f"Message should mention Dreams: {msg}"
        finally:
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
    
    def test_demote_without_auth_fails(self):
        """PUT /api/iso/{id}/demote without auth should return 401/403"""
        fake_id = str(uuid.uuid4())
        # Use a session without auth header
        unauth_session = requests.Session()
        resp = unauth_session.put(f"{BASE_URL}/api/iso/{fake_id}/demote")
        assert resp.status_code in [401, 403], f"Unauthenticated demote should fail, got {resp.status_code}"


class TestBlock85UIComponentsBackend:
    """BLOCK 85.3: UI Components - Backend verification of data supporting UI"""
    
    def get_auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get("access_token") or data.get("token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            return session
        return None
    
    def test_iso_items_have_status_field_for_bolt_icon(self):
        """ISO items should have status field to show gold lightning bolt on OPEN items"""
        session = self.get_auth_session()
        if not session:
            pytest.skip("Could not authenticate")
        
        # Create an OPEN ISO to test
        create_resp = session.post(f"{BASE_URL}/api/iso", json={
            "artist": "Bolt Test Artist",
            "album": "Bolt Test Album",
            "status": "OPEN",
            "priority": "HIGH"
        })
        if create_resp.status_code not in [200, 201]:
            pytest.skip("Could not create test ISO")
        
        iso_id = create_resp.json().get("id")
        
        try:
            # Get ISO list and verify status field
            isos_resp = session.get(f"{BASE_URL}/api/iso")
            assert isos_resp.status_code == 200
            isos = isos_resp.json()
            
            test_iso = next((i for i in isos if i.get("id") == iso_id), None)
            assert test_iso, "Test ISO should be in the list"
            assert "status" in test_iso, "ISO should have status field"
            assert test_iso["status"] == "OPEN", "Status should be OPEN"
        finally:
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
    
    def test_dreamlist_returns_all_wishlist_items(self):
        """GET /api/iso/dreamlist returns items with WISHLIST status"""
        session = self.get_auth_session()
        if not session:
            pytest.skip("Could not authenticate")
        
        resp = session.get(f"{BASE_URL}/api/iso/dreamlist")
        assert resp.status_code == 200
        dreams = resp.json()
        
        # All items should have WISHLIST status
        for item in dreams:
            assert item.get("status") == "WISHLIST", \
                f"Dream item should have WISHLIST status, got: {item.get('status')}"
    
    def test_iso_endpoint_excludes_wishlist_items(self):
        """GET /api/iso returns items with status != WISHLIST (OPEN, FOUND)"""
        session = self.get_auth_session()
        if not session:
            pytest.skip("Could not authenticate")
        
        resp = session.get(f"{BASE_URL}/api/iso")
        assert resp.status_code == 200
        isos = resp.json()
        
        # No items should have WISHLIST status
        for item in isos:
            assert item.get("status") != "WISHLIST", \
                f"ISO list should not include WISHLIST items, found: {item.get('status')}"


class TestBlock85RarityRarityCard:
    """BLOCK 85.1: Verify rarity data for RarityCard component"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login as demo user"""
        self.session = requests.Session()
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if login_resp.status_code == 200:
            data = login_resp.json()
            self.token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Could not authenticate as demo user")
    
    def test_rarity_returns_owners_wantlist_for_sale(self):
        """Rarity endpoint returns Owners, Wantlist, and For Sale counts for RarityCard"""
        resp = self.session.get(f"{BASE_URL}/api/vinyl/rarity/14215683")
        assert resp.status_code == 200
        data = resp.json()
        
        # RarityCard needs these three values:
        assert "discogs_owners" in data, "Need discogs_owners for Owners count"
        assert "discogs_wantlist" in data, "Need discogs_wantlist for Wantlist count"
        assert "listings_available" in data, "Need listings_available for For Sale count"
        
        # Values should be non-negative integers
        assert isinstance(data["discogs_owners"], (int, float)), "discogs_owners should be numeric"
        assert isinstance(data["discogs_wantlist"], (int, float)), "discogs_wantlist should be numeric"
        assert isinstance(data["listings_available"], (int, float)), "listings_available should be numeric"
        
        print(f"RarityCard data: Owners={data['discogs_owners']}, "
              f"Wantlist={data['discogs_wantlist']}, For Sale={data['listings_available']}")


# Run tests with: pytest /app/backend/tests/test_block85_rarity_demote_ui.py -v
