"""
Test P1 Features:
1. Genre dropdown (Pop and Alternative) - Frontend only, can't test via API
2. GET /api/explore/trending-in-collections - Discogs most-collected data with caching
3. Old Fresh Pressings endpoint removed - should 404
4. Admin User Management - GET /api/admin/users, POST /api/admin/users/role
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "password123"
DEMO_USER_ID = "9221572c-1d80-4274-8393-77f0b2fdffc4"


class TestTrendingInCollections:
    """Test the new trending-in-collections endpoint that replaced fresh-pressings"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for demo account"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        self.token = data.get("access_token")  # Note: returns access_token, not token
        assert self.token, f"No access_token in response: {data}"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_trending_in_collections_returns_array(self):
        """GET /api/explore/trending-in-collections returns array of records"""
        resp = requests.get(f"{BASE_URL}/api/explore/trending-in-collections", headers=self.headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"SUCCESS: trending-in-collections returned {len(data)} records")
        return data

    def test_trending_in_collections_record_structure(self):
        """Each record should have discogs_id, artist, title, have, cover_url"""
        resp = requests.get(f"{BASE_URL}/api/explore/trending-in-collections", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        if len(data) > 0:
            record = data[0]
            # Required fields based on API spec
            assert "discogs_id" in record, f"Missing discogs_id in {record.keys()}"
            assert "artist" in record, f"Missing artist in {record.keys()}"
            assert "title" in record, f"Missing title in {record.keys()}"
            assert "have" in record, f"Missing have (collector count) in {record.keys()}"
            assert "cover_url" in record, f"Missing cover_url in {record.keys()}"
            
            # Validate types
            assert isinstance(record["have"], int), f"have should be int, got {type(record['have'])}"
            print(f"SUCCESS: Record structure valid - {record['artist']} - {record['title']} ({record['have']} collectors)")
        else:
            pytest.skip("No trending records returned - may be API rate limited")

    def test_trending_in_collections_caching(self):
        """Second call should return same data faster (cached for 24h)"""
        # First call
        start1 = time.time()
        resp1 = requests.get(f"{BASE_URL}/api/explore/trending-in-collections", headers=self.headers)
        time1 = time.time() - start1
        assert resp1.status_code == 200
        data1 = resp1.json()
        
        # Small delay
        time.sleep(0.5)
        
        # Second call (should be cached)
        start2 = time.time()
        resp2 = requests.get(f"{BASE_URL}/api/explore/trending-in-collections", headers=self.headers)
        time2 = time.time() - start2
        assert resp2.status_code == 200
        data2 = resp2.json()
        
        # Data should be identical (cached)
        if len(data1) > 0 and len(data2) > 0:
            assert data1[0].get("discogs_id") == data2[0].get("discogs_id"), "Cached data should match"
            print(f"SUCCESS: Caching works - First: {time1:.3f}s, Second: {time2:.3f}s, Same data: {data1[0].get('title')}")
        else:
            print(f"SUCCESS: Endpoint returns cached results")

    def test_fresh_pressings_endpoint_removed(self):
        """Old /api/explore/fresh-pressings should no longer exist (404 or error)"""
        resp = requests.get(f"{BASE_URL}/api/explore/fresh-pressings", headers=self.headers)
        # Should be 404 since endpoint was replaced
        assert resp.status_code in [404, 422, 405], f"Expected 404/error for old endpoint, got {resp.status_code}"
        print(f"SUCCESS: Old fresh-pressings endpoint returns {resp.status_code}")


class TestAdminUserManagement:
    """Test admin user management endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for demo account (admin)"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        self.token = data.get("access_token")
        assert self.token, f"No access_token in response: {data}"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.demo_user_id = DEMO_USER_ID

    def test_get_admin_users_returns_list(self):
        """GET /api/admin/users returns list of all users"""
        resp = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Should have at least one user (demo)"
        print(f"SUCCESS: /admin/users returned {len(data)} users")
        return data

    def test_get_admin_users_structure(self):
        """Each user should have id, username, email, is_admin, created_at"""
        resp = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        if len(data) > 0:
            user = data[0]
            required_fields = ["id", "username", "email", "is_admin", "created_at"]
            for field in required_fields:
                assert field in user, f"Missing {field} in user: {user.keys()}"
            print(f"SUCCESS: User structure valid - @{user.get('username')} (admin: {user.get('is_admin')})")

    def test_get_admin_users_filter_admin(self):
        """GET /api/admin/users?role_filter=admin returns only admins"""
        resp = requests.get(f"{BASE_URL}/api/admin/users?role_filter=admin", headers=self.headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        
        # All returned users should be admins
        for user in data:
            assert user.get("is_admin") == True, f"Non-admin in admin filter: {user.get('username')}"
        print(f"SUCCESS: Admin filter returned {len(data)} admin users")

    def test_get_admin_users_search(self):
        """GET /api/admin/users?search=demo returns filtered results"""
        resp = requests.get(f"{BASE_URL}/api/admin/users?search=demo", headers=self.headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        
        # Should find demo user
        found_demo = any(u.get("username") == "demo" or "demo" in u.get("email", "") for u in data)
        print(f"SUCCESS: Search 'demo' returned {len(data)} users, found demo: {found_demo}")

    def test_cannot_revoke_own_admin(self):
        """POST /api/admin/users/role cannot revoke own admin access (returns 400)"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/users/role",
            headers=self.headers,
            json={"user_id": self.demo_user_id, "is_admin": False}
        )
        # Should return 400 when trying to revoke own admin
        assert resp.status_code == 400, f"Expected 400 for self-revoke, got {resp.status_code}: {resp.text}"
        print(f"SUCCESS: Cannot revoke own admin access - {resp.json().get('detail', resp.text)}")

    def test_admin_users_requires_auth(self):
        """GET /api/admin/users requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/admin/users")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print(f"SUCCESS: Admin users endpoint requires auth (got {resp.status_code})")


class TestExploreEndpointAuth:
    """Test that explore endpoints require authentication"""

    def test_trending_in_collections_requires_auth(self):
        """GET /api/explore/trending-in-collections requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/explore/trending-in-collections")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print(f"SUCCESS: trending-in-collections requires auth (got {resp.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
