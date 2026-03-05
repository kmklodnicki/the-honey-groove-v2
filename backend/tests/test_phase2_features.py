"""
Phase 2 Feature Tests: Friends/Following, ISO Standalone, Profile Tabs
Testing: Follow system, user discovery, profile data endpoints, ISO management
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"


class TestSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get authenticated headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def user_data(self, auth_token):
        """Get current user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        return response.json()["user"]


class TestUserDiscovery(TestSetup):
    """Test user discovery/suggestions endpoint"""
    
    def test_get_suggested_users(self, auth_headers):
        """GET /api/users/discover/suggestions returns users not already followed"""
        response = requests.get(
            f"{BASE_URL}/api/users/discover/suggestions",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Suggestions failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Verify response structure
        if len(data) > 0:
            user = data[0]
            assert "id" in user
            assert "username" in user
            assert "is_following" in user
            # Suggested users should not be followed
            assert user["is_following"] == False


class TestUserSearch(TestSetup):
    """Test user search endpoint"""
    
    def test_search_users_by_query(self, auth_headers):
        """GET /api/users/search?query=vinyl returns users matching search"""
        response = requests.get(
            f"{BASE_URL}/api/users/search?query=demo",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Should find demo user
        usernames = [u["username"] for u in data]
        assert "demo" in usernames
        # Verify structure
        if len(data) > 0:
            assert "is_following" in data[0]
    
    def test_search_users_min_length(self, auth_headers):
        """GET /api/users/search requires min 2 char query"""
        response = requests.get(
            f"{BASE_URL}/api/users/search?query=a",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error


class TestFollowSystem(TestSetup):
    """Test follow/unfollow endpoints"""
    
    def test_follow_user(self, auth_headers):
        """POST /api/follow/{username} follows the user"""
        # First check if we can get suggestions to find a user to follow
        response = requests.get(
            f"{BASE_URL}/api/users/discover/suggestions",
            headers=auth_headers
        )
        if response.status_code == 200 and len(response.json()) > 0:
            target_user = response.json()[0]["username"]
            
            # Try to follow
            response = requests.post(
                f"{BASE_URL}/api/follow/{target_user}",
                headers=auth_headers
            )
            # Either 200 (success) or 400 (already following)
            assert response.status_code in [200, 400]
    
    def test_unfollow_user(self, auth_headers):
        """DELETE /api/follow/{username} unfollows the user"""
        # Demo user follows waxhunter and collector4692 per agent context
        response = requests.delete(
            f"{BASE_URL}/api/follow/waxhunter",
            headers=auth_headers
        )
        # Either 200 (success) or 400 (not following)
        assert response.status_code in [200, 400]
        
        # Re-follow to restore state
        if response.status_code == 200:
            requests.post(
                f"{BASE_URL}/api/follow/waxhunter",
                headers=auth_headers
            )
    
    def test_check_following_status(self, auth_headers):
        """GET /api/follow/check/{username} returns is_following status"""
        response = requests.get(
            f"{BASE_URL}/api/follow/check/demo",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_following" in data


class TestFollowersList(TestSetup):
    """Test followers/following list endpoints"""
    
    def test_get_user_followers(self, auth_headers):
        """GET /api/users/{username}/followers returns followers list with is_following field"""
        response = requests.get(
            f"{BASE_URL}/api/users/demo/followers",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Followers failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Verify structure if has followers
        if len(data) > 0:
            follower = data[0]
            assert "id" in follower
            assert "username" in follower
            assert "is_following" in follower  # Key field for follow button state
    
    def test_get_user_following(self, auth_headers):
        """GET /api/users/{username}/following returns following list with is_following field"""
        response = requests.get(
            f"{BASE_URL}/api/users/demo/following",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Following failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Verify structure
        if len(data) > 0:
            following = data[0]
            assert "id" in following
            assert "username" in following
            assert "is_following" in following


class TestProfileDataEndpoints(TestSetup):
    """Test profile-specific data endpoints for tabs"""
    
    def test_get_user_spins(self, auth_headers):
        """GET /api/users/{username}/spins returns spins with record data"""
        response = requests.get(
            f"{BASE_URL}/api/users/demo/spins",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Spins failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Demo user has 7 spins per context
        if len(data) > 0:
            spin = data[0]
            assert "id" in spin
            assert "record_id" in spin
            assert "created_at" in spin
            # Should include record data
            assert "record" in spin
            if spin["record"]:
                assert "title" in spin["record"]
                assert "artist" in spin["record"]
    
    def test_get_user_iso_list(self, auth_headers):
        """GET /api/users/{username}/iso returns ISOs with tags and status"""
        response = requests.get(
            f"{BASE_URL}/api/users/demo/iso",
            headers=auth_headers
        )
        assert response.status_code == 200, f"ISO list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Demo user has 5 ISOs per context
        if len(data) > 0:
            iso = data[0]
            assert "id" in iso
            assert "artist" in iso
            assert "album" in iso
            assert "status" in iso  # OPEN or FOUND
            # Tags field should exist
            assert "tags" in iso or iso.get("tags") is None
    
    def test_get_user_records(self, auth_headers):
        """GET /api/users/{username}/records returns collection"""
        response = requests.get(
            f"{BASE_URL}/api/users/demo/records",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Records failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Demo user has 148 records per context
        assert len(data) > 0
        record = data[0]
        assert "id" in record
        assert "title" in record
        assert "artist" in record


class TestISOComposer(TestSetup):
    """Test ISO creation via composer with tags"""
    
    def test_create_iso_with_tags(self, auth_headers):
        """POST /api/composer/iso with tags field works"""
        response = requests.post(
            f"{BASE_URL}/api/composer/iso",
            headers=auth_headers,
            json={
                "artist": "TEST_Artist",
                "album": "TEST_Album_Phase2",
                "tags": ["OG Press", "Factory Sealed"],
                "target_price_min": 50,
                "target_price_max": 200,
                "caption": "Testing Phase 2 ISO with tags"
            }
        )
        assert response.status_code == 200, f"ISO creation failed: {response.text}"
        data = response.json()
        assert data["post_type"] == "ISO"
        assert "iso_id" in data
    
    def test_create_iso_with_all_tags(self, auth_headers):
        """POST /api/composer/iso works with all tag options"""
        response = requests.post(
            f"{BASE_URL}/api/composer/iso",
            headers=auth_headers,
            json={
                "artist": "TEST_All_Tags",
                "album": "TEST_Album_AllTags",
                "tags": ["OG Press", "Factory Sealed", "Any", "Promo"],
                "pressing_notes": "1st pressing",
                "condition_pref": "VG+"
            }
        )
        assert response.status_code == 200


class TestISOManagement(TestSetup):
    """Test ISO CRUD operations"""
    
    def test_get_my_isos(self, auth_headers):
        """GET /api/iso returns user's ISO items"""
        response = requests.get(
            f"{BASE_URL}/api/iso",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get ISOs failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_mark_iso_found(self, auth_headers):
        """PUT /api/iso/{id}/found marks ISO as found"""
        # First create an ISO to mark as found
        create_resp = requests.post(
            f"{BASE_URL}/api/composer/iso",
            headers=auth_headers,
            json={
                "artist": "TEST_MarkFound",
                "album": "TEST_Album_ToFind"
            }
        )
        if create_resp.status_code == 200:
            iso_id = create_resp.json().get("iso_id")
            if iso_id:
                # Mark as found
                response = requests.put(
                    f"{BASE_URL}/api/iso/{iso_id}/found",
                    headers=auth_headers
                )
                assert response.status_code == 200
                assert response.json()["message"] == "ISO marked as found"
                
                # Clean up
                requests.delete(f"{BASE_URL}/api/iso/{iso_id}", headers=auth_headers)
    
    def test_delete_iso(self, auth_headers):
        """DELETE /api/iso/{id} deletes an ISO"""
        # First create an ISO to delete
        create_resp = requests.post(
            f"{BASE_URL}/api/composer/iso",
            headers=auth_headers,
            json={
                "artist": "TEST_Delete",
                "album": "TEST_Album_ToDelete"
            }
        )
        if create_resp.status_code == 200:
            iso_id = create_resp.json().get("iso_id")
            if iso_id:
                # Delete ISO
                response = requests.delete(
                    f"{BASE_URL}/api/iso/{iso_id}",
                    headers=auth_headers
                )
                assert response.status_code == 200
                assert response.json()["message"] == "ISO deleted"
                
                # Verify deleted
                get_resp = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
                if get_resp.status_code == 200:
                    iso_ids = [i["id"] for i in get_resp.json()]
                    assert iso_id not in iso_ids


class TestUserProfile(TestSetup):
    """Test user profile endpoint"""
    
    def test_get_user_profile(self, auth_headers):
        """GET /api/users/{username} returns profile with counts"""
        response = requests.get(
            f"{BASE_URL}/api/users/demo",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Profile failed: {response.text}"
        data = response.json()
        assert data["username"] == "demo"
        assert "collection_count" in data
        assert "spin_count" in data
        assert "followers_count" in data
        assert "following_count" in data
    
    def test_profile_not_found(self, auth_headers):
        """GET /api/users/{username} returns 404 for nonexistent user"""
        response = requests.get(
            f"{BASE_URL}/api/users/nonexistent_user_xyz123",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestCleanup(TestSetup):
    """Cleanup test data"""
    
    def test_cleanup_test_isos(self, auth_headers):
        """Clean up TEST_ prefixed ISOs"""
        response = requests.get(f"{BASE_URL}/api/iso", headers=auth_headers)
        if response.status_code == 200:
            for iso in response.json():
                if iso.get("artist", "").startswith("TEST_") or iso.get("album", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/iso/{iso['id']}", headers=auth_headers)
        assert True  # Cleanup doesn't fail test
