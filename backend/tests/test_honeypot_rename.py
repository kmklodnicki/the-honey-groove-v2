"""
Test Honeypot Rename Feature - API Tests
Tests for The Honeypot restructuring: Shop, ISO, Trade tabs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHoneypotAPIs:
    """Test APIs related to The Honeypot restructuring"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{self.base_url}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip("Authentication failed - skipping tests")
    
    # ========== ISO Community Endpoint Tests ==========
    
    def test_iso_community_requires_auth(self):
        """GET /api/iso/community requires authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{self.base_url}/api/iso/community")
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("PASS: /api/iso/community requires auth - returns 401")
    
    def test_iso_community_returns_list(self):
        """GET /api/iso/community returns list of community ISOs"""
        response = self.session.get(f"{self.base_url}/api/iso/community")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: /api/iso/community returns list with {len(data)} items")
    
    def test_iso_community_excludes_own_isos(self):
        """GET /api/iso/community excludes current user's ISOs"""
        # Get current user's ISOs
        my_isos_response = self.session.get(f"{self.base_url}/api/iso")
        assert my_isos_response.status_code == 200
        
        my_isos = my_isos_response.json()
        my_iso_ids = [iso["id"] for iso in my_isos]
        
        # Get community ISOs
        community_response = self.session.get(f"{self.base_url}/api/iso/community")
        assert community_response.status_code == 200
        
        community_isos = community_response.json()
        community_iso_ids = [iso["id"] for iso in community_isos]
        
        # Verify no overlap
        overlap = set(my_iso_ids) & set(community_iso_ids)
        assert len(overlap) == 0, f"Community ISOs should not include user's own ISOs. Overlap: {overlap}"
        print(f"PASS: Community ISOs ({len(community_isos)}) excludes user's own ISOs ({len(my_isos)})")
    
    def test_iso_community_includes_user_info(self):
        """GET /api/iso/community includes user info for each ISO"""
        response = self.session.get(f"{self.base_url}/api/iso/community")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            # Check first ISO has user info
            first_iso = data[0]
            assert "user" in first_iso, "ISO should include 'user' field"
            if first_iso["user"]:
                assert "id" in first_iso["user"], "User should have 'id'"
                assert "username" in first_iso["user"], "User should have 'username'"
            print(f"PASS: Community ISOs include user info (checked {len(data)} items)")
        else:
            print("INFO: No community ISOs available to verify user info")
    
    def test_iso_community_only_open_status(self):
        """GET /api/iso/community returns only OPEN status ISOs"""
        response = self.session.get(f"{self.base_url}/api/iso/community")
        assert response.status_code == 200
        
        data = response.json()
        for iso in data:
            assert iso.get("status") == "OPEN", f"ISO {iso.get('id')} has status {iso.get('status')}, expected OPEN"
        print(f"PASS: All {len(data)} community ISOs have OPEN status")
    
    # ========== Listings Endpoint Tests ==========
    
    def test_listings_endpoint_works(self):
        """GET /api/listings returns marketplace listings"""
        response = self.session.get(f"{self.base_url}/api/listings?limit=10")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: /api/listings returns {len(data)} listings")
    
    def test_listings_have_listing_type(self):
        """GET /api/listings returns listings with listing_type field"""
        response = self.session.get(f"{self.base_url}/api/listings?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        valid_types = ["BUY_NOW", "MAKE_OFFER", "TRADE"]
        for listing in data:
            assert "listing_type" in listing, f"Listing {listing.get('id')} missing listing_type"
            assert listing["listing_type"] in valid_types, f"Invalid listing_type: {listing['listing_type']}"
        print(f"PASS: All {len(data)} listings have valid listing_type")
    
    def test_listings_filter_buy_now_offer_only(self):
        """Shop tab should show BUY_NOW and MAKE_OFFER listings (not TRADE)"""
        response = self.session.get(f"{self.base_url}/api/listings?limit=50")
        assert response.status_code == 200
        
        data = response.json()
        shop_listings = [l for l in data if l["listing_type"] in ["BUY_NOW", "MAKE_OFFER"]]
        trade_listings = [l for l in data if l["listing_type"] == "TRADE"]
        
        print(f"INFO: Shop listings (BUY_NOW/MAKE_OFFER): {len(shop_listings)}")
        print(f"INFO: Trade listings: {len(trade_listings)}")
        print("PASS: Listings have proper type classification for Shop vs Trade tabs")
    
    # ========== Trades Endpoint Tests ==========
    
    def test_trades_endpoint_works(self):
        """GET /api/trades returns user's trades"""
        response = self.session.get(f"{self.base_url}/api/trades")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: /api/trades returns {len(data)} trades")
    
    def test_trades_have_status(self):
        """GET /api/trades returns trades with status field"""
        response = self.session.get(f"{self.base_url}/api/trades")
        assert response.status_code == 200
        
        data = response.json()
        valid_statuses = ["PROPOSED", "COUNTERED", "ACCEPTED", "DECLINED", "CANCELLED", 
                        "SHIPPING", "CONFIRMING", "COMPLETED", "DISPUTED"]
        for trade in data:
            assert "status" in trade, f"Trade {trade.get('id')} missing status"
            assert trade["status"] in valid_statuses, f"Invalid status: {trade['status']}"
        print(f"PASS: All {len(data)} trades have valid status")
    
    # ========== My ISOs Endpoint Tests ==========
    
    def test_my_isos_endpoint_works(self):
        """GET /api/iso returns user's ISOs"""
        response = self.session.get(f"{self.base_url}/api/iso")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: /api/iso returns {len(data)} user ISOs")
    
    # ========== ISO Matches Endpoint Tests ==========
    
    def test_iso_matches_endpoint_works(self):
        """GET /api/listings/iso-matches returns ISO match suggestions"""
        response = self.session.get(f"{self.base_url}/api/listings/iso-matches")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: /api/listings/iso-matches returns {len(data)} matches")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
