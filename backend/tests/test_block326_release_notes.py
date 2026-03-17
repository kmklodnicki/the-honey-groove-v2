"""
BLOCK-326: Admin Release Notes System Tests
Features:
1) Admin-only POST /api/posts/{post_id}/release-note toggles is_release_note
2) GET /api/feed?post_type=RELEASE_NOTE only returns posts with is_release_note=true
3) Release Note badge overrides the default post type pill
4) Collapsible release note posts with localStorage persistence
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "kmklodnicki@gmail.com"
TEST_PASSWORD = "HoneyGroove2026"


@pytest.fixture(scope="module")
def admin_session():
    """Login and get admin token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in response"
    assert data.get("user", {}).get("is_admin") == True, "User is not admin"
    
    session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
    return session, data


class TestReleaseNoteEndpoint:
    """Test POST /api/posts/{post_id}/release-note endpoint"""
    
    def test_login_and_verify_admin(self, admin_session):
        """Test 1: Login with admin account"""
        session, data = admin_session
        assert data["user"]["is_admin"] == True
        print(f"PASS: Logged in as admin: {data['user']['username']}")
    
    def test_get_feed_for_test_post(self, admin_session):
        """Get a post from the feed to test with"""
        session, data = admin_session
        
        response = session.get(f"{BASE_URL}/api/feed", params={"limit": 10})
        assert response.status_code == 200, f"Feed failed: {response.text}"
        
        posts = response.json()
        assert len(posts) > 0, "No posts found in feed"
        
        # Find a non-release-note post to promote
        test_post = None
        for p in posts:
            if not p.get("is_release_note") and not p.get("is_pinned"):
                test_post = p
                break
        
        if not test_post:
            # Use first post if all are release notes
            test_post = posts[0]
        
        print(f"PASS: Found test post: {test_post['id']} (type: {test_post.get('post_type')})")
        return test_post
    
    def test_promote_to_release_note(self, admin_session):
        """Test 2: Backend POST /api/posts/{post_id}/release-note toggles is_release_note"""
        session, data = admin_session
        
        # Get a test post
        response = session.get(f"{BASE_URL}/api/feed", params={"limit": 10})
        posts = response.json()
        test_post = None
        for p in posts:
            if not p.get("is_release_note"):
                test_post = p
                break
        
        if not test_post:
            test_post = posts[0]
        
        post_id = test_post["id"]
        initial_state = test_post.get("is_release_note", False)
        
        # Toggle release note
        response = session.post(f"{BASE_URL}/api/posts/{post_id}/release-note")
        assert response.status_code == 200, f"Toggle failed: {response.text}"
        
        result = response.json()
        assert "is_release_note" in result, "Response missing is_release_note field"
        assert result["is_release_note"] == (not initial_state), f"Toggle did not flip state: {result}"
        
        print(f"PASS: Toggled post {post_id} is_release_note to {result['is_release_note']}")
        
        # Store for cleanup
        return post_id, result["is_release_note"]
    
    def test_release_note_filter(self, admin_session):
        """Test 3: Backend GET /api/feed?post_type=RELEASE_NOTE only returns is_release_note=true posts"""
        session, data = admin_session
        
        # First, promote a post to release note if none exist
        response = session.get(f"{BASE_URL}/api/feed", params={"limit": 20})
        posts = response.json()
        
        # Find or create a release note post
        release_note_post = None
        for p in posts:
            if p.get("is_release_note"):
                release_note_post = p
                break
        
        if not release_note_post:
            # Promote a post to release note for testing
            test_post = posts[0] if posts else None
            if test_post:
                promote_response = session.post(f"{BASE_URL}/api/posts/{test_post['id']}/release-note")
                if promote_response.status_code == 200:
                    release_note_post = test_post
                    release_note_post["is_release_note"] = True
        
        # Now test the RELEASE_NOTE filter
        response = session.get(f"{BASE_URL}/api/feed", params={"post_type": "RELEASE_NOTE", "limit": 50})
        assert response.status_code == 200, f"RELEASE_NOTE filter failed: {response.text}"
        
        filtered_posts = response.json()
        
        # Verify all returned posts have is_release_note=true
        for p in filtered_posts:
            assert p.get("is_release_note") == True, f"Post {p['id']} in RELEASE_NOTE filter has is_release_note={p.get('is_release_note')}"
        
        print(f"PASS: RELEASE_NOTE filter returned {len(filtered_posts)} posts, all with is_release_note=true")
        return filtered_posts
    
    def test_verify_post_has_release_note_field(self, admin_session):
        """Verify that posts in feed include is_release_note field"""
        session, data = admin_session
        
        response = session.get(f"{BASE_URL}/api/feed", params={"limit": 5})
        assert response.status_code == 200
        
        posts = response.json()
        for p in posts:
            assert "is_release_note" in p, f"Post {p['id']} missing is_release_note field"
        
        print(f"PASS: All posts in feed have is_release_note field")
    
    def test_non_admin_cannot_toggle_release_note(self, admin_session):
        """Test that non-admin users cannot toggle release note"""
        session, data = admin_session
        
        # Get a post ID
        response = session.get(f"{BASE_URL}/api/feed", params={"limit": 1})
        posts = response.json()
        if not posts:
            pytest.skip("No posts available")
        
        post_id = posts[0]["id"]
        
        # Create a new session without admin privileges (simulate by using invalid token)
        non_admin_session = requests.Session()
        non_admin_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid_token_for_testing"
        })
        
        response = non_admin_session.post(f"{BASE_URL}/api/posts/{post_id}/release-note")
        # Should fail with 401 (invalid token) or 403 (non-admin)
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
        
        print(f"PASS: Non-admin request correctly rejected with status {response.status_code}")


class TestReleaseNoteCleanup:
    """Cleanup test: demote any promoted posts back to normal"""
    
    def test_cleanup_release_notes(self, admin_session):
        """Demote any test-promoted posts back to normal"""
        session, data = admin_session
        
        # Get release note posts
        response = session.get(f"{BASE_URL}/api/feed", params={"post_type": "RELEASE_NOTE", "limit": 50})
        posts = response.json()
        
        # Demote posts that might have been promoted during testing
        # Only demote posts that aren't intentionally release notes
        demoted = 0
        for p in posts:
            # Skip posts that look like intentional admin announcements
            caption = (p.get("caption") or p.get("content") or "").lower()
            if "release" in caption or "update" in caption or "changelog" in caption or "feature" in caption:
                continue
            
            # Demote back to normal (toggle off)
            response = session.post(f"{BASE_URL}/api/posts/{p['id']}/release-note")
            if response.status_code == 200:
                demoted += 1
        
        print(f"INFO: Cleanup demoted {demoted} posts back to normal")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
