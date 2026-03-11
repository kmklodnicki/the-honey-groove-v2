"""
Test Backend Refactor - HoneyGroove API
Tests the modular route structure after splitting server.py into 8 route modules.
Also tests new Explore page endpoints.

Routes tested:
- auth.py: /api/auth/login, /api/auth/me, /api/users/*
- hive.py: /api/feed, /api/explore (posts feed)
- collection.py: /api/records, /api/discogs/*
- honeypot.py: /api/iso, /api/listings
- trades.py: /api/trades
- notifications.py: /api/notifications
- dms.py: /api/dm/*
- explore.py: /api/explore/trending, /api/explore/recent-hauls, /api/explore/suggested-collectors, /api/explore/active-isos
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://collector-beta-1.preview.emergentagent.com')

# Test credentials
DEMO_USER = {"email": "demo@example.com", "password": "password123"}
TRADER_USER = {"email": "trader@example.com", "password": "password123"}


class TestAPIRoot:
    """Test API root and health"""
    
    def test_api_root_accessible(self):
        """Verify API root endpoint returns expected response"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to HoneyGroove API"


class TestAuthRoutes:
    """Test auth routes from routes/auth.py"""
    
    def test_login_demo_user(self):
        """POST /api/auth/login - Demo user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == DEMO_USER["email"]
        assert "id" in data["user"]
        assert "username" in data["user"]
    
    def test_login_trader_user(self):
        """POST /api/auth/login - Trader user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TRADER_USER)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == TRADER_USER["email"]
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - Invalid credentials return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_get_me_requires_auth(self):
        """GET /api/auth/me - Requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
    
    def test_get_me_with_token(self):
        """GET /api/auth/me - Returns user with valid token"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        
        # Get profile
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == DEMO_USER["email"]
        assert "collection_count" in data
        assert "spin_count" in data


class TestHiveRoutes:
    """Test hive/feed routes from routes/hive.py"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_feed(self, auth_header):
        """GET /api/feed - Returns posts from followed users"""
        response = requests.get(f"{BASE_URL}/api/feed", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_explore_posts(self, auth_header):
        """GET /api/explore - Returns all posts (explore feed)"""
        response = requests.get(f"{BASE_URL}/api/explore", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCollectionRoutes:
    """Test collection routes from routes/collection.py"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_records(self, auth_header):
        """GET /api/records - Returns user's collection"""
        response = requests.get(f"{BASE_URL}/api/records", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_records_requires_auth(self):
        """GET /api/records - Requires authentication"""
        response = requests.get(f"{BASE_URL}/api/records")
        assert response.status_code == 401


class TestHoneypotRoutes:
    """Test honeypot routes from routes/honeypot.py"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_iso_list(self, auth_header):
        """GET /api/iso - Returns user's ISOs"""
        response = requests.get(f"{BASE_URL}/api/iso", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_listings(self):
        """GET /api/listings - Returns marketplace listings (public)"""
        response = requests.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTradeRoutes:
    """Test trade routes from routes/trades.py"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_trades(self, auth_header):
        """GET /api/trades - Returns user's trades"""
        response = requests.get(f"{BASE_URL}/api/trades", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestNotificationRoutes:
    """Test notification routes from routes/notifications.py"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_notifications(self, auth_header):
        """GET /api/notifications - Returns user's notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_unread_count(self, auth_header):
        """GET /api/notifications/unread-count - Returns unread notification count"""
        response = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)


class TestDMRoutes:
    """Test DM routes from routes/dms.py"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_conversations(self, auth_header):
        """GET /api/dm/conversations - Returns user's DM conversations"""
        response = requests.get(f"{BASE_URL}/api/dm/conversations", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_dm_unread_count(self, auth_header):
        """GET /api/dm/unread-count - Returns unread DM count"""
        response = requests.get(f"{BASE_URL}/api/dm/unread-count", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data


class TestExploreRoutes:
    """Test new Explore routes from routes/explore.py"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_trending_records(self, auth_header):
        """GET /api/explore/trending - Returns trending records with trending_spins count"""
        response = requests.get(f"{BASE_URL}/api/explore/trending", headers=auth_header)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # If there are trending records, verify they have trending_spins
        if len(data) > 0:
            record = data[0]
            assert "trending_spins" in record, "Trending records should have trending_spins count"
            assert "title" in record
            assert "artist" in record
    
    def test_get_trending_records_with_limit(self, auth_header):
        """GET /api/explore/trending?limit=5 - Respects limit parameter"""
        response = requests.get(f"{BASE_URL}/api/explore/trending?limit=5", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_recent_hauls(self, auth_header):
        """GET /api/explore/recent-hauls - Returns recent haul posts with user info"""
        response = requests.get(f"{BASE_URL}/api/explore/recent-hauls", headers=auth_header)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # If there are hauls, verify structure
        if len(data) > 0:
            haul = data[0]
            assert "user_id" in haul
            assert "post_type" in haul
            # Haul posts should have user info attached
            if haul.get("user"):
                assert "username" in haul["user"]
    
    def test_get_suggested_collectors(self, auth_header):
        """GET /api/explore/suggested-collectors - Returns suggested users with shared_artists count"""
        response = requests.get(f"{BASE_URL}/api/explore/suggested-collectors", headers=auth_header)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # If there are suggestions, verify structure
        if len(data) > 0:
            user = data[0]
            assert "id" in user
            assert "username" in user
            # Suggested collectors should have shared_artists count
            if "shared_artists" in user:
                assert isinstance(user["shared_artists"], int)
    
    def test_get_active_isos(self, auth_header):
        """GET /api/explore/active-isos - Returns ISO matches for current user"""
        response = requests.get(f"{BASE_URL}/api/explore/active-isos", headers=auth_header)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # If there are matches, they should be listings
        if len(data) > 0:
            match = data[0]
            # ISO matches are listings that match user's wantlist
            assert "artist" in match or "album" in match
    
    def test_explore_routes_require_auth(self):
        """All explore routes require authentication"""
        routes = [
            "/api/explore/trending",
            "/api/explore/recent-hauls",
            "/api/explore/suggested-collectors",
            "/api/explore/active-isos"
        ]
        for route in routes:
            response = requests.get(f"{BASE_URL}{route}")
            assert response.status_code == 401, f"Route {route} should require auth"


class TestBuzzingRoute:
    """Test buzzing/trending route"""
    
    def test_get_buzzing_records(self):
        """GET /api/buzzing - Returns buzzing/trending records"""
        response = requests.get(f"{BASE_URL}/api/buzzing")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestFollowRoutes:
    """Test follow routes from routes/explore.py"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_check_following_status(self, auth_header):
        """GET /api/follow/check/{username} - Check if following a user"""
        response = requests.get(f"{BASE_URL}/api/follow/check/trader", headers=auth_header)
        # Should return either 200 with is_following status or 404 if user not found
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "is_following" in data


class TestStatsRoute:
    """Test global stats route"""
    
    def test_get_global_stats(self):
        """GET /api/stats - Returns platform statistics"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "records" in data
        assert "spins" in data


class TestUserSearch:
    """Test user search functionality"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_search_users(self, auth_header):
        """GET /api/users/search?query=demo - Search for users"""
        response = requests.get(f"{BASE_URL}/api/users/search?query=demo", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_users_requires_min_length(self, auth_header):
        """GET /api/users/search?query=a - Should require min 2 characters"""
        response = requests.get(f"{BASE_URL}/api/users/search?query=a", headers=auth_header)
        # Should fail validation
        assert response.status_code == 422


class TestCommunityISO:
    """Test community ISO endpoint"""
    
    @pytest.fixture
    def auth_header(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_community_isos(self, auth_header):
        """GET /api/iso/community - Returns ISOs from other users"""
        response = requests.get(f"{BASE_URL}/api/iso/community", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestIntegration:
    """Integration tests - verify data flows work end-to-end"""
    
    def test_login_then_access_protected_routes(self):
        """Login and access multiple protected routes"""
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access multiple protected routes
        endpoints = [
            "/api/auth/me",
            "/api/feed",
            "/api/records",
            "/api/trades",
            "/api/notifications",
            "/api/dm/conversations",
            "/api/iso",
            "/api/explore/trending",
            "/api/explore/recent-hauls",
            "/api/explore/suggested-collectors",
            "/api/explore/active-isos"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            assert response.status_code == 200, f"Failed on {endpoint}: {response.status_code} - {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
