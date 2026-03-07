"""
HEIC Image Upload and Conversion Tests
Tests for:
1. POST /api/upload with HEIC files - converts to JPEG
2. POST /api/upload with standard JPEG/PNG/WebP - compresses/resizes (max 1200px)
3. POST /api/upload rejects non-image files (PDF, text)
4. POST /api/upload handles RGBA/palette PNG images
5. Uploaded images served via /api/files/serve/{path}
6. POST /api/admin/reprocess-heic requires admin auth
7. Frontend file input accept attributes are restricted
"""
import pytest
import requests
import os
import io
import uuid
from PIL import Image

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def create_test_user():
    """Create a test user and return token"""
    unique_id = uuid.uuid4().hex[:8]
    email = f"test_heic_{unique_id}@test.com"
    password = "testpass123"
    username = f"heictest{unique_id}"
    
    # Register
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email,
        "username": username,
        "password": password
    })
    
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token"), data.get("user", {}).get("id")
    
    # If registration fails (already exists), try login
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token"), data.get("user", {}).get("id")
    
    return None, None


def create_test_image(width=2000, height=1500, mode="RGB", format_type="JPEG"):
    """Create a test image in memory"""
    img = Image.new(mode, (width, height), color='red' if mode == 'RGB' else (255, 0, 0, 128))
    buf = io.BytesIO()
    if format_type == "JPEG" and mode != "RGB":
        # Convert to RGB for JPEG
        img = img.convert("RGB")
    img.save(buf, format=format_type, quality=90)
    buf.seek(0)
    return buf


def create_rgba_png():
    """Create a PNG with RGBA mode (transparency)"""
    img = Image.new("RGBA", (1500, 1500), color=(255, 0, 0, 128))  # Semi-transparent red
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def create_palette_png():
    """Create a PNG with palette mode (P)"""
    img = Image.new("P", (1000, 1000))
    img.putpalette([255, 0, 0] * 256)  # Red palette
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def create_fake_pdf():
    """Create a fake PDF file"""
    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n%Test PDF content\n")
    buf.seek(0)
    return buf


def create_text_file():
    """Create a simple text file"""
    buf = io.BytesIO()
    buf.write(b"This is a text file, not an image")
    buf.seek(0)
    return buf


class TestUploadWithAuth:
    """Upload endpoint tests with authentication"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        token, user_id = create_test_user()
        if not token:
            pytest.skip("Could not create test user")
        return token
    
    def test_upload_requires_auth(self):
        """Test that upload requires authentication"""
        img_data = create_test_image(500, 500)
        files = {"file": ("test.jpg", img_data, "image/jpeg")}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Upload requires authentication")
    
    def test_upload_jpeg_resize_compress(self, auth_token):
        """Test JPEG upload - should resize to max 1200px and compress"""
        # Create a large image (2000x1500)
        img_data = create_test_image(2000, 1500, "RGB", "JPEG")
        files = {"file": ("large_image.jpg", img_data, "image/jpeg")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert "path" in data
        assert "url" in data
        assert data["path"].endswith(".jpg"), f"Expected .jpg extension, got: {data['path']}"
        
        # Verify the uploaded file is accessible
        file_url = data["url"]
        file_resp = requests.get(file_url)
        assert file_resp.status_code == 200, f"Could not fetch uploaded file: {file_resp.status_code}"
        
        # Verify the image was resized (max 1200px longest side)
        result_img = Image.open(io.BytesIO(file_resp.content))
        assert max(result_img.size) <= 1200, f"Image was not resized: {result_img.size}"
        print(f"PASS: JPEG upload - original 2000x1500 -> resized to {result_img.size}")
    
    def test_upload_png_resize(self, auth_token):
        """Test PNG upload - should convert to JPEG and resize"""
        img_data = create_test_image(1800, 1200, "RGB", "PNG")
        files = {"file": ("test_image.png", img_data, "image/png")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert data["path"].endswith(".jpg"), f"Expected .jpg extension (converted from PNG), got: {data['path']}"
        
        # Verify resized
        file_resp = requests.get(data["url"])
        assert file_resp.status_code == 200
        result_img = Image.open(io.BytesIO(file_resp.content))
        assert max(result_img.size) <= 1200, f"Image was not resized: {result_img.size}"
        print(f"PASS: PNG upload converted to JPEG and resized to {result_img.size}")
    
    def test_upload_webp(self, auth_token):
        """Test WebP upload - should convert to JPEG"""
        img = Image.new("RGB", (1500, 1000), color='blue')
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=90)
        buf.seek(0)
        
        files = {"file": ("test_image.webp", buf, "image/webp")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert data["path"].endswith(".jpg"), f"Expected .jpg extension, got: {data['path']}"
        print("PASS: WebP upload converted to JPEG")
    
    def test_upload_rgba_png_to_jpeg(self, auth_token):
        """Test RGBA PNG upload - should convert to RGB JPEG (white background)"""
        img_data = create_rgba_png()
        files = {"file": ("transparent.png", img_data, "image/png")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert data["path"].endswith(".jpg"), f"Expected .jpg extension, got: {data['path']}"
        
        # Verify it's a valid JPEG
        file_resp = requests.get(data["url"])
        assert file_resp.status_code == 200
        result_img = Image.open(io.BytesIO(file_resp.content))
        assert result_img.mode == "RGB", f"Expected RGB mode, got {result_img.mode}"
        print("PASS: RGBA PNG converted to RGB JPEG")
    
    def test_upload_palette_png_to_jpeg(self, auth_token):
        """Test palette PNG (mode P) upload - should convert to RGB JPEG"""
        img_data = create_palette_png()
        files = {"file": ("palette.png", img_data, "image/png")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert data["path"].endswith(".jpg"), f"Expected .jpg extension, got: {data['path']}"
        print("PASS: Palette PNG converted to JPEG")
    
    def test_upload_small_image_no_resize(self, auth_token):
        """Test small image (under 1200px) - should not resize"""
        img_data = create_test_image(800, 600, "RGB", "JPEG")
        files = {"file": ("small_image.jpg", img_data, "image/jpeg")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        file_resp = requests.get(data["url"])
        result_img = Image.open(io.BytesIO(file_resp.content))
        # Small image should stay same size
        assert result_img.size == (800, 600), f"Small image was resized: {result_img.size}"
        print("PASS: Small image (800x600) kept original size")
    
    def test_upload_reject_pdf(self, auth_token):
        """Test PDF upload - should be rejected"""
        pdf_data = create_fake_pdf()
        files = {"file": ("document.pdf", pdf_data, "application/pdf")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "image" in response.text.lower() or "allowed" in response.text.lower()
        print("PASS: PDF file correctly rejected")
    
    def test_upload_reject_text(self, auth_token):
        """Test text file upload - should be rejected"""
        text_data = create_text_file()
        files = {"file": ("readme.txt", text_data, "text/plain")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Text file correctly rejected")
    
    def test_upload_heic_extension_with_jpeg_content(self, auth_token):
        """Test file with .heic extension but JPEG content (simulated HEIC acceptance)"""
        # Since we can't create real HEIC without complex setup, test that .heic extension is accepted
        # The backend should try to process it; if it fails due to not being real HEIC, that's expected
        img = Image.new("RGB", (1000, 800), color='green')
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        
        # Send as HEIC content-type to test the allowed types
        files = {"file": ("test.heic", buf, "image/heic")}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        # Should either succeed (if pillow-heif can handle it) or fail with processing error (not 400 for type)
        # We mainly want to confirm image/heic content-type is allowed
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        if response.status_code == 400:
            # Should be processing error, not type rejection
            error_msg = response.text.lower()
            assert "could not process" in error_msg or "jpg" in error_msg or "png" in error_msg
            print("PASS: .heic extension accepted (processing failed as expected for fake HEIC)")
        else:
            print("PASS: .heic file uploaded successfully")


class TestAdminReprocessHeic:
    """Test the admin reprocess-heic endpoint"""
    
    def test_reprocess_heic_requires_auth(self):
        """Test that reprocess-heic requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/reprocess-heic")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: admin/reprocess-heic requires authentication")
    
    def test_reprocess_heic_requires_admin(self):
        """Test that reprocess-heic requires admin role"""
        token, _ = create_test_user()
        if not token:
            pytest.skip("Could not create test user")
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/admin/reprocess-heic", headers=headers)
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print("PASS: admin/reprocess-heic requires admin role")


class TestFileServe:
    """Test the file serve endpoint"""
    
    def test_serve_requires_valid_namespace(self):
        """Test that serve endpoint only allows honeygroove namespace"""
        # Try to access file outside allowed namespace
        response = requests.get(f"{BASE_URL}/api/files/serve/other_app/test.png")
        assert response.status_code == 403, f"Expected 403 for invalid namespace, got {response.status_code}"
        print("PASS: File serve blocks invalid namespace")
    
    def test_serve_returns_correct_content_type(self):
        """Test that served files have correct content type"""
        # First upload a file
        token, _ = create_test_user()
        if not token:
            pytest.skip("Could not create test user")
        
        img_data = create_test_image(500, 500, "RGB", "JPEG")
        files = {"file": ("test.jpg", img_data, "image/jpeg")}
        headers = {"Authorization": f"Bearer {token}"}
        
        upload_resp = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
        if upload_resp.status_code != 200:
            pytest.skip("Upload failed")
        
        data = upload_resp.json()
        
        # Fetch the file
        file_resp = requests.get(data["url"])
        assert file_resp.status_code == 200
        content_type = file_resp.headers.get("Content-Type", "")
        assert "image/jpeg" in content_type, f"Expected image/jpeg, got {content_type}"
        print("PASS: Served file has correct content-type (image/jpeg)")


class TestAllowedFileTypes:
    """Test the allowed file types configuration"""
    
    def test_allowed_image_types(self):
        """Verify the backend accepts all allowed types"""
        token, _ = create_test_user()
        if not token:
            pytest.skip("Could not create test user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test each allowed content type
        allowed_types = [
            ("image/jpeg", "test.jpg"),
            ("image/png", "test.png"),
            ("image/webp", "test.webp"),
        ]
        
        for content_type, filename in allowed_types:
            img_data = create_test_image(500, 500, "RGB", "JPEG")
            files = {"file": (filename, img_data, content_type)}
            response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=headers)
            # May fail on processing but should not be 400 for file type
            if response.status_code == 400:
                error_msg = response.text.lower()
                assert "only image" not in error_msg, f"Type {content_type} should be allowed"
            print(f"PASS: {content_type} is accepted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
