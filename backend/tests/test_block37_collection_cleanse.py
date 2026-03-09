"""
Test BLOCK 37.1-37.3: Collection Cleanse Features
- BLOCK 37.1: Confirmation dialogs (frontend) for moving items from Reality to Dreaming/Hunt
- BLOCK 37.2: 'Seeking Upgrade' tag when moving to Hunt, immediate value updates
- BLOCK 37.3: Multi-select mode with bulk Dreamify and Huntify actions

Backend endpoints tested:
- POST /api/records/{id}/move-to-iso (should add 'Seeking Upgrade' tag)
- POST /api/records/{id}/move-to-wishlist
- POST /api/records/bulk-move-to-wishlist (accepts record_ids array)
- POST /api/records/bulk-move-to-iso (accepts record_ids array, adds 'Seeking Upgrade' tag)
- GET /api/valuation/record-value/{discogs_id} (returns median value)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBlock37CollectionCleanse:
    """Test Collection Cleanse (BLOCK 37) features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth and create test records"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Track created records for cleanup
        self.created_record_ids = []
        self.created_iso_ids = []
        yield
        
        # Cleanup
        for rid in self.created_record_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/records/{rid}")
            except:
                pass
        for iid in self.created_iso_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/iso/{iid}")
            except:
                pass
    
    def _create_test_record(self, title_suffix=""):
        """Helper to create a test record"""
        record_data = {
            "title": f"TEST_Block37_Record_{title_suffix}_{int(time.time())}",
            "artist": "TEST_Block37_Artist",
            "discogs_id": 12345,
            "cover_url": "https://example.com/cover.jpg"
        }
        resp = self.session.post(f"{BASE_URL}/api/records", json=record_data)
        assert resp.status_code == 200, f"Failed to create record: {resp.text}"
        record = resp.json()
        self.created_record_ids.append(record["id"])
        return record

    # ===== BLOCK 37.2: Move to ISO adds 'Seeking Upgrade' tag =====
    
    def test_move_to_iso_adds_seeking_upgrade_tag(self):
        """POST /api/records/{id}/move-to-iso should add 'Seeking Upgrade' tag"""
        record = self._create_test_record("SeekUpgrade")
        record_id = record["id"]
        
        # Move to ISO (The Hunt)
        resp = self.session.post(f"{BASE_URL}/api/records/{record_id}/move-to-iso")
        assert resp.status_code == 200, f"Move to ISO failed: {resp.text}"
        
        data = resp.json()
        assert "message" in data
        assert "hunt" in data["message"].lower() or "back on the hunt" in data["message"].lower()
        
        # Remove from created_records since it's now in ISO
        self.created_record_ids.remove(record_id)
        
        # Verify the ISO item was created with 'Seeking Upgrade' tag
        iso_resp = self.session.get(f"{BASE_URL}/api/iso")
        assert iso_resp.status_code == 200
        iso_items = iso_resp.json()
        
        # Find the newly created ISO item
        iso_item = next((i for i in iso_items if i.get("album") == record["title"]), None)
        assert iso_item is not None, "ISO item not found after move"
        self.created_iso_ids.append(iso_item["id"])
        
        # Verify 'Seeking Upgrade' tag
        tags = iso_item.get("tags", [])
        assert "Seeking Upgrade" in tags, f"'Seeking Upgrade' tag not found. Tags: {tags}"
        assert iso_item.get("status") == "OPEN", f"Expected OPEN status, got {iso_item.get('status')}"
    
    def test_move_to_wishlist_returns_success(self):
        """POST /api/records/{id}/move-to-wishlist should move to Dreaming"""
        record = self._create_test_record("Wishlist")
        record_id = record["id"]
        
        resp = self.session.post(f"{BASE_URL}/api/records/{record_id}/move-to-wishlist")
        assert resp.status_code == 200, f"Move to wishlist failed: {resp.text}"
        
        data = resp.json()
        assert "message" in data
        
        self.created_record_ids.remove(record_id)
        
        # Verify moved to ISO with WISHLIST status
        iso_resp = self.session.get(f"{BASE_URL}/api/iso")
        assert iso_resp.status_code == 200
        iso_items = iso_resp.json()
        
        wishlist_item = next((i for i in iso_items if i.get("album") == record["title"] and i.get("status") == "WISHLIST"), None)
        assert wishlist_item is not None, "Wishlist item not found"
        self.created_iso_ids.append(wishlist_item["id"])

    # ===== BLOCK 37.3: Bulk move endpoints =====
    
    def test_bulk_move_to_wishlist(self):
        """POST /api/records/bulk-move-to-wishlist should accept record_ids array"""
        # Create multiple test records
        record1 = self._create_test_record("Bulk1")
        record2 = self._create_test_record("Bulk2")
        record_ids = [record1["id"], record2["id"]]
        
        # Bulk move to wishlist (Dreamify)
        resp = self.session.post(f"{BASE_URL}/api/records/bulk-move-to-wishlist", json={
            "record_ids": record_ids
        })
        assert resp.status_code == 200, f"Bulk move to wishlist failed: {resp.text}"
        
        data = resp.json()
        assert "moved" in data
        assert data["moved"] == 2, f"Expected 2 moved, got {data['moved']}"
        
        # Remove from tracking
        for rid in record_ids:
            if rid in self.created_record_ids:
                self.created_record_ids.remove(rid)
        
        # Verify items are in wishlist
        iso_resp = self.session.get(f"{BASE_URL}/api/iso")
        assert iso_resp.status_code == 200
        iso_items = iso_resp.json()
        
        wishlist_items = [i for i in iso_items if i.get("status") == "WISHLIST" and "TEST_Block37" in i.get("album", "")]
        for item in wishlist_items:
            self.created_iso_ids.append(item["id"])
    
    def test_bulk_move_to_iso_adds_seeking_upgrade_tag(self):
        """POST /api/records/bulk-move-to-iso should add 'Seeking Upgrade' tag to all"""
        # Create multiple test records
        record1 = self._create_test_record("BulkHunt1")
        record2 = self._create_test_record("BulkHunt2")
        record_ids = [record1["id"], record2["id"]]
        titles = [record1["title"], record2["title"]]
        
        # Bulk move to ISO (Huntify)
        resp = self.session.post(f"{BASE_URL}/api/records/bulk-move-to-iso", json={
            "record_ids": record_ids
        })
        assert resp.status_code == 200, f"Bulk move to ISO failed: {resp.text}"
        
        data = resp.json()
        assert "moved" in data
        assert data["moved"] == 2, f"Expected 2 moved, got {data['moved']}"
        
        # Remove from tracking
        for rid in record_ids:
            if rid in self.created_record_ids:
                self.created_record_ids.remove(rid)
        
        # Verify items are in ISO with 'Seeking Upgrade' tag
        iso_resp = self.session.get(f"{BASE_URL}/api/iso")
        assert iso_resp.status_code == 200
        iso_items = iso_resp.json()
        
        for title in titles:
            iso_item = next((i for i in iso_items if i.get("album") == title), None)
            assert iso_item is not None, f"ISO item '{title}' not found"
            self.created_iso_ids.append(iso_item["id"])
            
            # Verify 'Seeking Upgrade' tag
            tags = iso_item.get("tags", [])
            assert "Seeking Upgrade" in tags, f"'Seeking Upgrade' tag missing for '{title}'. Tags: {tags}"
            assert iso_item.get("status") == "OPEN", f"Expected OPEN status for '{title}'"
    
    def test_bulk_move_empty_array(self):
        """Bulk move with empty array should return 0 moved"""
        resp = self.session.post(f"{BASE_URL}/api/records/bulk-move-to-wishlist", json={
            "record_ids": []
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["moved"] == 0
    
    def test_bulk_move_nonexistent_records(self):
        """Bulk move with non-existent IDs should skip them"""
        resp = self.session.post(f"{BASE_URL}/api/records/bulk-move-to-iso", json={
            "record_ids": ["nonexistent-id-1", "nonexistent-id-2"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["moved"] == 0

    # ===== Valuation endpoint for record-value =====
    
    def test_get_record_value_by_discogs_id(self):
        """GET /api/valuation/record-value/{discogs_id} should return median value"""
        # Use a known discogs_id (may not have cached value, but endpoint should work)
        discogs_id = 12345
        
        resp = self.session.get(f"{BASE_URL}/api/valuation/record-value/{discogs_id}")
        assert resp.status_code == 200, f"Get record value failed: {resp.text}"
        
        data = resp.json()
        assert "median_value" in data, f"median_value not in response: {data}"
        # Value can be 0 if not cached
        assert isinstance(data["median_value"], (int, float))
    
    def test_get_record_value_requires_auth(self):
        """GET /api/valuation/record-value/{discogs_id} requires authentication"""
        no_auth_session = requests.Session()
        resp = no_auth_session.get(f"{BASE_URL}/api/valuation/record-value/12345")
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"

    # ===== Auth requirements for move endpoints =====
    
    def test_move_to_iso_requires_auth(self):
        """POST /api/records/{id}/move-to-iso requires auth"""
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        resp = no_auth_session.post(f"{BASE_URL}/api/records/some-id/move-to-iso")
        assert resp.status_code in [401, 403]
    
    def test_bulk_move_requires_auth(self):
        """Bulk move endpoints require auth"""
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        resp1 = no_auth_session.post(f"{BASE_URL}/api/records/bulk-move-to-wishlist", json={"record_ids": []})
        assert resp1.status_code in [401, 403]
        
        resp2 = no_auth_session.post(f"{BASE_URL}/api/records/bulk-move-to-iso", json={"record_ids": []})
        assert resp2.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
