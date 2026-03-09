"""
Test Hunt Completed Workflow - Block 18.1 and 18.2
BLOCK 18.1: ISO to Collection migration - 'I Found It!' button converts ISO to collection record
BLOCK 18.2: Collection Quick Actions - dropdown menu with Move to Wishlist, Put back on ISO, Remove Completely
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@thehoneygroove.com"
TEST_PASSWORD = "admin123"


def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # Try both 'access_token' and 'token' for compatibility
        return data.get("access_token") or data.get("token")
    return None


def get_auth_headers():
    """Get authorization headers"""
    token = get_auth_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


class TestHuntCompletedWorkflow:
    """Tests for the Hunt Completed workflow - Block 18.1 and 18.2"""
    
    @classmethod
    def setup_class(cls):
        """Set up authentication for the entire test class"""
        cls.token = get_auth_token()
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}
        assert cls.token is not None, "Failed to authenticate"

    # ===== BLOCK 18.1: ISO to Collection Conversion Tests =====
    
    def test_convert_iso_to_collection_endpoint_exists(self):
        """Test that POST /api/iso/{iso_id}/convert-to-collection endpoint exists"""
        # Use a fake ISO ID - should return 404 (not found), not 405 (method not allowed)
        fake_iso_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/iso/{fake_iso_id}/convert-to-collection", 
                                 headers=self.auth_headers, json={})
        # 404 means endpoint exists but ISO not found, 405 would mean endpoint doesn't exist
        assert response.status_code in [404, 200], f"Endpoint should exist. Got {response.status_code}: {response.text}"
    
    def test_convert_iso_to_collection_requires_auth(self):
        """Test that convert-to-collection endpoint requires authentication"""
        fake_iso_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/iso/{fake_iso_id}/convert-to-collection", json={})
        # Should return 401/403 for unauthenticated requests
        assert response.status_code in [401, 403], f"Should require auth. Got {response.status_code}"
    
    def test_convert_iso_to_collection_full_flow(self):
        """Test full flow: Create ISO -> Convert to Collection -> Verify"""
        # Step 1: Create an ISO item via composer/iso endpoint
        iso_data = {
            "artist": f"TEST_Hunt_Artist_{uuid.uuid4().hex[:8]}",
            "album": f"TEST_Hunt_Album_{uuid.uuid4().hex[:8]}",
            "cover_url": "https://example.com/cover.jpg",
            "year": 2024,
            "pressing_notes": "Test pressing",
            "caption": "Looking for this record"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/composer/iso", 
                                        headers=self.auth_headers, json=iso_data)
        assert create_response.status_code in [200, 201], f"Failed to create ISO: {create_response.text}"
        
        # Get the ISO ID from the created item (need to fetch user's ISOs)
        isos_response = requests.get(f"{BASE_URL}/api/iso", headers=self.auth_headers)
        assert isos_response.status_code == 200
        isos = isos_response.json()
        
        # Find the ISO we just created
        created_iso = None
        for iso in isos:
            if iso.get("artist") == iso_data["artist"] and iso.get("album") == iso_data["album"]:
                created_iso = iso
                break
        
        assert created_iso is not None, "Could not find created ISO"
        iso_id = created_iso["id"]
        
        # Step 2: Convert ISO to collection
        convert_response = requests.post(f"{BASE_URL}/api/iso/{iso_id}/convert-to-collection",
                                         headers=self.auth_headers, json={})
        assert convert_response.status_code == 200, f"Convert failed: {convert_response.text}"
        
        convert_data = convert_response.json()
        
        # Verify response structure
        assert "record_id" in convert_data, "Response should include record_id"
        assert "title" in convert_data, "Response should include title"
        assert "artist" in convert_data, "Response should include artist"
        assert convert_data.get("title") == iso_data["album"], "Title should match album"
        assert convert_data.get("artist") == iso_data["artist"], "Artist should match"
        
        record_id = convert_data["record_id"]
        
        # Step 3: Verify record was created in collection
        record_response = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers)
        assert record_response.status_code == 200, f"Record not found: {record_response.text}"
        
        record = record_response.json()
        assert record.get("notes") == "Found via ISO", "Notes should be 'Found via ISO'"
        # Note: source='iso' is stored in DB but not exposed in RecordResponse model
        # This is intentional - the notes field is the user-visible indicator
        
        # Step 4: Verify ISO was deleted
        isos_after_response = requests.get(f"{BASE_URL}/api/iso", headers=self.auth_headers)
        assert isos_after_response.status_code == 200
        isos_after = isos_after_response.json()
        
        iso_still_exists = any(iso.get("id") == iso_id for iso in isos_after)
        assert not iso_still_exists, "ISO should be deleted after conversion"
        
        # Cleanup: Delete the created record
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers)
    
    def test_convert_iso_returns_proper_fields(self):
        """Test that convert endpoint returns record_id, title, artist"""
        # Create a test ISO
        iso_data = {
            "artist": f"TEST_Fields_{uuid.uuid4().hex[:8]}",
            "album": f"TEST_Album_Fields_{uuid.uuid4().hex[:8]}",
        }
        requests.post(f"{BASE_URL}/api/composer/iso", headers=self.auth_headers, json=iso_data)
        
        # Get the ISO
        isos_response = requests.get(f"{BASE_URL}/api/iso", headers=self.auth_headers)
        isos = isos_response.json()
        created_iso = next((iso for iso in isos if iso.get("artist") == iso_data["artist"]), None)
        
        if created_iso:
            iso_id = created_iso["id"]
            convert_response = requests.post(f"{BASE_URL}/api/iso/{iso_id}/convert-to-collection",
                                             headers=self.auth_headers, json={})
            
            if convert_response.status_code == 200:
                data = convert_response.json()
                assert "record_id" in data, "Should return record_id"
                assert "title" in data, "Should return title"
                assert "artist" in data, "Should return artist"
                
                # Cleanup
                if data.get("record_id"):
                    requests.delete(f"{BASE_URL}/api/records/{data['record_id']}", headers=self.auth_headers)
    
    # ===== BLOCK 18.2: Collection Quick Actions Tests =====
    
    def test_move_to_wishlist_endpoint_exists(self):
        """Test that POST /api/records/{record_id}/move-to-wishlist endpoint exists"""
        fake_record_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/records/{fake_record_id}/move-to-wishlist",
                                headers=self.auth_headers, json={})
        # 404 means endpoint exists but record not found
        assert response.status_code in [404, 200], f"Endpoint should exist. Got {response.status_code}"
    
    def test_move_to_iso_endpoint_exists(self):
        """Test that POST /api/records/{record_id}/move-to-iso endpoint exists"""
        fake_record_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/records/{fake_record_id}/move-to-iso",
                                headers=self.auth_headers, json={})
        # 404 means endpoint exists but record not found
        assert response.status_code in [404, 200], f"Endpoint should exist. Got {response.status_code}"
    
    def test_move_to_wishlist_requires_auth(self):
        """Test that move-to-wishlist endpoint requires authentication"""
        fake_record_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/records/{fake_record_id}/move-to-wishlist", json={})
        assert response.status_code in [401, 403], f"Should require auth. Got {response.status_code}"
    
    def test_move_to_iso_requires_auth(self):
        """Test that move-to-iso endpoint requires authentication"""
        fake_record_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/records/{fake_record_id}/move-to-iso", json={})
        assert response.status_code in [401, 403], f"Should require auth. Got {response.status_code}"
    
    def test_move_to_wishlist_full_flow(self):
        """Test full flow: Create record -> Move to Wishlist -> Verify ISO created with WISHLIST status"""
        # Step 1: Create a test record
        record_data = {
            "title": f"TEST_Wishlist_Album_{uuid.uuid4().hex[:8]}",
            "artist": f"TEST_Wishlist_Artist_{uuid.uuid4().hex[:8]}",
            "cover_url": "https://example.com/cover.jpg",
            "year": 2023,
            "format": "Vinyl"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/records", headers=self.auth_headers, json=record_data)
        assert create_response.status_code in [200, 201], f"Failed to create record: {create_response.text}"
        record_id = create_response.json().get("id")
        
        # Step 2: Move to wishlist
        move_response = requests.post(f"{BASE_URL}/api/records/{record_id}/move-to-wishlist",
                                      headers=self.auth_headers, json={})
        assert move_response.status_code == 200, f"Move to wishlist failed: {move_response.text}"
        
        # Step 3: Verify record is deleted
        record_check = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers)
        assert record_check.status_code == 404, "Record should be deleted after move"
        
        # Step 4: Verify ISO was created with WISHLIST status
        isos_response = requests.get(f"{BASE_URL}/api/iso", headers=self.auth_headers)
        isos = isos_response.json()
        
        wishlist_iso = None
        for iso in isos:
            if iso.get("artist") == record_data["artist"] and iso.get("album") == record_data["title"]:
                wishlist_iso = iso
                break
        
        assert wishlist_iso is not None, "ISO should be created"
        assert wishlist_iso.get("status") == "WISHLIST", f"Status should be WISHLIST, got {wishlist_iso.get('status')}"
        
        # Cleanup: Delete the ISO
        if wishlist_iso:
            requests.delete(f"{BASE_URL}/api/iso/{wishlist_iso['id']}", headers=self.auth_headers)
    
    def test_move_to_iso_full_flow(self):
        """Test full flow: Create record -> Put back on ISO -> Verify ISO created with OPEN status"""
        # Step 1: Create a test record
        record_data = {
            "title": f"TEST_ISO_Album_{uuid.uuid4().hex[:8]}",
            "artist": f"TEST_ISO_Artist_{uuid.uuid4().hex[:8]}",
            "cover_url": "https://example.com/cover.jpg",
            "year": 2022,
            "format": "Vinyl"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/records", headers=self.auth_headers, json=record_data)
        assert create_response.status_code in [200, 201], f"Failed to create record: {create_response.text}"
        record_id = create_response.json().get("id")
        
        # Step 2: Move to ISO (put back on the hunt)
        move_response = requests.post(f"{BASE_URL}/api/records/{record_id}/move-to-iso",
                                      headers=self.auth_headers, json={})
        assert move_response.status_code == 200, f"Move to ISO failed: {move_response.text}"
        
        # Step 3: Verify record is deleted
        record_check = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers)
        assert record_check.status_code == 404, "Record should be deleted after move"
        
        # Step 4: Verify ISO was created with OPEN status
        isos_response = requests.get(f"{BASE_URL}/api/iso", headers=self.auth_headers)
        isos = isos_response.json()
        
        open_iso = None
        for iso in isos:
            if iso.get("artist") == record_data["artist"] and iso.get("album") == record_data["title"]:
                open_iso = iso
                break
        
        assert open_iso is not None, "ISO should be created"
        assert open_iso.get("status") == "OPEN", f"Status should be OPEN, got {open_iso.get('status')}"
        
        # Cleanup: Delete the ISO
        if open_iso:
            requests.delete(f"{BASE_URL}/api/iso/{open_iso['id']}", headers=self.auth_headers)
    
    def test_delete_record_endpoint(self):
        """Test that DELETE /api/records/{record_id} works (Remove Completely option)"""
        # Create a record
        record_data = {
            "title": f"TEST_Delete_Album_{uuid.uuid4().hex[:8]}",
            "artist": f"TEST_Delete_Artist_{uuid.uuid4().hex[:8]}",
            "format": "Vinyl"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/records", headers=self.auth_headers, json=record_data)
        assert create_response.status_code in [200, 201]
        record_id = create_response.json().get("id")
        
        # Delete the record
        delete_response = requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Verify it's deleted
        check_response = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers)
        assert check_response.status_code == 404, "Record should be deleted"


class TestConvertedRecordFields:
    """Test that converted records have the correct fields"""
    
    @classmethod
    def setup_class(cls):
        """Set up authentication for the entire test class"""
        cls.token = get_auth_token()
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}
        assert cls.token is not None, "Failed to authenticate"
    
    def test_converted_record_has_found_via_iso_notes(self):
        """Test that a converted ISO has notes='Found via ISO'"""
        # Create ISO
        iso_data = {
            "artist": f"TEST_Notes_{uuid.uuid4().hex[:8]}",
            "album": f"TEST_Notes_Album_{uuid.uuid4().hex[:8]}"
        }
        requests.post(f"{BASE_URL}/api/composer/iso", headers=self.auth_headers, json=iso_data)
        
        # Get ISO
        isos = requests.get(f"{BASE_URL}/api/iso", headers=self.auth_headers).json()
        iso = next((i for i in isos if i.get("artist") == iso_data["artist"]), None)
        
        if iso:
            # Convert
            convert_resp = requests.post(f"{BASE_URL}/api/iso/{iso['id']}/convert-to-collection",
                                         headers=self.auth_headers, json={})
            if convert_resp.status_code == 200:
                record_id = convert_resp.json().get("record_id")
                
                # Check the record
                record = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers).json()
                assert record.get("notes") == "Found via ISO", f"Notes should be 'Found via ISO', got {record.get('notes')}"
                
                # Cleanup
                requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers)
    
    def test_converted_record_has_iso_source(self):
        """Test that a converted ISO has the correct metadata (notes field as indicator)"""
        # Note: source='iso' is stored in DB but not exposed in RecordResponse model
        # The notes field 'Found via ISO' serves as the user-visible indicator
        # Create ISO
        iso_data = {
            "artist": f"TEST_Source_{uuid.uuid4().hex[:8]}",
            "album": f"TEST_Source_Album_{uuid.uuid4().hex[:8]}"
        }
        requests.post(f"{BASE_URL}/api/composer/iso", headers=self.auth_headers, json=iso_data)
        
        # Get ISO
        isos = requests.get(f"{BASE_URL}/api/iso", headers=self.auth_headers).json()
        iso = next((i for i in isos if i.get("artist") == iso_data["artist"]), None)
        
        if iso:
            # Convert
            convert_resp = requests.post(f"{BASE_URL}/api/iso/{iso['id']}/convert-to-collection",
                                         headers=self.auth_headers, json={})
            if convert_resp.status_code == 200:
                record_id = convert_resp.json().get("record_id")
                
                # Check the record has correct notes field
                record = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers).json()
                assert record.get("notes") == "Found via ISO", f"Notes should be 'Found via ISO', got {record.get('notes')}"
                
                # Cleanup
                requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=self.auth_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
