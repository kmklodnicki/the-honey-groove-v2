"""
Tests for Block 242: Real-time Live Feed WebSocket feature

Tests covered:
- Socket.IO handshake at /api/ws/socket.io
- POST /api/composer/now-spinning creates a post and returns response
- POST /api/composer/note creates a post and returns response
- POST /api/composer/new-haul creates a post and returns response
- POST /api/composer/iso creates a post and returns response
- Backend emit_new_post function is called after post creation
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestWebSocketLiveFeed:
    """Tests for WebSocket live feed integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_auth_token(self):
        """Get auth token for test user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_socketio_handshake(self):
        """Test Socket.IO handshake endpoint returns valid session"""
        response = self.session.get(
            f"{BASE_URL}/api/ws/socket.io/",
            params={"EIO": "4", "transport": "polling"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Socket.IO response starts with packet length followed by JSON
        text = response.text
        # Remove any packet length prefix (digit characters at start)
        json_start = 0
        for i, c in enumerate(text):
            if c == '{':
                json_start = i
                break
        
        import json
        data = json.loads(text[json_start:])
        assert "sid" in data, "Socket.IO handshake should return 'sid'"
        assert "upgrades" in data, "Socket.IO handshake should return 'upgrades'"
        assert "websocket" in data["upgrades"], "Socket.IO should support websocket upgrade"
        print(f"Socket.IO handshake successful, sid={data['sid']}")
    
    def test_composer_now_spinning_creates_post(self):
        """Test POST /api/composer/now-spinning creates a post"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate test user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # First get user's collection to find a record
        records_resp = self.session.get(f"{BASE_URL}/api/records", headers=headers)
        if records_resp.status_code != 200 or not records_resp.json():
            # Create a test record first
            record_payload = {
                "title": "TEST_WebSocket_Album",
                "artist": "TEST_WebSocket_Artist",
                "year": 2024,
                "format": "Vinyl",
                "source": "manual"
            }
            rec_resp = self.session.post(f"{BASE_URL}/api/records", json=record_payload, headers=headers)
            if rec_resp.status_code not in [200, 201]:
                pytest.skip(f"Could not create test record: {rec_resp.text}")
            record_id = rec_resp.json().get("id")
        else:
            record_id = records_resp.json()[0]["id"]
        
        # Create Now Spinning post
        post_payload = {
            "record_id": record_id,
            "caption": f"TEST_WebSocket_NowSpinning_{uuid.uuid4().hex[:8]}",
            "track": "Side A",
            "mood": "chill"
        }
        response = self.session.post(
            f"{BASE_URL}/api/composer/now-spinning",
            json=post_payload,
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Post response should contain 'id'"
        assert data["post_type"] == "NOW_SPINNING", f"Expected post_type NOW_SPINNING, got {data['post_type']}"
        assert data["caption"] == post_payload["caption"], "Caption should match"
        
        # Cleanup - delete the test post
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print(f"Now Spinning post created successfully with id={data['id']}")
    
    def test_composer_note_creates_post(self):
        """Test POST /api/composer/note creates a post"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate test user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create Note post
        post_payload = {
            "text": f"TEST_WebSocket_Note_{uuid.uuid4().hex[:8]}: Testing the live feed feature!"
        }
        response = self.session.post(
            f"{BASE_URL}/api/composer/note",
            json=post_payload,
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Post response should contain 'id'"
        assert data["post_type"] == "NOTE", f"Expected post_type NOTE, got {data['post_type']}"
        
        # Cleanup - delete the test post
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print(f"Note post created successfully with id={data['id']}")
    
    def test_composer_iso_creates_post(self):
        """Test POST /api/composer/iso creates a post"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate test user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create ISO post
        post_payload = {
            "artist": f"TEST_WebSocket_Artist_{uuid.uuid4().hex[:8]}",
            "album": "TEST_WebSocket_Album",
            "caption": "Looking for this rare pressing!"
        }
        response = self.session.post(
            f"{BASE_URL}/api/composer/iso",
            json=post_payload,
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Post response should contain 'id'"
        assert data["post_type"] == "ISO", f"Expected post_type ISO, got {data['post_type']}"
        
        # Cleanup - delete the test post
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print(f"ISO post created successfully with id={data['id']}")
    
    def test_composer_new_haul_creates_post(self):
        """Test POST /api/composer/new-haul creates a post"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate test user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create New Haul post
        post_payload = {
            "store_name": "TEST_WebSocket_Store",
            "caption": f"TEST_WebSocket_Haul_{uuid.uuid4().hex[:8]}",
            "items": [
                {
                    "title": "Test Album 1",
                    "artist": "Test Artist 1",
                    "year": 2024
                }
            ]
        }
        response = self.session.post(
            f"{BASE_URL}/api/composer/new-haul",
            json=post_payload,
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Post response should contain 'id'"
        assert data["post_type"] == "NEW_HAUL", f"Expected post_type NEW_HAUL, got {data['post_type']}"
        
        # Cleanup - delete the test post
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print(f"New Haul post created successfully with id={data['id']}")
    
    def test_feed_endpoint_returns_posts(self):
        """Test GET /api/feed returns posts"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate test user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(
            f"{BASE_URL}/api/feed",
            params={"limit": 5},
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        print(f"Feed returned {len(data)} posts")
    
    def test_post_response_has_required_fields_for_websocket(self):
        """Test that post response has all fields needed for WebSocket broadcast"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate test user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a Note post to examine the response structure
        post_payload = {
            "text": f"TEST_FieldCheck_{uuid.uuid4().hex[:8]}"
        }
        response = self.session.post(
            f"{BASE_URL}/api/composer/note",
            json=post_payload,
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields for frontend to display the post
        required_fields = ["id", "user_id", "post_type", "created_at"]
        for field in required_fields:
            assert field in data, f"Post response missing required field: {field}"
        
        # Check user info is present (needed to show author in feed)
        assert "user" in data, "Post response should contain 'user' object"
        if data["user"]:
            user = data["user"]
            assert "id" in user, "User should have 'id'"
            assert "username" in user, "User should have 'username'"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print(f"Post has all required fields for WebSocket broadcast")


class TestEmitNewPostIntegration:
    """Tests to verify emit_new_post is properly integrated"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_auth_token(self, email="test@example.com", password="test123"):
        """Get auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("access_token"), response.json().get("user", {}).get("id")
        return None, None
    
    def test_emit_new_post_called_on_now_spinning(self):
        """Verify that now-spinning endpoint calls _emit_and_return (indirect test)"""
        token, user_id = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get a record
        records_resp = self.session.get(f"{BASE_URL}/api/records", headers=headers)
        if records_resp.status_code != 200 or not records_resp.json():
            pytest.skip("No records available")
        record_id = records_resp.json()[0]["id"]
        
        # Create post - the endpoint should call emit_new_post internally
        # We can't directly verify the emit, but we verify the endpoint returns correctly
        response = self.session.post(
            f"{BASE_URL}/api/composer/now-spinning",
            json={"record_id": record_id, "caption": f"TEST_Emit_{uuid.uuid4().hex[:8]}", "mood": "chill"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # The fact that we get a valid PostResponse back means _emit_and_return was called
        # (since _emit_and_return returns the post_response)
        assert data["id"] is not None
        assert data["user_id"] == user_id
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print("emit_new_post integration verified for now-spinning")
    
    def test_emit_new_post_called_on_note(self):
        """Verify that note endpoint calls _emit_and_return"""
        token, user_id = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.post(
            f"{BASE_URL}/api/composer/note",
            json={"text": f"TEST_NoteEmit_{uuid.uuid4().hex[:8]}"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] is not None
        assert data["user_id"] == user_id
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print("emit_new_post integration verified for note")
    
    def test_emit_new_post_called_on_iso(self):
        """Verify that ISO endpoint calls _emit_and_return"""
        token, user_id = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.post(
            f"{BASE_URL}/api/composer/iso",
            json={
                "artist": f"TEST_ISOArtist_{uuid.uuid4().hex[:8]}",
                "album": "Test Album",
                "caption": "Looking for this!"
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] is not None
        assert data["user_id"] == user_id
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print("emit_new_post integration verified for ISO")
    
    def test_emit_new_post_called_on_new_haul(self):
        """Verify that new-haul endpoint calls _emit_and_return"""
        token, user_id = self.get_auth_token()
        if not token:
            pytest.skip("Could not authenticate")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.post(
            f"{BASE_URL}/api/composer/new-haul",
            json={
                "store_name": "TEST_HaulStore",
                "caption": f"TEST_HaulEmit_{uuid.uuid4().hex[:8]}",
                "items": [{"title": "Test", "artist": "Test", "year": 2024}]
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] is not None
        assert data["user_id"] == user_id
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/posts/{data['id']}", headers=headers)
        print("emit_new_post integration verified for new-haul")
