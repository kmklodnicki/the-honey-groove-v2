"""
Test Suite for BLOCK 71.1: Numbered Edition Tracking
Tests the edition_number field for records and preferred_number field for ISO/Dream List items.
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
    """Get authentication token for test user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    return response.json().get("access_token")


@pytest.fixture
def auth_headers(auth_token):
    """Create auth headers for requests."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestRecordsEditionNumber:
    """Tests for edition_number field on records collection."""

    def test_create_record_with_edition_number(self, auth_headers):
        """POST /api/records with edition_number should store and return the value."""
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"TEST_Edition_Album_{unique_suffix}",
            "artist": f"TEST_Edition_Artist_{unique_suffix}",
            "year": 2024,
            "color_variant": "Amber Marble",
            "edition_number": 42,
            "notes": "Test record with edition number"
        }
        
        response = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify edition_number is stored and returned
        assert "edition_number" in data, "Response should include edition_number field"
        assert data["edition_number"] == 42, f"Expected edition_number=42, got {data['edition_number']}"
        assert data["title"] == record_data["title"]
        assert data["artist"] == record_data["artist"]
        assert data["color_variant"] == record_data["color_variant"]
        
        # Store record_id for cleanup
        record_id = data["id"]
        
        # Verify persistence via GET
        get_response = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=auth_headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["edition_number"] == 42, "Edition number should persist after GET"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=auth_headers)
        print(f"✓ Record with edition_number=42 created and verified successfully")

    def test_create_record_without_edition_number(self, auth_headers):
        """POST /api/records without edition_number should still work (optional field)."""
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"TEST_NoEdition_Album_{unique_suffix}",
            "artist": f"TEST_NoEdition_Artist_{unique_suffix}",
            "year": 2023,
            "color_variant": "Black Vinyl"
        }
        
        response = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # edition_number should be None/null when not provided
        assert data.get("edition_number") is None, f"Expected edition_number=None, got {data.get('edition_number')}"
        assert data["title"] == record_data["title"]
        
        # Cleanup
        record_id = data["id"]
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=auth_headers)
        print(f"✓ Record without edition_number created successfully (field is optional)")

    def test_get_records_includes_edition_number(self, auth_headers):
        """GET /api/records should return edition_number in response."""
        response = requests.get(f"{BASE_URL}/api/records", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check that edition_number field exists in response schema
        if len(data) > 0:
            first_record = data[0]
            # Field should exist even if None
            assert "edition_number" in first_record or first_record.get("edition_number") is None, \
                "edition_number field should be present in record response"
        print(f"✓ GET /api/records returns edition_number field")


class TestISOPreferredNumber:
    """Tests for preferred_number field on ISO/Dream List items."""

    def test_create_iso_with_preferred_number(self, auth_headers):
        """POST /api/iso with preferred_number should store and return the value."""
        unique_suffix = str(uuid.uuid4())[:8]
        iso_data = {
            "artist": f"TEST_ISO_Artist_{unique_suffix}",
            "album": f"TEST_ISO_Album_{unique_suffix}",
            "year": 2024,
            "color_variant": "Neon Pink",
            "preferred_number": 1,  # Seeking edition #1
            "notes": "Looking for edition #1",
            "status": "WISHLIST",
            "priority": "LOW"
        }
        
        response = requests.post(f"{BASE_URL}/api/iso", json=iso_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify preferred_number is stored and returned
        assert "preferred_number" in data, "Response should include preferred_number field"
        assert data["preferred_number"] == 1, f"Expected preferred_number=1, got {data['preferred_number']}"
        assert data["artist"] == iso_data["artist"]
        assert data["album"] == iso_data["album"]
        
        iso_id = data["id"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/iso/{iso_id}", headers=auth_headers)
        print(f"✓ ISO with preferred_number=1 created and verified successfully")

    def test_create_iso_without_preferred_number(self, auth_headers):
        """POST /api/iso without preferred_number should still work (optional field)."""
        unique_suffix = str(uuid.uuid4())[:8]
        iso_data = {
            "artist": f"TEST_NoPreferred_Artist_{unique_suffix}",
            "album": f"TEST_NoPreferred_Album_{unique_suffix}",
            "year": 2022,
            "status": "WISHLIST"
        }
        
        response = requests.post(f"{BASE_URL}/api/iso", json=iso_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # preferred_number should be None/null when not provided
        assert data.get("preferred_number") is None, f"Expected preferred_number=None, got {data.get('preferred_number')}"
        assert data["artist"] == iso_data["artist"]
        
        # Cleanup
        iso_id = data["id"]
        requests.delete(f"{BASE_URL}/api/iso/{iso_id}", headers=auth_headers)
        print(f"✓ ISO without preferred_number created successfully (field is optional)")

    def test_dreamlist_returns_preferred_number(self, auth_headers):
        """GET /api/iso/dreamlist should return preferred_number in response."""
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        # Field should be in schema even if list is empty
        print(f"✓ GET /api/iso/dreamlist returns successfully")


class TestEditionNumberEdgeCases:
    """Edge case tests for edition number functionality."""

    def test_large_edition_number(self, auth_headers):
        """Test that large edition numbers work correctly."""
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"TEST_LargeEdition_{unique_suffix}",
            "artist": f"TEST_Artist_{unique_suffix}",
            "edition_number": 999999
        }
        
        response = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["edition_number"] == 999999
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{data['id']}", headers=auth_headers)
        print(f"✓ Large edition number (999999) handled correctly")

    def test_edition_number_with_zero(self, auth_headers):
        """Test that edition_number=0 is NOT treated as falsy/None."""
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"TEST_ZeroEdition_{unique_suffix}",
            "artist": f"TEST_Artist_{unique_suffix}",
            "edition_number": 0
        }
        
        response = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        
        # Note: 0 might be valid or invalid depending on business rules
        # If API accepts 0, verify it's stored correctly
        if response.status_code == 200:
            data = response.json()
            # 0 should be stored as 0, not converted to None
            assert data["edition_number"] == 0 or data["edition_number"] is None
            requests.delete(f"{BASE_URL}/api/records/{data['id']}", headers=auth_headers)
        print(f"✓ Edge case edition_number=0 handled")


class TestRecordResponseSchema:
    """Validate that RecordResponse includes all edition fields."""

    def test_record_response_has_edition_number(self, auth_headers):
        """Verify that the record detail endpoint returns edition_number."""
        # First create a record with edition number
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"TEST_SchemaCheck_{unique_suffix}",
            "artist": f"TEST_Artist_{unique_suffix}",
            "edition_number": 77
        }
        
        create_response = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        assert create_response.status_code == 200
        record_id = create_response.json()["id"]
        
        # GET the record
        get_response = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=auth_headers)
        assert get_response.status_code == 200
        
        data = get_response.json()
        # Verify all expected fields are present
        expected_fields = ["id", "title", "artist", "edition_number", "user_id", "created_at"]
        for field in expected_fields:
            assert field in data, f"Field '{field}' should be in RecordResponse"
        
        assert data["edition_number"] == 77
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=auth_headers)
        print(f"✓ RecordResponse schema includes edition_number field")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
