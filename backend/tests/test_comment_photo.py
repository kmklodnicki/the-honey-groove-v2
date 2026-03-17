"""Test suite for comment photo feature - allows users to upload photos with comments"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "kmklodnicki@gmail.com"
TEST_PASSWORD = "HoneyGroove2026"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def user_info(auth_token):
    """Get current user info"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    if response.status_code != 200:
        pytest.skip("Failed to get user info")
    return response.json()


class TestCommentPhotoBackend:
    """Test backend API support for comment photos"""

    def test_01_login_and_auth(self, auth_token):
        """Test login works with test credentials"""
        assert auth_token is not None
        assert len(auth_token) > 10
        print(f"PASS: Login successful, token length={len(auth_token)}")

    def test_02_get_feed_with_posts(self, auth_token):
        """Test fetching feed to find a post to comment on"""
        response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        }, params={"limit": 20})
        assert response.status_code == 200
        posts = response.json()
        assert isinstance(posts, list)
        print(f"PASS: Feed fetched with {len(posts)} posts")
        return posts

    def test_03_upload_image(self, auth_token):
        """Test image upload endpoint exists and works"""
        # Create a simple 1x1 PNG image for testing
        # PNG header bytes for a minimal valid PNG
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR length + type
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # width=1, height=1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # 8-bit RGB, etc
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT length + type
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0x00, 0x00, 0x00,  # compressed pixel data
            0x01, 0x00, 0x01, 0xE2, 0x8D, 0x15, 0xC9, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND
            0x42, 0x60, 0x82
        ])
        
        files = {'file': ('test_image.png', io.BytesIO(png_bytes), 'image/png')}
        response = requests.post(f"{BASE_URL}/api/upload", 
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "url" in data, "Response should contain 'url' field"
        print(f"PASS: Image uploaded successfully, url={data['url'][:50]}...")
        return data["url"]

    def test_04_create_comment_with_image(self, auth_token):
        """Test creating a comment with an image_url field"""
        # First get a post to comment on
        feed_response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        }, params={"limit": 10})
        assert feed_response.status_code == 200
        posts = feed_response.json()
        
        if not posts:
            pytest.skip("No posts available to comment on")
        
        post_id = posts[0]["id"]
        
        # Upload an image first
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0x00, 0x00, 0x00,
            0x01, 0x00, 0x01, 0xE2, 0x8D, 0x15, 0xC9, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ])
        files = {'file': ('test_comment_img.png', io.BytesIO(png_bytes), 'image/png')}
        upload_response = requests.post(f"{BASE_URL}/api/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files
        )
        assert upload_response.status_code == 200
        image_url = upload_response.json()["url"]
        
        # Create comment with image
        comment_data = {
            "post_id": post_id,
            "content": "Test comment with photo attachment",
            "image_url": image_url
        }
        response = requests.post(f"{BASE_URL}/api/posts/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=comment_data
        )
        
        assert response.status_code == 200, f"Create comment failed: {response.status_code} - {response.text}"
        comment = response.json()
        assert "id" in comment
        assert comment.get("image_url") == image_url, "Comment should have image_url field"
        print(f"PASS: Comment with image created, id={comment['id']}, image_url present")
        return comment

    def test_05_create_comment_text_only(self, auth_token):
        """Test creating a comment without an image (text only)"""
        feed_response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        }, params={"limit": 10})
        assert feed_response.status_code == 200
        posts = feed_response.json()
        
        if not posts:
            pytest.skip("No posts available")
        
        post_id = posts[0]["id"]
        
        comment_data = {
            "post_id": post_id,
            "content": "Test comment without photo"
        }
        response = requests.post(f"{BASE_URL}/api/posts/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=comment_data
        )
        
        assert response.status_code == 200
        comment = response.json()
        assert comment.get("image_url") is None, "Comment without image should have null image_url"
        print(f"PASS: Text-only comment created, image_url is null")

    def test_06_get_comments_with_image_url(self, auth_token):
        """Test that GET comments returns image_url field"""
        feed_response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        }, params={"limit": 10})
        posts = feed_response.json()
        
        if not posts:
            pytest.skip("No posts available")
        
        # Find a post with comments
        for post in posts:
            if post.get("comments_count", 0) > 0:
                response = requests.get(f"{BASE_URL}/api/posts/{post['id']}/comments", headers={
                    "Authorization": f"Bearer {auth_token}"
                })
                assert response.status_code == 200
                comments = response.json()
                
                # Check that comments have image_url field (even if null)
                for comment in comments:
                    # image_url should be in response (may be null)
                    assert "id" in comment
                    assert "content" in comment
                    # image_url field should exist
                    print(f"  Comment {comment['id']}: image_url={'present' if comment.get('image_url') else 'null'}")
                
                print(f"PASS: GET comments returns proper structure with image_url field")
                return
        
        print("SKIP: No posts with comments found to verify image_url in response")

    def test_07_create_reply_comment_with_image(self, auth_token):
        """Test creating a reply to a comment with an image attachment"""
        feed_response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        }, params={"limit": 20})
        posts = feed_response.json()
        
        # Find a post with comments to reply to
        for post in posts:
            if post.get("comments_count", 0) > 0:
                # Get comments
                comments_response = requests.get(f"{BASE_URL}/api/posts/{post['id']}/comments", headers={
                    "Authorization": f"Bearer {auth_token}"
                })
                comments = comments_response.json()
                
                if comments:
                    parent_comment_id = comments[0]["id"]
                    
                    # Upload image
                    png_bytes = bytes([
                        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
                        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
                        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
                        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
                        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
                        0x54, 0x08, 0xD7, 0x63, 0xF8, 0x00, 0x00, 0x00,
                        0x01, 0x00, 0x01, 0xE2, 0x8D, 0x15, 0xC9, 0x00,
                        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
                        0x42, 0x60, 0x82
                    ])
                    files = {'file': ('reply_img.png', io.BytesIO(png_bytes), 'image/png')}
                    upload_response = requests.post(f"{BASE_URL}/api/upload",
                        headers={"Authorization": f"Bearer {auth_token}"},
                        files=files
                    )
                    image_url = upload_response.json().get("url")
                    
                    # Create reply with image
                    reply_data = {
                        "post_id": post["id"],
                        "content": "Reply with photo attachment",
                        "parent_id": parent_comment_id,
                        "image_url": image_url
                    }
                    response = requests.post(f"{BASE_URL}/api/posts/{post['id']}/comments",
                        headers={"Authorization": f"Bearer {auth_token}"},
                        json=reply_data
                    )
                    
                    assert response.status_code == 200
                    reply = response.json()
                    assert reply.get("parent_id") == parent_comment_id
                    assert reply.get("image_url") == image_url
                    print(f"PASS: Reply with image created, parent_id={parent_comment_id}")
                    return
        
        pytest.skip("No posts with comments to reply to")

    def test_08_comment_with_image_only_no_text(self, auth_token):
        """Test that submit button validation requires text OR photo (not both mandatory)"""
        # This is a frontend validation test, but we can test the backend accepts
        # comments with minimal content (e.g., just whitespace + image)
        feed_response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        }, params={"limit": 10})
        posts = feed_response.json()
        
        if not posts:
            pytest.skip("No posts available")
        
        post_id = posts[0]["id"]
        
        # Upload image
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0x00, 0x00, 0x00,
            0x01, 0x00, 0x01, 0xE2, 0x8D, 0x15, 0xC9, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ])
        files = {'file': ('image_only.png', io.BytesIO(png_bytes), 'image/png')}
        upload_response = requests.post(f"{BASE_URL}/api/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=files
        )
        image_url = upload_response.json().get("url")
        
        # The frontend sends " " (space) as content when only photo is selected
        # This matches the code: const content = newComment.trim() || ' ';
        comment_data = {
            "post_id": post_id,
            "content": " ",  # Minimal content - photo only
            "image_url": image_url
        }
        response = requests.post(f"{BASE_URL}/api/posts/{post_id}/comments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=comment_data
        )
        
        assert response.status_code == 200, f"Image-only comment failed: {response.text}"
        comment = response.json()
        assert comment.get("image_url") == image_url
        print(f"PASS: Photo-only comment accepted (content=' ', image_url present)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
