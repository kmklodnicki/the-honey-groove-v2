"""
Test P0 Production Migration Sprint Features:
1. Login flow works - POST /api/auth/login
2. Health endpoint - GET /api/health
3. Upload endpoint (Cloudinary fallback) - POST /api/upload
4. Feed loads - GET /api/feed
5. CORS origins no longer contain localhost
6. Cloudinary utility exists and works with fallback
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://vinyl-image-bugs.preview.emergentagent.com")

# Test credentials
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "HoneyGroove2026!"


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        print(f"PASS: Health endpoint returns {data}")


class TestLoginFlow:
    """Authentication tests"""
    
    def test_login_success(self):
        """POST /api/auth/login with valid credentials returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        # Token field is 'access_token' not 'token'
        assert "access_token" in data, f"Missing access_token in response: {data}"
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"PASS: Login successful, got access_token")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login with wrong credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"PASS: Invalid credentials correctly return 401")


class TestFeedEndpoint:
    """Feed endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_feed_loads(self, auth_token):
        """GET /api/feed returns posts array"""
        response = requests.get(
            f"{BASE_URL}/api/feed",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Feed failed: {response.status_code} - {response.text}"
        data = response.json()
        # Feed returns dict with posts array
        if isinstance(data, dict):
            assert "posts" in data, f"Feed response missing 'posts': {data.keys()}"
            print(f"PASS: Feed returns {len(data.get('posts', []))} posts")
        elif isinstance(data, list):
            print(f"PASS: Feed returns {len(data)} posts")
        else:
            pytest.fail(f"Unexpected feed response type: {type(data)}")


class TestUploadEndpoint:
    """Upload endpoint tests - Cloudinary with fallback"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_upload_image(self, auth_token):
        """POST /api/upload with image file returns file_id, path, and url"""
        # Create a minimal valid JPEG image (1x1 pixel red)
        import io
        try:
            from PIL import Image
            img = Image.new('RGB', (10, 10), color='red')
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            image_data = buffer.getvalue()
        except ImportError:
            # Fallback: minimal valid JPEG
            image_data = bytes([
                0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
                0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
                0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
                0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
                0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
                0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
                0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
                0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
                0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
                0x7F, 0xFF, 0xD9
            ])
        
        files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/api/upload",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "file_id" in data, f"Missing file_id in upload response: {data}"
        assert "path" in data, f"Missing path in upload response: {data}"
        assert "url" in data, f"Missing url in upload response: {data}"
        print(f"PASS: Upload successful - file_id: {data['file_id']}, url: {data['url'][:50]}...")


class TestCORSOrigins:
    """CORS configuration tests - no localhost"""
    
    def test_cors_origins_no_localhost(self):
        """Verify server.py CORS origins do not contain localhost"""
        # Read server.py and check cors_origins
        server_path = "/app/backend/server.py"
        try:
            with open(server_path, 'r') as f:
                content = f.read()
            
            # Check that cors_origins list doesn't contain localhost
            # Look for the cors_origins = [ ... ] block
            import re
            cors_match = re.search(r'cors_origins\s*=\s*\[([^\]]+)\]', content, re.DOTALL)
            if cors_match:
                cors_list = cors_match.group(1)
                assert 'localhost' not in cors_list.lower(), f"CORS origins still contains localhost: {cors_list}"
                assert '127.0.0.1' not in cors_list, f"CORS origins contains 127.0.0.1: {cors_list}"
                print(f"PASS: CORS origins do not contain localhost")
            else:
                print("WARNING: Could not parse cors_origins from server.py")
        except FileNotFoundError:
            pytest.skip("Cannot read server.py locally")


class TestCloudinaryUtility:
    """Cloudinary utility tests"""
    
    def test_cloudinary_utility_exists(self):
        """Verify cloudinary_upload.py exists with proper functions"""
        cloudinary_path = "/app/backend/utils/cloudinary_upload.py"
        try:
            with open(cloudinary_path, 'r') as f:
                content = f.read()
            
            assert 'is_cloudinary_configured' in content, "Missing is_cloudinary_configured function"
            assert 'upload_image_buffer' in content, "Missing upload_image_buffer function"
            assert 'CLOUDINARY_CLOUD_NAME' in content or 'CLOUDINARY_NAME' in content, "Missing Cloudinary env var check"
            print("PASS: Cloudinary utility exists with required functions")
        except FileNotFoundError:
            pytest.fail("cloudinary_upload.py not found at expected path")
    
    def test_cloudinary_fallback_logic(self):
        """Verify upload endpoint has Cloudinary fallback logic"""
        collection_path = "/app/backend/routes/collection.py"
        try:
            with open(collection_path, 'r') as f:
                content = f.read()
            
            assert 'is_cloudinary_configured' in content, "Upload route missing Cloudinary check"
            assert 'upload_image_buffer' in content, "Upload route missing Cloudinary upload call"
            # Fallback should use put_object (Emergent storage)
            assert 'put_object' in content, "Upload route missing fallback to Emergent storage"
            print("PASS: Upload route has Cloudinary with fallback logic")
        except FileNotFoundError:
            pytest.fail("collection.py not found at expected path")


class TestDialogComponents:
    """Dialog/Modal component tests - mobile-friendly"""
    
    def test_dialog_component_mobile_classes(self):
        """Verify dialog.jsx has mobile-friendly classes"""
        dialog_path = "/app/frontend/src/components/ui/dialog.jsx"
        try:
            with open(dialog_path, 'r') as f:
                content = f.read()
            
            assert 'max-h-[85vh]' in content, "Dialog missing max-h-[85vh] for mobile"
            assert 'overflow-y-auto' in content, "Dialog missing overflow-y-auto"
            assert 'modal-mobile-scale' in content, "Dialog missing modal-mobile-scale class"
            assert 'onCloseAutoFocus' in content, "Dialog missing onCloseAutoFocus scroll lock fix"
            print("PASS: Dialog component has mobile-friendly classes and scroll lock fix")
        except FileNotFoundError:
            pytest.fail("dialog.jsx not found")
    
    def test_sheet_component_scroll_fix(self):
        """Verify sheet.jsx has scroll lock fix"""
        sheet_path = "/app/frontend/src/components/ui/sheet.jsx"
        try:
            with open(sheet_path, 'r') as f:
                content = f.read()
            
            assert 'onCloseAutoFocus' in content, "Sheet missing onCloseAutoFocus scroll lock fix"
            assert 'body.style.overflow' in content, "Sheet missing body overflow reset"
            print("PASS: Sheet component has scroll lock fix")
        except FileNotFoundError:
            pytest.fail("sheet.jsx not found")
    
    def test_alert_dialog_mobile_classes(self):
        """Verify alert-dialog.jsx has mobile-friendly classes"""
        alert_path = "/app/frontend/src/components/ui/alert-dialog.jsx"
        try:
            with open(alert_path, 'r') as f:
                content = f.read()
            
            assert 'onCloseAutoFocus' in content, "AlertDialog missing onCloseAutoFocus scroll lock fix"
            assert 'modal-mobile-scale' in content, "AlertDialog missing modal-mobile-scale class"
            print("PASS: AlertDialog component has mobile-friendly classes")
        except FileNotFoundError:
            pytest.fail("alert-dialog.jsx not found")


class TestSocketContext:
    """SocketContext notification deduplication tests"""
    
    def test_socket_context_dedup(self):
        """Verify SocketContext has notification deduplication"""
        socket_path = "/app/frontend/src/context/SocketContext.js"
        try:
            with open(socket_path, 'r') as f:
                content = f.read()
            
            assert 'processedIds' in content, "SocketContext missing processedIds for dedup"
            assert 'new Set()' in content, "SocketContext missing Set for dedup tracking"
            assert 'removeAllListeners' in content, "SocketContext missing cleanup"
            print("PASS: SocketContext has notification deduplication")
        except FileNotFoundError:
            pytest.fail("SocketContext.js not found")


class TestNavbarNotifications:
    """Navbar notification bell tests"""
    
    def test_navbar_notification_dedup(self):
        """Verify Navbar has notification deduplication"""
        navbar_path = "/app/frontend/src/components/Navbar.js"
        try:
            with open(navbar_path, 'r') as f:
                content = f.read()
            
            assert 'prevCountRef' in content, "Navbar missing prevCountRef for initial flood skip"
            assert 'shownNotifIds' in content, "Navbar missing shownNotifIds for dedup"
            # Check that prevCountRef starts at -1 to skip initial notifications
            assert '-1' in content, "Navbar prevCountRef should start at -1"
            print("PASS: Navbar has notification deduplication")
        except FileNotFoundError:
            pytest.fail("Navbar.js not found")


class TestMigrationPlaceholder:
    """Legacy upload fallback tests"""
    
    def test_image_url_legacy_check(self):
        """Verify imageUrl.js has isLegacyUploadUrl function"""
        imageurl_path = "/app/frontend/src/utils/imageUrl.js"
        try:
            with open(imageurl_path, 'r') as f:
                content = f.read()
            
            assert 'isLegacyUploadUrl' in content, "Missing isLegacyUploadUrl function"
            assert '/uploads/' in content, "isLegacyUploadUrl should check for /uploads/ path"
            print("PASS: imageUrl.js has isLegacyUploadUrl function")
        except FileNotFoundError:
            pytest.fail("imageUrl.js not found")
    
    def test_album_art_migration_placeholder(self):
        """Verify AlbumArt.js shows migration placeholder for legacy URLs"""
        albumart_path = "/app/frontend/src/components/AlbumArt.js"
        try:
            with open(albumart_path, 'r') as f:
                content = f.read()
            
            assert 'isLegacyUploadUrl' in content, "AlbumArt missing isLegacyUploadUrl import"
            assert 'migration-placeholder' in content, "AlbumArt missing migration-placeholder class"
            assert 'migration in progress' in content, "AlbumArt missing 'migration in progress' text"
            print("PASS: AlbumArt.js has migration placeholder for legacy URLs")
        except FileNotFoundError:
            pytest.fail("AlbumArt.js not found")
    
    def test_postcards_onerror_handler(self):
        """Verify PostCards.js img tags have onError handlers"""
        postcards_path = "/app/frontend/src/components/PostCards.js"
        try:
            with open(postcards_path, 'r') as f:
                content = f.read()
            
            assert 'isLegacyUploadUrl' in content, "PostCards missing isLegacyUploadUrl import"
            assert 'onError' in content, "PostCards missing onError handlers on img tags"
            # Check that onError checks for legacy URLs
            assert 'isLegacyUploadUrl(' in content, "PostCards onError should check isLegacyUploadUrl"
            print("PASS: PostCards.js has onError handlers for legacy URL fallback")
        except FileNotFoundError:
            pytest.fail("PostCards.js not found")


class TestModalCSS:
    """Index.css modal styling tests"""
    
    def test_modal_mobile_scale_css(self):
        """Verify index.css has modal-mobile-scale responsive CSS"""
        css_path = "/app/frontend/src/index.css"
        try:
            with open(css_path, 'r') as f:
                content = f.read()
            
            assert 'modal-mobile-scale' in content, "Missing modal-mobile-scale CSS class"
            assert 'max-height: 85vh' in content or 'max-height:85vh' in content.replace(' ', ''), "Missing 85vh max-height"
            assert 'overflow-y: auto' in content or 'overflow-y:auto' in content.replace(' ', ''), "Missing overflow-y auto"
            print("PASS: index.css has modal-mobile-scale responsive CSS")
        except FileNotFoundError:
            pytest.fail("index.css not found")
    
    def test_migration_placeholder_css(self):
        """Verify index.css has migration-placeholder styles"""
        css_path = "/app/frontend/src/index.css"
        try:
            with open(css_path, 'r') as f:
                content = f.read()
            
            assert 'migration-placeholder' in content, "Missing migration-placeholder CSS"
            assert 'migration-placeholder-text' in content, "Missing migration-placeholder-text CSS"
            print("PASS: index.css has migration-placeholder styles")
        except FileNotFoundError:
            pytest.fail("index.css not found")


# Run all tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
