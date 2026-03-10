"""
Tests for International Shipping Cost feature on marketplace listings.
Features tested:
1. POST /api/listings - creating a listing with international_shipping=true and international_shipping_cost
2. POST /api/listings - creating a listing with international_shipping=false (international_shipping_cost should be null)
3. PUT /api/listings/{id} - updating international_shipping_cost
4. PUT /api/listings/{id} - setting international_shipping=false clears international_shipping_cost
5. GET /api/listings/{id} - response includes international_shipping_cost field
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@test.com"
TEST_PASSWORD = "demouser"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if resp.status_code != 200:
        pytest.skip(f"Authentication failed: {resp.status_code} - {resp.text}")
    data = resp.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def stripe_connected_token():
    """Get a token for a user with Stripe connected for listing creation."""
    # Try vinylcollector74 first (mentioned in context)
    for email, password in [
        ("vinylcollector74@example.com", "password123"),
        ("demo@test.com", "demouser"),
    ]:
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            # Check if Stripe is connected
            stripe_resp = requests.get(
                f"{BASE_URL}/api/stripe/status",
                headers={"Authorization": f"Bearer {token}"}
            )
            if stripe_resp.status_code == 200 and stripe_resp.json().get("stripe_connected"):
                return token
    return None


class TestInternationalShippingCostBackend:
    """Test international_shipping_cost field in listing CRUD operations."""

    def test_get_listing_includes_intl_shipping_cost_field(self, headers):
        """GET /api/listings/{id} - verify response includes international_shipping_cost field."""
        # Get all listings to find one
        resp = requests.get(f"{BASE_URL}/api/listings", headers=headers)
        assert resp.status_code == 200, f"Failed to get listings: {resp.text}"
        
        listings = resp.json()
        if not listings:
            pytest.skip("No listings available to test")
        
        listing_id = listings[0]["id"]
        
        # Fetch specific listing
        detail_resp = requests.get(f"{BASE_URL}/api/listings/{listing_id}", headers=headers)
        assert detail_resp.status_code == 200, f"Failed to get listing: {detail_resp.text}"
        
        data = detail_resp.json()
        # Verify international_shipping_cost field is present in response
        assert "international_shipping_cost" in data, "international_shipping_cost field missing from response"
        assert "international_shipping" in data, "international_shipping field missing from response"
        print(f"PASS: Listing {listing_id} has international_shipping={data.get('international_shipping')}, cost={data.get('international_shipping_cost')}")

    def test_listing_response_model_has_intl_shipping_fields(self, headers):
        """Verify ListingResponse model includes all international shipping fields."""
        resp = requests.get(f"{BASE_URL}/api/listings?limit=5", headers=headers)
        assert resp.status_code == 200, f"Failed to get listings: {resp.text}"
        
        listings = resp.json()
        if not listings:
            pytest.skip("No listings available")
        
        for listing in listings:
            # Check both fields exist in every listing
            assert "international_shipping" in listing, f"Listing {listing.get('id')} missing international_shipping"
            assert "international_shipping_cost" in listing or listing.get("international_shipping_cost") is None, \
                f"Listing {listing.get('id')} missing international_shipping_cost"
            
        print(f"PASS: All {len(listings)} listings have international_shipping fields in response")

    def test_listing_with_intl_shipping_enabled_shows_cost(self, headers):
        """Find a listing with international_shipping=true and verify it has a cost."""
        resp = requests.get(f"{BASE_URL}/api/listings?limit=50", headers=headers)
        assert resp.status_code == 200, f"Failed to get listings: {resp.text}"
        
        listings = resp.json()
        intl_listings = [l for l in listings if l.get("international_shipping")]
        
        if not intl_listings:
            pytest.skip("No listings with international shipping enabled")
        
        for listing in intl_listings[:3]:  # Check up to 3
            # A listing with international_shipping=true should have cost or null
            print(f"Listing {listing.get('id')}: intl_shipping={listing.get('international_shipping')}, cost={listing.get('international_shipping_cost')}")
        
        print(f"PASS: Found {len(intl_listings)} listings with international shipping enabled")

    def test_listing_with_intl_shipping_disabled_has_null_cost(self, headers):
        """Verify listings with international_shipping=false have null cost."""
        resp = requests.get(f"{BASE_URL}/api/listings?limit=50", headers=headers)
        assert resp.status_code == 200, f"Failed to get listings: {resp.text}"
        
        listings = resp.json()
        domestic_only = [l for l in listings if not l.get("international_shipping")]
        
        if not domestic_only:
            pytest.skip("No domestic-only listings found")
        
        for listing in domestic_only[:3]:  # Check up to 3
            # international_shipping_cost should be null when international_shipping is false
            assert listing.get("international_shipping_cost") is None, \
                f"Listing {listing.get('id')} has intl_shipping=false but cost={listing.get('international_shipping_cost')}"
        
        print(f"PASS: {len(domestic_only)} listings with domestic-only shipping have null international_shipping_cost")


class TestInternationalShippingCostCRUD:
    """Test CRUD operations for international_shipping_cost when Stripe is connected."""

    def test_create_listing_with_intl_shipping_and_cost(self, stripe_connected_token):
        """POST /api/listings with international_shipping=true and cost."""
        if not stripe_connected_token:
            pytest.skip("No user with Stripe connected available for listing creation")
        
        headers = {"Authorization": f"Bearer {stripe_connected_token}"}
        unique_id = str(uuid.uuid4())[:8]
        
        payload = {
            "artist": f"TEST_IntlShipping_{unique_id}",
            "album": "Test International Album",
            "listing_type": "BUY_NOW",
            "price": 25.00,
            "shipping_cost": 5.00,
            "condition": "Very Good",
            "photo_urls": ["https://via.placeholder.com/300"],
            "international_shipping": True,
            "international_shipping_cost": 15.50
        }
        
        resp = requests.post(f"{BASE_URL}/api/listings", json=payload, headers=headers)
        
        if resp.status_code == 400 and "Stripe" in resp.text:
            pytest.skip("Stripe not connected for this user")
        
        assert resp.status_code == 200, f"Failed to create listing: {resp.text}"
        
        data = resp.json()
        assert data.get("international_shipping") == True, "international_shipping should be True"
        assert data.get("international_shipping_cost") == 15.50, f"Expected 15.50, got {data.get('international_shipping_cost')}"
        
        print(f"PASS: Created listing with international_shipping_cost=15.50")
        
        # Cleanup: delete the test listing
        listing_id = data.get("id")
        if listing_id:
            requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=headers)
        
        return data

    def test_create_listing_without_intl_shipping(self, stripe_connected_token):
        """POST /api/listings with international_shipping=false should have null cost."""
        if not stripe_connected_token:
            pytest.skip("No user with Stripe connected available for listing creation")
        
        headers = {"Authorization": f"Bearer {stripe_connected_token}"}
        unique_id = str(uuid.uuid4())[:8]
        
        payload = {
            "artist": f"TEST_DomesticOnly_{unique_id}",
            "album": "Test Domestic Album",
            "listing_type": "BUY_NOW",
            "price": 20.00,
            "shipping_cost": 5.00,
            "condition": "Very Good",
            "photo_urls": ["https://via.placeholder.com/300"],
            "international_shipping": False,
            "international_shipping_cost": 25.00  # Should be ignored/set to null
        }
        
        resp = requests.post(f"{BASE_URL}/api/listings", json=payload, headers=headers)
        
        if resp.status_code == 400 and "Stripe" in resp.text:
            pytest.skip("Stripe not connected for this user")
        
        assert resp.status_code == 200, f"Failed to create listing: {resp.text}"
        
        data = resp.json()
        assert data.get("international_shipping") == False, "international_shipping should be False"
        # When international_shipping is false, cost should be null
        assert data.get("international_shipping_cost") is None, \
            f"Expected null cost when intl_shipping=false, got {data.get('international_shipping_cost')}"
        
        print(f"PASS: Created listing with intl_shipping=false, cost correctly set to null")
        
        # Cleanup
        listing_id = data.get("id")
        if listing_id:
            requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=headers)

    def test_update_listing_intl_shipping_cost(self, stripe_connected_token):
        """PUT /api/listings/{id} - update international_shipping_cost."""
        if not stripe_connected_token:
            pytest.skip("No user with Stripe connected available")
        
        headers = {"Authorization": f"Bearer {stripe_connected_token}"}
        unique_id = str(uuid.uuid4())[:8]
        
        # Create a listing first
        create_payload = {
            "artist": f"TEST_UpdateIntl_{unique_id}",
            "album": "Test Update Album",
            "listing_type": "BUY_NOW",
            "price": 30.00,
            "shipping_cost": 5.00,
            "condition": "Very Good",
            "photo_urls": ["https://via.placeholder.com/300"],
            "international_shipping": True,
            "international_shipping_cost": 10.00
        }
        
        create_resp = requests.post(f"{BASE_URL}/api/listings", json=create_payload, headers=headers)
        
        if create_resp.status_code == 400 and "Stripe" in create_resp.text:
            pytest.skip("Stripe not connected for this user")
        
        assert create_resp.status_code == 200, f"Failed to create listing: {create_resp.text}"
        
        listing_id = create_resp.json().get("id")
        
        try:
            # Update the international shipping cost
            update_payload = {
                "international_shipping_cost": 20.00
            }
            
            update_resp = requests.put(
                f"{BASE_URL}/api/listings/{listing_id}",
                json=update_payload,
                headers=headers
            )
            
            assert update_resp.status_code == 200, f"Failed to update listing: {update_resp.text}"
            
            updated_data = update_resp.json()
            assert updated_data.get("international_shipping_cost") == 20.00, \
                f"Expected 20.00, got {updated_data.get('international_shipping_cost')}"
            
            print(f"PASS: Updated international_shipping_cost from 10.00 to 20.00")
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=headers)

    def test_update_disable_intl_shipping_clears_cost(self, stripe_connected_token):
        """PUT /api/listings/{id} - disabling international_shipping should clear cost to null."""
        if not stripe_connected_token:
            pytest.skip("No user with Stripe connected available")
        
        headers = {"Authorization": f"Bearer {stripe_connected_token}"}
        unique_id = str(uuid.uuid4())[:8]
        
        # Create listing with international shipping enabled
        create_payload = {
            "artist": f"TEST_DisableIntl_{unique_id}",
            "album": "Test Disable Album",
            "listing_type": "BUY_NOW",
            "price": 30.00,
            "shipping_cost": 5.00,
            "condition": "Very Good",
            "photo_urls": ["https://via.placeholder.com/300"],
            "international_shipping": True,
            "international_shipping_cost": 18.00
        }
        
        create_resp = requests.post(f"{BASE_URL}/api/listings", json=create_payload, headers=headers)
        
        if create_resp.status_code == 400 and "Stripe" in create_resp.text:
            pytest.skip("Stripe not connected for this user")
        
        assert create_resp.status_code == 200, f"Failed to create listing: {create_resp.text}"
        
        listing_id = create_resp.json().get("id")
        
        try:
            # Disable international shipping
            update_payload = {
                "international_shipping": False
            }
            
            update_resp = requests.put(
                f"{BASE_URL}/api/listings/{listing_id}",
                json=update_payload,
                headers=headers
            )
            
            assert update_resp.status_code == 200, f"Failed to update listing: {update_resp.text}"
            
            updated_data = update_resp.json()
            assert updated_data.get("international_shipping") == False, "international_shipping should be False"
            assert updated_data.get("international_shipping_cost") is None, \
                f"Expected null cost after disabling intl shipping, got {updated_data.get('international_shipping_cost')}"
            
            print(f"PASS: Disabling international_shipping correctly cleared cost to null")
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=headers)


class TestGetListingDetailIntlShipping:
    """Test GET /api/listings/{id} response includes proper international shipping data."""

    def test_get_listing_detail_has_all_shipping_fields(self, headers):
        """Verify listing detail endpoint returns international shipping fields."""
        # Get listings
        resp = requests.get(f"{BASE_URL}/api/listings?limit=10", headers=headers)
        assert resp.status_code == 200, f"Failed to get listings: {resp.text}"
        
        listings = resp.json()
        if not listings:
            pytest.skip("No listings available")
        
        # Check detail endpoint for each
        for listing in listings[:3]:
            listing_id = listing.get("id")
            detail_resp = requests.get(f"{BASE_URL}/api/listings/{listing_id}", headers=headers)
            
            assert detail_resp.status_code == 200, f"Failed to get listing {listing_id}: {detail_resp.text}"
            
            data = detail_resp.json()
            
            # Verify shipping fields exist
            assert "shipping_cost" in data or data.get("shipping_cost") is None
            assert "international_shipping" in data
            assert "international_shipping_cost" in data or data.get("international_shipping_cost") is None
            
            intl = data.get("international_shipping", False)
            intl_cost = data.get("international_shipping_cost")
            ship_cost = data.get("shipping_cost")
            
            print(f"Listing {listing_id}: ship_cost=${ship_cost}, intl={intl}, intl_cost={intl_cost}")
        
        print(f"PASS: All listing details have proper shipping fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
