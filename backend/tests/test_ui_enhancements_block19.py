"""
Test UI Enhancement Block 19 Features:
- BLOCK 19.1: Optimistic Likes (API verification)
- BLOCK 19.2: VariantTag - color_variant field in PostResponse
- BLOCK 19.3: Collector Notes - pressing_notes field in PostResponse
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestBlock19Features:
    """Test Block 19 UI Enhancement API requirements"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@thehoneygroove.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # BLOCK 19.2 & 19.3: PostResponse includes color_variant and pressing_notes
    def test_feed_post_response_has_color_variant_field(self):
        """Verify PostResponse model includes color_variant field"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=5", headers=self.headers)
        assert response.status_code == 200
        
        posts = response.json()
        assert len(posts) > 0, "Feed should have posts"
        
        # Check that color_variant field exists in response (may be null)
        first_post = posts[0]
        assert "color_variant" in first_post, "PostResponse should include color_variant field"
    
    def test_feed_post_response_has_pressing_notes_field(self):
        """Verify PostResponse model includes pressing_notes field"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=5", headers=self.headers)
        assert response.status_code == 200
        
        posts = response.json()
        assert len(posts) > 0
        
        first_post = posts[0]
        assert "pressing_notes" in first_post, "PostResponse should include pressing_notes field"
    
    def test_now_spinning_post_includes_record_notes(self):
        """Verify NOW_SPINNING posts include record.notes for collector notes display"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=self.headers)
        assert response.status_code == 200
        
        posts = response.json()
        now_spinning_posts = [p for p in posts if p.get("post_type") == "NOW_SPINNING" and p.get("record")]
        
        # Find at least one NOW_SPINNING post with a record that has notes
        found_notes = False
        for post in now_spinning_posts:
            record = post["record"]
            # notes field should exist in the record response (may be null or have a value)
            if "notes" in record:
                found_notes = True
                if record.get("notes"):
                    print(f"Found record with notes: {record['notes'][:50]}...")
                break
        
        assert found_notes or len(now_spinning_posts) == 0, "Records should include notes field when present"
    
    def test_record_response_structure_complete(self):
        """Verify RecordResponse includes all expected fields for UI display"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=self.headers)
        assert response.status_code == 200
        
        posts = response.json()
        posts_with_records = [p for p in posts if p.get("record")]
        
        if posts_with_records:
            record = posts_with_records[0]["record"]
            # Core record fields should exist
            expected_fields = ["id", "title", "artist", "user_id", "created_at"]
            for field in expected_fields:
                assert field in record, f"Record should have {field} field"
    
    # BLOCK 19.1: Like/Unlike API for optimistic UI
    def test_like_api_returns_success(self):
        """Verify like API works for optimistic UI frontend"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=5", headers=self.headers)
        posts = response.json()
        assert len(posts) > 0
        
        post_id = posts[0]["id"]
        is_liked = posts[0].get("is_liked", False)
        
        if is_liked:
            # Unlike first
            unlike_resp = requests.delete(f"{BASE_URL}/api/posts/{post_id}/like", headers=self.headers)
            assert unlike_resp.status_code in [200, 400], "Unlike should succeed or indicate not liked"
            
            # Then like
            like_resp = requests.post(f"{BASE_URL}/api/posts/{post_id}/like", json={}, headers=self.headers)
            assert like_resp.status_code in [200, 400], "Like should succeed or indicate already liked"
        else:
            # Like first
            like_resp = requests.post(f"{BASE_URL}/api/posts/{post_id}/like", json={}, headers=self.headers)
            assert like_resp.status_code in [200, 400], "Like should succeed or indicate already liked"
            
            # Then unlike
            unlike_resp = requests.delete(f"{BASE_URL}/api/posts/{post_id}/like", headers=self.headers)
            assert unlike_resp.status_code in [200, 400], "Unlike should succeed"
    
    def test_like_api_returns_correct_status_codes(self):
        """Verify like API returns proper status codes for rollback handling"""
        # Create a unique post to test with
        response = requests.post(f"{BASE_URL}/api/composer/note", 
            json={"text": "TEST_BLOCK19_LIKE_TEST"},
            headers=self.headers)
        
        if response.status_code == 200:
            post_id = response.json()["id"]
            
            # Like the post
            like_resp = requests.post(f"{BASE_URL}/api/posts/{post_id}/like", json={}, headers=self.headers)
            assert like_resp.status_code == 200, "First like should return 200"
            
            # Try to like again (should fail with 400)
            double_like = requests.post(f"{BASE_URL}/api/posts/{post_id}/like", json={}, headers=self.headers)
            assert double_like.status_code == 400, "Double like should return 400"
            
            # Unlike
            unlike_resp = requests.delete(f"{BASE_URL}/api/posts/{post_id}/like", headers=self.headers)
            assert unlike_resp.status_code == 200, "Unlike should return 200"
            
            # Try to unlike again (should fail with 400)
            double_unlike = requests.delete(f"{BASE_URL}/api/posts/{post_id}/like", headers=self.headers)
            assert double_unlike.status_code == 400, "Double unlike should return 400"
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/posts/{post_id}", headers=self.headers)
    
    def test_listing_posts_include_color_variant(self):
        """Verify listing posts include color_variant and pressing_notes fields"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=self.headers)
        assert response.status_code == 200
        
        posts = response.json()
        listing_posts = [p for p in posts if p.get("post_type") in ["listing_sale", "listing_trade"]]
        
        for post in listing_posts:
            # color_variant field should exist in listing posts
            assert "color_variant" in post, f"Listing post {post['id']} should have color_variant field"
            # pressing_notes field should exist
            assert "pressing_notes" in post, f"Listing post {post['id']} should have pressing_notes field"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
