# Test: Listing Detail Modal Backend API
# Tests for GET /api/listings/{listing_id} enriched endpoint
# Verifies: user.rating, user.completed_sales, similar_listings array, on_wantlist boolean

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestListingDetailEndpoint:
    """Tests for GET /api/listings/{listing_id} enriched data"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}

    @pytest.fixture(scope="class")
    def sample_listing(self, auth_headers):
        """Get a sample listing from the shop to test detail endpoint"""
        response = requests.get(f"{BASE_URL}/api/listings", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get listings: {response.text}"
        listings = response.json()
        # Return the first listing or None if no listings
        return listings[0] if listings else None

    def test_listing_detail_returns_200(self, auth_headers, sample_listing):
        """GET /api/listings/{id} returns 200 for valid listing"""
        if not sample_listing:
            pytest.skip("No listings available to test")
        
        response = requests.get(f"{BASE_URL}/api/listings/{sample_listing['id']}", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"SUCCESS: GET /api/listings/{sample_listing['id']} returned 200")

    def test_listing_detail_has_user_object(self, auth_headers, sample_listing):
        """Listing detail includes enriched user object"""
        if not sample_listing:
            pytest.skip("No listings available to test")
        
        response = requests.get(f"{BASE_URL}/api/listings/{sample_listing['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data, "Response missing 'user' field"
        user = data["user"]
        assert user is not None, "User should not be None"
        print(f"SUCCESS: Listing detail has user object: {user.get('username')}")

    def test_listing_detail_user_has_rating(self, auth_headers, sample_listing):
        """User object includes rating (default 5.0)"""
        if not sample_listing:
            pytest.skip("No listings available to test")
        
        response = requests.get(f"{BASE_URL}/api/listings/{sample_listing['id']}", headers=auth_headers)
        data = response.json()
        user = data.get("user", {})
        
        assert "rating" in user, "User object missing 'rating' field"
        assert isinstance(user["rating"], (int, float)), "Rating should be numeric"
        # Rating should be between 0 and 5
        assert 0 <= user["rating"] <= 5, f"Rating {user['rating']} out of valid range 0-5"
        print(f"SUCCESS: User has rating field: {user['rating']}")

    def test_listing_detail_user_has_completed_sales(self, auth_headers, sample_listing):
        """User object includes completed_sales count"""
        if not sample_listing:
            pytest.skip("No listings available to test")
        
        response = requests.get(f"{BASE_URL}/api/listings/{sample_listing['id']}", headers=auth_headers)
        data = response.json()
        user = data.get("user", {})
        
        assert "completed_sales" in user, "User object missing 'completed_sales' field"
        assert isinstance(user["completed_sales"], int), "completed_sales should be integer"
        assert user["completed_sales"] >= 0, "completed_sales should be non-negative"
        print(f"SUCCESS: User has completed_sales: {user['completed_sales']}")

    def test_listing_detail_has_similar_listings(self, auth_headers, sample_listing):
        """Response includes similar_listings array"""
        if not sample_listing:
            pytest.skip("No listings available to test")
        
        response = requests.get(f"{BASE_URL}/api/listings/{sample_listing['id']}", headers=auth_headers)
        data = response.json()
        
        assert "similar_listings" in data, "Response missing 'similar_listings' field"
        assert isinstance(data["similar_listings"], list), "similar_listings should be an array"
        print(f"SUCCESS: Listing has similar_listings array (count: {len(data['similar_listings'])})")
        
        # If there are similar listings, verify they have basic structure
        if data["similar_listings"]:
            similar = data["similar_listings"][0]
            assert "id" in similar, "Similar listing missing 'id'"
            print(f"SUCCESS: Similar listings have valid structure")

    def test_listing_detail_has_on_wantlist(self, auth_headers, sample_listing):
        """Response includes on_wantlist boolean"""
        if not sample_listing:
            pytest.skip("No listings available to test")
        
        response = requests.get(f"{BASE_URL}/api/listings/{sample_listing['id']}", headers=auth_headers)
        data = response.json()
        
        assert "on_wantlist" in data, "Response missing 'on_wantlist' field"
        assert isinstance(data["on_wantlist"], bool), "on_wantlist should be boolean"
        print(f"SUCCESS: Listing has on_wantlist: {data['on_wantlist']}")

    def test_listing_detail_basic_fields(self, auth_headers, sample_listing):
        """Listing detail has all expected basic fields"""
        if not sample_listing:
            pytest.skip("No listings available to test")
        
        response = requests.get(f"{BASE_URL}/api/listings/{sample_listing['id']}", headers=auth_headers)
        data = response.json()
        
        # Required fields
        required_fields = ["id", "artist", "album", "listing_type", "status"]
        for field in required_fields:
            assert field in data, f"Response missing required field '{field}'"
        
        print(f"SUCCESS: Listing has all required fields: {', '.join(required_fields)}")

    def test_listing_detail_nonexistent_returns_404(self, auth_headers):
        """GET /api/listings/{invalid_id} returns 404"""
        response = requests.get(f"{BASE_URL}/api/listings/nonexistent-listing-id-12345", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: Nonexistent listing returns 404")

    def test_listing_detail_without_auth(self, sample_listing):
        """GET /api/listings/{id} works without auth (on_wantlist should be False)"""
        if not sample_listing:
            pytest.skip("No listings available to test")
        
        response = requests.get(f"{BASE_URL}/api/listings/{sample_listing['id']}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # on_wantlist should be False for unauthenticated requests
        assert "on_wantlist" in data, "Response missing on_wantlist field"
        assert data["on_wantlist"] is False, "on_wantlist should be False for unauthenticated user"
        print("SUCCESS: Listing detail works without auth, on_wantlist=False")


class TestListingsListEndpoint:
    """Tests for GET /api/listings (list endpoint)"""

    def test_listings_returns_200(self):
        """GET /api/listings returns 200"""
        response = requests.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert isinstance(response.json(), list), "Response should be a list"
        print(f"SUCCESS: GET /api/listings returns {len(response.json())} listings")

    def test_listings_filter_by_type(self):
        """GET /api/listings?listing_type=X filters correctly"""
        for listing_type in ["BUY_NOW", "MAKE_OFFER", "TRADE"]:
            response = requests.get(f"{BASE_URL}/api/listings?listing_type={listing_type}")
            assert response.status_code == 200
            listings = response.json()
            # All returned listings should have the filtered type
            for listing in listings:
                assert listing.get("listing_type") == listing_type, \
                    f"Expected type {listing_type}, got {listing.get('listing_type')}"
        print("SUCCESS: Listing type filter works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
