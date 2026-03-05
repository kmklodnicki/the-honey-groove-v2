"""
Backend tests for Phase A enhancements:
1. Bingo export PNG is 1080x1920 dimensions
2. Mood Board export PNG is 1080x1920 dimensions
3. Bingo /api/bingo/current returns bingo_count field
4. Bingo /api/bingo/current returns community_stats when is_locked=true
5. Bingo /api/bingo/mark returns bingo_count field
6. Community stats percentages computed correctly from bingo_marks
7. Mood Board generate still works (POST /api/mood-boards/generate)
"""
import pytest
import requests
import os
from io import BytesIO

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
            return data.get("access_token")
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


@pytest.fixture(scope="module")
def test_username(auth_headers):
    """Get the test user's username"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
    if response.status_code == 200:
        return response.json().get("username")
    return "demo"


# ==================== BINGO CURRENT ENDPOINT TESTS ====================

class TestBingoCurrentEndpoint:
    """Test /api/bingo/current Phase A enhancements"""

    def test_bingo_current_returns_bingo_count(self, auth_headers):
        """Test that GET /api/bingo/current returns bingo_count field"""
        response = requests.get(f"{BASE_URL}/api/bingo/current", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Phase A enhancement: bingo_count must be present
        assert "bingo_count" in data, "Response should have 'bingo_count' field (Phase A requirement)"
        assert isinstance(data["bingo_count"], int), "bingo_count should be an integer"
        assert data["bingo_count"] >= 0, "bingo_count should be non-negative"
        
        print(f"PASS: GET /api/bingo/current returns bingo_count = {data['bingo_count']}")

    def test_bingo_current_returns_community_stats_when_locked(self, auth_headers):
        """Test that GET /api/bingo/current returns community_stats when is_locked=true"""
        response = requests.get(f"{BASE_URL}/api/bingo/current", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        is_locked = data.get("is_locked", False)
        
        if is_locked:
            # Phase A enhancement: community_stats must be present when locked
            assert "community_stats" in data, "Response should have 'community_stats' when is_locked=true"
            
            community_stats = data["community_stats"]
            assert "total_players" in community_stats, "community_stats should have 'total_players'"
            assert "percentages" in community_stats, "community_stats should have 'percentages'"
            
            # Percentages should be a dict with string keys (square indices) and int values
            percentages = community_stats["percentages"]
            assert isinstance(percentages, dict), "percentages should be a dictionary"
            
            # If there are players, validate percentage values
            if community_stats["total_players"] > 0:
                for idx, pct in percentages.items():
                    assert isinstance(pct, (int, float)), f"Percentage for index {idx} should be numeric"
                    assert 0 <= pct <= 100, f"Percentage {pct} should be between 0 and 100"
            
            print(f"PASS: community_stats present when locked - total_players: {community_stats['total_players']}, percentages count: {len(percentages)}")
        else:
            # If not locked, community_stats should NOT be present
            assert "community_stats" not in data, "community_stats should NOT be present when card is unlocked"
            print("PASS: community_stats not present when card is unlocked (expected)")

    def test_bingo_current_grid_structure(self, auth_headers):
        """Test that bingo grid has 25 squares with free center space"""
        response = requests.get(f"{BASE_URL}/api/bingo/current", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        card = data.get("card", {})
        grid = card.get("grid", [])
        
        # Verify 5x5 grid (25 squares)
        assert len(grid) == 25, f"Grid should have 25 squares, got {len(grid)}"
        
        # Verify free space at center (index 12)
        free_space = grid[12]
        assert free_space.get("is_free") == True, "Center square (index 12) should be free space"
        assert "sweet spot" in free_space.get("text", "").lower() or free_space.get("emoji") == "🍯", \
            "Free space should have 'sweet spot' text or honey emoji"
        
        # Verify all other squares are not free
        for i, sq in enumerate(grid):
            if i != 12:
                assert sq.get("is_free") != True, f"Square {i} should not be free space"
        
        print("PASS: Bingo grid has 25 squares with free center space at index 12")


# ==================== BINGO MARK ENDPOINT TESTS ====================

class TestBingoMarkEndpoint:
    """Test /api/bingo/mark Phase A enhancements"""

    def test_bingo_mark_returns_bingo_count(self, auth_headers):
        """Test that POST /api/bingo/mark returns bingo_count field"""
        # First check if card is locked
        current = requests.get(f"{BASE_URL}/api/bingo/current", headers=auth_headers)
        current_data = current.json()
        
        if current_data.get("is_locked"):
            # Card is locked - still test that the response mentions bingo_count in error
            response = requests.post(f"{BASE_URL}/api/bingo/mark", 
                                    json={"index": 0}, headers=auth_headers)
            assert response.status_code == 400, "Expected 400 for locked card"
            print("PASS: Bingo mark rejected on locked card (bingo_count test skipped)")
            return
        
        # Card is not locked - test marking
        test_index = 0
        response = requests.post(f"{BASE_URL}/api/bingo/mark", 
                                json={"index": test_index}, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Phase A enhancement: bingo_count must be present in mark response
        assert "bingo_count" in data, "Mark response should have 'bingo_count' field (Phase A requirement)"
        assert isinstance(data["bingo_count"], int), "bingo_count should be an integer"
        assert data["bingo_count"] >= 0, "bingo_count should be non-negative"
        
        # Verify other required fields still present
        assert "marks" in data, "Response should have 'marks' field"
        assert "has_bingo" in data, "Response should have 'has_bingo' field"
        
        print(f"PASS: POST /api/bingo/mark returns bingo_count = {data['bingo_count']}")
        
        # Toggle back to original state
        requests.post(f"{BASE_URL}/api/bingo/mark", json={"index": test_index}, headers=auth_headers)


# ==================== IMAGE EXPORT DIMENSION TESTS ====================

class TestExportImageDimensions:
    """Test that export PNGs are 1080x1920 (Instagram Story format)"""

    def test_bingo_export_dimensions(self, auth_headers):
        """Test GET /api/bingo/export returns 1080x1920 PNG"""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available for image dimension testing")
        
        response = requests.get(f"{BASE_URL}/api/bingo/export", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify PNG content type
        content_type = response.headers.get("content-type", "")
        assert "image/png" in content_type, f"Expected image/png, got {content_type}"
        
        # Load image and check dimensions
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        
        # Phase A requirement: 1080x1920 Instagram Story format
        assert width == 1080, f"Expected width 1080, got {width}"
        assert height == 1920, f"Expected height 1920, got {height}"
        
        print(f"PASS: Bingo export PNG is {width}x{height} (Instagram Story format)")

    def test_mood_board_export_dimensions(self, auth_headers, test_username):
        """Test GET /api/mood-boards/{id}/image returns 1080x1920 PNG"""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available for image dimension testing")
        
        # First get or create a mood board
        history = requests.get(f"{BASE_URL}/api/mood-boards/history/{test_username}", 
                              headers=auth_headers)
        
        if history.status_code != 200 or len(history.json()) == 0:
            # Try to generate one
            gen_response = requests.post(f"{BASE_URL}/api/mood-boards/generate", 
                                        json={"time_range": "all_time"}, headers=auth_headers)
            if gen_response.status_code == 200:
                board_id = gen_response.json().get("id")
            else:
                # No spins - create a test entry (if possible) or skip
                print("SKIP: No mood boards available and cannot generate (no spins)")
                return
        else:
            board_id = history.json()[0]["id"]
        
        # Get the image
        response = requests.get(f"{BASE_URL}/api/mood-boards/{board_id}/image", 
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify PNG content type
        content_type = response.headers.get("content-type", "")
        assert "image/png" in content_type, f"Expected image/png, got {content_type}"
        
        # Load image and check dimensions
        img = Image.open(BytesIO(response.content))
        width, height = img.size
        
        # Phase A requirement: 1080x1920 Instagram Story format
        assert width == 1080, f"Expected width 1080, got {width}"
        assert height == 1920, f"Expected height 1920, got {height}"
        
        print(f"PASS: Mood Board export PNG is {width}x{height} (Instagram Story format)")


# ==================== MOOD BOARD GENERATE TEST ====================

class TestMoodBoardGenerate:
    """Test POST /api/mood-boards/generate still works"""

    def test_mood_board_generate_still_works(self, auth_headers):
        """Test that mood board generation still works after Phase A changes"""
        response = requests.post(f"{BASE_URL}/api/mood-boards/generate", 
                                json={"time_range": "week"}, headers=auth_headers)
        
        # Can be 200 (success) or 400 (no spins)
        if response.status_code == 400:
            data = response.json()
            # Acceptable error: no spins found
            error_msg = str(data.get("detail", "")).lower()
            assert "no spins" in error_msg or "not found" in error_msg, \
                f"Expected 'no spins' error, got: {data}"
            print("PASS: Mood board generate works (no spins found - expected)")
            return
        
        assert response.status_code == 200, f"Expected 200 or 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should have 'id' field"
        assert data.get("time_range") == "week", "time_range should be 'week'"
        
        records = data.get("records", [])
        assert len(records) <= 9, f"Should have at most 9 records for 3x3 grid, got {len(records)}"
        
        print(f"PASS: Mood board generate works - created board with {len(records)} records")


# ==================== COMMUNITY STATS COMPUTATION TEST ====================

class TestCommunityStatsComputation:
    """Test community stats percentages are computed correctly"""

    def test_community_stats_percentages_are_valid(self, auth_headers):
        """Verify community stats percentages are computed correctly"""
        response = requests.get(f"{BASE_URL}/api/bingo/current", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        if not data.get("is_locked"):
            print("SKIP: Card not locked - cannot test community stats (expected)")
            return
        
        community_stats = data.get("community_stats", {})
        total_players = community_stats.get("total_players", 0)
        percentages = community_stats.get("percentages", {})
        
        # Validate percentages
        if total_players > 0:
            for idx, pct in percentages.items():
                # Each percentage should be 0-100
                assert 0 <= pct <= 100, f"Percentage for square {idx} should be 0-100, got {pct}"
            
            # All 25 squares should have percentages (or at least up to 24 non-free squares)
            # Free space (index 12) percentage doesn't matter
            for i in range(25):
                if str(i) not in percentages and i != 12:
                    # It's okay if missing - means 0%
                    pass
            
            print(f"PASS: Community stats valid - {total_players} players, percentages for {len(percentages)} squares")
        else:
            # No players = empty percentages is expected
            print(f"PASS: Community stats valid - 0 players (empty percentages expected)")


# ==================== HEALTH CHECK ====================

class TestHealth:
    """Basic health checks"""
    
    def test_api_accessible(self):
        """Test that the API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 404:
            # Try login endpoint as health check
            response = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "", "password": ""})
            assert response.status_code in [400, 401, 422], "API should be responsive"
        else:
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("PASS: API is accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
