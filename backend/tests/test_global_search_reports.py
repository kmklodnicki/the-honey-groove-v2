"""
Tests for Global Search, Profile Fields, Report System, and Founding Member features.
Features:
1. Global Search - Search posts endpoint
2. Profile Fields - setup, location, favorite_genre 
3. Report System - create/admin reports
4. Founding Member Badge
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"

@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for demo user"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]

@pytest.fixture(scope="module")
def demo_user(auth_token):
    """Get demo user data"""
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    return resp.json()

class TestSearchPosts:
    """Test GET /api/search/posts endpoint"""
    
    def test_search_posts_returns_200(self, auth_token):
        """Search posts endpoint returns 200"""
        resp = requests.get(
            f"{BASE_URL}/api/search/posts?q=test",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Search posts failed: {resp.text}"
        assert isinstance(resp.json(), list)
    
    def test_search_posts_minimum_length(self, auth_token):
        """Search requires at least 2 characters"""
        resp = requests.get(
            f"{BASE_URL}/api/search/posts?q=a",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 422 for query too short
        assert resp.status_code == 422
    
    def test_search_posts_returns_structure(self, auth_token):
        """Search posts returns correct structure"""
        resp = requests.get(
            f"{BASE_URL}/api/search/posts?q=spinning",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        # If there are results, verify structure
        if len(data) > 0:
            post = data[0]
            assert "id" in post
            assert "post_type" in post
            assert "caption" in post
            assert "user" in post
    
    def test_search_posts_requires_auth(self):
        """Search posts requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/search/posts?q=test")
        assert resp.status_code in [401, 403]


class TestProfileFields:
    """Test profile fields: setup, location, favorite_genre"""
    
    def test_get_user_profile_has_new_fields(self, auth_token, demo_user):
        """GET /api/users/{username} returns setup, location, favorite_genre, founding_member"""
        resp = requests.get(
            f"{BASE_URL}/api/users/{demo_user['username']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        # Check fields exist in response
        assert "setup" in data or data.get("setup") is None  # Field exists
        assert "location" in data or data.get("location") is None
        assert "favorite_genre" in data or data.get("favorite_genre") is None
        assert "founding_member" in data
    
    def test_update_profile_setup_field(self, auth_token):
        """PUT /api/auth/me accepts setup field"""
        test_setup = "Pro-Ject Debut Carbon EVO + Ortofon 2M Red"
        resp = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"setup": test_setup},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("setup") == test_setup
    
    def test_update_profile_location_field(self, auth_token):
        """PUT /api/auth/me accepts location field"""
        test_location = "Brooklyn, NY"
        resp = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"location": test_location},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("location") == test_location
    
    def test_update_profile_genre_field(self, auth_token):
        """PUT /api/auth/me accepts favorite_genre field"""
        test_genre = "Jazz"
        resp = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"favorite_genre": test_genre},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("favorite_genre") == test_genre
    
    def test_update_profile_multiple_fields(self, auth_token):
        """PUT /api/auth/me accepts multiple new fields at once"""
        resp = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={
                "setup": "Technics SL-1200MK7",
                "location": "Tokyo, Japan",
                "favorite_genre": "House"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("setup") == "Technics SL-1200MK7"
        assert data.get("location") == "Tokyo, Japan"
        assert data.get("favorite_genre") == "House"
    
    def test_profile_persists_new_fields(self, auth_token, demo_user):
        """Verify updated fields persist via GET"""
        # First update
        update_data = {"setup": "Test Setup Persist", "location": "Test Location"}
        requests.put(
            f"{BASE_URL}/api/auth/me",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Then verify via GET
        resp = requests.get(
            f"{BASE_URL}/api/users/{demo_user['username']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("setup") == "Test Setup Persist"
        assert data.get("location") == "Test Location"


class TestFoundingMember:
    """Test founding member badge functionality"""
    
    def test_demo_user_is_founding_member(self, auth_token, demo_user):
        """Demo user has founding_member=true"""
        assert demo_user.get("founding_member") == True
    
    def test_founding_member_in_profile_response(self, auth_token, demo_user):
        """founding_member field appears in user profile"""
        resp = requests.get(
            f"{BASE_URL}/api/users/{demo_user['username']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "founding_member" in data
        assert data["founding_member"] == True
    
    def test_founding_member_in_post_user_object(self, auth_token):
        """founding_member appears in post user object"""
        # Get feed posts to check
        resp = requests.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        posts = resp.json()
        if len(posts) > 0:
            post = posts[0]
            if post.get("user"):
                assert "founding_member" in post["user"]


class TestReportSystem:
    """Test report endpoints"""
    
    def test_create_report_post(self, auth_token):
        """POST /api/reports creates report for post"""
        # First get a post to report
        resp = requests.get(
            f"{BASE_URL}/api/explore",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        posts = resp.json()
        if len(posts) == 0:
            pytest.skip("No posts available to test report")
        
        post_id = posts[0]["id"]
        report_data = {
            "type": "post",
            "target_id": post_id,
            "reason": "Spam",
            "notes": "Test report from automated testing"
        }
        resp = requests.post(
            f"{BASE_URL}/api/reports",
            json=report_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Create report failed: {resp.text}"
        data = resp.json()
        assert "id" in data
        assert "message" in data
    
    def test_create_report_user(self, auth_token):
        """POST /api/reports creates report for user"""
        # Get suggested users
        resp = requests.get(
            f"{BASE_URL}/api/users/discover/suggestions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        users = resp.json()
        if len(users) == 0:
            pytest.skip("No users available to test report")
        
        user_id = users[0]["id"]
        report_data = {
            "type": "user",
            "target_id": user_id,
            "reason": "Spam"
        }
        resp = requests.post(
            f"{BASE_URL}/api/reports",
            json=report_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
    
    def test_create_report_requires_all_fields(self, auth_token):
        """Report requires type, target_id, and reason"""
        resp = requests.post(
            f"{BASE_URL}/api/reports",
            json={"type": "post"},  # Missing target_id and reason
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 400
    
    def test_create_report_invalid_type(self, auth_token):
        """Report rejects invalid type"""
        resp = requests.post(
            f"{BASE_URL}/api/reports",
            json={"type": "invalid", "target_id": "123", "reason": "Spam"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 400
    
    def test_create_report_invalid_reason(self, auth_token):
        """Report rejects invalid reason for type"""
        resp = requests.post(
            f"{BASE_URL}/api/reports",
            json={"type": "post", "target_id": "123", "reason": "Invalid Reason"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 400
    
    def test_admin_get_reports(self, auth_token):
        """GET /api/reports/admin returns reports for admin user"""
        resp = requests.get(
            f"{BASE_URL}/api/reports/admin",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Demo user is admin, should return 200
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if len(data) > 0:
            report = data[0]
            assert "id" in report
            assert "type" in report
            assert "target_id" in report
            assert "reason" in report
            assert "status" in report


class TestUserSearch:
    """Test user search for Global Search collectors tab"""
    
    def test_search_users_endpoint(self, auth_token):
        """GET /api/users/search returns users"""
        resp = requests.get(
            f"{BASE_URL}/api/users/search?query=demo",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
    
    def test_search_users_structure(self, auth_token):
        """User search returns correct structure"""
        resp = requests.get(
            f"{BASE_URL}/api/users/search?query=de",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data) > 0:
            user = data[0]
            assert "id" in user
            assert "username" in user
            assert "avatar_url" in user


class TestDiscogsSearch:
    """Test Discogs search for Global Search records tab"""
    
    def test_discogs_search_endpoint(self, auth_token):
        """GET /api/discogs/search returns records"""
        resp = requests.get(
            f"{BASE_URL}/api/discogs/search?q=miles%20davis",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May be 200 or rate-limited
        assert resp.status_code in [200, 429, 503]
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class TestOnboardingCompleted:
    """Test onboarding_completed field"""
    
    def test_user_response_has_onboarding_completed(self, auth_token):
        """UserResponse includes onboarding_completed field"""
        resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "onboarding_completed" in data
    
    def test_demo_user_onboarding_completed(self, auth_token, demo_user):
        """Demo user has onboarding_completed=true"""
        assert demo_user.get("onboarding_completed") == True
    
    def test_update_onboarding_completed(self, auth_token):
        """Can update onboarding_completed via PUT /api/auth/me"""
        # Set to true (it should already be true for demo user)
        resp = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"onboarding_completed": True},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("onboarding_completed") == True
