"""
Tests for ISO/Wishlist bug fix (iteration 123):
- GET /api/iso should exclude WISHLIST items (fixed from returning ALL items)
- GET /api/users/{username}/iso should exclude WISHLIST items
- GET /api/users/{username}/dreaming should only return WISHLIST items
- PUT /api/iso/{id}/promote should change status from WISHLIST to OPEN
- POST /api/iso should create items with WISHLIST status by default
- POST /api/composer/iso should create items with OPEN status
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@example.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestISOWishlistBugfix:
    """Test the ISO/Wishlist separation fix"""
    
    def test_api_iso_get_excludes_wishlist(self, authenticated_client):
        """GET /api/iso should exclude WISHLIST status items"""
        response = authenticated_client.get(f"{BASE_URL}/api/iso")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # All returned items should NOT have status WISHLIST
        for item in data:
            assert item.get("status") != "WISHLIST", f"Found WISHLIST item in /api/iso: {item}"
        print(f"PASS: GET /api/iso returns {len(data)} items, none with WISHLIST status")
    
    def test_user_iso_endpoint_excludes_wishlist(self, authenticated_client):
        """GET /api/users/{username}/iso should exclude WISHLIST status items"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/demo/iso")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        for item in data:
            assert item.get("status") != "WISHLIST", f"Found WISHLIST item in /users/demo/iso: {item}"
        print(f"PASS: GET /api/users/demo/iso returns {len(data)} items, none with WISHLIST status")
    
    def test_user_dreaming_endpoint_only_returns_wishlist(self, authenticated_client):
        """GET /api/users/{username}/dreaming should only return WISHLIST status items"""
        response = authenticated_client.get(f"{BASE_URL}/api/users/demo/dreaming")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        for item in data:
            assert item.get("status") == "WISHLIST", f"Found non-WISHLIST item in /users/demo/dreaming: {item.get('status')}"
        print(f"PASS: GET /api/users/demo/dreaming returns {len(data)} items, all with WISHLIST status")


class TestISOPromote:
    """Test the promote endpoint for moving WISHLIST to OPEN"""
    
    def test_promote_endpoint_exists(self, authenticated_client):
        """PUT /api/iso/{id}/promote endpoint should exist"""
        # Use a fake ID - we expect 404, not 405 (method not allowed)
        response = authenticated_client.put(f"{BASE_URL}/api/iso/fake-id-12345/promote")
        # 404 = "ISO not found" is correct - endpoint exists
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        assert "not found" in response.json().get("detail", "").lower(), "Expected 'not found' error"
        print(f"PASS: PUT /api/iso/{{id}}/promote endpoint exists (404 for invalid ID)")
    
    def test_create_and_promote_wishlist_item(self, authenticated_client):
        """Create a WISHLIST item and promote it to OPEN"""
        # Create a WISHLIST item via /api/iso
        unique_id = str(uuid.uuid4())[:8]
        create_data = {
            "artist": f"TEST_Artist_{unique_id}",
            "album": f"TEST_Album_{unique_id}",
            # status defaults to WISHLIST
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/iso",
            json=create_data
        )
        assert create_response.status_code in [200, 201], f"Failed to create ISO: {create_response.text}"
        
        created_item = create_response.json()
        item_id = created_item.get("id")
        assert item_id is not None, "Created item should have an id"
        assert created_item.get("status") == "WISHLIST", f"Expected WISHLIST status, got {created_item.get('status')}"
        print(f"PASS: Created WISHLIST item with id: {item_id}")
        
        try:
            # Verify item appears in /dreaming
            dreaming_response = authenticated_client.get(f"{BASE_URL}/api/users/demo/dreaming")
            assert dreaming_response.status_code == 200
            found_in_dreaming = any(i.get("id") == item_id for i in dreaming_response.json())
            assert found_in_dreaming, "New WISHLIST item should appear in dreaming endpoint"
            print("PASS: WISHLIST item appears in dreaming endpoint")
            
            # Verify item does NOT appear in /api/iso
            iso_response = authenticated_client.get(f"{BASE_URL}/api/iso")
            assert iso_response.status_code == 200
            found_in_iso = any(i.get("id") == item_id for i in iso_response.json())
            assert not found_in_iso, "WISHLIST item should NOT appear in /api/iso"
            print("PASS: WISHLIST item does NOT appear in /api/iso")
            
            # Promote the item
            promote_response = authenticated_client.put(f"{BASE_URL}/api/iso/{item_id}/promote")
            assert promote_response.status_code == 200, f"Promote failed: {promote_response.text}"
            
            promote_data = promote_response.json()
            assert "hunt" in promote_data.get("message", "").lower(), f"Unexpected promote message: {promote_data}"
            print(f"PASS: Promoted item, message: {promote_data.get('message')}")
            
            # Verify item NOW appears in /api/iso (OPEN status)
            iso_response2 = authenticated_client.get(f"{BASE_URL}/api/iso")
            assert iso_response2.status_code == 200
            
            iso_items = iso_response2.json()
            promoted_item = next((i for i in iso_items if i.get("id") == item_id), None)
            assert promoted_item is not None, "Promoted item should appear in /api/iso"
            assert promoted_item.get("status") == "OPEN", f"Expected OPEN status, got {promoted_item.get('status')}"
            print("PASS: Promoted item found in /api/iso with OPEN status")
            
            # Verify item no longer appears in /dreaming
            dreaming_response2 = authenticated_client.get(f"{BASE_URL}/api/users/demo/dreaming")
            assert dreaming_response2.status_code == 200
            found_in_dreaming2 = any(i.get("id") == item_id for i in dreaming_response2.json())
            assert not found_in_dreaming2, "Promoted item should NOT appear in dreaming endpoint"
            print("PASS: Promoted item no longer in dreaming endpoint")
            
        finally:
            # Cleanup: delete the test item
            authenticated_client.delete(f"{BASE_URL}/api/iso/{item_id}")
            print(f"CLEANUP: Deleted test item {item_id}")


class TestISOCreation:
    """Test default status for different ISO creation endpoints"""
    
    def test_api_iso_creates_wishlist_by_default(self, authenticated_client):
        """POST /api/iso should create items with WISHLIST status by default"""
        unique_id = str(uuid.uuid4())[:8]
        create_data = {
            "artist": f"TEST_Default_Artist_{unique_id}",
            "album": f"TEST_Default_Album_{unique_id}",
            # Omit status to test default
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/iso",
            json=create_data
        )
        assert response.status_code in [200, 201], f"Failed to create: {response.text}"
        
        data = response.json()
        item_id = data.get("id")
        
        try:
            assert data.get("status") == "WISHLIST", f"Expected default WISHLIST, got {data.get('status')}"
            print(f"PASS: POST /api/iso creates with WISHLIST status by default")
        finally:
            if item_id:
                authenticated_client.delete(f"{BASE_URL}/api/iso/{item_id}")
    
    def test_composer_iso_creates_open_status(self, authenticated_client):
        """POST /api/composer/iso should create items with OPEN status"""
        unique_id = str(uuid.uuid4())[:8]
        create_data = {
            "artist": f"TEST_Composer_Artist_{unique_id}",
            "album": f"TEST_Composer_Album_{unique_id}",
            "caption": "Test ISO via composer"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/composer/iso",
            json=create_data
        )
        assert response.status_code in [200, 201], f"Failed to create via composer: {response.text}"
        
        data = response.json()
        iso_data = data.get("iso") or {}
        item_id = iso_data.get("id")
        post_id = data.get("id")
        
        try:
            # composer/iso returns a post response with iso data nested
            assert iso_data.get("status") == "OPEN", f"Expected OPEN status, got {iso_data.get('status')}"
            print(f"PASS: POST /api/composer/iso creates with OPEN status")
        finally:
            # Clean up both the post and the ISO item
            if post_id:
                authenticated_client.delete(f"{BASE_URL}/api/posts/{post_id}")
            if item_id:
                authenticated_client.delete(f"{BASE_URL}/api/iso/{item_id}")


class TestEndpointAvailability:
    """Quick availability checks for all relevant endpoints"""
    
    def test_all_endpoints_accessible(self, authenticated_client):
        """Verify all ISO-related endpoints are accessible"""
        endpoints = [
            ("GET", "/api/iso"),
            ("GET", "/api/users/demo/iso"),
            ("GET", "/api/users/demo/dreaming"),
        ]
        
        for method, path in endpoints:
            if method == "GET":
                response = authenticated_client.get(f"{BASE_URL}{path}")
            
            assert response.status_code == 200, f"{method} {path} returned {response.status_code}: {response.text}"
            print(f"PASS: {method} {path} accessible (200 OK)")
