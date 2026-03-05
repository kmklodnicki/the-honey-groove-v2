"""
Test suite for HoneyGroove Composer Endpoints and Post System
Tests: NOW_SPINNING, NEW_HAUL, ISO, VINYL_MOOD composers + feed/ISO endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"

class TestComposerEndpoints:
    """Tests for POST /api/composer/* endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def user_record_id(self, auth_token):
        """Get a record from user's collection for testing"""
        response = requests.get(f"{BASE_URL}/api/records", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        records = response.json()
        assert len(records) > 0, "User has no records in collection"
        return records[0]["id"]
    
    # --- NOW_SPINNING Composer Tests ---
    def test_now_spinning_creates_post_and_spin(self, auth_token, user_record_id):
        """POST /api/composer/now-spinning creates NOW_SPINNING post + logs spin"""
        response = requests.post(f"{BASE_URL}/api/composer/now-spinning", 
            json={
                "record_id": user_record_id,
                "track": "Side A, Track 1",
                "caption": "Test Now Spinning Post"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify post structure
        assert data["post_type"] == "NOW_SPINNING"
        assert data["record_id"] == user_record_id
        assert data["track"] == "Side A, Track 1"
        assert data["caption"] == "Test Now Spinning Post"
        assert data["user"] is not None
        assert data["record"] is not None
        assert "id" in data
        
        # Store post_id for later tests
        self.__class__.now_spinning_post_id = data["id"]
    
    def test_now_spinning_requires_record_id(self, auth_token):
        """POST /api/composer/now-spinning fails without record_id"""
        response = requests.post(f"{BASE_URL}/api/composer/now-spinning", 
            json={
                "track": "Test Track",
                "caption": "Missing record_id"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_now_spinning_invalid_record_returns_404(self, auth_token):
        """POST /api/composer/now-spinning with invalid record_id returns 404"""
        response = requests.post(f"{BASE_URL}/api/composer/now-spinning", 
            json={
                "record_id": "nonexistent-record-id"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404
    
    # --- NEW_HAUL Composer Tests ---
    def test_new_haul_creates_post_and_records(self, auth_token):
        """POST /api/composer/new-haul creates NEW_HAUL post + adds records to collection"""
        response = requests.post(f"{BASE_URL}/api/composer/new-haul", 
            json={
                "store_name": "Test Record Store",
                "caption": "Test haul from testing",
                "items": [
                    {
                        "discogs_id": 999999,
                        "title": "Test Album",
                        "artist": "Test Artist",
                        "year": 2024
                    },
                    {
                        "discogs_id": 999998,
                        "title": "Another Test Album",
                        "artist": "Another Artist",
                        "year": 2023
                    }
                ]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify post structure
        assert data["post_type"] == "NEW_HAUL"
        assert data["haul_id"] is not None
        assert data["caption"] == "Test haul from testing"
        assert data["haul"] is not None
        assert "items" in data["haul"]
        assert len(data["haul"]["items"]) == 2
        
        # Store for later cleanup
        self.__class__.new_haul_post_id = data["id"]
    
    def test_new_haul_empty_items_allowed(self, auth_token):
        """POST /api/composer/new-haul allows empty items (creates empty haul)"""
        response = requests.post(f"{BASE_URL}/api/composer/new-haul", 
            json={
                "store_name": "Empty Test Store",
                "items": []
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Backend allows empty items - creates haul with 0 items
        # Note: Frontend validates this client-side
        assert response.status_code == 200
    
    # --- ISO Composer Tests ---
    def test_iso_creates_post_and_iso_item(self, auth_token):
        """POST /api/composer/iso creates ISO post + iso_item"""
        response = requests.post(f"{BASE_URL}/api/composer/iso", 
            json={
                "artist": "Test Artist ISO",
                "album": "Rare Test Album",
                "pressing_notes": "Original US pressing",
                "condition_pref": "VG+ or better",
                "target_price_min": 25.00,
                "target_price_max": 75.00,
                "caption": "Looking for this rare test album"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify post structure
        assert data["post_type"] == "ISO"
        assert data["iso_id"] is not None
        assert data["iso"] is not None
        assert data["iso"]["artist"] == "Test Artist ISO"
        assert data["iso"]["album"] == "Rare Test Album"
        assert data["iso"]["pressing_notes"] == "Original US pressing"
        assert data["iso"]["status"] == "OPEN"
        
        # Store ISO id for found test
        self.__class__.iso_id = data["iso"]["id"]
        self.__class__.iso_post_id = data["id"]
    
    def test_iso_requires_artist_and_album(self, auth_token):
        """POST /api/composer/iso fails without artist or album"""
        response = requests.post(f"{BASE_URL}/api/composer/iso", 
            json={
                "pressing_notes": "Test"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422  # Validation error
    
    # --- VINYL_MOOD Composer Tests ---
    def test_vinyl_mood_creates_post(self, auth_token, user_record_id):
        """POST /api/composer/vinyl-mood creates VINYL_MOOD post"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood", 
            json={
                "mood": "Late Night",
                "caption": "Test mood post",
                "record_id": user_record_id
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify post structure
        assert data["post_type"] == "VINYL_MOOD"
        assert data["mood"] == "Late Night"
        assert data["caption"] == "Test mood post"
        assert data["record_id"] == user_record_id
        
        self.__class__.vinyl_mood_post_id = data["id"]
    
    def test_vinyl_mood_without_record(self, auth_token):
        """POST /api/composer/vinyl-mood works without record_id"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood", 
            json={
                "mood": "Sunday Morning",
                "caption": "Just vibing without a specific record"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["post_type"] == "VINYL_MOOD"
        assert data["mood"] == "Sunday Morning"
        assert data["record_id"] is None
    
    def test_vinyl_mood_requires_mood(self, auth_token):
        """POST /api/composer/vinyl-mood fails without mood"""
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood", 
            json={
                "caption": "No mood specified"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422  # Validation error


class TestFeedAndPostTypes:
    """Tests for GET /api/feed and post type normalization"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_feed_returns_posts_with_normalized_types(self, auth_token):
        """GET /api/feed returns posts with normalized post_type enum values"""
        response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        posts = response.json()
        
        # Valid post types
        valid_types = ["NOW_SPINNING", "NEW_HAUL", "ISO", "ADDED_TO_COLLECTION", "WEEKLY_WRAP", "VINYL_MOOD"]
        
        for post in posts:
            assert "post_type" in post, f"Post {post.get('id')} missing post_type"
            assert post["post_type"] in valid_types, f"Invalid post_type: {post['post_type']}"
            assert "user" in post
            assert "likes_count" in post
            assert "comments_count" in post
            assert "is_liked" in post
    
    def test_feed_includes_record_data_for_now_spinning(self, auth_token):
        """GET /api/feed includes full record data for NOW_SPINNING posts"""
        response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        posts = response.json()
        
        now_spinning_posts = [p for p in posts if p["post_type"] == "NOW_SPINNING"]
        if now_spinning_posts:
            post = now_spinning_posts[0]
            if post.get("record_id"):
                assert post["record"] is not None, "NOW_SPINNING post should have record data"
                assert "title" in post["record"]
                assert "artist" in post["record"]
    
    def test_feed_includes_haul_data_for_new_haul(self, auth_token):
        """GET /api/feed includes haul data for NEW_HAUL posts"""
        response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        posts = response.json()
        
        haul_posts = [p for p in posts if p["post_type"] == "NEW_HAUL"]
        if haul_posts:
            post = haul_posts[0]
            if post.get("haul_id"):
                assert post["haul"] is not None, "NEW_HAUL post should have haul data"
                assert "items" in post["haul"]
    
    def test_feed_includes_iso_data_for_iso_posts(self, auth_token):
        """GET /api/feed includes iso data for ISO posts"""
        response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        posts = response.json()
        
        iso_posts = [p for p in posts if p["post_type"] == "ISO"]
        if iso_posts:
            post = iso_posts[0]
            if post.get("iso_id"):
                assert post["iso"] is not None, "ISO post should have iso data"
                assert "artist" in post["iso"]
                assert "album" in post["iso"]
                assert "status" in post["iso"]


class TestISOEndpoints:
    """Tests for ISO CRUD endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_user_isos(self, auth_token):
        """GET /api/iso returns user's ISO items"""
        response = requests.get(f"{BASE_URL}/api/iso", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        isos = response.json()
        
        # Should be a list
        assert isinstance(isos, list)
        
        # If there are ISOs, verify structure
        if isos:
            iso = isos[0]
            assert "id" in iso
            assert "artist" in iso
            assert "album" in iso
            assert "status" in iso
    
    def test_mark_iso_found(self, auth_token):
        """PUT /api/iso/{id}/found marks ISO as FOUND"""
        # First create a new ISO to mark as found
        create_response = requests.post(f"{BASE_URL}/api/composer/iso", 
            json={
                "artist": "Found Test Artist",
                "album": "Found Test Album",
                "caption": "Testing mark as found"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert create_response.status_code == 200
        iso_id = create_response.json()["iso"]["id"]
        
        # Mark as found
        found_response = requests.put(f"{BASE_URL}/api/iso/{iso_id}/found", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert found_response.status_code == 200
        
        # Verify it's marked as found
        get_response = requests.get(f"{BASE_URL}/api/iso", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert get_response.status_code == 200
        isos = get_response.json()
        found_iso = next((i for i in isos if i["id"] == iso_id), None)
        assert found_iso is not None
        assert found_iso["status"] == "FOUND"
        assert found_iso["found_at"] is not None
    
    def test_mark_nonexistent_iso_returns_404(self, auth_token):
        """PUT /api/iso/{id}/found returns 404 for nonexistent ISO"""
        response = requests.put(f"{BASE_URL}/api/iso/nonexistent-id/found", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404


class TestLikesAndComments:
    """Test that likes and comments still work on all post types"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_post_id(self, auth_token):
        """Get a post ID from feed for testing"""
        response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        posts = response.json()
        assert len(posts) > 0, "No posts in feed"
        return posts[0]["id"]
    
    def test_like_post(self, auth_token, test_post_id):
        """POST /api/posts/{id}/like works"""
        # Try to unlike first (in case already liked)
        requests.delete(f"{BASE_URL}/api/posts/{test_post_id}/like", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Now like
        response = requests.post(f"{BASE_URL}/api/posts/{test_post_id}/like", 
            json={},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_unlike_post(self, auth_token, test_post_id):
        """DELETE /api/posts/{id}/like works"""
        # Make sure it's liked first
        requests.post(f"{BASE_URL}/api/posts/{test_post_id}/like", 
            json={},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Now unlike
        response = requests.delete(f"{BASE_URL}/api/posts/{test_post_id}/like", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_add_comment(self, auth_token, test_post_id):
        """POST /api/posts/{id}/comments works"""
        response = requests.post(f"{BASE_URL}/api/posts/{test_post_id}/comments", 
            json={
                "post_id": test_post_id,
                "content": "Test comment from pytest"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test comment from pytest"
        assert data["user"] is not None
    
    def test_get_comments(self, auth_token, test_post_id):
        """GET /api/posts/{id}/comments works"""
        response = requests.get(f"{BASE_URL}/api/posts/{test_post_id}/comments", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        comments = response.json()
        assert isinstance(comments, list)


class TestDiscogsSearch:
    """Test Discogs search for New Haul workflow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_discogs_search(self, auth_token):
        """GET /api/discogs/search returns results"""
        response = requests.get(f"{BASE_URL}/api/discogs/search?q=Beatles", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        
        # If we get results, verify structure
        if results:
            result = results[0]
            assert "discogs_id" in result
            assert "title" in result
            assert "artist" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
