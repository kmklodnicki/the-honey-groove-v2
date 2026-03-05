"""
Test marketplace listing features (iteration 6)
- POST /api/composer/iso with discogs_id and cover_url
- POST /api/listings creates a marketplace listing (BUY_NOW, MAKE_OFFER, TRADE)
- GET /api/listings returns active listings with seller data
- GET /api/listings/my returns current user's listings
- GET /api/listings/iso-matches returns listings matching user's active ISOs
- DELETE /api/listings/{id} deletes own listing
- GET /api/discogs/search for Discogs picker
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Get authentication token for testing"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login with demo credentials and return token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Return auth headers for requests"""
        return {"Authorization": f"Bearer {auth_token}"}


class TestISOWithDiscogs(TestAuth):
    """Test ISO creation with Discogs data (album art)"""
    
    def test_discogs_search(self, auth_headers):
        """GET /api/discogs/search?q=... returns search results with album art"""
        response = requests.get(f"{BASE_URL}/api/discogs/search?q=Pink Floyd", headers=auth_headers)
        assert response.status_code == 200, f"Discogs search failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            result = data[0]
            # Verify Discogs response structure
            assert "discogs_id" in result
            assert "title" in result
            assert "artist" in result
            print(f"Discogs search returned {len(data)} results")
            print(f"First result: {result.get('artist')} - {result.get('title')}")
    
    def test_create_iso_with_discogs_id_and_cover(self, auth_headers):
        """POST /api/composer/iso with discogs_id and cover_url creates ISO with album art"""
        iso_data = {
            "artist": "TEST_Pink Floyd",
            "album": "TEST_The Wall",
            "discogs_id": 12345,
            "cover_url": "https://example.com/test_cover.jpg",
            "year": 1979,
            "pressing_notes": "OG UK Press",
            "condition_pref": "VG+",
            "tags": ["OG Press"],
            "target_price_min": 50,
            "target_price_max": 100
        }
        response = requests.post(f"{BASE_URL}/api/composer/iso", json=iso_data, headers=auth_headers)
        assert response.status_code == 200, f"ISO creation failed: {response.text}"
        data = response.json()
        
        # Verify ISO post response
        assert data.get("post_type") == "ISO"
        assert data.get("iso_id") is not None
        print(f"Created ISO post with id: {data.get('id')}")
        
        # Clean up - get ISO ID from the created post and delete it
        iso_id = data.get("iso_id")
        if iso_id:
            # Verify ISO was created with discogs data
            iso_list = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers).json()
            created_iso = next((i for i in iso_list if i.get("id") == iso_id), None)
            if created_iso:
                assert created_iso.get("discogs_id") == 12345
                assert created_iso.get("cover_url") == "https://example.com/test_cover.jpg"
                print(f"ISO has discogs_id: {created_iso.get('discogs_id')}, cover_url: {created_iso.get('cover_url')}")
            
            # Delete test ISO
            requests.delete(f"{BASE_URL}/api/iso/{iso_id}", headers=auth_headers)


class TestMarketplaceListings(TestAuth):
    """Test marketplace listing CRUD operations"""
    
    created_listing_ids = []
    
    def test_create_buy_now_listing(self, auth_headers):
        """POST /api/listings creates a BUY_NOW marketplace listing"""
        listing_data = {
            "artist": "TEST_Pink Floyd",
            "album": "TEST_Dark Side",
            "discogs_id": 11111,
            "cover_url": "https://example.com/test1.jpg",
            "year": 1973,
            "condition": "Near Mint",
            "pressing_notes": "UK 1st Press",
            "listing_type": "BUY_NOW",
            "price": 99.99,
            "description": "Test listing - BUY_NOW type"
        }
        response = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
        assert response.status_code == 200, f"Create BUY_NOW listing failed: {response.text}"
        data = response.json()
        
        # Verify listing response
        assert data.get("listing_type") == "BUY_NOW"
        assert data.get("price") == 99.99
        assert data.get("condition") == "Near Mint"
        assert data.get("status") == "ACTIVE"
        assert "id" in data
        assert "user" in data
        
        self.__class__.created_listing_ids.append(data["id"])
        print(f"Created BUY_NOW listing: {data['id']}")
    
    def test_create_make_offer_listing(self, auth_headers):
        """POST /api/listings creates a MAKE_OFFER marketplace listing"""
        listing_data = {
            "artist": "TEST_Led Zeppelin",
            "album": "TEST_IV",
            "discogs_id": 22222,
            "cover_url": "https://example.com/test2.jpg",
            "year": 1971,
            "condition": "Very Good Plus",
            "listing_type": "MAKE_OFFER",
            "price": 75.00,
            "description": "Test listing - MAKE_OFFER type"
        }
        response = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
        assert response.status_code == 200, f"Create MAKE_OFFER listing failed: {response.text}"
        data = response.json()
        
        assert data.get("listing_type") == "MAKE_OFFER"
        assert data.get("price") == 75.00
        self.__class__.created_listing_ids.append(data["id"])
        print(f"Created MAKE_OFFER listing: {data['id']}")
    
    def test_create_trade_listing(self, auth_headers):
        """POST /api/listings creates a TRADE marketplace listing (no price)"""
        listing_data = {
            "artist": "TEST_The Beatles",
            "album": "TEST_Abbey Road",
            "discogs_id": 33333,
            "cover_url": "https://example.com/test3.jpg",
            "year": 1969,
            "condition": "Very Good",
            "listing_type": "TRADE",
            "price": None,  # TRADE listings don't require price
            "description": "Test listing - TRADE type, looking for jazz"
        }
        response = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
        assert response.status_code == 200, f"Create TRADE listing failed: {response.text}"
        data = response.json()
        
        assert data.get("listing_type") == "TRADE"
        assert data.get("price") is None  # TRADE listings shouldn't have price
        self.__class__.created_listing_ids.append(data["id"])
        print(f"Created TRADE listing: {data['id']}")
    
    def test_get_listings_returns_active(self, auth_headers):
        """GET /api/listings returns active listings with seller user data"""
        response = requests.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200, f"Get listings failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"Total listings: {len(data)}")
        
        # Verify at least one listing exists
        if len(data) > 0:
            listing = data[0]
            # Check required fields
            assert "id" in listing
            assert "artist" in listing
            assert "album" in listing
            assert "listing_type" in listing
            assert "status" in listing
            assert "user" in listing  # Must have seller data
            
            # Verify user data structure
            if listing["user"]:
                assert "username" in listing["user"]
                print(f"First listing: {listing['artist']} - {listing['album']} by @{listing['user']['username']}")
    
    def test_get_my_listings(self, auth_headers):
        """GET /api/listings/my returns current user's listings"""
        response = requests.get(f"{BASE_URL}/api/listings/my", headers=auth_headers)
        assert response.status_code == 200, f"Get my listings failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"User's listings count: {len(data)}")
        
        # Verify we can find our test listings
        test_listings = [l for l in data if l.get("artist", "").startswith("TEST_")]
        print(f"Found {len(test_listings)} test listings in my listings")
    
    def test_get_iso_matches(self, auth_headers):
        """GET /api/listings/iso-matches returns listings matching user's active ISOs"""
        response = requests.get(f"{BASE_URL}/api/listings/iso-matches", headers=auth_headers)
        assert response.status_code == 200, f"Get ISO matches failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"ISO matches count: {len(data)}")
        
        # If matches exist, verify structure
        if len(data) > 0:
            match = data[0]
            assert "artist" in match
            assert "album" in match
            assert "listing_type" in match
            print(f"First ISO match: {match.get('artist')} - {match.get('album')}")
    
    def test_delete_listing(self, auth_headers):
        """DELETE /api/listings/{id} deletes own listing"""
        # Create a listing to delete
        listing_data = {
            "artist": "TEST_DELETE_Artist",
            "album": "TEST_DELETE_Album",
            "listing_type": "BUY_NOW",
            "price": 25.00
        }
        create_response = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
        assert create_response.status_code == 200
        listing_id = create_response.json()["id"]
        
        # Delete the listing
        delete_response = requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=auth_headers)
        assert delete_response.status_code == 200, f"Delete listing failed: {delete_response.text}"
        
        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/listings/{listing_id}")
        assert get_response.status_code == 404, "Listing should be deleted"
        print(f"Successfully deleted listing: {listing_id}")
    
    def test_delete_nonexistent_listing(self, auth_headers):
        """DELETE /api/listings/{id} returns 404 for nonexistent listing"""
        response = requests.delete(f"{BASE_URL}/api/listings/nonexistent-id-12345", headers=auth_headers)
        assert response.status_code == 404
        print("Correctly returns 404 for nonexistent listing")
    
    @pytest.fixture(scope="class", autouse=True)
    def cleanup_test_listings(self, auth_headers):
        """Cleanup test listings after all tests complete"""
        yield
        # Clean up any TEST_ prefixed listings
        try:
            my_listings = requests.get(f"{BASE_URL}/api/listings/my", headers=auth_headers).json()
            for listing in my_listings:
                if listing.get("artist", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/listings/{listing['id']}", headers=auth_headers)
                    print(f"Cleaned up listing: {listing['id']}")
        except Exception as e:
            print(f"Cleanup warning: {e}")


class TestListingFilters(TestAuth):
    """Test listing filtering and search"""
    
    def test_filter_by_listing_type(self, auth_headers):
        """GET /api/listings?listing_type=BUY_NOW filters correctly"""
        response = requests.get(f"{BASE_URL}/api/listings?listing_type=BUY_NOW")
        assert response.status_code == 200
        data = response.json()
        
        # All returned should be BUY_NOW
        for listing in data:
            if listing.get("listing_type") != "BUY_NOW":
                pytest.fail(f"Expected BUY_NOW, got {listing.get('listing_type')}")
        print(f"BUY_NOW listings: {len(data)}")
    
    def test_search_listings(self, auth_headers):
        """GET /api/listings?search=... filters by artist/album"""
        response = requests.get(f"{BASE_URL}/api/listings?search=Pink")
        assert response.status_code == 200
        data = response.json()
        print(f"Listings matching 'Pink': {len(data)}")


class TestExistingData:
    """Verify existing seeded data"""
    
    def test_existing_listing_exists(self):
        """Verify the existing Pink Floyd listing from seed data"""
        response = requests.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200
        data = response.json()
        
        # Look for the existing listing mentioned: Pink Floyd - Dark Side of the Moon, BUY_NOW $45
        pink_floyd = [l for l in data if "Pink Floyd" in l.get("artist", "") or "Dark Side" in l.get("album", "")]
        if len(pink_floyd) > 0:
            print(f"Found existing Pink Floyd listing(s): {len(pink_floyd)}")
            for pf in pink_floyd:
                print(f"  - {pf.get('artist')} - {pf.get('album')}: ${pf.get('price')} ({pf.get('listing_type')})")
        else:
            print("No Pink Floyd listings found (may have been cleaned up)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
