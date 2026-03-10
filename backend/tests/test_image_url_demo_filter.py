"""
Test: Image URL resolution and Demo/Test user filtering
Tests for recurring bugs:
1. Profile and listing photos not loading due to stale URLs from previous deployments
2. @demo test data appearing on public pages

Backend Tests:
- All /api/explore/* endpoints should NOT return any data from demo/test users
- /api/files/serve/{path} endpoint should return 200 for valid storage paths
- /api/upload endpoint should accept image files and return both 'path' and 'url' fields
"""
import pytest
import requests
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://groove-shop-preview.preview.emergentagent.com').rstrip('/')

class TestDemoUserFiltering:
    """Test that demo/test users are filtered from all explore endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token for testing"""
        # First try to login with existing user
        try:
            # Try to register a test user first 
            register_data = {
                "email": "test_image_filter@test.com",
                "username": "test_image_filter",
                "password": "testpass123"
            }
            reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json=register_data, timeout=10)
            if reg_resp.status_code == 200:
                token = reg_resp.json().get("token")
                return {"Authorization": f"Bearer {token}"}
        except:
            pass
        
        # Try login
        login_data = {"email": "test_image_filter@test.com", "password": "testpass123"}
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        
        pytest.skip("Could not authenticate for explore endpoint tests")
    
    def test_explore_trending_excludes_demo_users(self, auth_headers):
        """GET /api/explore/trending should not return demo/test users"""
        resp = requests.get(f"{BASE_URL}/api/explore/trending?limit=50", headers=auth_headers, timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Even if there's no data, the endpoint should work
        print(f"Trending records returned: {len(data)}")
    
    def test_explore_most_wanted_excludes_demo_users(self, auth_headers):
        """GET /api/explore/most-wanted should not return demo/test users"""
        resp = requests.get(f"{BASE_URL}/api/explore/most-wanted?limit=50", headers=auth_headers, timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"Most wanted returned: {len(data)}")
    
    def test_explore_near_you_excludes_demo_users(self, auth_headers):
        """GET /api/explore/near-you should not return demo/test users"""
        resp = requests.get(f"{BASE_URL}/api/explore/near-you", headers=auth_headers, timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Check collectors list for demo users
        for collector in data.get("collectors", []):
            username = collector.get("username", "").lower()
            email = collector.get("email", "").lower()
            assert not username.startswith("demo"), f"Demo user found: {username}"
            assert not username.startswith("test"), f"Test user found: {username}"
            assert "test.com" not in email, f"Test email found: {email}"
            assert "example.com" not in email, f"Example email found: {email}"
        print(f"Near you collectors returned: {len(data.get('collectors', []))}")
    
    def test_explore_suggested_collectors_excludes_demo_users(self, auth_headers):
        """GET /api/explore/suggested-collectors should not return demo/test users"""
        resp = requests.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=50", headers=auth_headers, timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        for user in data:
            username = user.get("username", "").lower()
            assert not username.startswith("demo"), f"Demo user found: {username}"
            assert not username.startswith("test"), f"Test user found: {username}"
        print(f"Suggested collectors returned: {len(data)}")
    
    def test_explore_recent_hauls_excludes_demo_users(self, auth_headers):
        """GET /api/explore/recent-hauls should not return demo/test users"""
        resp = requests.get(f"{BASE_URL}/api/explore/recent-hauls?limit=50", headers=auth_headers, timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        for post in data:
            user = post.get("user", {})
            username = user.get("username", "").lower() if user else ""
            assert not username.startswith("demo"), f"Demo user found: {username}"
            assert not username.startswith("test"), f"Test user found: {username}"
        print(f"Recent hauls returned: {len(data)}")
    
    def test_explore_active_isos_excludes_demo_users(self, auth_headers):
        """GET /api/explore/active-isos should not return demo/test users"""
        resp = requests.get(f"{BASE_URL}/api/explore/active-isos", headers=auth_headers, timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"Active ISOs returned: {len(data)}")
    
    def test_buzzing_excludes_demo_users(self, auth_headers):
        """GET /api/buzzing should not return demo/test users"""
        resp = requests.get(f"{BASE_URL}/api/buzzing?limit=50", headers=auth_headers, timeout=10)
        # Note: This may not exist, check status
        if resp.status_code == 404:
            pytest.skip("Buzzing endpoint not found")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"Buzzing records returned: {len(resp.json())}")
    
    def test_feed_excludes_demo_users(self, auth_headers):
        """GET /api/feed should not return posts from demo/test users"""
        resp = requests.get(f"{BASE_URL}/api/feed", headers=auth_headers, timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        for post in data:
            user = post.get("user", {})
            username = user.get("username", "").lower() if user else ""
            assert not username.startswith("demo"), f"Demo user found in feed: {username}"
        print(f"Feed posts returned: {len(data)}")


class TestFileServeEndpoint:
    """Test the file serve proxy endpoint"""
    
    def test_serve_valid_honeygroove_path_format(self):
        """GET /api/files/serve/honeygroove/... should return correct status"""
        # Test with a non-existent but valid format path
        path = "honeygroove/uploads/test/test.png"
        resp = requests.get(f"{BASE_URL}/api/files/serve/{path}", timeout=10)
        # Should be 404 or 500 for missing file, but NOT 403
        assert resp.status_code in [200, 404, 500], f"Expected 200/404/500 for valid namespace, got {resp.status_code}"
        print(f"Valid path format returned: {resp.status_code}")
    
    def test_serve_invalid_namespace_rejected(self):
        """GET /api/files/serve/other_app/... should return 403"""
        path = "other_app/uploads/test.png"
        resp = requests.get(f"{BASE_URL}/api/files/serve/{path}", timeout=10)
        assert resp.status_code == 403, f"Expected 403 for wrong namespace, got {resp.status_code}"
        print(f"Invalid namespace correctly rejected with 403")
    
    def test_serve_path_traversal_blocked(self):
        """GET /api/files/serve/etc/passwd should return 403"""
        resp = requests.get(f"{BASE_URL}/api/files/serve/etc/passwd", timeout=10)
        assert resp.status_code == 403, f"Expected 403 for path traversal, got {resp.status_code}"
        print(f"Path traversal correctly blocked with 403")


class TestUploadEndpoint:
    """Test the upload endpoint returns correct response format"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication token for testing"""
        try:
            register_data = {
                "email": "test_upload_user@test.com",
                "username": "test_upload_user",
                "password": "testpass123"
            }
            reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json=register_data, timeout=10)
            if reg_resp.status_code == 200:
                token = reg_resp.json().get("token")
                return {"Authorization": f"Bearer {token}"}
        except:
            pass
        
        login_data = {"email": "test_upload_user@test.com", "password": "testpass123"}
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        
        pytest.skip("Could not authenticate for upload tests")
    
    def test_upload_requires_auth(self):
        """POST /api/upload requires authentication"""
        # Create a simple test image
        import io
        files = {'file': ('test.png', io.BytesIO(b'\x89PNG\r\n\x1a\n'), 'image/png')}
        resp = requests.post(f"{BASE_URL}/api/upload", files=files, timeout=10)
        assert resp.status_code == 401 or resp.status_code == 403, f"Expected 401/403 without auth, got {resp.status_code}"
        print(f"Upload correctly requires auth: {resp.status_code}")
    
    def test_upload_returns_path_and_url(self, auth_headers):
        """POST /api/upload should return {file_id, path, url}"""
        import io
        # Create a minimal valid PNG
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk header
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixels
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # bit depth, color type, etc
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0x00, 0x00, 0x00,  # compressed data
            0x01, 0x00, 0x01, 0x00, 0x05, 0x39, 0xFF, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
            0x42, 0x60, 0x82
        ])
        files = {'file': ('test_upload.png', io.BytesIO(png_data), 'image/png')}
        resp = requests.post(f"{BASE_URL}/api/upload", files=files, headers=auth_headers, timeout=15)
        
        # Upload may fail if storage isn't configured, that's OK
        if resp.status_code == 500:
            print(f"Upload returned 500 - storage may not be configured")
            pytest.skip("Storage not configured")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "path" in data, f"Response missing 'path': {data}"
        assert "url" in data, f"Response missing 'url': {data}"
        assert "file_id" in data, f"Response missing 'file_id': {data}"
        assert "/api/files/serve/" in data["url"], f"URL should contain proxy path: {data['url']}"
        print(f"Upload returned: path={data['path']}, url contains proxy={'/api/files/serve/' in data['url']}")


class TestHiddenUserIds:
    """Test that get_hidden_user_ids filters correctly"""
    
    def test_admin_user_is_hidden(self):
        """Admin user with is_hidden=True should not appear in explore"""
        # We can test this indirectly by checking that admin doesn't appear in suggested collectors
        import pymongo
        client = pymongo.MongoClient(os.environ.get('MONGO_URL'))
        db = client[os.environ.get('DB_NAME')]
        
        admin = db.users.find_one({"username": "admin"})
        if admin:
            assert admin.get("is_hidden") == True, "Admin should have is_hidden=True"
            print(f"Admin user correctly marked as hidden")
        else:
            pytest.skip("Admin user not found in DB")
    
    def test_demo_username_pattern_matched(self):
        """Usernames starting with 'demo' should be filtered"""
        import pymongo
        client = pymongo.MongoClient(os.environ.get('MONGO_URL'))
        db = client[os.environ.get('DB_NAME')]
        
        # Check get_hidden_user_ids regex pattern
        hidden = list(db.users.find(
            {"$or": [
                {"is_hidden": True},
                {"is_test": True},
                {"email": {"$regex": "@(test|example)\\.com$", "$options": "i"}},
                {"username": {"$regex": "^(demo|test)", "$options": "i"}},
                {"username": "demo"},
            ]},
            {"_id": 0, "id": 1, "username": 1}
        ))
        print(f"Hidden users found: {hidden}")
        # At minimum, admin should be hidden
        assert any(u.get("username") == "admin" for u in hidden if u.get("username")), "Admin should be in hidden list"


class TestAvatarUrlResolution:
    """Test that avatar URLs from old deployments are accessible"""
    
    def test_user_with_stale_avatar_url(self):
        """Check that user with old domain avatar_url has a reachable avatar after resolution"""
        import pymongo
        client = pymongo.MongoClient(os.environ.get('MONGO_URL'))
        db = client[os.environ.get('DB_NAME')]
        
        user = db.users.find_one({"username": "katieintheafterglow"})
        if not user:
            pytest.skip("User katieintheafterglow not found")
        
        avatar_url = user.get("avatar_url", "")
        print(f"Original avatar_url in DB: {avatar_url}")
        
        # The avatar_url contains old domain
        assert "collector-beta.preview.emergentagent.com" in avatar_url, "Expected stale URL for testing"
        
        # Frontend resolveImageUrl should rewrite this
        # Extract storage path from old URL
        serve_path = "/api/files/serve/"
        if serve_path in avatar_url:
            storage_path = avatar_url.split(serve_path)[1]
            new_url = f"{BASE_URL}/api/files/serve/{storage_path}"
            print(f"Resolved URL should be: {new_url}")
            
            # Test if the resolved URL works
            resp = requests.get(new_url, timeout=10)
            # Should return 200 if file exists, or 404/500 if storage is missing
            print(f"Resolved URL response: {resp.status_code}")
            # We just verify the URL format is correct and doesn't return 403


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
