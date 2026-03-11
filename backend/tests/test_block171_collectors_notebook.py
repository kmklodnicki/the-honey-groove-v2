"""
Backend tests for Block 171: Collector's Notebook feature
Tests PUT /api/records/{record_id}/notes endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test users
DEMO_USER = {"email": "demo@test.com", "password": "demouser"}
TEST_USER = {"email": "testuser1", "password": "test123"}


@pytest.fixture(scope="module")
def demo_session():
    """Get authenticated session for demo user (owns records)"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    response = session.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
    if response.status_code != 200:
        pytest.skip(f"Demo user login failed: {response.status_code} - {response.text}")
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


@pytest.fixture(scope="module")
def testuser_session():
    """Get authenticated session for testuser1 (non-owner)"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    response = session.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    if response.status_code != 200:
        pytest.skip(f"Test user login failed: {response.status_code} - {response.text}")
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


@pytest.fixture(scope="module")
def demo_record_id(demo_session):
    """Get the first record ID owned by demo user"""
    response = demo_session.get(f"{BASE_URL}/api/records")
    assert response.status_code == 200, f"Failed to get records: {response.text}"
    
    records = response.json()
    assert len(records) > 0, "Demo user has no records"
    
    return records[0]["id"]


class TestCollectorsNotebookEndpoint:
    """Tests for PUT /api/records/{record_id}/notes endpoint"""
    
    def test_owner_can_update_notes(self, demo_session, demo_record_id):
        """Owner should be able to update notes for their own record"""
        test_notes = "TEST_NOTEBOOK: Testing collector's notebook feature - NM+ sleeve, VG+ disc"
        
        response = demo_session.put(
            f"{BASE_URL}/api/records/{demo_record_id}/notes",
            json={"notes": test_notes}
        )
        
        assert response.status_code == 200, f"Failed to update notes: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("notes") == test_notes
        print(f"PASS: Owner can update notes - status {response.status_code}")
    
    def test_notes_persist_after_update(self, demo_session, demo_record_id):
        """Notes should persist and be returned in record detail"""
        # First update notes
        unique_note = "TEST_PERSIST: Persisted note verification test"
        demo_session.put(
            f"{BASE_URL}/api/records/{demo_record_id}/notes",
            json={"notes": unique_note}
        )
        
        # Get record detail and verify notes are there
        response = demo_session.get(f"{BASE_URL}/api/records/{demo_record_id}/detail")
        assert response.status_code == 200, f"Failed to get record detail: {response.text}"
        
        data = response.json()
        record = data.get("record", {})
        assert record.get("notes") == unique_note, f"Notes not persisted correctly. Got: {record.get('notes')}"
        print(f"PASS: Notes persist after update - verified in record detail")
    
    def test_non_owner_cannot_update_notes(self, testuser_session, demo_record_id):
        """Non-owner should get 403 Forbidden when trying to update notes"""
        response = testuser_session.put(
            f"{BASE_URL}/api/records/{demo_record_id}/notes",
            json={"notes": "Unauthorized note attempt"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"PASS: Non-owner gets 403 Forbidden - status {response.status_code}")
    
    def test_update_notes_empty_string(self, demo_session, demo_record_id):
        """Owner can clear notes by setting empty string"""
        response = demo_session.put(
            f"{BASE_URL}/api/records/{demo_record_id}/notes",
            json={"notes": ""}
        )
        
        assert response.status_code == 200, f"Failed to clear notes: {response.text}"
        data = response.json()
        assert data.get("notes") == ""
        print(f"PASS: Owner can clear notes with empty string")
        
        # Restore original notes for other tests
        demo_session.put(
            f"{BASE_URL}/api/records/{demo_record_id}/notes",
            json={"notes": "NM+ sleeve, VG+ disc. Picked up at Amoeba Records 2023."}
        )
    
    def test_update_notes_nonexistent_record(self, demo_session):
        """Updating notes for non-existent record should return 404"""
        fake_id = "nonexistent-record-id-12345"
        response = demo_session.put(
            f"{BASE_URL}/api/records/{fake_id}/notes",
            json={"notes": "Test note"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"PASS: Non-existent record returns 404")
    
    def test_unauthenticated_cannot_update_notes(self, demo_record_id):
        """Unauthenticated request should be rejected"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.put(
            f"{BASE_URL}/api/records/{demo_record_id}/notes",
            json={"notes": "Unauthorized test"}
        )
        
        # Should get 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"PASS: Unauthenticated request rejected - status {response.status_code}")


class TestRecordDetailForNotebook:
    """Tests to verify record detail endpoint returns notes properly"""
    
    def test_owner_sees_notes_in_detail(self, demo_session, demo_record_id):
        """Owner should see notes in record detail"""
        # Set a note first
        test_note = "TEST_DETAIL: Owner visibility test note"
        demo_session.put(
            f"{BASE_URL}/api/records/{demo_record_id}/notes",
            json={"notes": test_note}
        )
        
        # Get detail
        response = demo_session.get(f"{BASE_URL}/api/records/{demo_record_id}/detail")
        assert response.status_code == 200
        
        data = response.json()
        record = data.get("record", {})
        owner = data.get("owner", {})
        
        assert "notes" in record, "notes field should be in record"
        assert record["notes"] == test_note
        
        # Verify owner is returned
        assert owner is not None, "Owner should be returned in detail"
        print(f"PASS: Owner sees notes in record detail")
    
    def test_detail_returns_owner_info(self, demo_session, demo_record_id):
        """Record detail should include owner info for ownership check"""
        response = demo_session.get(f"{BASE_URL}/api/records/{demo_record_id}/detail")
        assert response.status_code == 200
        
        data = response.json()
        owner = data.get("owner")
        
        assert owner is not None, "Owner should be in response"
        assert "id" in owner, "Owner should have id"
        assert "username" in owner, "Owner should have username"
        print(f"PASS: Record detail returns owner info - username: {owner.get('username')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
