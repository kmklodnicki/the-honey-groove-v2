"""
Backend tests for Phase 2 features: Collector Bingo and Mood Board
Tests all endpoints for:
- Collector Bingo: /api/bingo/current, /api/bingo/mark, /api/bingo/export
- Mood Board: /api/mood-boards/generate, /api/mood-boards/history/{username}, /api/mood-boards/{board_id}/image
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"


class TestAuth:
    """Helper class to manage authentication"""
    
    @staticmethod
    def get_token():
        """Get auth token - returns access_token field"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")  # Note: API returns 'access_token' not 'token'
        return None


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for all tests"""
    token = TestAuth.get_token()
    if not token:
        pytest.skip("Authentication failed - skipping tests")
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Create auth headers with token"""
    return {"Authorization": f"Bearer {auth_token}"}


# ==================== COLLECTOR BINGO TESTS ====================

class TestCollectorBingo:
    """Test Collector Bingo endpoints"""

    def test_get_current_bingo_no_auth(self):
        """Test that /api/bingo/current requires authentication"""
        response = requests.get(f"{BASE_URL}/api/bingo/current")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/bingo/current requires authentication")

    def test_get_current_bingo(self, auth_headers):
        """Test GET /api/bingo/current returns weekly bingo card"""
        response = requests.get(f"{BASE_URL}/api/bingo/current", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "card" in data, "Response should have 'card' field"
        assert "marks" in data, "Response should have 'marks' field"
        assert "has_bingo" in data, "Response should have 'has_bingo' field"
        assert "is_locked" in data, "Response should have 'is_locked' field"
        
        # Verify card structure
        card = data["card"]
        assert "grid" in card, "Card should have 'grid' field"
        assert "week_start" in card, "Card should have 'week_start' field"
        assert "week_end" in card, "Card should have 'week_end' field"
        
        # Verify grid is 5x5 (25 squares)
        grid = card["grid"]
        assert len(grid) == 25, f"Grid should have 25 squares, got {len(grid)}"
        
        # Verify free space is at center (index 12)
        free_space = grid[12]
        assert free_space.get("is_free") == True, "Center square (index 12) should be free space"
        
        # Verify marks includes the free space (12)
        marks = data["marks"]
        assert 12 in marks, "Marks should include free space (index 12)"
        
        print(f"PASS: GET /api/bingo/current returns valid bingo card with {len(grid)} squares")
        print(f"  - is_locked: {data['is_locked']}, has_bingo: {data['has_bingo']}")
        print(f"  - marks: {marks}")

    def test_bingo_mark_toggle(self, auth_headers):
        """Test POST /api/bingo/mark - toggle a square mark"""
        # First get current bingo to check if locked
        current = requests.get(f"{BASE_URL}/api/bingo/current", headers=auth_headers)
        current_data = current.json()
        
        if current_data.get("is_locked"):
            print("SKIP: Bingo card is locked (expected behavior outside Friday-Sunday)")
            # Try marking anyway to verify locked message
            response = requests.post(f"{BASE_URL}/api/bingo/mark", 
                                     json={"index": 0}, headers=auth_headers)
            assert response.status_code == 400, f"Expected 400 for locked card, got {response.status_code}"
            assert "locked" in response.text.lower(), "Should mention locked card"
            print("PASS: Marking on locked card correctly rejected")
            return
        
        # Card is not locked - test marking
        test_index = 0  # First square (not free space)
        response = requests.post(f"{BASE_URL}/api/bingo/mark", 
                                json={"index": test_index}, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "marks" in data, "Response should have 'marks' field"
        assert "has_bingo" in data, "Response should have 'has_bingo' field"
        
        print(f"PASS: POST /api/bingo/mark toggled square {test_index}")
        print(f"  - marks: {data['marks']}, has_bingo: {data['has_bingo']}")

    def test_bingo_mark_free_space_rejected(self, auth_headers):
        """Test that marking free space (index 12) is rejected"""
        response = requests.post(f"{BASE_URL}/api/bingo/mark", 
                                json={"index": 12}, headers=auth_headers)
        # Should be rejected regardless of locked status
        assert response.status_code == 400, f"Expected 400 for free space, got {response.status_code}"
        assert "free" in response.text.lower() or "cannot" in response.text.lower(), \
            f"Should mention free space cannot be unmarked: {response.text}"
        print("PASS: Marking free space correctly rejected")

    def test_bingo_mark_invalid_index(self, auth_headers):
        """Test invalid square index rejection"""
        # Test index out of range
        response = requests.post(f"{BASE_URL}/api/bingo/mark", 
                                json={"index": 25}, headers=auth_headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Invalid index (25) correctly rejected")

        response = requests.post(f"{BASE_URL}/api/bingo/mark", 
                                json={"index": -1}, headers=auth_headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Invalid index (-1) correctly rejected")

    def test_bingo_mark_no_auth(self):
        """Test that /api/bingo/mark requires authentication"""
        response = requests.post(f"{BASE_URL}/api/bingo/mark", json={"index": 0})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/bingo/mark requires authentication")

    def test_bingo_export(self, auth_headers):
        """Test GET /api/bingo/export returns PNG image"""
        response = requests.get(f"{BASE_URL}/api/bingo/export", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify it's a PNG image
        content_type = response.headers.get("content-type", "")
        assert "image/png" in content_type, f"Expected image/png, got {content_type}"
        
        # Verify PNG signature
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n', "Response should start with PNG signature"
        
        print(f"PASS: GET /api/bingo/export returns PNG ({len(response.content)} bytes)")

    def test_bingo_export_no_auth(self):
        """Test that /api/bingo/export requires authentication"""
        response = requests.get(f"{BASE_URL}/api/bingo/export")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/bingo/export requires authentication")


# ==================== MOOD BOARD TESTS ====================

class TestMoodBoard:
    """Test Mood Board endpoints"""
    
    @pytest.fixture(scope="class")
    def test_username(self, auth_headers):
        """Get the test user's username"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        if response.status_code == 200:
            return response.json().get("username")
        return "demo"  # fallback

    def test_mood_board_history_no_auth(self):
        """Test that /api/mood-boards/history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/mood-boards/history/demo")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/mood-boards/history/{username} requires authentication")

    def test_mood_board_history(self, auth_headers, test_username):
        """Test GET /api/mood-boards/history/{username} returns list"""
        response = requests.get(f"{BASE_URL}/api/mood-boards/history/{test_username}", 
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            board = data[0]
            assert "id" in board, "Board should have 'id' field"
            assert "time_range" in board, "Board should have 'time_range' field"
            assert "records" in board, "Board should have 'records' field"
            assert "created_at" in board, "Board should have 'created_at' field"
            print(f"PASS: GET /api/mood-boards/history/{test_username} returns {len(data)} boards")
            print(f"  - Latest board: {board['time_range']}, {len(board.get('records', []))} records")
        else:
            print(f"PASS: GET /api/mood-boards/history/{test_username} returns empty list (no boards yet)")

    def test_mood_board_history_invalid_user(self, auth_headers):
        """Test mood board history for non-existent user"""
        response = requests.get(f"{BASE_URL}/api/mood-boards/history/nonexistent_user_12345", 
                               headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Mood board history for non-existent user returns 404")

    def test_mood_board_generate_no_auth(self):
        """Test that /api/mood-boards/generate requires authentication"""
        response = requests.post(f"{BASE_URL}/api/mood-boards/generate", 
                                json={"time_range": "week"})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/mood-boards/generate requires authentication")

    def test_mood_board_generate_week(self, auth_headers):
        """Test POST /api/mood-boards/generate with time_range='week'"""
        response = requests.post(f"{BASE_URL}/api/mood-boards/generate", 
                                json={"time_range": "week"}, headers=auth_headers)
        
        # Could be 200 (success) or 400 (no spins found)
        if response.status_code == 400:
            # No spins - acceptable
            assert "no spins" in response.text.lower() or "not found" in response.text.lower(), \
                f"Expected 'no spins' message: {response.text}"
            print("PASS: Generate mood board (week) - no spins found (expected if user has no recent spins)")
            return None
        
        assert response.status_code == 200, f"Expected 200 or 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should have 'id' field"
        assert data.get("time_range") == "week", "time_range should be 'week'"
        
        # Verify records is 3x3 grid (up to 9 records)
        records = data.get("records", [])
        assert len(records) <= 9, f"Should have at most 9 records, got {len(records)}"
        
        print(f"PASS: POST /api/mood-boards/generate (week) created board with {len(records)} records")
        return data.get("id")

    def test_mood_board_generate_month(self, auth_headers):
        """Test POST /api/mood-boards/generate with time_range='month'"""
        response = requests.post(f"{BASE_URL}/api/mood-boards/generate", 
                                json={"time_range": "month"}, headers=auth_headers)
        
        if response.status_code == 400:
            print("PASS: Generate mood board (month) - no spins found")
            return
        
        assert response.status_code == 200, f"Expected 200 or 400, got {response.status_code}"
        data = response.json()
        assert data.get("time_range") == "month", "time_range should be 'month'"
        print(f"PASS: POST /api/mood-boards/generate (month) created board with {len(data.get('records', []))} records")

    def test_mood_board_generate_all_time(self, auth_headers):
        """Test POST /api/mood-boards/generate with time_range='all_time'"""
        response = requests.post(f"{BASE_URL}/api/mood-boards/generate", 
                                json={"time_range": "all_time"}, headers=auth_headers)
        
        if response.status_code == 400:
            print("PASS: Generate mood board (all_time) - no spins found")
            return
        
        assert response.status_code == 200, f"Expected 200 or 400, got {response.status_code}"
        data = response.json()
        assert data.get("time_range") == "all_time", "time_range should be 'all_time'"
        print(f"PASS: POST /api/mood-boards/generate (all_time) created board with {len(data.get('records', []))} records")

    def test_mood_board_generate_invalid_range(self, auth_headers):
        """Test that invalid time_range is rejected"""
        response = requests.post(f"{BASE_URL}/api/mood-boards/generate", 
                                json={"time_range": "invalid"}, headers=auth_headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Invalid time_range correctly rejected")

    def test_mood_board_image_export(self, auth_headers, test_username):
        """Test GET /api/mood-boards/{board_id}/image returns PNG"""
        # First get history to find a board
        history = requests.get(f"{BASE_URL}/api/mood-boards/history/{test_username}", 
                              headers=auth_headers)
        
        if history.status_code != 200 or len(history.json()) == 0:
            # Try to generate one first
            gen_response = requests.post(f"{BASE_URL}/api/mood-boards/generate", 
                                        json={"time_range": "all_time"}, headers=auth_headers)
            if gen_response.status_code == 200:
                board_id = gen_response.json().get("id")
            else:
                print("SKIP: No mood boards available to test export")
                return
        else:
            board_id = history.json()[0]["id"]
        
        # Test export
        response = requests.get(f"{BASE_URL}/api/mood-boards/{board_id}/image", 
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content_type = response.headers.get("content-type", "")
        assert "image/png" in content_type, f"Expected image/png, got {content_type}"
        
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n', "Response should start with PNG signature"
        
        print(f"PASS: GET /api/mood-boards/{board_id}/image returns PNG ({len(response.content)} bytes)")

    def test_mood_board_image_invalid_id(self, auth_headers):
        """Test mood board image for non-existent board"""
        response = requests.get(f"{BASE_URL}/api/mood-boards/invalid-board-id-12345/image", 
                               headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Mood board image for non-existent board returns 404")

    def test_mood_board_image_no_auth(self):
        """Test that /api/mood-boards/{board_id}/image requires authentication"""
        response = requests.get(f"{BASE_URL}/api/mood-boards/some-id/image")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/mood-boards/{board_id}/image requires authentication")


# ==================== HEALTH CHECK ====================

class TestHealth:
    """Basic health checks"""
    
    def test_api_accessible(self):
        """Test that the API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        # Health endpoint may or may not exist
        if response.status_code == 404:
            # Try login endpoint as health check
            response = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "", "password": ""})
            assert response.status_code in [400, 401, 422], "API should be responsive"
        else:
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("PASS: API is accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
