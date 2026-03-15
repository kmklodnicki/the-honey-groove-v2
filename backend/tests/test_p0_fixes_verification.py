"""
P0 Fixes Verification Tests - Iteration 254
Tests for:
1. Note Composer UI: record selector is now a search input (not dropdown)
2. Image URL proxy: uses dynamic API URL for legacy images
3. Cloudinary upload: better error handling with fallback
4. Hidden gems endpoint: returns 200 with data
5. Login flow: works with email/password
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "kmklodnicki@gmail.com"
TEST_PASSWORD = "HoneyGroove2026"


@pytest.fixture
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "Response should have 'access_token' field (not 'token')"
    return data["access_token"]


class TestLoginFlow:
    """Test login flow works with email/password"""
    
    def test_login_returns_access_token(self):
        """P0 Fix: Login returns access_token field"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, "Login should return 'access_token'"
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL

    def test_login_invalid_credentials(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestUploadEndpoint:
    """Test upload endpoint with Cloudinary fallback"""
    
    def test_upload_image_returns_url(self, auth_token):
        """P0 Fix: Upload should return file_id, path, and url"""
        import base64
        
        # Create minimal test PNG (1x1 pixel)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        files = {"file": ("test.png", png_data, "image/png")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert "file_id" in data, "Upload should return file_id"
        assert "url" in data, "Upload should return url"
        assert "path" in data, "Upload should return path"
        
        # URL should be valid (either Cloudinary or Emergent storage)
        url = data["url"]
        assert url.startswith("http"), f"URL should start with http: {url}"


class TestHiddenGems:
    """Test hidden gems valuation endpoint"""
    
    def test_hidden_gems_returns_data(self, auth_token):
        """P0 Fix: GET /api/valuation/hidden-gems returns 200 with data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/valuation/hidden-gems", headers=headers)
        
        assert response.status_code == 200, f"Hidden gems failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list of records"
        
        # If there's data, verify structure
        if len(data) > 0:
            first = data[0]
            assert "id" in first
            assert "title" in first
            assert "artist" in first


class TestImageUrlProxy:
    """Test image URL proxy configuration"""
    
    def test_imageurl_uses_dynamic_api(self):
        """P0 Fix: imageUrl.js uses dynamic API URL (not hardcoded)"""
        imageurl_path = "/app/frontend/src/utils/imageUrl.js"
        
        with open(imageurl_path, "r") as f:
            content = f.read()
        
        # Should use ${API}/files/serve/ - dynamic
        assert "${API}/files/serve/" in content, "EMERGENT_STORAGE_PROXY should use dynamic ${API}"
        
        # Should NOT have hardcoded emergent preview URL
        assert "preview.emergentagent.com" not in content or content.count("preview.emergentagent.com") == 0, \
            "Should not have hardcoded preview URL"

    def test_files_serve_endpoint_exists(self, auth_token):
        """Files serve endpoint should return 404 for non-existent files (not 500)"""
        response = requests.get(f"{BASE_URL}/api/files/serve/honeygroove/test.jpg")
        # Should be 404 (not found) or 403 (access denied), not 500
        assert response.status_code in [403, 404], f"Files serve should return 404/403, got {response.status_code}"


class TestNoteComposerUI:
    """Verify Note composer UI changes"""
    
    def test_composerbar_note_search_elements(self):
        """P0 Fix: ComposerBar.js has search input for notes (not Select dropdown)"""
        composer_path = "/app/frontend/src/components/ComposerBar.js"
        
        with open(composer_path, "r") as f:
            content = f.read()
        
        # Should have noteSearch state for search input
        assert "noteSearch" in content, "Should have noteSearch state"
        assert "noteSearchResults" in content, "Should have noteSearchResults state"
        assert "searchCollectionForNote" in content, "Should have searchCollectionForNote function"
        
        # Should have note-record-search data-testid (search input)
        assert 'data-testid="note-record-search"' in content, "Should have note-record-search test id"
        
        # Search input should have placeholder for vault search
        assert 'search your vault' in content.lower(), "Should have vault search placeholder"


class TestCloudinaryUpload:
    """Test Cloudinary upload utility"""
    
    def test_cloudinary_utility_has_error_handling(self):
        """P0 Fix: cloudinary_upload.py has improved error handling"""
        cloudinary_path = "/app/backend/utils/cloudinary_upload.py"
        
        with open(cloudinary_path, "r") as f:
            content = f.read()
        
        # Should have logging for diagnostics
        assert "logger.error" in content, "Should have error logging"
        
        # Should log Cloudinary config details on error
        assert "cloud_name" in content, "Should log cloud_name"
        assert "api_key" in content, "Should log api_key"
        
    def test_collection_upload_has_fallback(self):
        """P0 Fix: collection.py upload route falls back to Emergent storage"""
        collection_path = "/app/backend/routes/collection.py"
        
        with open(collection_path, "r") as f:
            content = f.read()
        
        # Should check if Cloudinary is configured
        assert "is_cloudinary_configured()" in content, "Should check Cloudinary config"
        
        # Should have fallback to Emergent storage
        assert "put_object" in content, "Should use put_object for fallback"
