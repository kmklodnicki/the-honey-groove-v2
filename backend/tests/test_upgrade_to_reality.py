"""
Test suite for 'Upgrade to Reality' feature - ISO acquire endpoint
Tests POST /api/iso/{iso_id}/acquire which converts ISO items to collection records with condition/price details
Also tests backwards compatibility with old POST /api/iso/{iso_id}/convert-to-collection endpoint
"""

import pytest
import requests
import os
import uuid

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
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def session(auth_token):
    """Create authenticated session"""
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return s


class TestISOAcquireEndpoint:
    """Tests for POST /api/iso/{iso_id}/acquire endpoint"""
    
    def test_acquire_with_full_condition_data(self, session):
        """Test acquiring ISO with media condition, sleeve condition, and price paid"""
        # Create a test ISO first
        iso_data = {
            "artist": "TEST_Artist_Acquire1",
            "album": "TEST_Album_Acquire1",
            "status": "OPEN",
            "priority": "HIGH"
        }
        create_resp = session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200, f"Failed to create ISO: {create_resp.text}"
        iso_id = create_resp.json()["id"]
        
        try:
            # Acquire the ISO with full condition data
            acquire_data = {
                "media_condition": "VG+",
                "sleeve_condition": "VG",
                "price_paid": 29.99
            }
            acquire_resp = session.post(f"{BASE_URL}/api/iso/{iso_id}/acquire", json=acquire_data)
            
            assert acquire_resp.status_code == 200, f"Acquire failed: {acquire_resp.text}"
            result = acquire_resp.json()
            
            # Verify response structure
            assert "message" in result
            assert "record_id" in result
            assert "title" in result
            assert "artist" in result
            
            # Verify message mentions Reality
            assert "Reality" in result["message"]
            
            # Verify record was created by fetching it
            record_id = result["record_id"]
            record_resp = session.get(f"{BASE_URL}/api/records/{record_id}")
            assert record_resp.status_code == 200, f"Failed to fetch created record: {record_resp.text}"
            
            record = record_resp.json()
            notes = record.get("notes", "")
            # Conditions and price are stored in the notes field
            assert "Found via The Hunt" in notes
            assert "Media: VG+" in notes
            assert "Sleeve: VG" in notes
            assert "Paid: $29.99" in notes
            
            print("PASSED: Acquire ISO with full condition data")
            
            # Cleanup - delete the created record
            session.delete(f"{BASE_URL}/api/records/{record_id}")
            
        except Exception as e:
            # Cleanup ISO if it still exists
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
            raise e
    
    def test_acquire_with_partial_data(self, session):
        """Test acquiring ISO with only media condition (optional fields)"""
        # Create a test ISO
        iso_data = {
            "artist": "TEST_Artist_Acquire2",
            "album": "TEST_Album_Acquire2",
            "status": "OPEN"
        }
        create_resp = session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200, f"Failed to create ISO: {create_resp.text}"
        iso_id = create_resp.json()["id"]
        
        try:
            # Acquire with only media condition
            acquire_data = {
                "media_condition": "NM"
            }
            acquire_resp = session.post(f"{BASE_URL}/api/iso/{iso_id}/acquire", json=acquire_data)
            
            assert acquire_resp.status_code == 200, f"Acquire failed: {acquire_resp.text}"
            result = acquire_resp.json()
            
            record_id = result["record_id"]
            record_resp = session.get(f"{BASE_URL}/api/records/{record_id}")
            record = record_resp.json()
            
            notes = record.get("notes", "")
            assert "Found via The Hunt" in notes
            assert "Media: NM" in notes
            # sleeve_condition and price_paid were not provided
            assert "Sleeve:" not in notes
            assert "Paid:" not in notes
            
            print("PASSED: Acquire ISO with partial data")
            
            # Cleanup
            session.delete(f"{BASE_URL}/api/records/{record_id}")
            
        except Exception as e:
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
            raise e
    
    def test_acquire_with_no_condition_data(self, session):
        """Test acquiring ISO without any condition data (all optional)"""
        # Create a test ISO
        iso_data = {
            "artist": "TEST_Artist_Acquire3",
            "album": "TEST_Album_Acquire3",
            "status": "OPEN"
        }
        create_resp = session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200, f"Failed to create ISO: {create_resp.text}"
        iso_id = create_resp.json()["id"]
        
        try:
            # Acquire with empty body
            acquire_resp = session.post(f"{BASE_URL}/api/iso/{iso_id}/acquire", json={})
            
            assert acquire_resp.status_code == 200, f"Acquire failed: {acquire_resp.text}"
            result = acquire_resp.json()
            
            record_id = result["record_id"]
            record_resp = session.get(f"{BASE_URL}/api/records/{record_id}")
            record = record_resp.json()
            
            # Should still have basic notes
            assert "Found via The Hunt" in record.get("notes", "")
            
            print("PASSED: Acquire ISO with no condition data")
            
            # Cleanup
            session.delete(f"{BASE_URL}/api/records/{record_id}")
            
        except Exception as e:
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
            raise e
    
    def test_acquire_nonexistent_iso(self, session):
        """Test acquiring a non-existent ISO returns 404"""
        fake_id = str(uuid.uuid4())
        acquire_resp = session.post(f"{BASE_URL}/api/iso/{fake_id}/acquire", json={
            "media_condition": "VG+"
        })
        
        assert acquire_resp.status_code == 404, f"Expected 404, got {acquire_resp.status_code}"
        print("PASSED: Acquire non-existent ISO returns 404")
    
    def test_acquire_removes_iso_from_list(self, session):
        """Test that acquiring ISO removes it from the ISO list"""
        # Create a test ISO
        iso_data = {
            "artist": "TEST_Artist_Acquire4",
            "album": "TEST_Album_Acquire4",
            "status": "OPEN"
        }
        create_resp = session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200
        iso_id = create_resp.json()["id"]
        
        try:
            # Verify ISO exists in list
            list_resp = session.get(f"{BASE_URL}/api/iso")
            isos_before = [iso["id"] for iso in list_resp.json()]
            assert iso_id in isos_before, "ISO should exist before acquire"
            
            # Acquire the ISO
            acquire_resp = session.post(f"{BASE_URL}/api/iso/{iso_id}/acquire", json={
                "media_condition": "VG+"
            })
            assert acquire_resp.status_code == 200
            record_id = acquire_resp.json()["record_id"]
            
            # Verify ISO no longer in list
            list_resp = session.get(f"{BASE_URL}/api/iso")
            isos_after = [iso["id"] for iso in list_resp.json()]
            assert iso_id not in isos_after, "ISO should be removed after acquire"
            
            print("PASSED: Acquire removes ISO from list")
            
            # Cleanup
            session.delete(f"{BASE_URL}/api/records/{record_id}")
            
        except Exception as e:
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
            raise e


class TestBackwardsCompatibility:
    """Tests for old POST /api/iso/{iso_id}/convert-to-collection endpoint (backwards compat)"""
    
    def test_old_convert_endpoint_still_works(self, session):
        """Test that old convert-to-collection endpoint still functions"""
        # Create a test ISO
        iso_data = {
            "artist": "TEST_Artist_Compat1",
            "album": "TEST_Album_Compat1",
            "status": "OPEN"
        }
        create_resp = session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200, f"Failed to create ISO: {create_resp.text}"
        iso_id = create_resp.json()["id"]
        
        try:
            # Use old endpoint
            convert_resp = session.post(f"{BASE_URL}/api/iso/{iso_id}/convert-to-collection")
            
            assert convert_resp.status_code == 200, f"Old convert endpoint failed: {convert_resp.text}"
            result = convert_resp.json()
            
            # Verify response structure
            assert "message" in result
            assert "record_id" in result
            assert "Hive" in result["message"]  # Old endpoint says "Hive"
            
            print("PASSED: Old convert-to-collection endpoint works")
            
            # Cleanup
            session.delete(f"{BASE_URL}/api/records/{result['record_id']}")
            
        except Exception as e:
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
            raise e
    
    def test_old_endpoint_uses_default_notes(self, session):
        """Test old endpoint creates record with default notes"""
        # Create a test ISO
        iso_data = {
            "artist": "TEST_Artist_Compat2",
            "album": "TEST_Album_Compat2",
            "status": "OPEN"
        }
        create_resp = session.post(f"{BASE_URL}/api/iso", json=iso_data)
        assert create_resp.status_code == 200
        iso_id = create_resp.json()["id"]
        
        try:
            # Use old endpoint
            convert_resp = session.post(f"{BASE_URL}/api/iso/{iso_id}/convert-to-collection")
            assert convert_resp.status_code == 200
            
            record_id = convert_resp.json()["record_id"]
            record_resp = session.get(f"{BASE_URL}/api/records/{record_id}")
            record = record_resp.json()
            
            # Old endpoint uses "Found via ISO" notes
            assert "Found via ISO" in record.get("notes", "")
            
            print("PASSED: Old endpoint uses default notes")
            
            # Cleanup
            session.delete(f"{BASE_URL}/api/records/{record_id}")
            
        except Exception as e:
            session.delete(f"{BASE_URL}/api/iso/{iso_id}")
            raise e


class TestGradeOptionsInAcquire:
    """Tests for grade options used in acquire endpoint"""
    
    def test_acquire_with_all_honey_grade_options(self, session):
        """Test acquiring with various honey-themed grade values"""
        grade_options = ["NM", "VG+", "VG", "G+", "F"]
        
        for grade in grade_options:
            # Create ISO
            iso_data = {
                "artist": f"TEST_Artist_Grade_{grade}",
                "album": f"TEST_Album_Grade_{grade}",
                "status": "OPEN"
            }
            create_resp = session.post(f"{BASE_URL}/api/iso", json=iso_data)
            assert create_resp.status_code == 200
            iso_id = create_resp.json()["id"]
            
            try:
                # Acquire with this grade
                acquire_resp = session.post(f"{BASE_URL}/api/iso/{iso_id}/acquire", json={
                    "media_condition": grade,
                    "sleeve_condition": grade
                })
                
                assert acquire_resp.status_code == 200, f"Failed for grade {grade}: {acquire_resp.text}"
                
                record_id = acquire_resp.json()["record_id"]
                record_resp = session.get(f"{BASE_URL}/api/records/{record_id}")
                record = record_resp.json()
                
                notes = record.get("notes", "")
                assert f"Media: {grade}" in notes
                assert f"Sleeve: {grade}" in notes
                
                # Cleanup
                session.delete(f"{BASE_URL}/api/records/{record_id}")
                
            except Exception as e:
                session.delete(f"{BASE_URL}/api/iso/{iso_id}")
                raise e
        
        print("PASSED: All honey-themed grade options work in acquire")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
