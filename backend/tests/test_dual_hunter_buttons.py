"""
BLOCK 75.2: Dual-Action Hunter Buttons - Backend API Tests
Tests for the 'Add to Collection' and 'Actively Seeking' buttons on Dream List cards

Endpoints tested:
- POST /api/iso/{id}/convert-to-collection - Converts dream item to collection record
- PUT /api/iso/{id}/promote - Promotes dream item to active ISO (Actively Seeking)
- DELETE /api/iso/{id} - Deletes dream item (delete trash button)
- GET /api/iso/dreamlist - Gets user's dream list items
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "demo@test.com"
TEST_USER_PASSWORD = "demouser"


class TestDualHunterButtons:
    """Test the dual-action hunter buttons on Dream List cards"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_dreamlist(self):
        """Test GET /api/iso/dreamlist returns dream items"""
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=self.headers)
        assert response.status_code == 200, f"Failed to get dreamlist: {response.text}"
        dreamlist = response.json()
        assert isinstance(dreamlist, list), "Dreamlist should be a list"
        print(f"Found {len(dreamlist)} dream items")
        for item in dreamlist:
            assert "id" in item, "Dream item should have id"
            assert "album" in item, "Dream item should have album"
            assert "artist" in item, "Dream item should have artist"
            assert "status" in item, "Dream item should have status"
            assert item["status"] == "WISHLIST", f"Dream item status should be WISHLIST, got {item['status']}"
            print(f"  - {item['artist']} - {item['album']} (id: {item['id']})")
    
    def test_create_and_convert_to_collection(self):
        """Test POST /api/iso/{id}/convert-to-collection - converts dream item to collection"""
        # First create a test dream item
        create_response = requests.post(f"{BASE_URL}/api/iso", json={
            "artist": "TEST_Artist_Convert",
            "album": "TEST_Album_Convert",
            "status": "WISHLIST"
        }, headers=self.headers)
        assert create_response.status_code == 200, f"Failed to create ISO: {create_response.text}"
        iso_item = create_response.json()
        iso_id = iso_item["id"]
        print(f"Created test dream item: {iso_id}")
        
        # Now convert it to collection
        convert_response = requests.post(
            f"{BASE_URL}/api/iso/{iso_id}/convert-to-collection",
            headers=self.headers
        )
        assert convert_response.status_code == 200, f"Convert failed: {convert_response.text}"
        result = convert_response.json()
        assert "message" in result, "Response should have message"
        assert "record_id" in result, "Response should have record_id"
        print(f"Converted to collection: {result}")
        
        # Verify item no longer in dreamlist
        verify_response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=self.headers)
        dreamlist = verify_response.json()
        item_ids = [item["id"] for item in dreamlist]
        assert iso_id not in item_ids, "Converted item should not be in dreamlist"
        print("Verified: item removed from dream list")
        
        # Clean up - delete the record that was created
        record_id = result["record_id"]
        delete_response = requests.delete(
            f"{BASE_URL}/api/records/{record_id}",
            headers=self.headers
        )
        print(f"Cleanup: deleted record {record_id}")
    
    def test_create_and_promote_to_active(self):
        """Test PUT /api/iso/{id}/promote - promotes dream item to actively seeking"""
        # First create a test dream item
        create_response = requests.post(f"{BASE_URL}/api/iso", json={
            "artist": "TEST_Artist_Promote",
            "album": "TEST_Album_Promote",
            "status": "WISHLIST"
        }, headers=self.headers)
        assert create_response.status_code == 200, f"Failed to create ISO: {create_response.text}"
        iso_item = create_response.json()
        iso_id = iso_item["id"]
        print(f"Created test dream item: {iso_id}")
        
        # Promote to active
        promote_response = requests.put(
            f"{BASE_URL}/api/iso/{iso_id}/promote",
            headers=self.headers
        )
        assert promote_response.status_code == 200, f"Promote failed: {promote_response.text}"
        result = promote_response.json()
        assert "message" in result, "Response should have message"
        assert "on the hunt" in result["message"].lower(), f"Message should contain 'on the hunt': {result['message']}"
        print(f"Promoted to active: {result}")
        
        # Verify item no longer in dreamlist (since status changed from WISHLIST to OPEN)
        dreamlist_response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=self.headers)
        dreamlist = dreamlist_response.json()
        item_ids = [item["id"] for item in dreamlist]
        assert iso_id not in item_ids, "Promoted item should not be in dreamlist"
        print("Verified: item removed from dream list (status changed to OPEN)")
        
        # Verify item now in active ISO list
        iso_response = requests.get(f"{BASE_URL}/api/iso", headers=self.headers)
        iso_list = iso_response.json()
        iso_ids = [item["id"] for item in iso_list]
        assert iso_id in iso_ids, "Promoted item should be in ISO list"
        promoted_item = next(item for item in iso_list if item["id"] == iso_id)
        assert promoted_item["status"] == "OPEN", f"Promoted item status should be OPEN, got {promoted_item['status']}"
        assert promoted_item["priority"] == "HIGH", f"Promoted item priority should be HIGH, got {promoted_item['priority']}"
        print("Verified: item now in active ISO list with OPEN status and HIGH priority")
        
        # Clean up - delete the ISO
        cleanup_response = requests.delete(
            f"{BASE_URL}/api/iso/{iso_id}",
            headers=self.headers
        )
        print(f"Cleanup: deleted ISO {iso_id}")
    
    def test_delete_dream_item(self):
        """Test DELETE /api/iso/{id} - deletes dream item (trash button)"""
        # First create a test dream item
        create_response = requests.post(f"{BASE_URL}/api/iso", json={
            "artist": "TEST_Artist_Delete",
            "album": "TEST_Album_Delete",
            "status": "WISHLIST"
        }, headers=self.headers)
        assert create_response.status_code == 200, f"Failed to create ISO: {create_response.text}"
        iso_item = create_response.json()
        iso_id = iso_item["id"]
        print(f"Created test dream item: {iso_id}")
        
        # Delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/iso/{iso_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        result = delete_response.json()
        assert "message" in result, "Response should have message"
        print(f"Deleted: {result}")
        
        # Verify item no longer exists
        verify_response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=self.headers)
        dreamlist = verify_response.json()
        item_ids = [item["id"] for item in dreamlist]
        assert iso_id not in item_ids, "Deleted item should not be in dreamlist"
        print("Verified: item deleted from dream list")
    
    def test_convert_nonexistent_item(self):
        """Test convert to collection with non-existent ID returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/iso/{fake_id}/convert-to-collection",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404 for non-existent item, got {response.status_code}"
        print("Correctly returned 404 for non-existent item")
    
    def test_promote_nonexistent_item(self):
        """Test promote with non-existent ID returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.put(
            f"{BASE_URL}/api/iso/{fake_id}/promote",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404 for non-existent item, got {response.status_code}"
        print("Correctly returned 404 for non-existent item")
    
    def test_delete_nonexistent_item(self):
        """Test delete with non-existent ID returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/iso/{fake_id}",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404 for non-existent item, got {response.status_code}"
        print("Correctly returned 404 for non-existent item")
    
    def test_convert_requires_auth(self):
        """Test convert-to-collection requires authentication"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/iso/{fake_id}/convert-to-collection")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("Correctly requires authentication for convert")
    
    def test_promote_requires_auth(self):
        """Test promote requires authentication"""
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/iso/{fake_id}/promote")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("Correctly requires authentication for promote")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
