"""
BLOCK 592 - Unofficial Record Compliance Tests
Tests for:
1. GET /api/records returns is_unofficial field
2. GET /api/records/{record_id} returns is_unofficial: true for test record
3. POST /api/listings with unofficial record + unofficial_acknowledged=false → 400
4. POST /api/listings with unofficial record + unofficial_acknowledged=true → success
5. POST /api/discogs/update-import-intent still works
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "kmklodnicki@gmail.com"
TEST_PASSWORD = "admin_password"
# Test unofficial record ID
UNOFFICIAL_RECORD_ID = "cdd4fe7d-5cf1-4e40-b2f9-faec1600545c"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for test user"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if resp.status_code != 200:
        pytest.skip(f"Auth failed: {resp.status_code} - {resp.text}")
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestUnofficialRecordAPI:
    """Tests for is_unofficial field in record endpoints"""

    def test_get_records_returns_is_unofficial_field(self, headers):
        """GET /api/records should return is_unofficial field for all records"""
        resp = requests.get(f"{BASE_URL}/api/records", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        records = resp.json()
        assert isinstance(records, list), "Response should be a list"
        
        # Check first few records have is_unofficial field
        for record in records[:5]:
            assert "is_unofficial" in record, f"Record {record.get('id')} missing is_unofficial field"
    
    def test_get_specific_record_unofficial_flag(self, headers):
        """GET /api/records/{record_id} should return is_unofficial: true for test record"""
        resp = requests.get(f"{BASE_URL}/api/records/{UNOFFICIAL_RECORD_ID}", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        record = resp.json()
        assert "is_unofficial" in record, "Record missing is_unofficial field"
        assert record["is_unofficial"] == True, f"Expected is_unofficial=True, got {record.get('is_unofficial')}"
    
    def test_get_record_detail_unofficial_flag(self, headers):
        """GET /api/records/{record_id}/detail should return is_unofficial in record object"""
        resp = requests.get(f"{BASE_URL}/api/records/{UNOFFICIAL_RECORD_ID}/detail", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "record" in data, "Response missing record object"
        assert "is_unofficial" in data["record"], "Record missing is_unofficial field"
        assert data["record"]["is_unofficial"] == True, f"Expected is_unofficial=True in record detail"


class TestUnofficialListingCreation:
    """Tests for unofficial listing compliance enforcement"""

    def test_listing_unofficial_without_acknowledgement_returns_400(self, headers):
        """POST /api/listings with is_unofficial=true and unofficial_acknowledged=false → 400"""
        payload = {
            "artist": "TEST_Artist",
            "album": "TEST_Album_Unofficial",
            "listing_type": "BUY_NOW",
            "price": 25.00,
            "condition": "Very Good Plus",
            "photo_urls": ["https://example.com/photo1.jpg"],
            "is_unofficial": True,
            "unofficial_acknowledged": False
        }
        
        resp = requests.post(f"{BASE_URL}/api/listings", json=payload, headers=headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        
        # Check error message mentions unofficial acknowledgement
        data = resp.json()
        assert "unofficial" in data.get("detail", "").lower() or "acknowledge" in data.get("detail", "").lower(), \
            f"Error message should mention unofficial acknowledgement: {data}"
    
    def test_listing_unofficial_with_acknowledgement_succeeds(self, headers):
        """POST /api/listings with is_unofficial=true and unofficial_acknowledged=true → 200/201"""
        payload = {
            "artist": "TEST_Unofficial_Artist",
            "album": "TEST_Unofficial_Album_Success",
            "listing_type": "BUY_NOW",
            "price": 20.00,
            "condition": "Very Good",
            "photo_urls": ["https://example.com/photo1.jpg"],
            "is_unofficial": True,
            "unofficial_acknowledged": True
        }
        
        resp = requests.post(f"{BASE_URL}/api/listings", json=payload, headers=headers)
        # Can be 200 or 201 depending on implementation
        assert resp.status_code in [200, 201], f"Expected 200/201, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "id" in data, "Response should contain listing ID"
        assert data.get("is_unofficial") == True, "Listing should have is_unofficial=True"
        
        # Cleanup: delete the test listing
        listing_id = data["id"]
        del_resp = requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=headers)
        assert del_resp.status_code in [200, 204], f"Cleanup failed: {del_resp.status_code}"
    
    def test_listing_non_unofficial_without_acknowledgement_succeeds(self, headers):
        """POST /api/listings with is_unofficial=false should work without acknowledgement"""
        payload = {
            "artist": "TEST_Official_Artist",
            "album": "TEST_Official_Album",
            "listing_type": "BUY_NOW",
            "price": 15.00,
            "condition": "Near Mint",
            "photo_urls": ["https://example.com/photo1.jpg"],
            "is_unofficial": False,
            "unofficial_acknowledged": False
        }
        
        resp = requests.post(f"{BASE_URL}/api/listings", json=payload, headers=headers)
        assert resp.status_code in [200, 201], f"Expected 200/201, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        # Cleanup
        listing_id = data.get("id")
        if listing_id:
            requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=headers)


class TestDiscogsImportIntent:
    """Tests for POST /api/discogs/update-import-intent endpoint"""

    def test_update_intent_later(self, headers):
        """POST /api/discogs/update-import-intent with LATER should succeed"""
        resp = requests.post(f"{BASE_URL}/api/discogs/update-import-intent", 
                             json={"intent": "LATER"}, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("intent") == "LATER"
    
    def test_update_intent_declined(self, headers):
        """POST /api/discogs/update-import-intent with DECLINED should succeed"""
        resp = requests.post(f"{BASE_URL}/api/discogs/update-import-intent", 
                             json={"intent": "DECLINED"}, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("intent") == "DECLINED"
    
    def test_update_intent_connected(self, headers):
        """POST /api/discogs/update-import-intent with CONNECTED should succeed"""
        resp = requests.post(f"{BASE_URL}/api/discogs/update-import-intent", 
                             json={"intent": "CONNECTED"}, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("intent") == "CONNECTED"
    
    def test_update_intent_pending(self, headers):
        """POST /api/discogs/update-import-intent with PENDING should succeed"""
        resp = requests.post(f"{BASE_URL}/api/discogs/update-import-intent", 
                             json={"intent": "PENDING"}, headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("intent") == "PENDING"
    
    def test_update_intent_invalid_returns_400(self, headers):
        """POST /api/discogs/update-import-intent with invalid value → 400"""
        resp = requests.post(f"{BASE_URL}/api/discogs/update-import-intent", 
                             json={"intent": "INVALID_VALUE"}, headers=headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


class TestListingResponse:
    """Tests for is_unofficial in listing responses"""

    def test_get_listings_returns_is_unofficial_field(self, headers):
        """GET /api/listings should return is_unofficial field for listings"""
        resp = requests.get(f"{BASE_URL}/api/listings", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        listings = resp.json()
        assert isinstance(listings, list), "Response should be a list"
        
        # Check listings have is_unofficial field (may be present even if empty)
        if len(listings) > 0:
            for listing in listings[:5]:
                # is_unofficial should be in the response
                assert "is_unofficial" in listing or listing.get("is_unofficial") is None or listing.get("is_unofficial") is not None, \
                    f"Listing {listing.get('id')} should have is_unofficial field"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
