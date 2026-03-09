"""
Backend tests for Block 27 features:
- PUT /api/iso/{iso_id}/promote endpoint (Wishlist to Wantlist promotion)
- GET /api/valuation/wishlist endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@thehoneygroove.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # API returns 'access_token' not 'token'
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestValuationWishlist:
    """Tests for GET /api/valuation/wishlist endpoint"""
    
    def test_wishlist_valuation_endpoint_exists(self, auth_headers):
        """GET /api/valuation/wishlist endpoint should exist"""
        response = requests.get(f"{BASE_URL}/api/valuation/wishlist", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("SUCCESS: GET /api/valuation/wishlist endpoint exists and returns 200")
    
    def test_wishlist_valuation_requires_auth(self):
        """GET /api/valuation/wishlist should require authentication"""
        response = requests.get(f"{BASE_URL}/api/valuation/wishlist")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("SUCCESS: GET /api/valuation/wishlist requires authentication")
    
    def test_wishlist_valuation_returns_proper_structure(self, auth_headers):
        """GET /api/valuation/wishlist should return total_value, valued_count, total_count"""
        response = requests.get(f"{BASE_URL}/api/valuation/wishlist", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data, "Missing 'total_value' in response"
        assert "valued_count" in data, "Missing 'valued_count' in response"
        assert "total_count" in data, "Missing 'total_count' in response"
        print(f"SUCCESS: Wishlist valuation structure correct - total_value: ${data['total_value']}, valued_count: {data['valued_count']}, total_count: {data['total_count']}")


class TestISOPromote:
    """Tests for PUT /api/iso/{iso_id}/promote endpoint"""
    
    def test_promote_endpoint_requires_auth(self):
        """PUT /api/iso/{iso_id}/promote should require authentication"""
        response = requests.put(f"{BASE_URL}/api/iso/fake-id/promote")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("SUCCESS: PUT /api/iso/{iso_id}/promote requires authentication")
    
    def test_promote_nonexistent_iso_returns_404(self, auth_headers):
        """PUT /api/iso/{iso_id}/promote should return 404 for non-existent ISO"""
        response = requests.put(f"{BASE_URL}/api/iso/nonexistent-id/promote", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: Promote non-existent ISO returns 404")
    
    def test_get_user_isos(self, auth_headers):
        """GET /api/iso should return user's ISOs"""
        response = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of ISOs"
        print(f"SUCCESS: GET /api/iso returns {len(data)} ISO items")
        return data
    
    def test_iso_items_have_status_field(self, auth_headers):
        """ISO items should have status field"""
        response = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            for iso in data:
                assert "status" in iso, f"ISO {iso.get('id')} missing 'status' field"
            print(f"SUCCESS: All {len(data)} ISO items have status field")
        else:
            print("INFO: No ISO items to check for status field")
    
    def test_promote_changes_status_from_wishlist_to_open(self, auth_headers):
        """
        Test the full promote flow:
        1. Create a WISHLIST ISO item
        2. Call PUT /api/iso/{id}/promote
        3. Verify status changes to OPEN
        """
        # First, create a WISHLIST ISO item via composer endpoint
        create_response = requests.post(
            f"{BASE_URL}/api/composer/iso",
            json={
                "artist": "TEST_Promote_Artist",
                "album": "TEST_Promote_Album",
                "status": "WISHLIST"
            },
            headers=auth_headers
        )
        
        if create_response.status_code not in [200, 201]:
            # Try to find an existing WISHLIST item
            isos_response = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
            if isos_response.status_code == 200:
                isos = isos_response.json()
                wishlist_isos = [iso for iso in isos if iso.get("status") == "WISHLIST"]
                if wishlist_isos:
                    iso_id = wishlist_isos[0]["id"]
                    print(f"Using existing WISHLIST ISO: {iso_id}")
                else:
                    pytest.skip("No WISHLIST ISO items to test promotion")
            else:
                pytest.skip("Could not get ISO items for testing")
        else:
            created_data = create_response.json()
            iso_id = created_data.get("iso_id") or created_data.get("id")
            print(f"Created WISHLIST ISO: {iso_id}")
        
        # Now call promote endpoint
        promote_response = requests.put(
            f"{BASE_URL}/api/iso/{iso_id}/promote",
            headers=auth_headers
        )
        assert promote_response.status_code == 200, f"Promote failed: {promote_response.status_code} - {promote_response.text}"
        promote_data = promote_response.json()
        assert "message" in promote_data, "Expected 'message' in promote response"
        print(f"SUCCESS: Promote endpoint returned: {promote_data['message']}")
        
        # Verify the ISO status changed to OPEN
        verify_response = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
        assert verify_response.status_code == 200
        isos = verify_response.json()
        promoted_iso = next((iso for iso in isos if iso.get("id") == iso_id), None)
        if promoted_iso:
            assert promoted_iso.get("status") == "OPEN", f"Expected OPEN status, got {promoted_iso.get('status')}"
            assert promoted_iso.get("priority") == "HIGH", f"Expected HIGH priority, got {promoted_iso.get('priority')}"
            print(f"SUCCESS: ISO {iso_id} status changed to OPEN with HIGH priority")
        else:
            print(f"INFO: ISO {iso_id} may have been processed/deleted after promotion")


class TestISOEndpointIntegration:
    """Integration tests for ISO endpoints"""
    
    def test_iso_and_valuation_wishlist_consistency(self, auth_headers):
        """
        Verify that valuation/wishlist total_count matches number of WISHLIST ISOs
        """
        # Get ISO items
        isos_response = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
        assert isos_response.status_code == 200
        isos = isos_response.json()
        wishlist_count = len([iso for iso in isos if iso.get("status") == "WISHLIST"])
        
        # Get wishlist valuation
        val_response = requests.get(f"{BASE_URL}/api/valuation/wishlist", headers=auth_headers)
        assert val_response.status_code == 200
        val_data = val_response.json()
        
        assert val_data["total_count"] == wishlist_count, f"Mismatch: valuation says {val_data['total_count']} but found {wishlist_count} WISHLIST ISOs"
        print(f"SUCCESS: Wishlist valuation count ({val_data['total_count']}) matches ISO WISHLIST count ({wishlist_count})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
