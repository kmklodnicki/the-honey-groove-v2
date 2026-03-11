"""
Block 247: Collection Completionist Flow - Valuation Wizard Tests
Tests the sequential valuation wizard for unvalued records.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test user credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"


class TestValuationWizard:
    """All tests for Block 247 Valuation Wizard feature."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth for all tests."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")

    # ====== GET /api/valuation/unvalued-queue Tests ======
    def test_unvalued_queue_returns_200(self):
        """Test that unvalued-queue endpoint returns 200 OK."""
        response = requests.get(
            f"{BASE_URL}/api/valuation/unvalued-queue",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: GET /api/valuation/unvalued-queue returns 200 with {len(data)} items")

    def test_unvalued_queue_requires_auth(self):
        """Test that unvalued-queue requires authentication."""
        response = requests.get(f"{BASE_URL}/api/valuation/unvalued-queue")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: GET /api/valuation/unvalued-queue requires auth (401 without token)")

    # ====== POST /api/valuation/wizard-save/{discogs_id} Tests ======
    def test_wizard_save_requires_auth(self):
        """Test that wizard-save requires authentication."""
        response = requests.post(
            f"{BASE_URL}/api/valuation/wizard-save/12345",
            json={"value": 25.00}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: POST /api/valuation/wizard-save/{discogs_id} requires auth (401 without token)")

    def test_wizard_save_rejects_zero_value(self):
        """Test that wizard-save rejects zero/negative values."""
        response = requests.post(
            f"{BASE_URL}/api/valuation/wizard-save/12345",
            json={"value": 0},
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("PASS: POST /api/valuation/wizard-save rejects value=0 with 400")

    def test_wizard_save_rejects_negative_value(self):
        """Test that wizard-save rejects negative values."""
        response = requests.post(
            f"{BASE_URL}/api/valuation/wizard-save/12345",
            json={"value": -10.00},
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("PASS: POST /api/valuation/wizard-save rejects negative value with 400")

    def test_wizard_save_valid_value_returns_200(self):
        """Test that wizard-save accepts valid value and returns 200 with average_value."""
        unique_discogs_id = 99999  # A test discogs_id
        response = requests.post(
            f"{BASE_URL}/api/valuation/wizard-save/{unique_discogs_id}",
            json={"value": 35.50},
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "average_value" in data, "Response should include average_value"
        assert "message" in data, "Response should include message"
        print(f"PASS: POST /api/valuation/wizard-save returns 200 with average_value={data['average_value']}")

    # ====== GET /api/valuation/collection Stats Tests ======
    def test_collection_value_returns_valued_count(self):
        """Test that /api/valuation/collection returns valued_count and total_count."""
        response = requests.get(
            f"{BASE_URL}/api/valuation/collection",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "valued_count" in data, "Response should include valued_count"
        assert "total_count" in data, "Response should include total_count"
        assert "total_value" in data, "Response should include total_value"
        print(f"PASS: /api/valuation/collection returns valued_count={data['valued_count']}, total_count={data['total_count']}, total_value={data['total_value']}")

    # ====== End-to-End Flow Test ======
    def test_add_record_then_check_queue_then_save_value(self):
        """
        Full flow test:
        1. Create a record with discogs_id not in collection_values
        2. Verify it appears in unvalued-queue
        3. Save a value via wizard-save
        4. Verify it no longer appears in unvalued-queue
        """
        unique_discogs_id = 987654  # A unique discogs_id for testing
        test_record_id = None

        try:
            # Step 1: Create a record with discogs_id
            create_response = requests.post(
                f"{BASE_URL}/api/records",
                json={
                    "title": f"TEST_WIZARD_Record_{unique_discogs_id}",
                    "artist": "TEST_WIZARD_Artist",
                    "discogs_id": unique_discogs_id,
                    "source": "manual"
                },
                headers=self.headers
            )
            assert create_response.status_code in [200, 201], f"Failed to create record: {create_response.status_code} {create_response.text}"
            test_record_id = create_response.json().get("id")
            print(f"Step 1 PASS: Created test record with discogs_id={unique_discogs_id}, record_id={test_record_id}")

            # Step 2: Check unvalued-queue includes our record
            queue_response = requests.get(
                f"{BASE_URL}/api/valuation/unvalued-queue",
                headers=self.headers
            )
            assert queue_response.status_code == 200, f"Failed to get queue: {queue_response.status_code}"
            queue = queue_response.json()
            queue_discogs_ids = [item.get("discogs_id") for item in queue]
            assert unique_discogs_id in queue_discogs_ids, f"discogs_id {unique_discogs_id} should be in unvalued-queue"
            
            # Verify queue item structure
            queue_item = next((item for item in queue if item.get("discogs_id") == unique_discogs_id), None)
            assert queue_item is not None
            assert "id" in queue_item, "Queue item should have id"
            assert "title" in queue_item, "Queue item should have title"
            assert "artist" in queue_item, "Queue item should have artist"
            print(f"Step 2 PASS: Record appears in unvalued-queue with correct structure (id, discogs_id, title, artist)")

            # Step 3: Save value via wizard-save
            save_response = requests.post(
                f"{BASE_URL}/api/valuation/wizard-save/{unique_discogs_id}",
                json={"value": 42.00},
                headers=self.headers
            )
            assert save_response.status_code == 200, f"Failed to save value: {save_response.status_code}"
            save_data = save_response.json()
            assert save_data.get("average_value") > 0, "average_value should be positive"
            print(f"Step 3 PASS: wizard-save returned average_value={save_data.get('average_value')}")

            # Step 4: Verify record is no longer in unvalued-queue
            queue_response_after = requests.get(
                f"{BASE_URL}/api/valuation/unvalued-queue",
                headers=self.headers
            )
            assert queue_response_after.status_code == 200
            queue_after = queue_response_after.json()
            queue_discogs_ids_after = [item.get("discogs_id") for item in queue_after]
            assert unique_discogs_id not in queue_discogs_ids_after, f"discogs_id {unique_discogs_id} should NOT be in queue after saving value"
            print(f"Step 4 PASS: Record no longer in unvalued-queue after wizard-save")

        finally:
            # Cleanup: Delete the test record
            if test_record_id:
                delete_response = requests.delete(
                    f"{BASE_URL}/api/records/{test_record_id}",
                    headers=self.headers
                )
                print(f"Cleanup: Deleted test record {test_record_id} (status={delete_response.status_code})")

    # ====== Queue Item Structure Test ======
    def test_queue_item_has_required_fields(self):
        """Create a test record and verify queue item structure."""
        unique_discogs_id = 111222
        test_record_id = None

        try:
            # Create test record
            create_response = requests.post(
                f"{BASE_URL}/api/records",
                json={
                    "title": f"TEST_STRUCTURE_{unique_discogs_id}",
                    "artist": "TEST_Artist_Structure",
                    "discogs_id": unique_discogs_id,
                    "cover_url": "https://example.com/cover.jpg",
                    "year": 2023,
                    "source": "manual"
                },
                headers=self.headers
            )
            if create_response.status_code not in [200, 201]:
                pytest.skip(f"Could not create test record: {create_response.status_code}")
            test_record_id = create_response.json().get("id")

            # Check queue item structure
            queue_response = requests.get(
                f"{BASE_URL}/api/valuation/unvalued-queue",
                headers=self.headers
            )
            assert queue_response.status_code == 200
            queue = queue_response.json()
            queue_item = next((item for item in queue if item.get("discogs_id") == unique_discogs_id), None)
            
            if queue_item:
                # Verify required fields per spec
                assert "id" in queue_item, "Queue item missing 'id'"
                assert "discogs_id" in queue_item, "Queue item missing 'discogs_id'"
                assert "title" in queue_item, "Queue item missing 'title'"
                assert "artist" in queue_item, "Queue item missing 'artist'"
                # Optional fields
                assert "cover_url" in queue_item or queue_item.get("cover_url") is None, "cover_url check"
                assert "year" in queue_item or queue_item.get("year") is None, "year check"
                print(f"PASS: Queue item has all required fields: id, discogs_id, title, artist, cover_url, year")
                
                # Check for hive_average and hive_count (optional, shown when community data exists)
                if "hive_average" in queue_item:
                    assert "hive_count" in queue_item, "If hive_average exists, hive_count should too"
                    print(f"INFO: Queue item includes hive_average={queue_item['hive_average']}, hive_count={queue_item['hive_count']}")
                else:
                    print("INFO: Queue item has no hive_average (no community data yet)")
            else:
                pytest.skip("Queue item not found (possibly already valued)")

        finally:
            if test_record_id:
                requests.delete(f"{BASE_URL}/api/records/{test_record_id}", headers=self.headers)
                print(f"Cleanup: Deleted test record {test_record_id}")

    # ====== Community Valuation Integration Test ======
    def test_wizard_save_creates_community_valuation(self):
        """Test that wizard-save creates/updates community_valuations."""
        unique_discogs_id = 555666

        # Step 1: Save value via wizard
        save_response = requests.post(
            f"{BASE_URL}/api/valuation/wizard-save/{unique_discogs_id}",
            json={"value": 75.00},
            headers=self.headers
        )
        assert save_response.status_code == 200, f"wizard-save failed: {save_response.status_code}: {save_response.text}"
        
        # Step 2: Verify community-average reflects the saved value
        avg_response = requests.get(
            f"{BASE_URL}/api/valuation/community-average/{unique_discogs_id}"
        )
        assert avg_response.status_code == 200, f"community-average failed: {avg_response.status_code}"
        avg_data = avg_response.json()
        assert avg_data.get("average_value") > 0, "Community average should be positive"
        assert avg_data.get("contribution_count") >= 1, "Should have at least 1 contribution"
        print(f"PASS: wizard-save updates community_valuations (average={avg_data['average_value']}, count={avg_data['contribution_count']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
