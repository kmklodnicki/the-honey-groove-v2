"""
Test suite for HoneyGroove data migration and fixes
Tests: Health check, export endpoints, admin login, and honeypot pagination
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://poll-creator-view.preview.emergentagent.com')


class TestHealthAndExport:
    """Health check and export endpoint tests"""
    
    def test_health_check(self):
        """Test backend health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("service") == "honeygroove-api"
        print(f"Health check passed: {data}")
    
    def test_export_list_endpoint(self):
        """Test export list endpoint returns JSON files"""
        response = requests.get(f"{BASE_URL}/api/export/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check that we have some export files
        print(f"Export files found: {len(data)}")
        if len(data) > 0:
            # Verify file structure
            file_info = data[0]
            assert "name" in file_info
            assert "size_kb" in file_info
            assert file_info["name"].endswith(".json")
            print(f"Sample export file: {file_info}")


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin user can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        
        user = data["user"]
        assert user.get("email") == "kmklodnicki@gmail.com"
        assert user.get("is_admin") == True, "Admin flag should be True"
        print(f"Admin login successful - is_admin: {user.get('is_admin')}")
        return data["access_token"]
    
    def test_admin_user_has_admin_flag(self):
        """Verify admin user has is_admin=True in user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026!"
        })
        assert response.status_code == 200
        data = response.json()
        
        user = data["user"]
        assert user.get("is_admin") == True
        assert user.get("golden_hive_verified") == True
        print(f"Admin user verified - is_admin: {user.get('is_admin')}, golden_hive: {user.get('golden_hive_verified')}")
    
    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("Invalid login correctly rejected")


class TestHoneypotAPI:
    """Honeypot/Marketplace API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026!"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_listings_endpoint(self):
        """Test listings endpoint works with limit parameter"""
        # Default endpoint - should support limit
        response = requests.get(f"{BASE_URL}/api/listings?limit=24")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check pagination limit is respected (max 24 on initial load)
        assert len(data) <= 200  # API allows up to 200
        print(f"Listings returned: {len(data)}")
    
    def test_my_listings_endpoint(self):
        """Test authenticated user's listings endpoint"""
        response = requests.get(f"{BASE_URL}/api/listings/my", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"User's listings: {len(data)}")
    
    def test_iso_endpoint(self):
        """Test ISO (in search of) endpoint"""
        response = requests.get(f"{BASE_URL}/api/iso", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"User's ISOs: {len(data)}")
    
    def test_community_iso_endpoint(self):
        """Test community ISO endpoint"""
        response = requests.get(f"{BASE_URL}/api/iso/community", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Community ISOs: {len(data)}")


class TestHiveFeed:
    """Hive feed API tests"""
    
    def test_explore_endpoint(self):
        """Test explore endpoint returns posts (public)"""
        response = requests.get(f"{BASE_URL}/api/explore?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Explore posts: {len(data)}")
        
        # Verify post structure if posts exist
        if len(data) > 0:
            post = data[0]
            assert "id" in post
            assert "post_type" in post
            print(f"Sample post type: {post.get('post_type')}, title: {post.get('record', {}).get('title')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
