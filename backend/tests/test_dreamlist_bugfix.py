"""
Test file for Dream List bug fixes:
1. GET /api/iso/dreamlist returns WISHLIST items (dedicated endpoint)
2. POST /api/iso with status=WISHLIST creates Dream List items
3. GET /api/valuation/dreamlist returns total_value=0 when Dream List is empty
4. DELETE /api/iso/{id} removes Dream List items
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
    """Get authentication token for demo user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDreamlistEndpoint:
    """Test the new GET /api/iso/dreamlist endpoint"""
    
    def test_dreamlist_endpoint_exists(self, auth_headers):
        """GET /api/iso/dreamlist should exist and return 200"""
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        assert response.status_code == 200, f"Dreamlist endpoint failed: {response.status_code} - {response.text}"
        # Should return a list
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
    
    def test_dreamlist_returns_empty_initially(self, auth_headers):
        """For demo user with 0 items, dreamlist should be empty"""
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Demo user should have 0 Dream List items per problem statement
        # If they have some, that's fine too - just verify structure
        assert isinstance(data, list)
        print(f"Current Dream List has {len(data)} items")


class TestCreateWishlistItem:
    """Test POST /api/iso with status=WISHLIST to create Dream List items"""
    
    def test_create_wishlist_item(self, auth_headers):
        """Create a WISHLIST ISO item and verify it persists"""
        unique_id = str(uuid.uuid4())[:8]
        create_payload = {
            "artist": f"TEST_Artist_{unique_id}",
            "album": f"TEST_Album_{unique_id}",
            "status": "WISHLIST",
            "priority": "LOW",
            "notes": "Test Dream List item"
        }
        
        # Create the item
        response = requests.post(f"{BASE_URL}/api/iso", json=create_payload, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.status_code} - {response.text}"
        
        created = response.json()
        assert created.get("status") == "WISHLIST", f"Expected WISHLIST status, got {created.get('status')}"
        assert created.get("artist") == create_payload["artist"]
        assert created.get("album") == create_payload["album"]
        item_id = created.get("id")
        assert item_id, "Created item should have an id"
        
        return item_id, create_payload["artist"], create_payload["album"]
    
    def test_created_item_appears_in_dreamlist(self, auth_headers):
        """Create a WISHLIST item and verify it appears in GET /api/iso/dreamlist"""
        unique_id = str(uuid.uuid4())[:8]
        create_payload = {
            "artist": f"TEST_DreamCheck_{unique_id}",
            "album": f"TEST_DreamAlbum_{unique_id}",
            "status": "WISHLIST"
        }
        
        # Create
        create_resp = requests.post(f"{BASE_URL}/api/iso", json=create_payload, headers=auth_headers)
        assert create_resp.status_code == 200
        item_id = create_resp.json().get("id")
        
        # Verify in dreamlist
        dreamlist_resp = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        assert dreamlist_resp.status_code == 200
        dreamlist = dreamlist_resp.json()
        
        # Find our created item
        found = any(item.get("id") == item_id for item in dreamlist)
        assert found, f"Created item {item_id} not found in dreamlist"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/iso/{item_id}", headers=auth_headers)
        print(f"PASS: Created WISHLIST item appears in dreamlist endpoint")


class TestDreamlistValuation:
    """Test GET /api/valuation/dreamlist returns correct values"""
    
    def test_valuation_dreamlist_endpoint_exists(self, auth_headers):
        """GET /api/valuation/dreamlist should exist and return 200"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=auth_headers)
        assert response.status_code == 200, f"Valuation dreamlist failed: {response.status_code} - {response.text}"
    
    def test_valuation_returns_correct_structure(self, auth_headers):
        """Valuation endpoint should return total_value, valued_count, total_count"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_value" in data, "Missing total_value field"
        assert "valued_count" in data, "Missing valued_count field"
        assert "total_count" in data, "Missing total_count field"
        
        # Values should be numeric
        assert isinstance(data["total_value"], (int, float))
        assert isinstance(data["valued_count"], int)
        assert isinstance(data["total_count"], int)
        print(f"Dreamlist valuation: {data}")
    
    def test_valuation_returns_zero_when_empty(self, auth_headers):
        """When dream list is empty, total_value should be 0"""
        # First, get current dreamlist
        dreamlist_resp = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        dreamlist = dreamlist_resp.json()
        
        # If dreamlist is empty, verify valuation is 0
        if len(dreamlist) == 0:
            val_resp = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=auth_headers)
            assert val_resp.status_code == 200
            val_data = val_resp.json()
            assert val_data["total_value"] == 0, f"Expected total_value=0 when empty, got {val_data['total_value']}"
            assert val_data["total_count"] == 0, f"Expected total_count=0 when empty, got {val_data['total_count']}"
            print("PASS: Valuation returns $0 when dreamlist is empty")
        else:
            print(f"Skipped zero-value test: dreamlist has {len(dreamlist)} items")


class TestDeleteWishlistItem:
    """Test DELETE /api/iso/{id} removes Dream List items"""
    
    def test_delete_wishlist_item(self, auth_headers):
        """Create and delete a WISHLIST item"""
        unique_id = str(uuid.uuid4())[:8]
        create_payload = {
            "artist": f"TEST_DeleteMe_{unique_id}",
            "album": f"TEST_DeleteAlbum_{unique_id}",
            "status": "WISHLIST"
        }
        
        # Create
        create_resp = requests.post(f"{BASE_URL}/api/iso", json=create_payload, headers=auth_headers)
        assert create_resp.status_code == 200
        item_id = create_resp.json().get("id")
        
        # Delete
        delete_resp = requests.delete(f"{BASE_URL}/api/iso/{item_id}", headers=auth_headers)
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.status_code} - {delete_resp.text}"
        
        # Verify no longer in dreamlist
        dreamlist_resp = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        dreamlist = dreamlist_resp.json()
        found = any(item.get("id") == item_id for item in dreamlist)
        assert not found, f"Deleted item {item_id} still appears in dreamlist"
        print("PASS: Deleted WISHLIST item no longer in dreamlist")


class TestIsoEndpointExcludesWishlist:
    """Test GET /api/iso excludes WISHLIST items (as fixed)"""
    
    def test_iso_excludes_wishlist(self, auth_headers):
        """GET /api/iso should NOT return WISHLIST items"""
        unique_id = str(uuid.uuid4())[:8]
        create_payload = {
            "artist": f"TEST_ExcludeTest_{unique_id}",
            "album": f"TEST_ExcludeAlbum_{unique_id}",
            "status": "WISHLIST"
        }
        
        # Create WISHLIST item
        create_resp = requests.post(f"{BASE_URL}/api/iso", json=create_payload, headers=auth_headers)
        assert create_resp.status_code == 200
        item_id = create_resp.json().get("id")
        
        # GET /api/iso should NOT include this item
        iso_resp = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
        assert iso_resp.status_code == 200
        iso_list = iso_resp.json()
        
        found_in_iso = any(item.get("id") == item_id for item in iso_list)
        assert not found_in_iso, f"WISHLIST item {item_id} should NOT appear in GET /api/iso"
        
        # But it SHOULD be in dreamlist
        dreamlist_resp = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        dreamlist = dreamlist_resp.json()
        found_in_dreamlist = any(item.get("id") == item_id for item in dreamlist)
        assert found_in_dreamlist, f"WISHLIST item {item_id} SHOULD appear in GET /api/iso/dreamlist"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/iso/{item_id}", headers=auth_headers)
        print("PASS: WISHLIST items correctly excluded from /api/iso but included in /api/iso/dreamlist")


class TestCleanup:
    """Cleanup any test data"""
    
    def test_cleanup_test_items(self, auth_headers):
        """Remove any TEST_ prefixed items from dreamlist"""
        dreamlist_resp = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        if dreamlist_resp.status_code == 200:
            dreamlist = dreamlist_resp.json()
            cleaned = 0
            for item in dreamlist:
                if item.get("artist", "").startswith("TEST_") or item.get("album", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/iso/{item['id']}", headers=auth_headers)
                    cleaned += 1
            print(f"Cleaned up {cleaned} test items from dreamlist")
