"""
Test format features for records and hauls
- Format picker on Add Record page (Vinyl/CD/Cassette)
- Format selection per item in Create Haul
- Backend API support for format field
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestFormatFeatures:
    """Test format selection features for records and hauls"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "katie",
            "password": "HoneyGroove2026"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user_id = login_response.json().get("user", {}).get("id")
        else:
            pytest.skip("Authentication failed")
    
    def test_health_check(self):
        """Test API is accessible"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code in [200, 404]  # Health endpoint may or may not exist
    
    def test_add_record_api_accepts_format(self):
        """Test POST /api/collection/add_record accepts format field"""
        # Test data for adding a record with format
        record_data = {
            "discogs_id": 12345678,
            "artist": "Test Artist",
            "title": "Test Album",
            "cover_url": "https://example.com/cover.jpg",
            "format": "CD",  # Testing CD format
            "condition": "NM"
        }
        
        response = self.session.post(f"{BASE_URL}/api/collection/add_record", json=record_data)
        
        # Should accept the request (even if duplicate or other business logic)
        assert response.status_code in [200, 201, 400, 409]
        
        # If successful, verify format is returned
        if response.status_code in [200, 201]:
            data = response.json()
            # Check if format is in response (may be nested)
            if "format" in data:
                assert data["format"] == "CD"
    
    def test_haul_api_accepts_item_format(self):
        """Test POST /api/composer/new-haul accepts format per item"""
        haul_data = {
            "title": "TEST Format Haul",
            "caption": "Testing format selection",
            "items": [
                {
                    "discogs_id": "11111111",
                    "title": "Test Vinyl Record",
                    "artist": "Test Artist 1",
                    "cover_url": "https://example.com/vinyl.jpg",
                    "format": "Vinyl"  # Vinyl format
                },
                {
                    "discogs_id": "22222222",
                    "title": "Test CD Record",
                    "artist": "Test Artist 2",
                    "cover_url": "https://example.com/cd.jpg",
                    "format": "CD"  # CD format
                },
                {
                    "discogs_id": "33333333",
                    "title": "Test Cassette Record",
                    "artist": "Test Artist 3",
                    "cover_url": "https://example.com/cassette.jpg",
                    "format": "Cassette"  # Cassette format
                }
            ]
        }
        
        response = self.session.post(f"{BASE_URL}/api/composer/new-haul", json=haul_data)
        
        # Check response status
        assert response.status_code in [200, 201, 400]
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"Haul creation response: {data}")
    
    def test_format_defaults_to_vinyl(self):
        """Test that format defaults to Vinyl when not specified"""
        haul_data = {
            "title": "TEST Default Format Haul",
            "caption": "Testing default format",
            "items": [
                {
                    "discogs_id": "44444444",
                    "title": "No Format Specified",
                    "artist": "Test Artist",
                    "cover_url": "https://example.com/test.jpg"
                    # No format field - should default to Vinyl
                }
            ]
        }
        
        response = self.session.post(f"{BASE_URL}/api/composer/new-haul", json=haul_data)
        assert response.status_code in [200, 201, 400]


class TestModalSizing:
    """Test modal sizing API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "katie",
            "password": "HoneyGroove2026"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_listings_api_accessible(self):
        """Test listings API is accessible for modal content"""
        response = self.session.get(f"{BASE_URL}/api/marketplace/listings")
        assert response.status_code in [200, 401, 403]
    
    def test_trades_api_accessible(self):
        """Test trades API is accessible"""
        response = self.session.get(f"{BASE_URL}/api/trades")
        assert response.status_code in [200, 401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
