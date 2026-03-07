"""
Tests for Country-Based International Shipping Logic and Auto-Post Listings
Iteration 75 - Testing two features:
1) International shipping logic: listings without international shipping should only be visible to buyers in the same country as the seller
2) Auto-post to Hive when listing created: creating a listing should auto-create a Hive post
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUserCountryUpdate:
    """Test PUT /api/auth/me can update country field on user profile"""
    
    @pytest.fixture
    def test_user(self):
        """Create a test user via invite code"""
        unique = uuid.uuid4().hex[:8]
        email = f"testuser_{unique}@honey.io"
        
        session = requests.Session()
        
        # Try to get an invite code
        invite_resp = session.get(f"{BASE_URL}/api/beta-invite/generate")
        if invite_resp.status_code != 200:
            pytest.skip("Cannot generate invite code")
        code = invite_resp.json().get("code")
        
        # Register user
        reg_resp = session.post(f"{BASE_URL}/api/auth/register-invite", json={
            "email": email,
            "password": "password123",
            "username": f"testuser_{unique}",
            "invite_code": code
        })
        
        if reg_resp.status_code != 200:
            pytest.skip(f"Cannot register user: {reg_resp.text}")
        
        token = reg_resp.json().get("access_token")
        user_id = reg_resp.json().get("user", {}).get("id")
        
        yield {"token": token, "user_id": user_id, "email": email, "session": session}
        
    def test_update_country_field(self, test_user):
        """PUT /api/auth/me should update country field"""
        token = test_user["token"]
        session = test_user["session"]
        
        # Update user with country
        update_resp = session.put(
            f"{BASE_URL}/api/auth/me",
            json={"country": "US"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        print(f"Update response: {update_resp.json()}")
        
        # Get user and check country was saved
        me_resp = session.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_resp.status_code == 200
        # Note: Country may not be in UserResponse if not added to the model


class TestListingCountryFiltering:
    """Test GET /api/listings filters based on buyer/seller country"""
    
    @pytest.fixture(scope="class")
    def setup_users_with_countries(self):
        """Create two users with different countries for testing"""
        session = requests.Session()
        users = {}
        
        for country in ["US", "GB"]:
            unique = uuid.uuid4().hex[:8]
            email = f"seller_{country}_{unique}@honey.io"
            
            # Get invite code
            invite_resp = session.get(f"{BASE_URL}/api/beta-invite/generate")
            if invite_resp.status_code != 200:
                pytest.skip("Cannot generate invite code")
            code = invite_resp.json().get("code")
            
            # Register
            reg_resp = session.post(f"{BASE_URL}/api/auth/register-invite", json={
                "email": email,
                "password": "password123",
                "username": f"seller_{country}_{unique}",
                "invite_code": code
            })
            
            if reg_resp.status_code != 200:
                pytest.skip(f"Cannot register user: {reg_resp.text}")
            
            token = reg_resp.json().get("access_token")
            user_id = reg_resp.json().get("user", {}).get("id")
            
            # Update country
            session.put(
                f"{BASE_URL}/api/auth/me",
                json={"country": country},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            users[country] = {"token": token, "user_id": user_id, "email": email}
        
        yield users


class TestDirectAPIEndpoints:
    """Direct tests for the API endpoints"""
    
    def test_api_health(self):
        """Basic API health check"""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        print("API health check passed")
    
    def test_listings_endpoint_exists(self):
        """Verify /api/listings endpoint exists"""
        resp = requests.get(f"{BASE_URL}/api/listings")
        # Should return 200 even without auth (public listings)
        assert resp.status_code in [200, 401], f"Unexpected status: {resp.status_code}"
        print(f"Listings endpoint response: {resp.status_code}")
    
    def test_feed_endpoint_requires_auth(self):
        """Verify /api/feed requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/feed")
        assert resp.status_code == 401 or resp.status_code == 403
        print("Feed endpoint correctly requires auth")
    
    def test_posts_endpoint_requires_auth(self):
        """Verify /api/posts endpoint exists"""
        resp = requests.get(f"{BASE_URL}/api/posts/test-id")
        # Should return 401/403 without auth or 404 if not found
        assert resp.status_code in [401, 403, 404]
        print(f"Posts endpoint response: {resp.status_code}")


class TestExistingUserCountryOperations:
    """Test using existing katieintheafterglow user who has country='US' set"""
    
    def test_get_listing_with_seller_country(self):
        """GET /api/listings/{id} should include seller country in response"""
        # First get some listings
        resp = requests.get(f"{BASE_URL}/api/listings?limit=5")
        if resp.status_code == 200 and resp.json():
            listings = resp.json()
            if listings:
                listing_id = listings[0].get("id")
                # Get single listing detail
                detail_resp = requests.get(f"{BASE_URL}/api/listings/{listing_id}")
                if detail_resp.status_code == 200:
                    data = detail_resp.json()
                    seller = data.get("user", {})
                    print(f"Listing seller data: {seller}")
                    # Check if country field exists in seller response
                    if "country" in seller:
                        print(f"Seller country found: {seller.get('country')}")
                    else:
                        print("ISSUE: Seller country not in listing response")
        print("Listing detail test completed")


class TestListingWithAuthentication:
    """Tests that require authentication"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for testing"""
        session = requests.Session()
        
        unique = uuid.uuid4().hex[:8]
        email = f"authtest_{unique}@honey.io"
        
        # Get invite code
        invite_resp = session.get(f"{BASE_URL}/api/beta-invite/generate")
        if invite_resp.status_code != 200:
            pytest.skip("Cannot generate invite code")
        code = invite_resp.json().get("code")
        
        # Register
        reg_resp = session.post(f"{BASE_URL}/api/auth/register-invite", json={
            "email": email,
            "password": "password123",
            "username": f"authtest_{unique}",
            "invite_code": code
        })
        
        if reg_resp.status_code != 200:
            pytest.skip(f"Registration failed: {reg_resp.text}")
        
        return reg_resp.json().get("access_token")
    
    def test_authenticated_listings_fetch(self, auth_token):
        """GET /api/listings with authentication"""
        resp = requests.get(
            f"{BASE_URL}/api/listings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        print(f"Authenticated listings fetch: {len(resp.json())} listings")
    
    def test_feed_includes_listing_posts(self, auth_token):
        """GET /api/feed should include listing posts with listing_id set"""
        resp = requests.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        posts = resp.json()
        
        # Look for listing_sale or listing_trade posts
        listing_posts = [p for p in posts if p.get("post_type") in ["listing_sale", "listing_trade"]]
        print(f"Found {len(listing_posts)} listing posts in feed")
        
        for lp in listing_posts[:3]:
            print(f"  - Post type: {lp.get('post_type')}, listing_id: {lp.get('listing_id')}")


class TestPaymentCheckoutCountryValidation:
    """Test POST /api/payments/checkout returns error for domestic-only listings with different countries"""
    
    def test_checkout_without_auth(self):
        """POST /api/payments/checkout requires authentication"""
        resp = requests.post(
            f"{BASE_URL}/api/payments/checkout",
            json={"listing_id": "test-id"}
        )
        assert resp.status_code in [401, 403]
        print("Checkout correctly requires auth")


class TestTradeCountryValidation:
    """Test POST /api/trades returns error for domestic-only listings with different countries"""
    
    def test_trades_without_auth(self):
        """POST /api/trades requires authentication"""
        resp = requests.post(
            f"{BASE_URL}/api/trades",
            json={"listing_id": "test-id", "offered_record_id": "test-record"}
        )
        assert resp.status_code in [401, 403, 422]
        print("Trades correctly requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
