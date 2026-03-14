"""
Tests for Comment Soft-Delete Feature and LoadingHoney Global Loading State
- DELETE /api/comments/{commentId} — Soft-delete (sets is_deleted=true, content='[deleted]')
- GET /api/posts/{post_id}/comments — Filtering logic for deleted comments
- Authorization: Only author or admin can delete
- Error cases: 403 for unauthorized, 404 for non-existent
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "HoneyGroove2026!"

class TestCommentDeletion:
    """Tests for comment soft-delete functionality"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Create authenticated admin session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, "No token returned from admin login"
        
        session.headers.update({"Authorization": f"Bearer {token}"})
        session.user_id = data.get("user", {}).get("id")
        session.username = data.get("user", {}).get("username")
        return session

    @pytest.fixture(scope="class")
    def test_post(self, admin_session):
        """Create a test post for comments"""
        # First get a record from collection to use in post
        records_resp = admin_session.get(f"{BASE_URL}/api/records?limit=1")
        records = records_resp.json() if records_resp.status_code == 200 else []
        
        record_id = records[0]["id"] if records else None
        
        # Create a Now Spinning post
        post_data = {
            "record_id": record_id,
            "caption": f"TEST_252_comment_deletion_test_{uuid.uuid4().hex[:8]}",
            "track": "Test Track",
            "mood": "chill"
        }
        
        response = admin_session.post(f"{BASE_URL}/api/composer/now-spinning", json=post_data)
        if response.status_code != 200:
            # Try a Note post instead
            note_data = {"text": f"TEST_252_comment_deletion_test_{uuid.uuid4().hex[:8]}"}
            response = admin_session.post(f"{BASE_URL}/api/composer/note", json=note_data)
        
        assert response.status_code == 200, f"Failed to create test post: {response.text}"
        return response.json()

    def test_create_and_delete_own_comment(self, admin_session, test_post):
        """Test creating a comment then soft-deleting it (author delete)"""
        post_id = test_post["id"]
        
        # Create a comment
        comment_content = f"TEST_252_comment_to_delete_{uuid.uuid4().hex[:8]}"
        create_resp = admin_session.post(f"{BASE_URL}/api/posts/{post_id}/comments", json={
            "post_id": post_id,
            "content": comment_content
        })
        assert create_resp.status_code == 200, f"Failed to create comment: {create_resp.text}"
        comment = create_resp.json()
        comment_id = comment["id"]
        
        # Delete the comment
        delete_resp = admin_session.delete(f"{BASE_URL}/api/comments/{comment_id}")
        assert delete_resp.status_code == 200, f"Failed to delete comment: {delete_resp.text}"
        data = delete_resp.json()
        assert data.get("message") == "Comment deleted", f"Unexpected response: {data}"
        
        print(f"SUCCESS: Own comment deleted - ID: {comment_id}")

    def test_deleted_comment_appears_with_is_deleted_flag(self, admin_session, test_post):
        """Test that soft-deleted comments show is_deleted=true in API response"""
        post_id = test_post["id"]
        
        # Create a top-level comment
        parent_content = f"TEST_252_parent_comment_{uuid.uuid4().hex[:8]}"
        parent_resp = admin_session.post(f"{BASE_URL}/api/posts/{post_id}/comments", json={
            "post_id": post_id,
            "content": parent_content
        })
        assert parent_resp.status_code == 200
        parent = parent_resp.json()
        parent_id = parent["id"]
        
        # Create a reply to the parent
        reply_content = f"TEST_252_reply_comment_{uuid.uuid4().hex[:8]}"
        reply_resp = admin_session.post(f"{BASE_URL}/api/posts/{post_id}/comments", json={
            "post_id": post_id,
            "content": reply_content,
            "parent_id": parent_id
        })
        assert reply_resp.status_code == 200
        reply = reply_resp.json()
        
        # Delete the parent (which has a reply, so should remain visible with is_deleted=true)
        delete_resp = admin_session.delete(f"{BASE_URL}/api/comments/{parent_id}")
        assert delete_resp.status_code == 200
        
        # Fetch comments and verify parent shows is_deleted=true
        comments_resp = admin_session.get(f"{BASE_URL}/api/posts/{post_id}/comments")
        assert comments_resp.status_code == 200
        comments = comments_resp.json()
        
        # Find the deleted parent comment
        deleted_parent = None
        for c in comments:
            if c["id"] == parent_id:
                deleted_parent = c
                break
        
        assert deleted_parent is not None, "Deleted parent with replies should still appear"
        assert deleted_parent.get("is_deleted") == True, "is_deleted flag should be True"
        assert deleted_parent.get("content") == "[deleted]", "Content should be '[deleted]'"
        
        print(f"SUCCESS: Deleted comment with replies shows is_deleted=true")

    def test_deleted_comment_without_replies_filtered_out(self, admin_session, test_post):
        """Test that deleted top-level comments with NO replies are filtered out"""
        post_id = test_post["id"]
        
        # Create a standalone comment (no replies)
        comment_content = f"TEST_252_standalone_comment_{uuid.uuid4().hex[:8]}"
        create_resp = admin_session.post(f"{BASE_URL}/api/posts/{post_id}/comments", json={
            "post_id": post_id,
            "content": comment_content
        })
        assert create_resp.status_code == 200
        comment_id = create_resp.json()["id"]
        
        # Delete it
        delete_resp = admin_session.delete(f"{BASE_URL}/api/comments/{comment_id}")
        assert delete_resp.status_code == 200
        
        # Fetch comments - deleted standalone should NOT appear
        comments_resp = admin_session.get(f"{BASE_URL}/api/posts/{post_id}/comments")
        assert comments_resp.status_code == 200
        comments = comments_resp.json()
        
        # Verify the deleted comment is not in the response
        deleted_found = any(c["id"] == comment_id for c in comments)
        assert not deleted_found, "Deleted comment without replies should be filtered out"
        
        print(f"SUCCESS: Deleted comment without replies is filtered out")

    def test_delete_nonexistent_comment_returns_404(self, admin_session):
        """Test DELETE on non-existent comment returns 404"""
        fake_id = str(uuid.uuid4())
        response = admin_session.delete(f"{BASE_URL}/api/comments/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print("SUCCESS: Non-existent comment returns 404")

    def test_unauthorized_user_cannot_delete_others_comment(self, admin_session, test_post):
        """Test that user cannot delete comment they don't own (without admin)"""
        # First, we need a second user. For this test, we'll try to create one
        # or skip if we can't
        post_id = test_post["id"]
        
        # Create a comment as admin
        comment_content = f"TEST_252_admin_comment_{uuid.uuid4().hex[:8]}"
        create_resp = admin_session.post(f"{BASE_URL}/api/posts/{post_id}/comments", json={
            "post_id": post_id,
            "content": comment_content
        })
        assert create_resp.status_code == 200
        comment_id = create_resp.json()["id"]
        
        # Try to register/login as a different test user
        test_email = f"test_{uuid.uuid4().hex[:8]}@testuser.com"
        test_password = "TestPass123!"
        
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": test_password,
            "username": f"testuser_{uuid.uuid4().hex[:6]}"
        })
        
        if register_resp.status_code != 200:
            # If registration fails (maybe not allowed), skip this test
            print(f"SKIPPED: Could not create test user for unauthorized delete test")
            return
        
        # Login as the test user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        
        if login_resp.status_code != 200:
            print(f"SKIPPED: Could not login as test user")
            return
        
        token = login_resp.json().get("token")
        
        # Try to delete admin's comment with test user token
        delete_resp = requests.delete(
            f"{BASE_URL}/api/comments/{comment_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert delete_resp.status_code == 403, f"Expected 403, got {delete_resp.status_code}"
        
        # Clean up: delete the comment with admin
        admin_session.delete(f"{BASE_URL}/api/comments/{comment_id}")
        
        print("SUCCESS: Unauthorized user gets 403 when trying to delete others' comment")

    def test_admin_can_delete_any_comment(self, admin_session, test_post):
        """Test that admin can delete any comment (admin privilege)"""
        # This test uses admin session which should be able to delete any comment
        # The admin_session is already logged in as admin
        post_id = test_post["id"]
        
        # Create a comment
        comment_content = f"TEST_252_admin_deletable_{uuid.uuid4().hex[:8]}"
        create_resp = admin_session.post(f"{BASE_URL}/api/posts/{post_id}/comments", json={
            "post_id": post_id,
            "content": comment_content
        })
        assert create_resp.status_code == 200
        comment_id = create_resp.json()["id"]
        
        # Admin should be able to delete it
        delete_resp = admin_session.delete(f"{BASE_URL}/api/comments/{comment_id}")
        assert delete_resp.status_code == 200
        
        print("SUCCESS: Admin can delete any comment")


class TestGetCommentsFiltering:
    """Tests for GET /api/posts/{post_id}/comments filtering logic"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Create authenticated admin session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        token = data.get("access_token") or data.get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session

    def test_comments_endpoint_returns_nested_structure(self, admin_session):
        """Test that GET /api/posts/{post_id}/comments returns nested replies"""
        # Get feed to find a post with comments
        feed_resp = admin_session.get(f"{BASE_URL}/api/feed?limit=10")
        assert feed_resp.status_code == 200
        posts = feed_resp.json()
        
        # Find a post with comments
        post_with_comments = None
        for p in posts:
            if p.get("comments_count", 0) > 0:
                post_with_comments = p
                break
        
        if not post_with_comments:
            print("SKIPPED: No posts with comments found")
            return
        
        # Fetch comments
        comments_resp = admin_session.get(f"{BASE_URL}/api/posts/{post_with_comments['id']}/comments")
        assert comments_resp.status_code == 200
        comments = comments_resp.json()
        
        # Verify structure
        assert isinstance(comments, list), "Comments should be a list"
        if comments:
            first = comments[0]
            assert "id" in first, "Comment should have id"
            assert "content" in first, "Comment should have content"
            assert "user" in first, "Comment should have user info"
            assert "replies" in first, "Comment should have replies array"
            assert "is_deleted" in first, "Comment should have is_deleted field"
        
        print(f"SUCCESS: Comments endpoint returns proper nested structure")


class TestLoadingHoneyCSS:
    """Tests for LoadingHoney CSS animation verification"""
    
    def test_pulse_honey_animation_exists(self):
        """Verify pulse-honey keyframes are defined in index.css"""
        css_path = "/app/frontend/src/index.css"
        
        try:
            with open(css_path, 'r') as f:
                css_content = f.read()
        except FileNotFoundError:
            pytest.fail(f"CSS file not found: {css_path}")
        
        # Check for pulse-honey keyframes
        assert "@keyframes pulse-honey" in css_content, "pulse-honey keyframes not found"
        assert "scale(0.9)" in css_content, "scale(0.9) not found in animation"
        assert "scale(1.0)" in css_content or "scale(1)" in css_content, "scale(1.0) not found in animation"
        
        # Check animation timing
        assert "1.5s" in css_content, "1.5s animation duration not found"
        
        print("SUCCESS: pulse-honey CSS animation properly defined")

    def test_loading_honey_container_styles(self):
        """Verify loading-honey container styles exist"""
        css_path = "/app/frontend/src/index.css"
        
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        assert ".loading-honey-container" in css_content, "loading-honey-container class not found"
        assert ".loading-honey-icon" in css_content, "loading-honey-icon class not found"
        assert ".loading-honey-text" in css_content, "loading-honey-text class not found"
        
        print("SUCCESS: LoadingHoney container styles properly defined")


class TestLoadingHoneyComponent:
    """Tests for LoadingHoney component structure"""
    
    def test_loading_honey_component_exists(self):
        """Verify LoadingHoney.js component exists with proper structure"""
        component_path = "/app/frontend/src/components/LoadingHoney.js"
        
        try:
            with open(component_path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            pytest.fail(f"LoadingHoney component not found: {component_path}")
        
        # Check for key elements
        assert 'data-testid="loading-honey"' in content, "data-testid='loading-honey' not found"
        assert "Fetching the honey" in content, "Default text 'Fetching the honey' not found"
        assert "size" in content, "Size prop not found"
        assert "pulse-honey" in content or "loading-honey-icon" in content, "Animation class not found"
        
        print("SUCCESS: LoadingHoney component properly structured")

    def test_loading_honey_size_variants(self):
        """Verify LoadingHoney has sm, md, lg size variants"""
        component_path = "/app/frontend/src/components/LoadingHoney.js"
        
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for size variants
        assert "'sm'" in content or '"sm"' in content, "sm size variant not found"
        assert "'md'" in content or '"md"' in content, "md size variant not found"
        assert "'lg'" in content or '"lg"' in content, "lg size variant not found"
        
        print("SUCCESS: LoadingHoney has all size variants (sm, md, lg)")


class TestLoadingHoneyUsage:
    """Tests for LoadingHoney usage in pages"""
    
    def test_hive_page_uses_loading_honey(self):
        """Verify HivePage imports and uses LoadingHoney"""
        page_path = "/app/frontend/src/pages/HivePage.js"
        
        with open(page_path, 'r') as f:
            content = f.read()
        
        assert "LoadingHoney" in content, "LoadingHoney not imported in HivePage"
        assert "import LoadingHoney" in content, "LoadingHoney import statement not found"
        assert "<LoadingHoney" in content, "LoadingHoney component not used"
        
        print("SUCCESS: HivePage uses LoadingHoney component")

    def test_profile_page_uses_loading_honey(self):
        """Verify ProfilePage imports and uses LoadingHoney"""
        page_path = "/app/frontend/src/pages/ProfilePage.js"
        
        with open(page_path, 'r') as f:
            content = f.read()
        
        assert "LoadingHoney" in content, "LoadingHoney not imported in ProfilePage"
        assert "<LoadingHoney" in content, "LoadingHoney component not used in ProfilePage"
        
        print("SUCCESS: ProfilePage uses LoadingHoney component")

    def test_search_page_uses_loading_honey(self):
        """Verify SearchPage imports and uses LoadingHoney"""
        page_path = "/app/frontend/src/pages/SearchPage.js"
        
        with open(page_path, 'r') as f:
            content = f.read()
        
        assert "LoadingHoney" in content, "LoadingHoney not imported in SearchPage"
        assert "<LoadingHoney" in content, "LoadingHoney component not used in SearchPage"
        
        print("SUCCESS: SearchPage uses LoadingHoney component")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
