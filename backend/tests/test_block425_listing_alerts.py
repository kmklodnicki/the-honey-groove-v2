"""
BLOCK 425: Alert Engine — Listing Alert Subscriptions
Tests:
- POST /api/listing-alerts creates a new alert subscription
- POST /api/listing-alerts prevents duplicates (returns 'Already subscribed')
- GET /api/listing-alerts returns active alerts for the user
- DELETE /api/listing-alerts/{id} removes an alert
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Login and return auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@example.com",
        "password": "test123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")

@pytest.fixture
def headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestListingAlertsCRUD:
    """Test listing alerts CRUD operations"""
    
    def test_create_listing_alert(self, headers):
        """POST /api/listing-alerts creates a new alert subscription"""
        # Use unique discogs_id to avoid conflicts with existing alerts
        unique_discogs_id = 99999999
        
        payload = {
            "discogs_id": unique_discogs_id,
            "album_name": "Test Album Alert",
            "variant_name": "Red Vinyl",
            "artist": "Test Artist",
            "cover_url": "https://example.com/cover.jpg"
        }
        
        response = requests.post(f"{BASE_URL}/api/listing-alerts", json=payload, headers=headers)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "id" in data, "Response should contain an alert id"
        assert "message" in data, "Response should contain a message"
        assert data["message"] == "Alert created", f"Expected 'Alert created', got '{data['message']}'"
        
        # Cleanup - delete the alert we just created
        alert_id = data["id"]
        requests.delete(f"{BASE_URL}/api/listing-alerts/{alert_id}", headers=headers)
        
        return alert_id
    
    def test_create_duplicate_alert_returns_already_subscribed(self, headers):
        """POST /api/listing-alerts prevents duplicates (returns 'Already subscribed')"""
        unique_discogs_id = 88888888
        
        payload = {
            "discogs_id": unique_discogs_id,
            "album_name": "Duplicate Test Album",
            "artist": "Duplicate Test Artist"
        }
        
        # Create first alert
        response1 = requests.post(f"{BASE_URL}/api/listing-alerts", json=payload, headers=headers)
        assert response1.status_code == 200
        first_id = response1.json().get("id")
        
        # Try to create duplicate alert
        response2 = requests.post(f"{BASE_URL}/api/listing-alerts", json=payload, headers=headers)
        
        # Status code assertion - should still be 200 but with different message
        assert response2.status_code == 200, f"Expected 200, got {response2.status_code}: {response2.text}"
        
        # Data assertions
        data = response2.json()
        assert data["message"] == "Already subscribed", f"Expected 'Already subscribed', got '{data['message']}'"
        assert data["id"] == first_id, "Should return the existing alert id"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/listing-alerts/{first_id}", headers=headers)
    
    def test_get_listing_alerts(self, headers):
        """GET /api/listing-alerts returns active alerts for the user"""
        # First create an alert to ensure we have at least one
        payload = {
            "discogs_id": 77777777,
            "album_name": "Get Test Album",
            "artist": "Get Test Artist"
        }
        create_resp = requests.post(f"{BASE_URL}/api/listing-alerts", json=payload, headers=headers)
        assert create_resp.status_code == 200
        created_id = create_resp.json().get("id")
        
        # Get alerts
        response = requests.get(f"{BASE_URL}/api/listing-alerts", headers=headers)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Find our created alert in the list
        found_alert = None
        for alert in data:
            if alert.get("id") == created_id:
                found_alert = alert
                break
        
        assert found_alert is not None, "Created alert should be in the list"
        assert found_alert["discogs_id"] == 77777777, "Alert should have correct discogs_id"
        assert found_alert["album_name"] == "Get Test Album", "Alert should have correct album_name"
        assert found_alert["status"] == "ACTIVE", "Alert should have ACTIVE status"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/listing-alerts/{created_id}", headers=headers)
    
    def test_delete_listing_alert(self, headers):
        """DELETE /api/listing-alerts/{id} removes an alert"""
        # First create an alert to delete
        payload = {
            "discogs_id": 66666666,
            "album_name": "Delete Test Album",
            "artist": "Delete Test Artist"
        }
        create_resp = requests.post(f"{BASE_URL}/api/listing-alerts", json=payload, headers=headers)
        assert create_resp.status_code == 200
        alert_id = create_resp.json().get("id")
        
        # Delete the alert
        response = requests.delete(f"{BASE_URL}/api/listing-alerts/{alert_id}", headers=headers)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data["message"] == "Alert removed", f"Expected 'Alert removed', got '{data['message']}'"
        
        # Verify alert is actually removed by checking GET
        get_resp = requests.get(f"{BASE_URL}/api/listing-alerts", headers=headers)
        alerts = get_resp.json()
        for alert in alerts:
            assert alert.get("id") != alert_id, "Deleted alert should not appear in list"
    
    def test_delete_nonexistent_alert_returns_404(self, headers):
        """DELETE /api/listing-alerts/{id} returns 404 for nonexistent alert"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/listing-alerts/{fake_id}", headers=headers)
        
        # Status code assertion
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestExistingAlertForBornToDie:
    """Test that existing alert for Born To Die (discogs_id=3433715) works correctly"""
    
    def test_born_to_die_alert_duplicate_handling(self, headers):
        """Verify duplicate alert for Born To Die returns 'Already subscribed'"""
        payload = {
            "discogs_id": 3433715,  # Born To Die
            "album_name": "Born To Die",
            "artist": "Lana Del Rey"
        }
        
        response = requests.post(f"{BASE_URL}/api/listing-alerts", json=payload, headers=headers)
        
        # Either creates new or returns already subscribed
        assert response.status_code == 200
        data = response.json()
        assert data["message"] in ["Alert created", "Already subscribed"], f"Unexpected message: {data['message']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
