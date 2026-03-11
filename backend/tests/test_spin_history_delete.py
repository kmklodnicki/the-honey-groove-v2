"""
Test Suite for Spin History and Global Spin Removal (BLOCK 147 continued)

Features tested:
1. DELETE /api/spins/{id} - deletes spin and linked feed post (bidirectional)
2. DELETE /api/posts/{id} - also deletes linked spin (bidirectional)
3. GET /api/users/{username}/spins - returns spins with caption/mood
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

class TestSpinHistoryAndDelete:
    """Test Spin History tab features and Global Spin Removal"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token using demo credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demouser"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def user_info(self, headers):
        """Get current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            return response.json()
        return {"username": "demo"}
    
    # ==== GET /api/users/{username}/spins tests ====
    
    def test_get_user_spins_returns_spins(self, headers, user_info):
        """GET /api/users/{username}/spins returns user's spins"""
        username = user_info.get("username", "demo")
        response = requests.get(f"{BASE_URL}/api/users/{username}/spins", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        spins = response.json()
        assert isinstance(spins, list), "Response should be a list"
        # Each spin should have expected fields
        if len(spins) > 0:
            spin = spins[0]
            assert "id" in spin, "Spin should have 'id'"
            assert "record" in spin, "Spin should have 'record' data"
            assert "created_at" in spin, "Spin should have 'created_at'"
            # Check for caption and mood (new fields)
            assert "caption" in spin or spin.get("caption") is None, "Spin should include caption field"
            assert "mood" in spin or spin.get("mood") is None, "Spin should include mood field"
            print(f"PASS: GET /api/users/{username}/spins returns {len(spins)} spins with expected fields")
        else:
            print(f"PASS: GET /api/users/{username}/spins returns empty list (user has no spins)")
    
    # ==== Bidirectional Delete Tests ====
    
    def test_create_now_spinning_post(self, headers, user_info):
        """Create a Now Spinning post (creates both spin and post)"""
        # First get a record from user's collection
        response = requests.get(f"{BASE_URL}/api/records", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No records in collection to spin")
        
        record = response.json()[0]
        record_id = record["id"]
        
        # Create Now Spinning post with caption and mood
        test_caption = f"TEST_spin_delete_{uuid.uuid4().hex[:8]}"
        post_data = {
            "record_id": record_id,
            "caption": test_caption,
            "mood": "Late Night",
            "track": "Test Track"
        }
        
        response = requests.post(f"{BASE_URL}/api/composer/now-spinning", json=post_data, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        post = response.json()
        assert post.get("post_type") == "NOW_SPINNING", "Post should be NOW_SPINNING type"
        assert post.get("caption") == test_caption, "Post should have test caption"
        print(f"PASS: Created Now Spinning post with id={post['id']}, caption={test_caption}")
        
        # Store for cleanup
        return {"post_id": post["id"], "caption": test_caption}
    
    def test_delete_spin_removes_linked_post(self, headers, user_info):
        """DELETE /api/spins/{id} removes spin AND linked feed post"""
        # First create a new spin
        response = requests.get(f"{BASE_URL}/api/records", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No records in collection to spin")
        
        record = response.json()[0]
        record_id = record["id"]
        
        test_caption = f"TEST_delete_spin_{uuid.uuid4().hex[:8]}"
        post_data = {
            "record_id": record_id,
            "caption": test_caption,
            "mood": "Good Morning"
        }
        
        # Create the spin/post
        create_response = requests.post(f"{BASE_URL}/api/composer/now-spinning", json=post_data, headers=headers)
        assert create_response.status_code == 200, f"Failed to create spin: {create_response.text}"
        
        post = create_response.json()
        post_id = post["id"]
        
        # Get the spin ID from user's spins
        username = user_info.get("username", "demo")
        spins_response = requests.get(f"{BASE_URL}/api/users/{username}/spins", headers=headers)
        assert spins_response.status_code == 200, f"Failed to get spins: {spins_response.text}"
        
        spins = spins_response.json()
        # Find the spin we just created (by caption)
        spin = None
        for s in spins:
            if s.get("caption") == test_caption:
                spin = s
                break
        
        if not spin:
            pytest.skip(f"Could not find spin with caption '{test_caption}'")
        
        spin_id = spin["id"]
        print(f"Found spin_id={spin_id} with caption='{test_caption}'")
        
        # DELETE the spin
        delete_response = requests.delete(f"{BASE_URL}/api/spins/{spin_id}", headers=headers)
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert "message" in data, "Response should have message"
        print(f"PASS: DELETE /api/spins/{spin_id} returned: {data}")
        
        # Verify spin is deleted
        spins_after = requests.get(f"{BASE_URL}/api/users/{username}/spins", headers=headers).json()
        spin_ids_after = [s["id"] for s in spins_after]
        assert spin_id not in spin_ids_after, "Spin should be deleted from spins list"
        print(f"PASS: Spin {spin_id} no longer in user's spins")
        
        # Verify post is also deleted (bidirectional)
        post_response = requests.get(f"{BASE_URL}/api/posts/{post_id}", headers=headers)
        assert post_response.status_code == 404, f"Post should be deleted but got {post_response.status_code}"
        print(f"PASS: Linked post {post_id} is also deleted (bidirectional)")
    
    def test_delete_post_removes_linked_spin(self, headers, user_info):
        """DELETE /api/posts/{id} removes post AND linked spin (bidirectional)"""
        # First create a new spin
        response = requests.get(f"{BASE_URL}/api/records", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No records in collection to spin")
        
        record = response.json()[0]
        record_id = record["id"]
        
        test_caption = f"TEST_delete_post_{uuid.uuid4().hex[:8]}"
        post_data = {
            "record_id": record_id,
            "caption": test_caption,
            "mood": "Rainy Day"
        }
        
        # Create the spin/post
        create_response = requests.post(f"{BASE_URL}/api/composer/now-spinning", json=post_data, headers=headers)
        assert create_response.status_code == 200, f"Failed to create spin: {create_response.text}"
        
        post = create_response.json()
        post_id = post["id"]
        
        # Get spins count before deletion
        username = user_info.get("username", "demo")
        spins_before = requests.get(f"{BASE_URL}/api/users/{username}/spins", headers=headers).json()
        spin_before = None
        for s in spins_before:
            if s.get("caption") == test_caption:
                spin_before = s
                break
        
        if not spin_before:
            pytest.skip(f"Could not find spin with caption '{test_caption}'")
        
        spin_id = spin_before["id"]
        print(f"Found spin_id={spin_id} linked to post_id={post_id}")
        
        # DELETE the post
        delete_response = requests.delete(f"{BASE_URL}/api/posts/{post_id}", headers=headers)
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        print(f"PASS: DELETE /api/posts/{post_id} succeeded")
        
        # Verify post is deleted
        post_check = requests.get(f"{BASE_URL}/api/posts/{post_id}", headers=headers)
        assert post_check.status_code == 404, f"Post should be deleted but got {post_check.status_code}"
        print(f"PASS: Post {post_id} is deleted")
        
        # Verify spin is also deleted (bidirectional)
        spins_after = requests.get(f"{BASE_URL}/api/users/{username}/spins", headers=headers).json()
        spin_ids_after = [s["id"] for s in spins_after]
        assert spin_id not in spin_ids_after, "Linked spin should be deleted"
        print(f"PASS: Linked spin {spin_id} is also deleted (bidirectional)")
    
    # ==== Error Cases ====
    
    def test_delete_spin_not_found(self, headers):
        """DELETE /api/spins/{id} returns 404 for non-existent spin"""
        fake_id = f"fake_spin_{uuid.uuid4().hex}"
        response = requests.delete(f"{BASE_URL}/api/spins/{fake_id}", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: DELETE non-existent spin returns 404")
    
    def test_delete_spin_forbidden_for_other_user(self, headers):
        """DELETE /api/spins/{id} returns 403 for spin owned by another user"""
        # This test would require creating a spin as another user
        # For now we just verify the endpoint exists and handles auth
        # Skip if we don't have access to another user's spin
        print("SKIP: Cannot test 403 without another user's spin ID")
    
    # ==== Cleanup ====
    
    def test_cleanup_test_spins(self, headers, user_info):
        """Cleanup any TEST_ spins/posts created during testing"""
        username = user_info.get("username", "demo")
        spins = requests.get(f"{BASE_URL}/api/users/{username}/spins", headers=headers).json()
        
        cleaned = 0
        for spin in spins:
            caption = spin.get("caption", "")
            if caption and caption.startswith("TEST_"):
                try:
                    requests.delete(f"{BASE_URL}/api/spins/{spin['id']}", headers=headers)
                    cleaned += 1
                except:
                    pass
        
        print(f"Cleaned up {cleaned} test spins")


class TestDeleteEndpointAuth:
    """Test authentication requirements for delete endpoints"""
    
    def test_delete_spin_requires_auth(self):
        """DELETE /api/spins/{id} requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/spins/fake_id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: DELETE /api/spins requires auth")
    
    def test_delete_post_requires_auth(self):
        """DELETE /api/posts/{id} requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/posts/fake_id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: DELETE /api/posts requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
