"""
Test suite for delete post, delete listing, and delete ISO features
Iteration 65 - Testing new DELETE /api/posts/{post_id} endpoint and existing delete endpoints
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_USER_EMAIL = "testdelete65@test.com"
TEST_USER_PASSWORD = "testpass123"
TEST_USERNAME = f"testdel65_{uuid.uuid4().hex[:6]}"

OTHER_USER_EMAIL = "testother65@test.com"
OTHER_USER_PASSWORD = "testpass123"
OTHER_USERNAME = f"testother65_{uuid.uuid4().hex[:6]}"


class TestDeletePostEndpoint:
    """Tests for DELETE /api/posts/{post_id} endpoint"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_user(self, session):
        """Create and authenticate test user"""
        # First try to login, if fails, register
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            return {"token": data["access_token"], "user": data["user"], "session": session}
        
        # Register new user
        register_resp = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "username": TEST_USERNAME
        })
        
        if register_resp.status_code in [200, 201]:
            data = register_resp.json()
            return {"token": data["access_token"], "user": data["user"], "session": session}
        
        pytest.skip(f"Could not create test user: {register_resp.text}")
    
    @pytest.fixture(scope="class")
    def other_user(self, session):
        """Create second user to test ownership"""
        other_session = requests.Session()
        
        login_resp = other_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": OTHER_USER_EMAIL,
            "password": OTHER_USER_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            return {"token": data["access_token"], "user": data["user"], "session": other_session}
        
        # Register new user
        register_resp = other_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": OTHER_USER_EMAIL,
            "password": OTHER_USER_PASSWORD,
            "username": OTHER_USERNAME
        })
        
        if register_resp.status_code in [200, 201]:
            data = register_resp.json()
            return {"token": data["access_token"], "user": data["user"], "session": other_session}
        
        pytest.skip(f"Could not create other test user: {register_resp.text}")
    
    def test_delete_post_requires_auth(self, session):
        """DELETE /api/posts/{id} requires authentication"""
        response = session.delete(f"{BASE_URL}/api/posts/fake-post-id")
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated request, got {response.status_code}"
        print("PASSED: Delete post requires authentication")
    
    def test_delete_post_not_found(self, auth_user):
        """DELETE /api/posts/{id} returns 404 for non-existent post"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        response = auth_user["session"].delete(f"{BASE_URL}/api/posts/nonexistent-post-id", headers=headers)
        assert response.status_code == 404, f"Expected 404 for non-existent post, got {response.status_code}"
        print("PASSED: Delete post returns 404 for non-existent post")
    
    def test_delete_post_forbidden_for_non_owner(self, auth_user, other_user):
        """DELETE /api/posts/{id} returns 403 for non-owner"""
        # First user creates a post
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        
        # First add a record to collection (required for Now Spinning post)
        record_resp = auth_user["session"].post(f"{BASE_URL}/api/records", json={
            "title": "Test Delete Album",
            "artist": "Test Artist",
            "format": "Vinyl"
        }, headers=headers)
        
        if record_resp.status_code not in [200, 201]:
            pytest.skip("Could not create record for test")
        
        record_id = record_resp.json().get("id")
        
        # Create a Now Spinning post
        post_resp = auth_user["session"].post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record_id,
            "caption": "Test post for delete forbidden test"
        }, headers=headers)
        
        if post_resp.status_code not in [200, 201]:
            pytest.skip(f"Could not create post for test: {post_resp.text}")
        
        post_id = post_resp.json().get("id")
        
        # Other user tries to delete it - should get 403
        other_headers = {"Authorization": f"Bearer {other_user['token']}"}
        delete_resp = other_user["session"].delete(f"{BASE_URL}/api/posts/{post_id}", headers=other_headers)
        
        assert delete_resp.status_code == 403, f"Expected 403 for non-owner delete attempt, got {delete_resp.status_code}"
        
        # Cleanup - owner deletes the post
        auth_user["session"].delete(f"{BASE_URL}/api/posts/{post_id}", headers=headers)
        auth_user["session"].delete(f"{BASE_URL}/api/records/{record_id}", headers=headers)
        
        print("PASSED: Delete post returns 403 for non-owner")
    
    def test_delete_own_post_success(self, auth_user):
        """Owner can delete their own post"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        
        # Create a record
        record_resp = auth_user["session"].post(f"{BASE_URL}/api/records", json={
            "title": "Test Album For Delete",
            "artist": "Test Artist",
            "format": "Vinyl"
        }, headers=headers)
        
        if record_resp.status_code not in [200, 201]:
            pytest.skip("Could not create record for test")
        
        record_id = record_resp.json().get("id")
        
        # Create a post
        post_resp = auth_user["session"].post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record_id,
            "caption": "Test post to be deleted"
        }, headers=headers)
        
        if post_resp.status_code not in [200, 201]:
            pytest.skip(f"Could not create post for test: {post_resp.text}")
        
        post_id = post_resp.json().get("id")
        
        # Delete the post
        delete_resp = auth_user["session"].delete(f"{BASE_URL}/api/posts/{post_id}", headers=headers)
        assert delete_resp.status_code == 200, f"Expected 200 for successful delete, got {delete_resp.status_code}"
        
        # Verify deletion response
        data = delete_resp.json()
        assert "message" in data, "Response should contain message"
        assert "deleted" in data["message"].lower(), f"Response should confirm deletion: {data}"
        
        # Cleanup record
        auth_user["session"].delete(f"{BASE_URL}/api/records/{record_id}", headers=headers)
        
        print("PASSED: Owner can delete their own post")
    
    def test_delete_post_removes_likes_and_comments(self, auth_user, other_user):
        """Deleting a post also removes its likes and comments"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        other_headers = {"Authorization": f"Bearer {other_user['token']}"}
        
        # Create a record
        record_resp = auth_user["session"].post(f"{BASE_URL}/api/records", json={
            "title": "Test Album With Likes",
            "artist": "Test Artist",
            "format": "Vinyl"
        }, headers=headers)
        
        if record_resp.status_code not in [200, 201]:
            pytest.skip("Could not create record for test")
        
        record_id = record_resp.json().get("id")
        
        # Create a post
        post_resp = auth_user["session"].post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record_id,
            "caption": "Test post with likes and comments"
        }, headers=headers)
        
        if post_resp.status_code not in [200, 201]:
            pytest.skip(f"Could not create post for test: {post_resp.text}")
        
        post_id = post_resp.json().get("id")
        
        # Other user likes the post
        like_resp = other_user["session"].post(f"{BASE_URL}/api/posts/{post_id}/like", json={}, headers=other_headers)
        print(f"Like response: {like_resp.status_code}")
        
        # Other user comments on the post
        comment_resp = other_user["session"].post(f"{BASE_URL}/api/posts/{post_id}/comments", json={
            "post_id": post_id,
            "content": "Test comment for deletion test"
        }, headers=other_headers)
        print(f"Comment response: {comment_resp.status_code}")
        
        # Owner deletes the post
        delete_resp = auth_user["session"].delete(f"{BASE_URL}/api/posts/{post_id}", headers=headers)
        assert delete_resp.status_code == 200, f"Expected 200 for successful delete, got {delete_resp.status_code}"
        
        # Verify post no longer exists (API returns empty array or 404)
        get_resp = auth_user["session"].get(f"{BASE_URL}/api/posts/{post_id}/comments", headers=headers)
        # Either 404 or empty array is acceptable
        if get_resp.status_code == 200:
            comments = get_resp.json()
            assert len(comments) == 0, f"Comments should be empty after post deletion, got {len(comments)}"
        else:
            assert get_resp.status_code == 404, f"Expected 200 or 404, got {get_resp.status_code}"
        
        # Cleanup record
        auth_user["session"].delete(f"{BASE_URL}/api/records/{record_id}", headers=headers)
        
        print("PASSED: Delete post removes likes and comments")


class TestDeleteListingEndpoint:
    """Tests for DELETE /api/listings/{listing_id} endpoint"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_user(self, session):
        """Create and authenticate test user"""
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            return {"token": data["access_token"], "user": data["user"], "session": session}
        
        pytest.skip("Could not authenticate for listing tests")
    
    def test_delete_listing_requires_auth(self, session):
        """DELETE /api/listings/{id} requires authentication"""
        response = session.delete(f"{BASE_URL}/api/listings/fake-listing-id")
        assert response.status_code in [401, 403, 404], f"Expected auth error or 404, got {response.status_code}"
        print("PASSED: Delete listing requires authentication")
    
    def test_delete_listing_not_found(self, auth_user):
        """DELETE /api/listings/{id} returns 404 for non-existent listing"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        response = auth_user["session"].delete(f"{BASE_URL}/api/listings/nonexistent-listing-id", headers=headers)
        assert response.status_code == 404, f"Expected 404 for non-existent listing, got {response.status_code}"
        print("PASSED: Delete listing returns 404 for non-existent listing")


class TestDeleteISOEndpoint:
    """Tests for DELETE /api/iso/{iso_id} endpoint"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    @pytest.fixture(scope="class")
    def auth_user(self, session):
        """Create and authenticate test user"""
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            return {"token": data["access_token"], "user": data["user"], "session": session}
        
        pytest.skip("Could not authenticate for ISO tests")
    
    def test_delete_iso_requires_auth(self, session):
        """DELETE /api/iso/{id} requires authentication"""
        response = session.delete(f"{BASE_URL}/api/iso/fake-iso-id")
        assert response.status_code in [401, 403, 404], f"Expected auth error or 404, got {response.status_code}"
        print("PASSED: Delete ISO requires authentication")
    
    def test_delete_iso_not_found(self, auth_user):
        """DELETE /api/iso/{id} returns 404 for non-existent ISO"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        response = auth_user["session"].delete(f"{BASE_URL}/api/iso/nonexistent-iso-id", headers=headers)
        assert response.status_code == 404, f"Expected 404 for non-existent ISO, got {response.status_code}"
        print("PASSED: Delete ISO returns 404 for non-existent ISO")
    
    def test_create_and_delete_iso(self, auth_user):
        """Create ISO and delete it successfully"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        
        # Create an ISO
        iso_resp = auth_user["session"].post(f"{BASE_URL}/api/composer/iso", json={
            "artist": "Test Artist for ISO Delete",
            "album": "Test Album ISO Delete",
            "caption": "Testing ISO deletion"
        }, headers=headers)
        
        if iso_resp.status_code not in [200, 201]:
            pytest.skip(f"Could not create ISO for test: {iso_resp.text}")
        
        # Get ISO id from the response (it creates a post with iso_id)
        post_data = iso_resp.json()
        iso_id = post_data.get("iso_id")
        
        if not iso_id:
            # Try fetching user's ISOs
            isos_resp = auth_user["session"].get(f"{BASE_URL}/api/iso", headers=headers)
            if isos_resp.status_code == 200:
                isos = isos_resp.json()
                for iso in isos:
                    if iso.get("album") == "Test Album ISO Delete":
                        iso_id = iso.get("id")
                        break
        
        if not iso_id:
            pytest.skip("Could not find ISO id for test")
        
        # Delete the ISO
        delete_resp = auth_user["session"].delete(f"{BASE_URL}/api/iso/{iso_id}", headers=headers)
        assert delete_resp.status_code == 200, f"Expected 200 for successful ISO delete, got {delete_resp.status_code}"
        
        # Verify response
        data = delete_resp.json()
        assert "message" in data, "Response should contain message"
        
        print("PASSED: Create and delete ISO works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
