"""
Test Block 30: Context-sensitive 'Add Record' button features
- POST /api/records accepts color_variant field  
- POST /api/iso creates WISHLIST ISO items (for AddRecordPage dreaming mode)
- Verify color_variant is returned in record/ISO responses
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestBlock30ContextAddButton:
    """Test context-sensitive Add Record button (Block 30)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session and authenticate"""
        self.session = requests.Session()
        self.test_prefix = f"TEST_B30_{uuid.uuid4().hex[:6]}"
        
        # Login with test credentials
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin123"
        })
        
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping tests")
        
        yield
        
        # Cleanup: Delete test records and ISO items
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Clean up test-created data"""
        try:
            # Get all records and delete test ones
            records_resp = self.session.get(f"{BASE_URL}/api/records")
            if records_resp.status_code == 200:
                for record in records_resp.json():
                    if self.test_prefix in record.get("title", "") or self.test_prefix in record.get("artist", ""):
                        self.session.delete(f"{BASE_URL}/api/records/{record['id']}")
            
            # Get all ISO items and delete test ones
            iso_resp = self.session.get(f"{BASE_URL}/api/iso")
            if iso_resp.status_code == 200:
                for iso in iso_resp.json():
                    if self.test_prefix in iso.get("album", "") or self.test_prefix in iso.get("artist", ""):
                        self.session.delete(f"{BASE_URL}/api/iso/{iso['id']}")
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    # ========== POST /api/records with color_variant ==========
    
    def test_add_record_with_color_variant(self):
        """POST /api/records accepts color_variant field and returns it"""
        record_data = {
            "title": f"{self.test_prefix}_Reality_Album",
            "artist": f"{self.test_prefix}_Artist",
            "year": 2024,
            "color_variant": "Limited Edition Blue Marble"
        }
        
        response = self.session.post(f"{BASE_URL}/api/records", json=record_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["title"] == record_data["title"]
        assert data["artist"] == record_data["artist"]
        assert data["color_variant"] == "Limited Edition Blue Marble", f"color_variant not returned: {data}"
        assert "id" in data
        print(f"PASS: POST /api/records with color_variant returns: {data['color_variant']}")
    
    def test_add_record_without_color_variant(self):
        """POST /api/records works without color_variant (optional field)"""
        record_data = {
            "title": f"{self.test_prefix}_NoVariant_Album",
            "artist": f"{self.test_prefix}_Artist"
        }
        
        response = self.session.post(f"{BASE_URL}/api/records", json=record_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["title"] == record_data["title"]
        # color_variant should be None or missing
        assert data.get("color_variant") is None, f"Expected null color_variant: {data}"
        print("PASS: POST /api/records without color_variant works")
    
    def test_get_record_includes_color_variant(self):
        """GET /api/records/{id} returns color_variant"""
        # First create a record with color_variant
        record_data = {
            "title": f"{self.test_prefix}_GetVariant_Album",
            "artist": f"{self.test_prefix}_Artist",
            "color_variant": "180g Black Vinyl"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/records", json=record_data)
        assert create_resp.status_code == 200
        record_id = create_resp.json()["id"]
        
        # GET the record
        get_resp = self.session.get(f"{BASE_URL}/api/records/{record_id}")
        assert get_resp.status_code == 200
        
        data = get_resp.json()
        assert data["color_variant"] == "180g Black Vinyl"
        print(f"PASS: GET /api/records/{record_id} includes color_variant")
    
    # ========== POST /api/iso (Dreaming mode) ==========
    
    def test_create_iso_wishlist_item(self):
        """POST /api/iso creates a WISHLIST ISO item (dreaming mode)"""
        iso_data = {
            "artist": f"{self.test_prefix}_Dream_Artist",
            "album": f"{self.test_prefix}_Dream_Album",
            "year": 2025,
            "color_variant": "Transparent Orange",
            "status": "WISHLIST",
            "priority": "LOW"
        }
        
        response = self.session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["artist"] == iso_data["artist"]
        assert data["album"] == iso_data["album"]
        assert data["status"] == "WISHLIST", f"Expected WISHLIST status: {data}"
        assert data["priority"] == "LOW"
        assert data.get("color_variant") == "Transparent Orange", f"color_variant not returned: {data}"
        assert "id" in data
        print(f"PASS: POST /api/iso creates WISHLIST item with color_variant: {data['color_variant']}")
    
    def test_create_iso_without_color_variant(self):
        """POST /api/iso works without color_variant"""
        iso_data = {
            "artist": f"{self.test_prefix}_Dream_Artist2",
            "album": f"{self.test_prefix}_Dream_Album2",
            "status": "WISHLIST"
        }
        
        response = self.session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["status"] == "WISHLIST"
        print("PASS: POST /api/iso without color_variant works")
    
    def test_iso_appears_in_get_iso_list(self):
        """Created ISO item appears in GET /api/iso"""
        # Create ISO item
        iso_data = {
            "artist": f"{self.test_prefix}_ListTest_Artist",
            "album": f"{self.test_prefix}_ListTest_Album",
            "status": "WISHLIST"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200
        iso_id = create_resp.json()["id"]
        
        # GET all ISO items
        list_resp = self.session.get(f"{BASE_URL}/api/iso")
        assert list_resp.status_code == 200
        
        iso_list = list_resp.json()
        iso_ids = [i["id"] for i in iso_list]
        assert iso_id in iso_ids, f"Created ISO not in list: {iso_id}"
        print(f"PASS: Created ISO {iso_id} appears in GET /api/iso list")
    
    def test_iso_promote_to_open(self):
        """PUT /api/iso/{id}/promote changes WISHLIST to OPEN"""
        # Create WISHLIST ISO
        iso_data = {
            "artist": f"{self.test_prefix}_Promote_Artist",
            "album": f"{self.test_prefix}_Promote_Album",
            "status": "WISHLIST"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200
        iso_id = create_resp.json()["id"]
        
        # Promote to OPEN
        promote_resp = self.session.put(f"{BASE_URL}/api/iso/{iso_id}/promote")
        assert promote_resp.status_code == 200, f"Promote failed: {promote_resp.text}"
        
        # Verify status changed
        list_resp = self.session.get(f"{BASE_URL}/api/iso")
        assert list_resp.status_code == 200
        
        iso_list = list_resp.json()
        promoted_iso = next((i for i in iso_list if i["id"] == iso_id), None)
        assert promoted_iso is not None
        assert promoted_iso["status"] == "OPEN", f"Expected OPEN status: {promoted_iso}"
        print(f"PASS: ISO {iso_id} promoted from WISHLIST to OPEN")
    
    def test_iso_delete(self):
        """DELETE /api/iso/{id} removes the ISO item"""
        # Create ISO
        iso_data = {
            "artist": f"{self.test_prefix}_Delete_Artist",
            "album": f"{self.test_prefix}_Delete_Album",
            "status": "WISHLIST"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200
        iso_id = create_resp.json()["id"]
        
        # Delete it
        delete_resp = self.session.delete(f"{BASE_URL}/api/iso/{iso_id}")
        assert delete_resp.status_code == 200
        
        # Verify it's gone
        list_resp = self.session.get(f"{BASE_URL}/api/iso")
        iso_ids = [i["id"] for i in list_resp.json()]
        assert iso_id not in iso_ids, f"ISO {iso_id} still exists after delete"
        print(f"PASS: ISO {iso_id} deleted successfully")
    
    # ========== Integration: Dreaming mode creates ISO, Reality mode creates record ==========
    
    def test_reality_vs_dreaming_mode_difference(self):
        """Reality creates record, Dreaming creates ISO - both with color_variant"""
        # Reality mode: POST /api/records
        reality_data = {
            "title": f"{self.test_prefix}_Reality_Mode",
            "artist": f"{self.test_prefix}_Artist",
            "color_variant": "Red Splatter"
        }
        reality_resp = self.session.post(f"{BASE_URL}/api/records", json=reality_data)
        assert reality_resp.status_code == 200
        reality_record = reality_resp.json()
        assert "id" in reality_record
        assert reality_record["color_variant"] == "Red Splatter"
        
        # Dreaming mode: POST /api/iso
        dreaming_data = {
            "artist": f"{self.test_prefix}_Artist",
            "album": f"{self.test_prefix}_Dreaming_Mode",
            "color_variant": "Galaxy Purple",
            "status": "WISHLIST"
        }
        dreaming_resp = self.session.post(f"{BASE_URL}/api/iso", json=dreaming_data)
        assert dreaming_resp.status_code == 200
        dreaming_iso = dreaming_resp.json()
        assert "id" in dreaming_iso
        assert dreaming_iso["status"] == "WISHLIST"
        assert dreaming_iso.get("color_variant") == "Galaxy Purple"
        
        # Verify they are in separate collections
        records_resp = self.session.get(f"{BASE_URL}/api/records")
        record_titles = [r["title"] for r in records_resp.json()]
        assert f"{self.test_prefix}_Reality_Mode" in record_titles
        
        iso_resp = self.session.get(f"{BASE_URL}/api/iso")
        iso_albums = [i["album"] for i in iso_resp.json()]
        assert f"{self.test_prefix}_Dreaming_Mode" in iso_albums
        
        print("PASS: Reality mode creates record, Dreaming mode creates ISO with color_variant")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
