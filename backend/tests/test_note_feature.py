"""
Test suite for HoneyGroove 'A Note' Feature
Tests: POST /api/composer/note endpoint (fourth free-form text post type on The Hive)
- 280 character limit
- optional record tag
- optional image_url
- post_type=NOTE
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"


class TestNoteComposerEndpoint:
    """Tests for POST /api/composer/note endpoint"""
    
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
        """Get a record from user's collection for testing record tagging"""
        response = requests.get(f"{BASE_URL}/api/records", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        records = response.json()
        if len(records) == 0:
            pytest.skip("User has no records in collection - cannot test record tagging")
        return records[0]["id"]
    
    # --- Basic Note Creation Tests ---
    def test_note_creates_post_with_text_only(self, auth_token):
        """POST /api/composer/note creates NOTE post with just text"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": "Test note - just a quick thought on my mind!"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify post structure
        assert data["post_type"] == "NOTE", f"Expected NOTE, got {data['post_type']}"
        assert data["caption"] == "Test note - just a quick thought on my mind!"
        assert data["user"] is not None
        assert "id" in data
        assert data["record_id"] is None
        assert data["image_url"] is None
        
        # Store for later tests
        self.__class__.note_post_id = data["id"]
        print(f"Created NOTE post with id: {data['id']}")
    
    def test_note_with_record_tag(self, auth_token, user_record_id):
        """POST /api/composer/note creates NOTE post with record tag"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": "Listening to this gem right now. The B-side is incredible!",
                "record_id": user_record_id
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify post structure
        assert data["post_type"] == "NOTE"
        assert data["record_id"] == user_record_id
        assert data["record"] is not None, "Note with record_id should include record data"
        assert "title" in data["record"]
        assert "artist" in data["record"]
        print(f"Created NOTE post with record tag: {data['record']['artist']} - {data['record']['title']}")
    
    def test_note_with_image_url(self, auth_token):
        """POST /api/composer/note creates NOTE post with image_url"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": "Check out this setup!",
                "image_url": "https://example.com/test-image.jpg"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["post_type"] == "NOTE"
        assert data["image_url"] == "https://example.com/test-image.jpg"
        print(f"Created NOTE post with image")
    
    def test_note_with_all_optional_fields(self, auth_token, user_record_id):
        """POST /api/composer/note with both record tag and image_url"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": "Full featured note with everything!",
                "record_id": user_record_id,
                "image_url": "https://example.com/full-test.jpg"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["post_type"] == "NOTE"
        assert data["record_id"] == user_record_id
        assert data["image_url"] == "https://example.com/full-test.jpg"
        assert data["record"] is not None
        print("Created NOTE post with all optional fields")
    
    # --- Validation Tests ---
    def test_note_requires_text(self, auth_token):
        """POST /api/composer/note fails without text"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "record_id": "some-record-id"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422, "Should fail without text field"
    
    def test_note_rejects_empty_text(self, auth_token):
        """POST /api/composer/note rejects empty text string"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": ""
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400, f"Should reject empty text, got {response.status_code}"
        assert "required" in response.text.lower() or "text" in response.text.lower()
    
    def test_note_rejects_whitespace_only_text(self, auth_token):
        """POST /api/composer/note rejects whitespace-only text"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": "   \n\t   "
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400, f"Should reject whitespace-only text, got {response.status_code}"
    
    def test_note_max_280_characters(self, auth_token):
        """POST /api/composer/note allows exactly 280 characters"""
        text_280 = "A" * 280
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": text_280
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Should allow 280 chars, got {response.status_code}: {response.text}"
        data = response.json()
        assert len(data["caption"]) == 280
        print("280 character note created successfully")
    
    def test_note_rejects_over_280_characters(self, auth_token):
        """POST /api/composer/note rejects text over 280 characters"""
        text_281 = "A" * 281
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": text_281
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400, f"Should reject 281 chars, got {response.status_code}"
        assert "280" in response.text.lower() or "character" in response.text.lower()
        print("281 character note correctly rejected")
    
    def test_note_invalid_record_id_returns_404(self, auth_token):
        """POST /api/composer/note with invalid record_id returns 404"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": "Note with invalid record tag",
                "record_id": "nonexistent-record-id"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404, f"Should return 404 for invalid record, got {response.status_code}"
    
    # --- Feed Integration Tests ---
    def test_note_appears_in_feed(self, auth_token):
        """NOTE posts appear in feed with post_type=NOTE"""
        # Create a note first
        create_response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": "Feed test note - should appear in feed!"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert create_response.status_code == 200
        note_id = create_response.json()["id"]
        
        # Check feed
        feed_response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert feed_response.status_code == 200
        posts = feed_response.json()
        
        # Find our note
        note_post = next((p for p in posts if p["id"] == note_id), None)
        assert note_post is not None, "Note should appear in feed"
        assert note_post["post_type"] == "NOTE"
        print(f"Note found in feed with post_type=NOTE")
    
    def test_note_appears_in_explore_feed(self, auth_token):
        """NOTE posts appear in explore feed"""
        feed_response = requests.get(f"{BASE_URL}/api/explore", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert feed_response.status_code == 200
        posts = feed_response.json()
        
        # Check if there are any NOTE posts
        note_posts = [p for p in posts if p["post_type"] == "NOTE"]
        print(f"Found {len(note_posts)} NOTE posts in explore feed")
        
        if note_posts:
            note = note_posts[0]
            assert note["post_type"] == "NOTE"
            assert note["user"] is not None


class TestNoteLikesAndComments:
    """Test that NOTE posts support likes and comments like other post types"""
    
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
    def note_post_id(self, auth_token):
        """Create a note post for testing likes/comments"""
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={
                "text": "Note for like/comment testing"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        return response.json()["id"]
    
    def test_like_note_post(self, auth_token, note_post_id):
        """POST /api/posts/{id}/like works on NOTE posts"""
        # Unlike first if already liked
        requests.delete(f"{BASE_URL}/api/posts/{note_post_id}/like", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Like the note
        response = requests.post(f"{BASE_URL}/api/posts/{note_post_id}/like", 
            json={},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        print("Note post liked successfully")
    
    def test_unlike_note_post(self, auth_token, note_post_id):
        """DELETE /api/posts/{id}/like works on NOTE posts"""
        # Ensure it's liked first
        requests.post(f"{BASE_URL}/api/posts/{note_post_id}/like", 
            json={},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Unlike
        response = requests.delete(f"{BASE_URL}/api/posts/{note_post_id}/like", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        print("Note post unliked successfully")
    
    def test_comment_on_note_post(self, auth_token, note_post_id):
        """POST /api/posts/{id}/comments works on NOTE posts"""
        response = requests.post(f"{BASE_URL}/api/posts/{note_post_id}/comments", 
            json={
                "post_id": note_post_id,
                "content": "Great note! Love this thought."
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Great note! Love this thought."
        assert data["user"] is not None
        print("Comment on note post created successfully")
    
    def test_get_comments_on_note_post(self, auth_token, note_post_id):
        """GET /api/posts/{id}/comments works on NOTE posts"""
        response = requests.get(f"{BASE_URL}/api/posts/{note_post_id}/comments", 
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        comments = response.json()
        assert isinstance(comments, list)
        if comments:
            assert "content" in comments[0]
            assert "user" in comments[0]
        print(f"Got {len(comments)} comments on note post")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
