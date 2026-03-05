"""
Test cases for Vinyl Mood overhaul (12 moods) and Marketplace photo upload features.
Tests:
1. Vinyl Mood - POST /api/composer/vinyl-mood with all 12 moods
2. Vinyl Mood - Feed cards show mood name in response
3. Marketplace - POST /api/listings requires photo_urls (1-10)
4. Marketplace - POST /api/listings without photos returns 422
5. Marketplace - GET /api/listings returns photo_urls in response
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"

# All 12 mood presets as per MOOD_CONFIG in ComposerBar.js
MOOD_PRESETS = [
    'Late Night',
    'Sunday Morning', 
    'Rainy Day',
    'Road Trip',
    'Golden Hour',
    'Deep Focus',
    'Party Mode',
    'Lazy Afternoon',
    'Melancholy',
    'Upbeat Vibes',
    'Cozy Evening',
    'Workout'
]


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestVinylMoodFeature:
    """Tests for the Vinyl Mood feature with 12 mood presets"""
    
    def test_create_vinyl_mood_late_night(self, auth_headers):
        """Test creating a Late Night mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood", 
            json={"mood": "Late Night", "caption": "Testing late night vibes"},
            headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["post_type"] == "VINYL_MOOD"
        assert data["mood"] == "Late Night"
        print(f"✓ Late Night mood post created: {data['id']}")
    
    def test_create_vinyl_mood_sunday_morning(self, auth_headers):
        """Test creating a Sunday Morning mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Sunday Morning", "caption": "Slow mornings, good records"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Sunday Morning"
        print(f"✓ Sunday Morning mood post created")
    
    def test_create_vinyl_mood_rainy_day(self, auth_headers):
        """Test creating a Rainy Day mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Rainy Day"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Rainy Day"
        print(f"✓ Rainy Day mood post created")
    
    def test_create_vinyl_mood_road_trip(self, auth_headers):
        """Test creating a Road Trip mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Road Trip", "caption": "Where are you headed?"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Road Trip"
        print(f"✓ Road Trip mood post created")
    
    def test_create_vinyl_mood_golden_hour(self, auth_headers):
        """Test creating a Golden Hour mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Golden Hour"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Golden Hour"
        print(f"✓ Golden Hour mood post created")
    
    def test_create_vinyl_mood_deep_focus(self, auth_headers):
        """Test creating a Deep Focus mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Deep Focus"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Deep Focus"
        print(f"✓ Deep Focus mood post created")
    
    def test_create_vinyl_mood_party_mode(self, auth_headers):
        """Test creating a Party Mode mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Party Mode"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Party Mode"
        print(f"✓ Party Mode mood post created")
    
    def test_create_vinyl_mood_lazy_afternoon(self, auth_headers):
        """Test creating a Lazy Afternoon mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Lazy Afternoon"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Lazy Afternoon"
        print(f"✓ Lazy Afternoon mood post created")
    
    def test_create_vinyl_mood_melancholy(self, auth_headers):
        """Test creating a Melancholy mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Melancholy"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Melancholy"
        print(f"✓ Melancholy mood post created")
    
    def test_create_vinyl_mood_upbeat_vibes(self, auth_headers):
        """Test creating an Upbeat Vibes mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Upbeat Vibes"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Upbeat Vibes"
        print(f"✓ Upbeat Vibes mood post created")
    
    def test_create_vinyl_mood_cozy_evening(self, auth_headers):
        """Test creating a Cozy Evening mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Cozy Evening"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Cozy Evening"
        print(f"✓ Cozy Evening mood post created")
    
    def test_create_vinyl_mood_workout(self, auth_headers):
        """Test creating a Workout mood post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood",
            json={"mood": "Workout"},
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "Workout"
        print(f"✓ Workout mood post created")
    
    def test_feed_contains_mood_posts(self, auth_headers):
        """Test that the feed returns VINYL_MOOD posts with mood field"""
        response = requests.get(f"{BASE_URL}/api/feed", headers=auth_headers)
        assert response.status_code == 200
        posts = response.json()
        mood_posts = [p for p in posts if p.get("post_type") == "VINYL_MOOD"]
        assert len(mood_posts) > 0, "Expected at least one VINYL_MOOD post in feed"
        # Check that mood field is present
        for mp in mood_posts[:5]:  # Check first 5
            assert "mood" in mp, f"Missing 'mood' field in post {mp['id']}"
            assert mp["mood"] in MOOD_PRESETS, f"Invalid mood: {mp['mood']}"
        print(f"✓ Feed contains {len(mood_posts)} VINYL_MOOD posts with mood data")


class TestMarketplacePhotoUpload:
    """Tests for Marketplace photo upload requirement"""
    
    def test_listing_requires_photos(self, auth_headers):
        """Test that creating a listing without photos returns 422"""
        response = requests.post(f"{BASE_URL}/api/listings",
            json={
                "artist": "TEST_Photo_Required",
                "album": "No Photos Album",
                "listing_type": "BUY_NOW",
                "price": 25.00,
                "photo_urls": []  # Empty array should fail
            },
            headers=auth_headers)
        # Pydantic validation should catch min_length=1
        assert response.status_code == 422, f"Expected 422 for missing photos, got {response.status_code}: {response.text}"
        print(f"✓ Listing without photos returns 422")
    
    def test_listing_requires_photo_urls_field(self, auth_headers):
        """Test that creating a listing without photo_urls field returns 422"""
        response = requests.post(f"{BASE_URL}/api/listings",
            json={
                "artist": "TEST_No_Field",
                "album": "Missing Field Album",
                "listing_type": "BUY_NOW",
                "price": 30.00
                # photo_urls field missing entirely
            },
            headers=auth_headers)
        assert response.status_code == 422, f"Expected 422 for missing photo_urls field, got {response.status_code}"
        print(f"✓ Listing without photo_urls field returns 422")
    
    def test_listing_with_one_photo(self, auth_headers):
        """Test creating a listing with 1 photo (minimum required)"""
        response = requests.post(f"{BASE_URL}/api/listings",
            json={
                "artist": "TEST_One_Photo_Artist",
                "album": "One Photo Album",
                "listing_type": "BUY_NOW",
                "price": 35.00,
                "photo_urls": ["https://example.com/photo1.jpg"]
            },
            headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "photo_urls" in data
        assert len(data["photo_urls"]) == 1
        print(f"✓ Listing with 1 photo created: {data['id']}")
        # Cleanup
        requests.delete(f"{BASE_URL}/api/listings/{data['id']}", headers=auth_headers)
    
    def test_listing_with_multiple_photos(self, auth_headers):
        """Test creating a listing with multiple photos"""
        photo_urls = [f"https://example.com/photo{i}.jpg" for i in range(1, 6)]
        response = requests.post(f"{BASE_URL}/api/listings",
            json={
                "artist": "TEST_Multi_Photo_Artist",
                "album": "Multi Photo Album",
                "listing_type": "MAKE_OFFER",
                "price": 50.00,
                "condition": "Near Mint",
                "photo_urls": photo_urls
            },
            headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "photo_urls" in data
        assert len(data["photo_urls"]) == 5
        print(f"✓ Listing with 5 photos created: {data['id']}")
        # Cleanup
        requests.delete(f"{BASE_URL}/api/listings/{data['id']}", headers=auth_headers)
    
    def test_listing_max_10_photos(self, auth_headers):
        """Test creating a listing with 10 photos (max allowed)"""
        photo_urls = [f"https://example.com/photo{i}.jpg" for i in range(1, 11)]
        response = requests.post(f"{BASE_URL}/api/listings",
            json={
                "artist": "TEST_Max_Photo_Artist",
                "album": "Max Photo Album",
                "listing_type": "TRADE",
                "photo_urls": photo_urls
            },
            headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert len(data["photo_urls"]) == 10
        print(f"✓ Listing with 10 photos created: {data['id']}")
        # Cleanup
        requests.delete(f"{BASE_URL}/api/listings/{data['id']}", headers=auth_headers)
    
    def test_listing_over_max_photos_rejected(self, auth_headers):
        """Test that creating a listing with >10 photos is rejected"""
        photo_urls = [f"https://example.com/photo{i}.jpg" for i in range(1, 13)]  # 12 photos
        response = requests.post(f"{BASE_URL}/api/listings",
            json={
                "artist": "TEST_Too_Many_Photos",
                "album": "Too Many Photos Album",
                "listing_type": "BUY_NOW",
                "price": 99.00,
                "photo_urls": photo_urls
            },
            headers=auth_headers)
        # Pydantic validation should catch max_length=10
        assert response.status_code == 422, f"Expected 422 for >10 photos, got {response.status_code}"
        print(f"✓ Listing with >10 photos returns 422")
    
    def test_get_listings_includes_photo_urls(self, auth_headers):
        """Test that GET /api/listings returns photo_urls in response"""
        # First create a test listing with photos
        response = requests.post(f"{BASE_URL}/api/listings",
            json={
                "artist": "TEST_Get_Photos_Artist",
                "album": "Get Photos Album",
                "listing_type": "BUY_NOW",
                "price": 40.00,
                "photo_urls": ["https://example.com/test1.jpg", "https://example.com/test2.jpg"]
            },
            headers=auth_headers)
        assert response.status_code == 200
        listing_id = response.json()["id"]
        
        # Get all listings and verify photo_urls is present
        response = requests.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200
        listings = response.json()
        
        # Find our test listing
        test_listing = next((l for l in listings if l["id"] == listing_id), None)
        assert test_listing is not None, "Test listing not found in GET response"
        assert "photo_urls" in test_listing, "photo_urls field missing from listing response"
        assert len(test_listing["photo_urls"]) == 2
        print(f"✓ GET /api/listings returns photo_urls field")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=auth_headers)
    
    def test_my_listings_includes_photo_urls(self, auth_headers):
        """Test that GET /api/listings/my returns photo_urls"""
        response = requests.get(f"{BASE_URL}/api/listings/my", headers=auth_headers)
        assert response.status_code == 200
        listings = response.json()
        # Check that each listing has photo_urls field (even if empty for old listings)
        for listing in listings:
            assert "photo_urls" in listing, f"photo_urls missing from listing {listing['id']}"
        print(f"✓ GET /api/listings/my returns photo_urls in all {len(listings)} listings")


class TestExistingListingsPhotoCompatibility:
    """Test that existing listings without photos still work"""
    
    def test_old_listings_return_empty_photo_urls(self, auth_headers):
        """Test that listings created before photo requirement return empty array"""
        response = requests.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200
        listings = response.json()
        
        # All listings should have photo_urls field (defaulting to [])
        for listing in listings:
            assert "photo_urls" in listing, f"photo_urls missing from listing {listing['id']}"
            assert isinstance(listing["photo_urls"], list), f"photo_urls should be a list"
        print(f"✓ All {len(listings)} listings have photo_urls field (backward compatible)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
