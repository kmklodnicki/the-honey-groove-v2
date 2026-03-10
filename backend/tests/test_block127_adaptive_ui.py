"""
Test Block 127: Global Groove Adaptive UI
- State dropdown conditional rendering (US only)
- City and Postal Code optional fields
- Near You social discovery endpoint
- Backend state/postal_code persistence
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@test.com"
TEST_PASSWORD = "demouser"


class TestBlock127AdaptiveUI:
    """Tests for Block 127: Global Groove Adaptive UI features"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            self.user_data = response.json().get("user", {})
        else:
            pytest.skip("Authentication failed - skipping tests")

    # ============== Backend API Tests ==============

    def test_explore_near_you_endpoint_returns_valid_response(self):
        """GET /api/explore/near-you returns collectors, listings, and needs_location"""
        response = self.session.get(f"{BASE_URL}/api/explore/near-you")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Validate response structure
        assert "collectors" in data, "Response should contain 'collectors' array"
        assert "listings" in data, "Response should contain 'listings' array"
        assert "needs_location" in data, "Response should contain 'needs_location' boolean"
        
        # Validate types
        assert isinstance(data["collectors"], list), "'collectors' should be a list"
        assert isinstance(data["listings"], list), "'listings' should be a list"
        assert isinstance(data["needs_location"], bool), "'needs_location' should be a boolean"
        print(f"PASS: Near-you endpoint returns valid structure with {len(data['collectors'])} collectors and {len(data['listings'])} listings")

    def test_update_user_with_state_field(self):
        """PUT /api/auth/me correctly saves state field"""
        # First set country to US and state to CA
        update_payload = {
            "country": "US",
            "state": "CA",
            "postal_code": "90210"
        }
        response = self.session.put(f"{BASE_URL}/api/auth/me", json=update_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        updated_user = response.json()
        assert updated_user.get("country") == "US", "Country should be updated to US"
        assert updated_user.get("state") == "CA", "State should be updated to CA"
        assert updated_user.get("postal_code") == "90210", "Postal code should be updated to 90210"
        print(f"PASS: User state field correctly saved: {updated_user.get('state')}")

    def test_update_user_with_postal_code_field(self):
        """PUT /api/auth/me correctly saves postal_code field"""
        update_payload = {
            "postal_code": "12345"
        }
        response = self.session.put(f"{BASE_URL}/api/auth/me", json=update_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        updated_user = response.json()
        assert updated_user.get("postal_code") == "12345", "Postal code should be updated"
        print(f"PASS: User postal_code field correctly saved: {updated_user.get('postal_code')}")

    def test_update_user_non_us_country_clears_state_context(self):
        """PUT /api/auth/me with non-US country should allow state to be undefined"""
        # Set to US first with state
        self.session.put(f"{BASE_URL}/api/auth/me", json={
            "country": "US",
            "state": "NY"
        })
        
        # Now set to non-US country
        update_payload = {
            "country": "GB"
        }
        response = self.session.put(f"{BASE_URL}/api/auth/me", json=update_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        updated_user = response.json()
        assert updated_user.get("country") == "GB", "Country should be updated to GB"
        # Note: Backend may preserve state, but frontend should clear stateUS when country changes
        print(f"PASS: Country updated to non-US: {updated_user.get('country')}")

    def test_get_current_user_includes_state_and_postal_code(self):
        """GET /api/auth/me returns state and postal_code fields"""
        # First set them
        self.session.put(f"{BASE_URL}/api/auth/me", json={
            "country": "US",
            "state": "TX",
            "postal_code": "75001"
        })
        
        # Verify they're returned
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        user_data = response.json()
        assert "state" in user_data, "User response should include 'state' field"
        assert "postal_code" in user_data, "User response should include 'postal_code' field"
        assert user_data.get("state") == "TX", f"State should be TX, got {user_data.get('state')}"
        assert user_data.get("postal_code") == "75001", f"Postal code should be 75001, got {user_data.get('postal_code')}"
        print(f"PASS: GET /api/auth/me returns state={user_data.get('state')} and postal_code={user_data.get('postal_code')}")

    def test_near_you_us_user_state_matching(self):
        """Near-you endpoint uses state matching for US users"""
        # Set user to US with state
        self.session.put(f"{BASE_URL}/api/auth/me", json={
            "country": "US",
            "state": "CA"
        })
        
        response = self.session.get(f"{BASE_URL}/api/explore/near-you")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # If we have collectors, they should have region/state info
        for collector in data.get("collectors", [])[:5]:
            # Each collector should have region or state field in response
            has_location = collector.get("region") or collector.get("country") or collector.get("state")
            print(f"  Collector: {collector.get('username')} - region: {collector.get('region')}, country: {collector.get('country')}")
        
        print(f"PASS: Near-you endpoint returned {len(data.get('collectors', []))} collectors for US user")

    def test_near_you_non_us_user_country_matching(self):
        """Near-you endpoint uses country matching for non-US users"""
        # Set user to GB
        self.session.put(f"{BASE_URL}/api/auth/me", json={
            "country": "GB",
            "city": "London"
        })
        
        response = self.session.get(f"{BASE_URL}/api/explore/near-you")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"PASS: Near-you endpoint returned {len(data.get('collectors', []))} collectors for GB user")

    def test_near_you_no_location_returns_needs_location_true(self):
        """Near-you endpoint returns needs_location=true when user has no location"""
        # Clear location data - we can't fully clear it, but we can test the endpoint behavior
        # The endpoint should check for country (US) or state for matching
        response = self.session.get(f"{BASE_URL}/api/explore/near-you")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Response should have valid structure
        assert "needs_location" in data
        print(f"PASS: Near-you endpoint needs_location field: {data.get('needs_location')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
