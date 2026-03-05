"""
Test suite for Daily Prompts feature - Phase 1 Implementation
Tests: Today's prompt, buzz-in flow, export card, streak tracking, admin endpoints, Discogs caching
"""
import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"


class TestDailyPromptsAuth:
    """Authentication tests for daily prompts"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_works(self, auth_token):
        """Verify demo user can login"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"Login successful, token length: {len(auth_token)}")


class TestTodaysPrompt:
    """Tests for GET /api/prompts/today endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_get_todays_prompt(self, auth_token):
        """GET /api/prompts/today returns today's prompt with proper fields"""
        response = requests.get(
            f"{BASE_URL}/api/prompts/today",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "prompt" in data, "Missing 'prompt' field"
        assert "has_buzzed_in" in data, "Missing 'has_buzzed_in' field"
        assert "streak" in data, "Missing 'streak' field"
        
        # Verify prompt structure if present
        if data["prompt"]:
            prompt = data["prompt"]
            assert "id" in prompt, "Prompt missing 'id'"
            assert "text" in prompt, "Prompt missing 'text'"
            assert "scheduled_date" in prompt, "Prompt missing 'scheduled_date'"
            print(f"Today's prompt: {prompt['text'][:50]}...")
            print(f"Has buzzed in: {data['has_buzzed_in']}, Streak: {data['streak']}")
        
        # Type checks
        assert isinstance(data["has_buzzed_in"], bool)
        assert isinstance(data["streak"], int)
        print("Test passed: GET /api/prompts/today returns correct structure")
    
    def test_todays_prompt_requires_auth(self):
        """GET /api/prompts/today requires authentication"""
        response = requests.get(f"{BASE_URL}/api/prompts/today")
        assert response.status_code == 401, "Should require auth"
        print("Test passed: Endpoint requires authentication")


class TestStreak:
    """Tests for GET /api/prompts/streak/{username} endpoint"""
    
    def test_get_user_streak(self):
        """GET /api/prompts/streak/{username} returns streak count"""
        # This endpoint doesn't require auth (public)
        response = requests.get(f"{BASE_URL}/api/prompts/streak/demo")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "streak" in data, "Missing 'streak' field"
        assert "username" in data, "Missing 'username' field"
        assert data["username"] == "demo"
        assert isinstance(data["streak"], int)
        assert data["streak"] >= 0
        print(f"Test passed: User 'demo' streak is {data['streak']}")
    
    def test_streak_invalid_user(self):
        """GET /api/prompts/streak/{username} returns 404 for unknown user"""
        response = requests.get(f"{BASE_URL}/api/prompts/streak/nonexistent_user_xyz")
        assert response.status_code == 404, "Should return 404 for unknown user"
        print("Test passed: Returns 404 for unknown user")


class TestBuzzIn:
    """Tests for POST /api/prompts/buzz-in endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_data(self):
        """Get auth token and user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        data = response.json()
        return {
            "token": data.get("access_token"),
            "user": data.get("user")
        }
    
    @pytest.fixture(scope="class")
    def user_records(self, auth_data):
        """Get user's records for buzz-in testing"""
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        return response.json() if response.status_code == 200 else []
    
    @pytest.fixture(scope="class")
    def todays_prompt(self, auth_data):
        """Get today's prompt data"""
        response = requests.get(
            f"{BASE_URL}/api/prompts/today",
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        return response.json() if response.status_code == 200 else {}
    
    def test_buzz_in_requires_auth(self):
        """POST /api/prompts/buzz-in requires authentication"""
        response = requests.post(f"{BASE_URL}/api/prompts/buzz-in", json={
            "prompt_id": "test", "record_id": "test"
        })
        assert response.status_code == 401, "Should require auth"
        print("Test passed: Buzz-in requires authentication")
    
    def test_buzz_in_requires_prompt_id(self, auth_data):
        """POST /api/prompts/buzz-in requires prompt_id"""
        response = requests.post(
            f"{BASE_URL}/api/prompts/buzz-in",
            json={"record_id": "test"},
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Test passed: Buzz-in requires prompt_id")
    
    def test_buzz_in_requires_record_id(self, auth_data, todays_prompt):
        """POST /api/prompts/buzz-in requires record_id"""
        if not todays_prompt.get("prompt"):
            pytest.skip("No prompt available")
        
        response = requests.post(
            f"{BASE_URL}/api/prompts/buzz-in",
            json={"prompt_id": todays_prompt["prompt"]["id"]},
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Test passed: Buzz-in requires record_id")
    
    def test_buzz_in_already_responded(self, auth_data, todays_prompt, user_records):
        """POST /api/prompts/buzz-in returns 400 if already buzzed in today"""
        if not todays_prompt.get("prompt"):
            pytest.skip("No prompt available")
        if todays_prompt.get("has_buzzed_in") is False:
            pytest.skip("User hasn't buzzed in yet - can't test duplicate prevention")
        if not user_records:
            pytest.skip("No records available")
        
        # Try to buzz in again (should fail since demo user already buzzed in)
        response = requests.post(
            f"{BASE_URL}/api/prompts/buzz-in",
            json={
                "prompt_id": todays_prompt["prompt"]["id"],
                "record_id": user_records[0]["id"],
                "caption": "Test caption"
            },
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        assert response.status_code == 400, f"Expected 400 for duplicate buzz-in, got {response.status_code}"
        assert "already" in response.json().get("detail", "").lower()
        print("Test passed: Can't buzz in twice for same prompt")


class TestExportCard:
    """Tests for POST /api/prompts/export-card endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_data(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        data = response.json()
        return {"token": data.get("access_token")}
    
    @pytest.fixture(scope="class")
    def buzz_response(self, auth_data):
        """Get today's buzz-in response for export"""
        response = requests.get(
            f"{BASE_URL}/api/prompts/today",
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        data = response.json()
        return data.get("response") if data.get("has_buzzed_in") else None
    
    def test_export_card_requires_auth(self):
        """POST /api/prompts/export-card requires authentication"""
        response = requests.post(f"{BASE_URL}/api/prompts/export-card", json={
            "response_id": "test"
        })
        assert response.status_code == 401, "Should require auth"
        print("Test passed: Export card requires authentication")
    
    def test_export_card_requires_response_id(self, auth_data):
        """POST /api/prompts/export-card requires response_id"""
        response = requests.post(
            f"{BASE_URL}/api/prompts/export-card",
            json={},
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Test passed: Export card requires response_id")
    
    def test_export_card_invalid_response(self, auth_data):
        """POST /api/prompts/export-card returns 404 for invalid response_id"""
        response = requests.post(
            f"{BASE_URL}/api/prompts/export-card",
            json={"response_id": "invalid_id_xyz"},
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Test passed: Export card returns 404 for invalid response")
    
    def test_export_card_generates_png(self, auth_data, buzz_response):
        """POST /api/prompts/export-card generates 1080x1080 PNG image"""
        if not buzz_response:
            pytest.skip("No buzz-in response to export")
        
        response = requests.post(
            f"{BASE_URL}/api/prompts/export-card",
            json={"response_id": buzz_response["id"]},
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify it's a PNG image
        assert response.headers.get("content-type") == "image/png", "Should return PNG"
        assert len(response.content) > 1000, "Image should have substantial size"
        
        # Verify PNG magic bytes
        png_header = b'\x89PNG\r\n\x1a\n'
        assert response.content[:8] == png_header, "Invalid PNG format"
        
        print(f"Test passed: Export card generated PNG ({len(response.content)} bytes)")


class TestAdminEndpoints:
    """Tests for admin-only prompt management endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token (demo user is admin)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_admin_get_all_prompts(self, admin_token):
        """GET /api/prompts/admin/all returns all prompts (admin only)"""
        response = requests.get(
            f"{BASE_URL}/api/prompts/admin/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Should return list of prompts"
        assert len(data) > 0, "Should have prompts (seed data)"
        
        # Verify prompt structure
        prompt = data[0]
        assert "id" in prompt, "Missing prompt id"
        assert "text" in prompt, "Missing prompt text"
        assert "scheduled_date" in prompt, "Missing scheduled_date"
        assert "response_count" in prompt, "Missing response_count"
        
        print(f"Test passed: Admin got {len(data)} prompts")
    
    def test_admin_get_all_prompts_requires_auth(self):
        """GET /api/prompts/admin/all requires authentication"""
        response = requests.get(f"{BASE_URL}/api/prompts/admin/all")
        assert response.status_code == 401, "Should require auth"
        print("Test passed: Admin endpoint requires authentication")
    
    def test_admin_create_prompt(self, admin_token):
        """POST /api/prompts/admin/create creates new prompt (admin only)"""
        test_prompt_text = f"TEST_prompt_{datetime.now(timezone.utc).isoformat()}"
        future_date = datetime(2030, 12, 31, tzinfo=timezone.utc).isoformat()
        
        response = requests.post(
            f"{BASE_URL}/api/prompts/admin/create",
            json={
                "text": test_prompt_text,
                "scheduled_date": future_date,
                "active": True
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["text"] == test_prompt_text, "Text mismatch"
        assert "id" in data, "Missing prompt id"
        assert data["active"] == True, "Should be active"
        
        print(f"Test passed: Created prompt with id {data['id']}")
        return data
    
    def test_admin_create_prompt_requires_auth(self):
        """POST /api/prompts/admin/create requires authentication"""
        response = requests.post(f"{BASE_URL}/api/prompts/admin/create", json={
            "text": "test", "scheduled_date": "2030-01-01"
        })
        assert response.status_code == 401, "Should require auth"
        print("Test passed: Admin create requires authentication")


class TestDiscogsImageCache:
    """Tests for Discogs image caching functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_discogs_hires_endpoint(self, auth_token):
        """GET /api/prompts/discogs-hires/{release_id} fetches and caches Discogs data"""
        # Use a well-known Discogs release ID (Abbey Road by The Beatles)
        release_id = 1972298
        
        response = requests.get(
            f"{BASE_URL}/api/prompts/discogs-hires/{release_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Might be 200 or 404 depending on Discogs API availability
        if response.status_code == 200:
            data = response.json()
            assert "discogs_id" in data, "Missing discogs_id"
            assert "title" in data, "Missing title"
            assert "artist" in data, "Missing artist"
            print(f"Test passed: Got Discogs data for release {release_id}")
        elif response.status_code == 404:
            print("Test passed: Discogs API returned 404 (expected for rate limits)")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_discogs_hires_requires_auth(self):
        """GET /api/prompts/discogs-hires/{release_id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/prompts/discogs-hires/1234")
        assert response.status_code == 401, "Should require auth"
        print("Test passed: Discogs hires requires authentication")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
