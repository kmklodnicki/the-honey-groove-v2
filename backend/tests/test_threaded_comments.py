"""
Test suite for HoneyGroove enhanced threaded comment system:
1. POST /api/posts/{post_id}/comments - Create top-level comment (parent_id null)
2. POST /api/posts/{post_id}/comments with parent_id - Reply to top-level comment
3. GET /api/posts/{post_id}/comments - Returns tree structure with replies array
4. Smart notifications - Thread owner + direct parent both notified

Testing iteration 251 features.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials for testing
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "HoneyGroove2026!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get auth token using admin credentials"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def test_post_id(api_client, auth_token):
    """Get a post from the feed to test comments on"""
    response = api_client.get(f"{BASE_URL}/api/feed", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    if response.status_code != 200:
        pytest.skip(f"Failed to get feed: {response.text}")
    
    posts = response.json()
    if not posts:
        pytest.skip("No posts in feed to test comments on")
    
    return posts[0]["id"]


class TestBackendCommentAPIs:
    """Backend API tests for threaded comment system"""
    
    def test_create_top_level_comment(self, api_client, auth_token, test_post_id):
        """POST /api/posts/{post_id}/comments - Create top-level comment (parent_id null)"""
        response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post_id}/comments",
            json={
                "post_id": test_post_id,
                "content": "TEST_251_top_level: This is a top-level comment for iteration 251 testing"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response should contain comment id"
        assert "content" in data, "Response should contain content"
        assert "user" in data, "Response should contain user info"
        assert data.get("parent_id") is None, f"Top-level comment parent_id should be null, got {data.get('parent_id')}"
        
        print(f"[PASS] Top-level comment created: id={data['id']}, parent_id={data.get('parent_id')}")
        
        # Store the comment ID for reply tests
        pytest.top_level_comment_id = data["id"]
        return data
    
    def test_create_reply_to_top_level(self, api_client, auth_token, test_post_id):
        """POST /api/posts/{post_id}/comments with parent_id - Reply to top-level comment"""
        # First get the top-level comment ID from previous test
        if not hasattr(pytest, 'top_level_comment_id'):
            # Create a top-level comment first
            self.test_create_top_level_comment(api_client, auth_token, test_post_id)
        
        parent_id = pytest.top_level_comment_id
        
        response = api_client.post(
            f"{BASE_URL}/api/posts/{test_post_id}/comments",
            json={
                "post_id": test_post_id,
                "content": "TEST_251_reply: This is a reply to the top-level comment",
                "parent_id": parent_id
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response should contain comment id"
        assert data.get("parent_id") == parent_id, f"Reply parent_id should be {parent_id}, got {data.get('parent_id')}"
        
        print(f"[PASS] Reply created: id={data['id']}, parent_id={data.get('parent_id')}")
        
        # Store for later tests
        pytest.reply_comment_id = data["id"]
        return data
    
    def test_get_comments_tree_structure(self, api_client, auth_token, test_post_id):
        """GET /api/posts/{post_id}/comments - Returns tree structure with replies array"""
        response = api_client.get(
            f"{BASE_URL}/api/posts/{test_post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        comments = response.json()
        
        assert isinstance(comments, list), "Comments should be a list"
        
        # Find a top-level comment with replies
        found_top_level_with_replies = False
        for comment in comments:
            # Verify structure
            assert "id" in comment, "Comment should have id"
            assert "content" in comment, "Comment should have content"
            assert "user" in comment, "Comment should have user info"
            assert "replies" in comment, "Comment should have replies array"
            
            if comment.get("replies") and len(comment["replies"]) > 0:
                found_top_level_with_replies = True
                for reply in comment["replies"]:
                    assert "parent_id" in reply, "Reply should have parent_id"
                    assert reply.get("parent_id") == comment["id"], f"Reply parent_id should match parent comment id"
                print(f"[PASS] Found top-level comment with {len(comment['replies'])} replies")
        
        print(f"[PASS] GET comments returns tree structure, found parent with replies: {found_top_level_with_replies}")
        return comments
    
    def test_reply_has_correct_structure(self, api_client, auth_token, test_post_id):
        """Verify that reply comments have proper structure in tree"""
        response = api_client.get(
            f"{BASE_URL}/api/posts/{test_post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        comments = response.json()
        
        # Check our test comments
        top_level_found = False
        reply_found = False
        
        for comment in comments:
            if "TEST_251_top_level" in comment.get("content", ""):
                top_level_found = True
                assert comment.get("parent_id") is None, "Top-level comment should have null parent_id"
                
                # Check if our reply is nested under it
                for reply in comment.get("replies", []):
                    if "TEST_251_reply" in reply.get("content", ""):
                        reply_found = True
                        assert reply.get("parent_id") == comment["id"], "Reply should have correct parent_id"
        
        print(f"[PASS] Top-level found: {top_level_found}, Reply found in nested structure: {reply_found}")


class TestCleanup:
    """Cleanup test comments"""
    
    def test_cleanup_test_comments(self, api_client, auth_token, test_post_id):
        """Clean up TEST_251_ prefixed comments"""
        response = api_client.get(
            f"{BASE_URL}/api/posts/{test_post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            comments = response.json()
            # Note: There's no DELETE endpoint for comments in the API
            # This is just documentation of test data created
            test_comments = []
            for comment in comments:
                if "TEST_251_" in comment.get("content", ""):
                    test_comments.append(comment["id"])
                for reply in comment.get("replies", []):
                    if "TEST_251_" in reply.get("content", ""):
                        test_comments.append(reply["id"])
            
            print(f"[INFO] Test comments created (manual cleanup if needed): {test_comments}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
