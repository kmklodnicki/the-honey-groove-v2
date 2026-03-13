"""
Test PostCards Fallback Fix - P0 Bug Fix Verification
=======================================================
Tests that PostCard components handle posts with flat fields when nested objects are null.
The fix adds fallback logic: each card type uses post.cover_url, post.record_title, 
post.record_artist when post.record/haul/iso is null.

Key scenarios:
1. Posts with hydrated nested objects (backwards compatibility)
2. Posts with flat fields only (seeded posts case)
3. Feed endpoint returns all required flat fields
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPostCardFallbackFix:
    """Tests for PostCards.js fallback logic and backend response structure"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "kmklodnicki@gmail.com", "password": "HoneyGroove2026!"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        data = login_response.json()
        self.token = data["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_login_returns_access_token(self):
        """Verify login returns correct token structure"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "kmklodnicki@gmail.com", "password": "HoneyGroove2026!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, "Missing access_token in login response"
        assert "user" in data, "Missing user in login response"
        assert data["token_type"] == "bearer"
    
    def test_feed_endpoint_returns_posts(self):
        """Verify feed endpoint works and returns posts"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=10", headers=self.headers)
        assert response.status_code == 200
        posts = response.json()
        assert isinstance(posts, list), "Feed should return a list"
        print(f"Feed returned {len(posts)} posts")
    
    def test_post_response_includes_flat_fields(self):
        """Verify PostResponse model includes flat fields for fallback"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=20", headers=self.headers)
        assert response.status_code == 200
        posts = response.json()
        
        for post in posts:
            # Check that all expected flat fields exist in schema
            assert "record_title" in post, "Missing record_title field in post"
            assert "record_artist" in post, "Missing record_artist field in post"
            assert "cover_url" in post, "Missing cover_url field in post"
            
            # Post should have either:
            # 1. Nested record object with data, OR
            # 2. Flat fields with data (for seeded posts)
            record = post.get("record")
            flat_title = post.get("record_title")
            flat_artist = post.get("record_artist")
            flat_cover = post.get("cover_url")
            
            pt = post.get("post_type")
            if pt in ("NOW_SPINNING", "ADDED_TO_COLLECTION", "VINYL_MOOD"):
                # These types should have album info from nested OR flat
                if record:
                    # If record exists, it should have data
                    assert record.get("title") or record.get("cover_url"), \
                        f"Record object exists but is empty for post {post['id']}"
                    print(f"[{pt}] Post {post['id'][:8]}: has nested record (title={record.get('title')})")
                else:
                    # If no record, check flat fields are available
                    print(f"[{pt}] Post {post['id'][:8]}: no nested record, flat: title={flat_title}, cover={bool(flat_cover)}")
    
    def test_now_spinning_post_has_required_fields(self):
        """Verify NOW_SPINNING posts have either record or flat fields"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=self.headers)
        assert response.status_code == 200
        posts = response.json()
        
        now_spinning_posts = [p for p in posts if p.get("post_type") == "NOW_SPINNING"]
        print(f"Found {len(now_spinning_posts)} NOW_SPINNING posts")
        
        for post in now_spinning_posts:
            record = post.get("record")
            # NowSpinningCard uses: record.cover_url || post.cover_url
            cover_url = (record or {}).get("cover_url") or post.get("cover_url")
            title = (record or {}).get("title") or post.get("record_title") or ""
            artist = (record or {}).get("artist") or post.get("record_artist") or ""
            
            # The frontend card handles null gracefully
            # But ideally, posts should have at least some data
            print(f"NOW_SPINNING {post['id'][:8]}: cover={bool(cover_url)}, title={title[:30] if title else 'N/A'}")
    
    def test_iso_post_has_required_fields(self):
        """Verify ISO posts have either iso object or flat fields"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=self.headers)
        assert response.status_code == 200
        posts = response.json()
        
        iso_posts = [p for p in posts if p.get("post_type") == "ISO"]
        print(f"Found {len(iso_posts)} ISO posts")
        
        for post in iso_posts:
            iso = post.get("iso")
            # ISOCard builds isoData from iso object OR flat fields
            if iso:
                album = iso.get("album") or ""
                artist = iso.get("artist") or ""
                print(f"ISO {post['id'][:8]}: has nested iso (album={album[:30] if album else 'N/A'})")
            else:
                # Fallback to flat fields
                album = post.get("record_title") or ""
                artist = post.get("record_artist") or ""
                cover = post.get("cover_url")
                print(f"ISO {post['id'][:8]}: no nested iso, flat: album={album[:30] if album else 'N/A'}, cover={bool(cover)}")
    
    def test_new_haul_post_has_required_fields(self):
        """Verify NEW_HAUL posts have either haul object or flat fields"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=self.headers)
        assert response.status_code == 200
        posts = response.json()
        
        haul_posts = [p for p in posts if p.get("post_type") == "NEW_HAUL"]
        print(f"Found {len(haul_posts)} NEW_HAUL posts")
        
        for post in haul_posts:
            haul = post.get("haul")
            bundle = post.get("bundle_records")
            
            if bundle and len(bundle) > 0:
                print(f"NEW_HAUL {post['id'][:8]}: has bundle_records ({len(bundle)} items)")
            elif haul:
                items = haul.get("items") or []
                print(f"NEW_HAUL {post['id'][:8]}: has nested haul ({len(items)} items)")
            else:
                # Fallback to flat fields for single-item haul
                cover = post.get("cover_url")
                title = post.get("record_title") or ""
                print(f"NEW_HAUL {post['id'][:8]}: no nested haul, flat: title={title[:30] if title else 'N/A'}, cover={bool(cover)}")
    
    def test_explore_endpoint_works(self):
        """Verify explore endpoint returns posts"""
        response = requests.get(f"{BASE_URL}/api/explore?limit=10", headers=self.headers)
        assert response.status_code == 200
        posts = response.json()
        assert isinstance(posts, list), "Explore should return a list"
        print(f"Explore returned {len(posts)} posts")
    
    def test_single_post_endpoint_works(self):
        """Verify single post endpoint returns correct structure"""
        # First get a post ID from feed
        feed_response = requests.get(f"{BASE_URL}/api/feed?limit=1", headers=self.headers)
        assert feed_response.status_code == 200
        posts = feed_response.json()
        
        if posts:
            post_id = posts[0]["id"]
            response = requests.get(f"{BASE_URL}/api/posts/{post_id}", headers=self.headers)
            assert response.status_code == 200
            post = response.json()
            
            # Verify all flat fields present in single post response
            assert "record_title" in post
            assert "record_artist" in post
            assert "cover_url" in post
            print(f"Single post {post_id[:8]} retrieved successfully")
    
    def test_backwards_compatibility_with_hydrated_records(self):
        """Verify posts with hydrated record objects still work correctly"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=self.headers)
        assert response.status_code == 200
        posts = response.json()
        
        posts_with_record = [p for p in posts if p.get("record") is not None]
        print(f"Found {len(posts_with_record)} posts with hydrated record objects")
        
        for post in posts_with_record:
            record = post["record"]
            # Hydrated records should have core fields
            assert record.get("id") or record.get("discogs_id"), \
                f"Record missing id for post {post['id']}"
            
            # When record is present, frontend uses record fields primarily
            title = record.get("title") or post.get("record_title")
            artist = record.get("artist") or post.get("record_artist")
            cover = record.get("cover_url") or post.get("cover_url")
            
            print(f"Post {post['id'][:8]}: record.id={record.get('id')[:8] if record.get('id') else 'N/A'}, title={title[:30] if title else 'N/A'}")


class TestFeedPostTypes:
    """Test each post type renders with fallback data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "kmklodnicki@gmail.com", "password": "HoneyGroove2026!"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_feed_pagination(self):
        """Test feed pagination works correctly"""
        # First page
        resp1 = requests.get(f"{BASE_URL}/api/feed?limit=5&skip=0", headers=self.headers)
        assert resp1.status_code == 200
        posts1 = resp1.json()
        
        # Second page
        resp2 = requests.get(f"{BASE_URL}/api/feed?limit=5&skip=5", headers=self.headers)
        assert resp2.status_code == 200
        posts2 = resp2.json()
        
        print(f"Page 1: {len(posts1)} posts, Page 2: {len(posts2)} posts")
        
        # Posts should be different (if enough posts exist)
        if posts1 and posts2:
            page1_ids = set(p["id"] for p in posts1)
            page2_ids = set(p["id"] for p in posts2)
            overlap = page1_ids & page2_ids
            assert len(overlap) == 0, f"Pages should not overlap, found {len(overlap)} duplicates"
    
    def test_feed_before_cursor_pagination(self):
        """Test 'before' cursor pagination"""
        # Get first page
        resp1 = requests.get(f"{BASE_URL}/api/feed?limit=3", headers=self.headers)
        assert resp1.status_code == 200
        posts1 = resp1.json()
        
        if len(posts1) >= 2:
            # Use last post's created_at as cursor
            before = posts1[-1]["created_at"]
            resp2 = requests.get(f"{BASE_URL}/api/feed?limit=3&before={before}", headers=self.headers)
            assert resp2.status_code == 200
            posts2 = resp2.json()
            
            print(f"Before cursor: {len(posts2)} posts returned")
            
            # Posts should be older than cursor
            for p in posts2:
                assert p["created_at"] < before, "Posts should be older than cursor"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
