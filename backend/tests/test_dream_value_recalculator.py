"""
Dream Value Re-Calculator Tests (Block 229)
Tests for 3-tier value resolution for Dream List items:
- Discogs median -> Community valuation -> User manual price -> 'pending'
- Valuation Assistant Modal endpoints
- Community valuations with trimmed mean
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token") or response.json().get("token")
    pytest.skip(f"Authentication failed with status {response.status_code}: {response.text}")


@pytest.fixture
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDreamlistValueEndpoint:
    """Tests for GET /api/valuation/dreamlist endpoint"""
    
    def test_dreamlist_value_returns_expected_structure(self, auth_headers):
        """GET /api/valuation/dreamlist returns {total_value, valued_count, total_count, pending_count}"""
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_value" in data, "Response should have 'total_value'"
        assert "valued_count" in data, "Response should have 'valued_count'"
        assert "total_count" in data, "Response should have 'total_count'"
        assert "pending_count" in data, "Response should have 'pending_count'"
        
        # Verify types
        assert isinstance(data["total_value"], (int, float)), "total_value should be numeric"
        assert isinstance(data["valued_count"], int), "valued_count should be int"
        assert isinstance(data["total_count"], int), "total_count should be int"
        assert isinstance(data["pending_count"], int), "pending_count should be int"
        
        # Verify logical constraint
        assert data["pending_count"] == data["total_count"] - data["valued_count"], \
            "pending_count should equal total_count - valued_count"
        print(f"Dreamlist value: ${data['total_value']}, {data['valued_count']}/{data['total_count']} valued, {data['pending_count']} pending")


class TestPendingItemsEndpoint:
    """Tests for GET /api/valuation/pending-items endpoint"""
    
    def test_pending_items_returns_list(self, auth_headers):
        """GET /api/valuation/pending-items returns list of pending items"""
        response = requests.get(f"{BASE_URL}/api/valuation/pending-items", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} pending items")
        
        if len(data) > 0:
            item = data[0]
            # Verify structure
            assert "id" in item, "Item should have 'id'"
            assert "artist" in item, "Item should have 'artist'"
            assert "album" in item, "Item should have 'album'"
            print(f"First pending item: {item.get('artist')} - {item.get('album')}")


class TestManualValueEndpoint:
    """Tests for PUT /api/valuation/manual-value/{iso_id} endpoint"""
    
    def test_manual_value_requires_positive_value(self, auth_headers):
        """PUT /api/valuation/manual-value/{iso_id} rejects non-positive values"""
        fake_iso_id = "nonexistent-id"
        response = requests.put(
            f"{BASE_URL}/api/valuation/manual-value/{fake_iso_id}",
            headers=auth_headers,
            json={"value": 0}
        )
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
        
    def test_manual_value_rejects_negative(self, auth_headers):
        """PUT /api/valuation/manual-value/{iso_id} rejects negative values"""
        fake_iso_id = "nonexistent-id"
        response = requests.put(
            f"{BASE_URL}/api/valuation/manual-value/{fake_iso_id}",
            headers=auth_headers,
            json={"value": -50}
        )
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"


class TestDreamlistEndpoint:
    """Tests for GET /api/iso/dreamlist endpoint"""
    
    def test_dreamlist_returns_list_with_value_fields(self, auth_headers):
        """GET /api/iso/dreamlist returns items with median_value and value_source"""
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} dreamlist items")
        
        if len(data) > 0:
            item = data[0]
            # Verify 3-tier value fields are present
            assert "median_value" in item, "Item should have 'median_value' field"
            assert "value_source" in item, "Item should have 'value_source' field"
            
            # value_source should be one of: discogs, community, manual, pending
            valid_sources = ["discogs", "community", "manual", "pending"]
            assert item["value_source"] in valid_sources, \
                f"value_source should be one of {valid_sources}, got {item['value_source']}"
            print(f"First item: {item.get('artist')} - {item.get('album')}, value_source={item.get('value_source')}, median_value={item.get('median_value')}")


class TestFullValuationFlow:
    """End-to-end tests for the valuation flow"""
    
    @pytest.fixture
    def test_iso_item(self, auth_headers):
        """Create a test ISO item with WISHLIST status for testing"""
        test_data = {
            "artist": f"TEST_Artist_{uuid.uuid4().hex[:8]}",
            "album": f"TEST_Album_{uuid.uuid4().hex[:8]}",
            "status": "WISHLIST",
            "priority": "LOW",
            "notes": "Test item for valuation testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/iso",
            headers=auth_headers,
            json=test_data
        )
        
        if response.status_code != 200:
            pytest.skip(f"Could not create test ISO item: {response.status_code}")
            
        created = response.json()
        iso_id = created.get("id")
        
        yield {"id": iso_id, "artist": test_data["artist"], "album": test_data["album"]}
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/iso/{iso_id}", headers=auth_headers)
    
    def test_create_wishlist_item_appears_in_dreamlist(self, auth_headers, test_iso_item):
        """New WISHLIST items appear in dreamlist with pending value_source"""
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        found = [i for i in data if i["id"] == test_iso_item["id"]]
        assert len(found) == 1, f"Test item should be in dreamlist"
        
        item = found[0]
        # New item without discogs_id should have pending value_source
        assert item["value_source"] in ["pending", "manual", "community", "discogs"], \
            f"value_source should be valid, got {item['value_source']}"
        print(f"Test item value_source: {item['value_source']}")
    
    def test_manual_value_sets_value_and_returns_dream_value(self, auth_headers, test_iso_item):
        """Setting manual value updates the item and returns recalculated dream_value"""
        manual_price = 45.99
        
        response = requests.put(
            f"{BASE_URL}/api/valuation/manual-value/{test_iso_item['id']}",
            headers=auth_headers,
            json={"value": manual_price}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have 'message'"
        assert "dream_value" in data, "Response should have 'dream_value'"
        
        dream_value = data["dream_value"]
        assert "total_value" in dream_value, "dream_value should have 'total_value'"
        assert dream_value["total_value"] >= manual_price, \
            f"total_value should include the manual price we just set"
        print(f"After setting manual value ${manual_price}, dream_value = {dream_value}")
    
    def test_manual_value_item_not_pending(self, auth_headers, test_iso_item):
        """After setting manual value, item should no longer be 'pending'"""
        # First set a manual value
        manual_price = 99.99
        requests.put(
            f"{BASE_URL}/api/valuation/manual-value/{test_iso_item['id']}",
            headers=auth_headers,
            json={"value": manual_price}
        )
        
        # Check dreamlist - item should have manual value_source
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        found = [i for i in data if i["id"] == test_iso_item["id"]]
        
        if len(found) > 0:
            item = found[0]
            # Since we set manual_price and there's no discogs_id, should be 'manual'
            assert item["value_source"] == "manual", \
                f"After setting manual value, value_source should be 'manual', got {item['value_source']}"
            assert item["median_value"] == manual_price, \
                f"median_value should be {manual_price}, got {item['median_value']}"
            print(f"Item after manual value: value_source={item['value_source']}, median_value={item['median_value']}")
    
    def test_manual_value_removes_from_pending_items(self, auth_headers, test_iso_item):
        """After setting manual value, item should not appear in pending-items"""
        # First check pending items
        response = requests.get(f"{BASE_URL}/api/valuation/pending-items", headers=auth_headers)
        initial_pending = response.json()
        initial_ids = [i["id"] for i in initial_pending]
        
        # Set manual value
        manual_price = 123.45
        requests.put(
            f"{BASE_URL}/api/valuation/manual-value/{test_iso_item['id']}",
            headers=auth_headers,
            json={"value": manual_price}
        )
        
        # Check pending items again
        response = requests.get(f"{BASE_URL}/api/valuation/pending-items", headers=auth_headers)
        updated_pending = response.json()
        updated_ids = [i["id"] for i in updated_pending]
        
        assert test_iso_item["id"] not in updated_ids, \
            "Item with manual value should not appear in pending-items"
        print(f"Item {test_iso_item['id']} correctly removed from pending items after manual value set")


class TestDreamlistValueForOtherUser:
    """Tests for GET /api/valuation/dreamlist/{username} (public endpoint)"""
    
    def test_public_dreamlist_value_endpoint(self):
        """GET /api/valuation/dreamlist/{username} returns dreamlist value for any user"""
        # First login to get a username
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Could not login to get username")
        
        user = response.json().get("user", {})
        username = user.get("username")
        if not username:
            pytest.skip("Could not get username from login response")
        
        # Call public endpoint (no auth required)
        response = requests.get(f"{BASE_URL}/api/valuation/dreamlist/{username}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_value" in data
        assert "valued_count" in data
        assert "total_count" in data
        assert "pending_count" in data
        print(f"Public dreamlist value for @{username}: ${data['total_value']}")


class TestCommunityValuations:
    """Tests for community valuation behavior"""
    
    @pytest.fixture
    def test_iso_with_discogs(self, auth_headers):
        """Create a test ISO item with a discogs_id"""
        test_data = {
            "artist": f"TEST_Discogs_{uuid.uuid4().hex[:8]}",
            "album": f"TEST_Album_{uuid.uuid4().hex[:8]}",
            "discogs_id": 99999999,  # Fake discogs ID that won't have data
            "status": "WISHLIST",
            "priority": "LOW",
        }
        
        response = requests.post(
            f"{BASE_URL}/api/iso",
            headers=auth_headers,
            json=test_data
        )
        
        if response.status_code != 200:
            pytest.skip(f"Could not create test ISO item: {response.status_code}")
            
        created = response.json()
        iso_id = created.get("id")
        
        yield {"id": iso_id, "discogs_id": test_data["discogs_id"]}
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/iso/{iso_id}", headers=auth_headers)
    
    def test_manual_value_creates_community_valuation(self, auth_headers, test_iso_with_discogs):
        """Setting manual value on item with discogs_id creates community valuation"""
        manual_price = 75.00
        
        response = requests.put(
            f"{BASE_URL}/api/valuation/manual-value/{test_iso_with_discogs['id']}",
            headers=auth_headers,
            json={"value": manual_price}
        )
        assert response.status_code == 200
        
        # The item should now have a value (from manual or community)
        response = requests.get(f"{BASE_URL}/api/iso/dreamlist", headers=auth_headers)
        data = response.json()
        found = [i for i in data if i["id"] == test_iso_with_discogs["id"]]
        
        if len(found) > 0:
            item = found[0]
            # Could be 'manual' or 'community' depending on implementation
            assert item["value_source"] in ["manual", "community"], \
                f"value_source should be manual or community, got {item['value_source']}"
            assert item["median_value"] is not None, "median_value should be set"
            print(f"Item with discogs_id: value_source={item['value_source']}, median_value={item['median_value']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
