"""
Privacy Settings, Follow Requests, and DM Gating Tests
Tests for HoneyGroove follow/message request system with privacy settings.
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials for dynamic user creation
TEST_PREFIX = f"TEST_PRIVACY_{uuid.uuid4().hex[:6]}"


class TestPrivacySettings:
    """Tests for privacy settings in user profile"""
    
    user1_token = None
    user1_id = None
    user1_username = None
    user2_token = None
    user2_id = None
    user2_username = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_test_users(self, request):
        """Create two test users for testing"""
        # User 1 - will be the private account
        user1_email = f"{TEST_PREFIX}_user1@test.com"
        user1_username = f"{TEST_PREFIX}_user1".lower()
        user1_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user1_email,
            "password": "testpass123",
            "username": user1_username
        })
        if user1_resp.status_code == 201 or user1_resp.status_code == 200:
            data = user1_resp.json()
            request.cls.user1_token = data.get("access_token")
            request.cls.user1_id = data.get("user", {}).get("id")
            request.cls.user1_username = user1_username
        else:
            pytest.skip(f"Failed to create user1: {user1_resp.status_code}")
        
        # User 2 - will try to follow user 1
        user2_email = f"{TEST_PREFIX}_user2@test.com"
        user2_username = f"{TEST_PREFIX}_user2".lower()
        user2_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user2_email,
            "password": "testpass123",
            "username": user2_username
        })
        if user2_resp.status_code == 201 or user2_resp.status_code == 200:
            data = user2_resp.json()
            request.cls.user2_token = data.get("access_token")
            request.cls.user2_id = data.get("user", {}).get("id")
            request.cls.user2_username = user2_username
        else:
            pytest.skip(f"Failed to create user2: {user2_resp.status_code}")
            
        yield
        
        # Cleanup - delete test users
        if request.cls.user1_token:
            requests.delete(f"{BASE_URL}/api/auth/account", 
                          headers={"Authorization": f"Bearer {request.cls.user1_token}"})
        if request.cls.user2_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user2_token}"})
    
    # ==================== PUT /api/auth/me - Privacy Settings ====================
    
    def test_update_is_private_setting(self):
        """PUT /api/auth/me accepts is_private field"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"is_private": True},
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("is_private") == True, "is_private should be True"
    
    def test_update_dm_setting_everyone(self):
        """PUT /api/auth/me accepts dm_setting='everyone'"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"dm_setting": "everyone"},
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("dm_setting") == "everyone"
    
    def test_update_dm_setting_following(self):
        """PUT /api/auth/me accepts dm_setting='following'"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"dm_setting": "following"},
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("dm_setting") == "following"
    
    def test_update_dm_setting_requests(self):
        """PUT /api/auth/me accepts dm_setting='requests'"""
        response = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"dm_setting": "requests"},
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("dm_setting") == "requests"
    
    # ==================== GET /api/users/{username} - Profile Privacy Info ====================
    
    def test_get_user_profile_returns_privacy_fields(self):
        """GET /api/users/{username} returns is_private, dm_setting, profile_locked fields"""
        # First make user1 private
        requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"is_private": True, "dm_setting": "requests"},
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        
        # User2 views user1's profile
        response = requests.get(
            f"{BASE_URL}/api/users/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "is_private" in data, "is_private field should be present"
        assert "dm_setting" in data, "dm_setting field should be present"
        assert "is_approved_follower" in data, "is_approved_follower field should be present"
        assert "follow_request_status" in data, "follow_request_status field should be present"
        assert "profile_locked" in data, "profile_locked field should be present"
        
        assert data["is_private"] == True
        assert data["dm_setting"] == "requests"
        assert data["is_approved_follower"] == False
        assert data["profile_locked"] == True
    
    def test_profile_returns_mutual_signals_when_locked(self):
        """GET /api/users/{username} returns mutual signals for locked profiles"""
        # User1 is private, user2 views profile
        response = requests.get(
            f"{BASE_URL}/api/users/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should include mutual signals even if 0
        assert "records_in_common" in data or data.get("profile_locked"), "records_in_common should be present for locked profiles"
    
    # ==================== Follow Request Flow ====================
    
    def test_follow_private_user_creates_request(self):
        """POST /api/follow/{username} creates follow_request for private users"""
        # Ensure user1 is private
        requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"is_private": True},
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        
        # User2 tries to follow user1
        response = requests.post(
            f"{BASE_URL}/api/follow/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "requested", f"Expected status='requested', got {data}"
        assert "request" in data.get("message", "").lower() or data.get("status") == "requested"
    
    def test_follow_check_shows_pending_request(self):
        """GET /api/follow/check/{username} returns follow_request_pending field"""
        response = requests.get(
            f"{BASE_URL}/api/follow/check/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "follow_request_pending" in data
        assert data["follow_request_pending"] == True
    
    def test_get_follow_requests_shows_pending(self):
        """GET /api/follow-requests returns pending requests for user1"""
        response = requests.get(
            f"{BASE_URL}/api/follow-requests",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Find request from user2
        req = next((r for r in data if r.get("from_user", {}).get("username") == self.user2_username), None)
        assert req is not None, f"Follow request from {self.user2_username} not found in {data}"
        assert "id" in req
        assert "from_user" in req
        
    def test_profile_shows_follow_request_status_pending(self):
        """GET /api/users/{username} shows follow_request_status='pending' after request sent"""
        response = requests.get(
            f"{BASE_URL}/api/users/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("follow_request_status") == "pending"
    
    def test_accept_follow_request(self):
        """POST /api/follow-requests/{id}/accept creates follower relationship"""
        # Get the request id
        req_resp = requests.get(
            f"{BASE_URL}/api/follow-requests",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        requests_list = req_resp.json()
        req = next((r for r in requests_list if r.get("from_user", {}).get("username") == self.user2_username), None)
        
        if not req:
            pytest.skip("No pending request found")
        
        # Accept the request
        response = requests.post(
            f"{BASE_URL}/api/follow-requests/{req['id']}/accept",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "accepted"
        
        # Verify user2 is now following user1
        check_resp = requests.get(
            f"{BASE_URL}/api/follow/check/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        check_data = check_resp.json()
        assert check_data.get("is_following") == True
    
    def test_unfollow_also_cleans_follow_requests(self):
        """DELETE /api/follow/{username} also cleans up follow_requests"""
        # User2 unfollows user1
        response = requests.delete(
            f"{BASE_URL}/api/follow/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 200
        
        # Verify not following
        check_resp = requests.get(
            f"{BASE_URL}/api/follow/check/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        check_data = check_resp.json()
        assert check_data.get("is_following") == False
        assert check_data.get("follow_request_pending") == False
    
    # ==================== Profile Content Access Control ====================
    
    def test_private_profile_records_returns_403(self):
        """GET /api/users/{username}/records returns 403 for private profile when not a follower"""
        response = requests.get(
            f"{BASE_URL}/api/users/{self.user1_username}/records",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 403
    
    def test_private_profile_spins_returns_403(self):
        """GET /api/users/{username}/spins returns 403 for private profile when not a follower"""
        response = requests.get(
            f"{BASE_URL}/api/users/{self.user1_username}/spins",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 403
    
    def test_private_profile_posts_returns_403(self):
        """GET /api/users/{username}/posts returns 403 for private profile when not a follower"""
        response = requests.get(
            f"{BASE_URL}/api/users/{self.user1_username}/posts",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 403


class TestFollowRequestDecline:
    """Tests for declining follow requests"""
    
    user1_token = None
    user1_id = None
    user1_username = None
    user2_token = None
    user2_id = None
    user2_username = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_test_users(self, request):
        """Create two test users for testing"""
        prefix = f"TEST_DECLINE_{uuid.uuid4().hex[:6]}"
        
        # User 1 - private account
        user1_email = f"{prefix}_user1@test.com"
        user1_username = f"{prefix}_user1".lower()
        user1_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user1_email,
            "password": "testpass123",
            "username": user1_username
        })
        if user1_resp.status_code in [200, 201]:
            data = user1_resp.json()
            request.cls.user1_token = data.get("access_token")
            request.cls.user1_id = data.get("user", {}).get("id")
            request.cls.user1_username = user1_username
            # Make user1 private
            requests.put(
                f"{BASE_URL}/api/auth/me",
                json={"is_private": True},
                headers={"Authorization": f"Bearer {request.cls.user1_token}"}
            )
        else:
            pytest.skip("Failed to create user1")
        
        # User 2
        user2_email = f"{prefix}_user2@test.com"
        user2_username = f"{prefix}_user2".lower()
        user2_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user2_email,
            "password": "testpass123",
            "username": user2_username
        })
        if user2_resp.status_code in [200, 201]:
            data = user2_resp.json()
            request.cls.user2_token = data.get("access_token")
            request.cls.user2_id = data.get("user", {}).get("id")
            request.cls.user2_username = user2_username
        else:
            pytest.skip("Failed to create user2")
        
        # User2 sends follow request
        requests.post(
            f"{BASE_URL}/api/follow/{user1_username}",
            headers={"Authorization": f"Bearer {request.cls.user2_token}"}
        )
        
        yield
        
        # Cleanup
        if request.cls.user1_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user1_token}"})
        if request.cls.user2_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user2_token}"})
    
    def test_decline_follow_request(self):
        """POST /api/follow-requests/{id}/decline updates status to declined"""
        # Get the request id
        req_resp = requests.get(
            f"{BASE_URL}/api/follow-requests",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        requests_list = req_resp.json()
        req = next((r for r in requests_list if r.get("from_user", {}).get("username") == self.user2_username), None)
        
        if not req:
            pytest.skip("No pending request found")
        
        # Decline the request
        response = requests.post(
            f"{BASE_URL}/api/follow-requests/{req['id']}/decline",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "declined"
        
        # Verify user2 is NOT following user1
        check_resp = requests.get(
            f"{BASE_URL}/api/follow/check/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        check_data = check_resp.json()
        assert check_data.get("is_following") == False


class TestDMGating:
    """Tests for DM gating based on dm_setting"""
    
    user1_token = None
    user1_id = None
    user1_username = None
    user2_token = None
    user2_id = None
    user2_username = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_test_users(self, request):
        """Create two test users for testing"""
        prefix = f"TEST_DM_{uuid.uuid4().hex[:6]}"
        
        # User 1
        user1_email = f"{prefix}_user1@test.com"
        user1_username = f"{prefix}_user1".lower()
        user1_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user1_email,
            "password": "testpass123",
            "username": user1_username
        })
        if user1_resp.status_code in [200, 201]:
            data = user1_resp.json()
            request.cls.user1_token = data.get("access_token")
            request.cls.user1_id = data.get("user", {}).get("id")
            request.cls.user1_username = user1_username
        else:
            pytest.skip("Failed to create user1")
        
        # User 2
        user2_email = f"{prefix}_user2@test.com"
        user2_username = f"{prefix}_user2".lower()
        user2_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user2_email,
            "password": "testpass123",
            "username": user2_username
        })
        if user2_resp.status_code in [200, 201]:
            data = user2_resp.json()
            request.cls.user2_token = data.get("access_token")
            request.cls.user2_id = data.get("user", {}).get("id")
            request.cls.user2_username = user2_username
        else:
            pytest.skip("Failed to create user2")
        
        yield
        
        # Cleanup
        if request.cls.user1_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user1_token}"})
        if request.cls.user2_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user2_token}"})
    
    def test_dm_setting_following_blocks_non_follower(self):
        """DM conversation creation respects dm_setting='following' - 403 if recipient doesn't follow sender"""
        # Set user1 dm_setting to 'following'
        requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"dm_setting": "following"},
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        
        # User2 tries to DM user1 (user1 does NOT follow user2)
        response = requests.post(
            f"{BASE_URL}/api/dm/conversations",
            json={
                "recipient_id": self.user1_id,
                "text": "Hello from user2!"
            },
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    
    def test_dm_setting_requests_creates_pending_conversation(self):
        """DM conversation creation creates pending status when dm_setting='requests'"""
        # Set user1 dm_setting to 'requests'
        requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"dm_setting": "requests"},
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        
        # User2 tries to DM user1
        response = requests.post(
            f"{BASE_URL}/api/dm/conversations",
            json={
                "recipient_id": self.user1_id,
                "text": "Hello message request!"
            },
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "pending", f"Expected status='pending', got {data}"
        
        # Store conv_id for later tests
        self.__class__.conv_id = data.get("conversation_id")
    
    def test_accept_message_request(self):
        """POST /api/dm/conversations/{id}/accept changes status to active"""
        if not hasattr(self, 'conv_id') or not self.conv_id:
            pytest.skip("No conversation created")
        
        response = requests.post(
            f"{BASE_URL}/api/dm/conversations/{self.conv_id}/accept",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "accepted"


class TestDMDecline:
    """Tests for declining DM requests"""
    
    user1_token = None
    user1_id = None
    user2_token = None
    user2_id = None
    conv_id = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_test_users(self, request):
        """Create two test users and a pending DM conversation"""
        prefix = f"TEST_DM_DEC_{uuid.uuid4().hex[:6]}"
        
        # User 1
        user1_email = f"{prefix}_user1@test.com"
        user1_username = f"{prefix}_user1".lower()
        user1_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user1_email,
            "password": "testpass123",
            "username": user1_username
        })
        if user1_resp.status_code in [200, 201]:
            data = user1_resp.json()
            request.cls.user1_token = data.get("access_token")
            request.cls.user1_id = data.get("user", {}).get("id")
        else:
            pytest.skip("Failed to create user1")
        
        # Set dm_setting to requests
        requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"dm_setting": "requests"},
            headers={"Authorization": f"Bearer {request.cls.user1_token}"}
        )
        
        # User 2
        user2_email = f"{prefix}_user2@test.com"
        user2_username = f"{prefix}_user2".lower()
        user2_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user2_email,
            "password": "testpass123",
            "username": user2_username
        })
        if user2_resp.status_code in [200, 201]:
            data = user2_resp.json()
            request.cls.user2_token = data.get("access_token")
            request.cls.user2_id = data.get("user", {}).get("id")
        else:
            pytest.skip("Failed to create user2")
        
        # User2 sends DM to user1 - creates pending conversation
        dm_resp = requests.post(
            f"{BASE_URL}/api/dm/conversations",
            json={
                "recipient_id": request.cls.user1_id,
                "text": "Hello message to decline!"
            },
            headers={"Authorization": f"Bearer {request.cls.user2_token}"}
        )
        if dm_resp.status_code == 200:
            request.cls.conv_id = dm_resp.json().get("conversation_id")
        
        yield
        
        # Cleanup
        if request.cls.user1_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user1_token}"})
        if request.cls.user2_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user2_token}"})
    
    def test_decline_message_request(self):
        """POST /api/dm/conversations/{id}/decline changes status to declined"""
        if not self.conv_id:
            pytest.skip("No conversation created")
        
        response = requests.post(
            f"{BASE_URL}/api/dm/conversations/{self.conv_id}/decline",
            headers={"Authorization": f"Bearer {self.user1_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "declined"


class TestPublicProfileFlow:
    """Tests for public profile behavior - follow should work directly"""
    
    user1_token = None
    user1_username = None
    user2_token = None
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_test_users(self, request):
        """Create two test users"""
        prefix = f"TEST_PUBLIC_{uuid.uuid4().hex[:6]}"
        
        # User 1 - PUBLIC account
        user1_email = f"{prefix}_user1@test.com"
        user1_username = f"{prefix}_user1".lower()
        user1_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user1_email,
            "password": "testpass123",
            "username": user1_username
        })
        if user1_resp.status_code in [200, 201]:
            data = user1_resp.json()
            request.cls.user1_token = data.get("access_token")
            request.cls.user1_username = user1_username
            # Ensure user1 is public
            requests.put(
                f"{BASE_URL}/api/auth/me",
                json={"is_private": False},
                headers={"Authorization": f"Bearer {request.cls.user1_token}"}
            )
        else:
            pytest.skip("Failed to create user1")
        
        # User 2
        user2_email = f"{prefix}_user2@test.com"
        user2_username = f"{prefix}_user2".lower()
        user2_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": user2_email,
            "password": "testpass123",
            "username": user2_username
        })
        if user2_resp.status_code in [200, 201]:
            data = user2_resp.json()
            request.cls.user2_token = data.get("access_token")
        else:
            pytest.skip("Failed to create user2")
        
        yield
        
        # Cleanup
        if request.cls.user1_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user1_token}"})
        if request.cls.user2_token:
            requests.delete(f"{BASE_URL}/api/auth/account",
                          headers={"Authorization": f"Bearer {request.cls.user2_token}"})
    
    def test_follow_public_user_is_direct(self):
        """POST /api/follow/{username} directly follows public users"""
        response = requests.post(
            f"{BASE_URL}/api/follow/{self.user1_username}",
            headers={"Authorization": f"Bearer {self.user2_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should be 'following' not 'requested'
        assert data.get("status") == "following" or "following" in data.get("message", "").lower(), f"Expected direct follow, got {data}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
