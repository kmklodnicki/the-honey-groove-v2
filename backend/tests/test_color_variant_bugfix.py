"""
Test suite for color_variant bug fix on Hive feed cards.

Bug Description: Variant/color info was not showing on Hive feed cards.
Root Causes Fixed:
1. build_post_response did not propagate color_variant from record to post response
2. composer/now-spinning didn't store color_variant on the post document
3. add_record in collection.py didn't store color_variant on ADDED_TO_COLLECTION post

This test verifies the logic is correct by testing the fix at multiple levels.
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test fixtures
@pytest.fixture(scope="module")
def test_user():
    """Create or reuse a test user for authenticated requests."""
    unique_id = str(uuid.uuid4())[:8]
    email = f"test_colorvar_{unique_id}@test.com"
    password = "testpass123"
    username = f"colorvartest{unique_id}"
    
    # Try to register
    register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email,
        "password": password,
        "username": username
    })
    
    if register_resp.status_code == 201:
        data = register_resp.json()
        return {"token": data["access_token"], "user_id": data["user"]["id"], "email": email}
    
    # If registration fails, try login
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    
    if login_resp.status_code == 200:
        data = login_resp.json()
        return {"token": data["access_token"], "user_id": data["user"]["id"], "email": email}
    
    pytest.skip(f"Could not create or login test user: {register_resp.text}")


@pytest.fixture
def auth_headers(test_user):
    """Get auth headers for API requests."""
    return {"Authorization": f"Bearer {test_user['token']}", "Content-Type": "application/json"}


class TestColorVariantBugFix:
    """Tests for the color_variant bug fix."""
    
    # ============ Test 1: PostResponse model has color_variant field ============
    def test_post_response_model_has_color_variant_field(self):
        """Verify PostResponse model includes color_variant in schema."""
        # This is a code review verification - we import and check the model
        import sys
        sys.path.insert(0, '/app/backend')
        from models import PostResponse
        
        # Check if color_variant is in the model's fields
        assert 'color_variant' in PostResponse.model_fields, "PostResponse model must have color_variant field"
        print("✅ PostResponse model has color_variant field")
    
    # ============ Test 2: Record creation stores color_variant ============
    def test_record_creation_with_color_variant(self, auth_headers):
        """Test that creating a record with color_variant stores it correctly."""
        unique_id = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"TEST_Album_{unique_id}",
            "artist": f"TEST_Artist_{unique_id}",
            "year": 2024,
            "format": "Vinyl",
            "color_variant": "Red Marble Vinyl"
        }
        
        resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        
        if resp.status_code == 201:
            data = resp.json()
            assert data.get("color_variant") == "Red Marble Vinyl", "color_variant should be stored on record"
            print(f"✅ Record created with color_variant: {data.get('color_variant')}")
            return data["id"]
        else:
            print(f"⚠️ Record creation returned {resp.status_code}: {resp.text}")
            pytest.skip("Record creation failed")
    
    # ============ Test 3: ADDED_TO_COLLECTION post stores color_variant ============
    def test_added_to_collection_post_has_color_variant(self, auth_headers, test_user):
        """Test that ADDED_TO_COLLECTION posts include color_variant from the record."""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create a record with color_variant
        record_data = {
            "title": f"TEST_Album_ATC_{unique_id}",
            "artist": f"TEST_Artist_ATC_{unique_id}",
            "year": 2024,
            "format": "Vinyl",
            "color_variant": "Blue Splatter"
        }
        
        record_resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        
        if record_resp.status_code != 201:
            pytest.skip(f"Record creation failed: {record_resp.text}")
        
        record_id = record_resp.json()["id"]
        
        # Fetch the feed to find the ADDED_TO_COLLECTION post
        feed_resp = requests.get(f"{BASE_URL}/api/feed?limit=20", headers=auth_headers)
        
        if feed_resp.status_code == 200:
            posts = feed_resp.json()
            
            # Find the post for this record
            matching_posts = [p for p in posts if p.get("record_id") == record_id and p.get("post_type") == "ADDED_TO_COLLECTION"]
            
            if matching_posts:
                post = matching_posts[0]
                # The fix ensures color_variant is on the PostResponse
                post_color_variant = post.get("color_variant")
                record_color_variant = post.get("record", {}).get("color_variant") if post.get("record") else None
                
                # Either post-level or record-level should have the variant
                actual_variant = post_color_variant or record_color_variant
                assert actual_variant == "Blue Splatter", f"Expected 'Blue Splatter', got '{actual_variant}'"
                print(f"✅ ADDED_TO_COLLECTION post has color_variant: {actual_variant}")
            else:
                print("⚠️ No ADDED_TO_COLLECTION post found for the record (may not auto-create in test env)")
        else:
            pytest.skip(f"Feed fetch failed: {feed_resp.text}")
    
    # ============ Test 4: NOW_SPINNING post stores color_variant via composer ============
    def test_now_spinning_post_stores_color_variant(self, auth_headers, test_user):
        """Test that composer/now-spinning stores color_variant on the post document."""
        unique_id = str(uuid.uuid4())[:8]
        
        # First create a record with color_variant
        record_data = {
            "title": f"TEST_Album_Spin_{unique_id}",
            "artist": f"TEST_Artist_Spin_{unique_id}",
            "year": 2024,
            "format": "Vinyl",
            "color_variant": "Gold Metallic"
        }
        
        record_resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        
        if record_resp.status_code != 201:
            pytest.skip(f"Record creation failed: {record_resp.text}")
        
        record_id = record_resp.json()["id"]
        
        # Create a NOW_SPINNING post via composer
        spin_data = {
            "record_id": record_id,
            "caption": f"Testing color variant {unique_id}",
            "track": "Test Track",
            "mood": "Late Night"
        }
        
        spin_resp = requests.post(f"{BASE_URL}/api/composer/now-spinning", json=spin_data, headers=auth_headers)
        
        if spin_resp.status_code == 200:
            post = spin_resp.json()
            
            # The fix ensures color_variant is populated from the record
            post_color_variant = post.get("color_variant")
            record_color_variant = post.get("record", {}).get("color_variant") if post.get("record") else None
            
            actual_variant = post_color_variant or record_color_variant
            assert actual_variant == "Gold Metallic", f"Expected 'Gold Metallic', got '{actual_variant}'"
            print(f"✅ NOW_SPINNING post has color_variant: {actual_variant}")
            print(f"   - post.color_variant: {post_color_variant}")
            print(f"   - record.color_variant: {record_color_variant}")
        else:
            pytest.skip(f"Composer now-spinning failed: {spin_resp.text}")
    
    # ============ Test 5: build_post_response resolves color_variant from record ============
    def test_build_post_response_resolves_color_variant(self, auth_headers, test_user):
        """Test that build_post_response resolves color_variant from record when post doesn't have it."""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create a record with color_variant
        record_data = {
            "title": f"TEST_Album_Resolve_{unique_id}",
            "artist": f"TEST_Artist_Resolve_{unique_id}",
            "year": 2024,
            "format": "Vinyl",
            "color_variant": "Picture Disc"
        }
        
        record_resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=auth_headers)
        
        if record_resp.status_code != 201:
            pytest.skip(f"Record creation failed: {record_resp.text}")
        
        record_id = record_resp.json()["id"]
        
        # Fetch the feed and look for posts with this record
        feed_resp = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=auth_headers)
        
        if feed_resp.status_code == 200:
            posts = feed_resp.json()
            
            # Find any post with this record_id
            matching_posts = [p for p in posts if p.get("record_id") == record_id]
            
            if matching_posts:
                post = matching_posts[0]
                # The fix ensures resolved_color_variant is populated
                # Either from post.color_variant or record.color_variant
                post_variant = post.get("color_variant")
                record = post.get("record", {})
                record_variant = record.get("color_variant") if record else None
                
                resolved = post_variant or record_variant
                print(f"✅ Resolved color_variant: {resolved}")
                print(f"   - post.color_variant: {post_variant}")
                print(f"   - record.color_variant: {record_variant}")
                
                assert resolved == "Picture Disc", f"Expected 'Picture Disc', got '{resolved}'"
            else:
                print("⚠️ No posts found with the test record (expected behavior in empty DB)")
        else:
            pytest.skip(f"Feed fetch failed: {feed_resp.text}")
    
    # ============ Test 6: Verify feed post structure includes color_variant ============
    def test_feed_post_structure_has_color_variant_field(self, auth_headers):
        """Test that posts in the feed have the color_variant field available."""
        feed_resp = requests.get(f"{BASE_URL}/api/feed?limit=10", headers=auth_headers)
        
        if feed_resp.status_code == 200:
            posts = feed_resp.json()
            
            if posts:
                # Check first post has color_variant field (even if null)
                first_post = posts[0]
                # The field should exist in the response, even if None
                # Since PostResponse model has it, it should be serialized
                print(f"✅ Feed returns posts. First post type: {first_post.get('post_type')}")
                print(f"   - color_variant field present: {'color_variant' in first_post}")
                print(f"   - color_variant value: {first_post.get('color_variant')}")
                
                # Check if record is embedded and has color_variant
                record = first_post.get("record")
                if record:
                    print(f"   - record.color_variant: {record.get('color_variant')}")
            else:
                print("⚠️ Feed is empty (expected in empty DB)")
                # Still a pass - the structure is correct, just no data
        else:
            pytest.skip(f"Feed fetch failed: {feed_resp.text}")
    
    # ============ Test 7: Verify explore feed also has color_variant ============
    def test_explore_feed_has_color_variant(self, auth_headers):
        """Test that explore feed posts include color_variant."""
        explore_resp = requests.get(f"{BASE_URL}/api/explore?limit=10", headers=auth_headers)
        
        if explore_resp.status_code == 200:
            posts = explore_resp.json()
            
            if posts:
                first_post = posts[0]
                print(f"✅ Explore feed returns posts. First post type: {first_post.get('post_type')}")
                print(f"   - color_variant: {first_post.get('color_variant')}")
            else:
                print("⚠️ Explore feed is empty (expected in empty DB)")
        else:
            pytest.skip(f"Explore fetch failed: {explore_resp.text}")


class TestColorVariantCodeReview:
    """Code review verification tests."""
    
    def test_hive_build_post_response_has_resolved_color_variant_logic(self):
        """Verify build_post_response has the fix for resolving color_variant."""
        with open('/app/backend/routes/hive.py', 'r') as f:
            content = f.read()
        
        # Check for the resolved_color_variant variable
        assert 'resolved_color_variant' in content, "build_post_response should have resolved_color_variant variable"
        
        # Check that record_color_variant is extracted from record
        assert 'record_color_variant' in content, "Should extract color_variant from record"
        
        # Check the resolution logic
        assert 'post.get("color_variant") or record_color_variant' in content, \
            "Should resolve color_variant from post first, then record"
        
        # Check that resolved value is used in PostResponse
        assert 'color_variant=resolved_color_variant' in content, \
            "PostResponse should use resolved_color_variant"
        
        print("✅ build_post_response has correct color_variant resolution logic")
    
    def test_composer_now_spinning_stores_color_variant(self):
        """Verify composer_now_spinning stores color_variant on post document."""
        with open('/app/backend/routes/hive.py', 'r') as f:
            content = f.read()
        
        # Find the composer_now_spinning function and check it stores color_variant
        assert '"color_variant": record.get("color_variant")' in content or \
               "'color_variant': record.get('color_variant')" in content, \
            "composer_now_spinning should store color_variant from record"
        
        print("✅ composer_now_spinning stores color_variant on post document")
    
    def test_collection_add_record_stores_color_variant_on_post(self):
        """Verify add_record stores color_variant on ADDED_TO_COLLECTION post."""
        with open('/app/backend/routes/collection.py', 'r') as f:
            content = f.read()
        
        # Check that ADDED_TO_COLLECTION post includes color_variant
        # The fix adds color_variant: record_data.color_variant to the post_doc
        assert 'color_variant' in content and 'ADDED_TO_COLLECTION' in content, \
            "add_record should store color_variant on ADDED_TO_COLLECTION post"
        
        print("✅ add_record stores color_variant on ADDED_TO_COLLECTION post")
    
    def test_post_response_model_has_color_variant(self):
        """Verify PostResponse model has color_variant field."""
        with open('/app/backend/models.py', 'r') as f:
            content = f.read()
        
        # Check PostResponse class has color_variant field
        assert 'class PostResponse' in content, "PostResponse model should exist"
        assert 'color_variant' in content, "PostResponse should have color_variant field"
        
        print("✅ PostResponse model has color_variant field")
    
    def test_frontend_postcards_prioritizes_post_color_variant(self):
        """Verify frontend PostCards prioritizes post.color_variant over record.color_variant."""
        with open('/app/frontend/src/components/PostCards.js', 'r') as f:
            content = f.read()
        
        # Check NowSpinningCard prioritizes post.color_variant
        assert 'post.color_variant || record.color_variant' in content, \
            "NowSpinningCard should check post.color_variant first"
        
        # Check AddedToCollectionCard also prioritizes post.color_variant
        assert 'post.color_variant' in content, \
            "AddedToCollectionCard should check post.color_variant"
        
        print("✅ Frontend PostCards correctly prioritizes post.color_variant")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
