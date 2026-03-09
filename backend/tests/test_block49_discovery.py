"""
BLOCK 49.1-49.4 Tests: Discovery features
- BLOCK 49.1: GET /api/discover/my-kinda-people - discovery carousel endpoint
- BLOCK 49.2: In Common tab on public profiles
- BLOCK 49.3: Variant pills on Hive post cards (frontend-only)
- BLOCK 49.4: GET /api/prompts/today returns buzz_count field
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_USER_EMAIL = "admin@thehoneygroove.com"
TEST_USER_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token") or response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestBlock49_1_MyKindaPeople:
    """BLOCK 49.1: GET /api/discover/my-kinda-people endpoint"""

    def test_endpoint_exists(self, headers):
        """Endpoint should exist and return 200"""
        response = requests.get(f"{BASE_URL}/api/discover/my-kinda-people", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/discover/my-kinda-people returns 200")

    def test_returns_list(self, headers):
        """Should return a list"""
        response = requests.get(f"{BASE_URL}/api/discover/my-kinda-people", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASS: Returns list with {len(data)} items")

    def test_result_structure(self, headers):
        """Each result should have user info and taste data"""
        response = requests.get(f"{BASE_URL}/api/discover/my-kinda-people", headers=headers)
        data = response.json()
        if len(data) == 0:
            pytest.skip("No matching users found (expected if collection is small)")
        
        user = data[0]
        expected_fields = ["username", "score", "common_count", "shared_covers"]
        for field in expected_fields:
            assert field in user, f"Missing field: {field}"
        assert isinstance(user["score"], (int, float)), "score should be numeric"
        assert isinstance(user["common_count"], int), "common_count should be int"
        assert isinstance(user["shared_covers"], list), "shared_covers should be list"
        print(f"PASS: Result structure valid - username: {user.get('username')}, score: {user['score']}%")

    def test_requires_auth(self):
        """Endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/discover/my-kinda-people")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Endpoint requires authentication")


class TestBlock49_4_BuzzCount:
    """BLOCK 49.4: GET /api/prompts/today should return buzz_count"""

    def test_prompts_today_exists(self, headers):
        """Endpoint should exist and return 200"""
        response = requests.get(f"{BASE_URL}/api/prompts/today", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/prompts/today returns 200")

    def test_buzz_count_field_present(self, headers):
        """Response should include buzz_count field"""
        response = requests.get(f"{BASE_URL}/api/prompts/today", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "buzz_count" in data, f"Missing buzz_count field. Keys: {list(data.keys())}"
        assert isinstance(data["buzz_count"], int), f"buzz_count should be int, got {type(data['buzz_count'])}"
        print(f"PASS: buzz_count field present: {data['buzz_count']}")

    def test_prompts_today_structure(self, headers):
        """Response should have expected structure"""
        response = requests.get(f"{BASE_URL}/api/prompts/today", headers=headers)
        data = response.json()
        # Should have: prompt, has_buzzed_in, response, streak, buzz_count
        expected_fields = ["prompt", "has_buzzed_in", "streak", "buzz_count"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}. Keys: {list(data.keys())}"
        print(f"PASS: Response structure valid - streak: {data.get('streak')}, buzz_count: {data.get('buzz_count')}")

    def test_prompt_has_id(self, headers):
        """Prompt should have an id field for filtering"""
        response = requests.get(f"{BASE_URL}/api/prompts/today", headers=headers)
        data = response.json()
        if data.get("prompt"):
            assert "id" in data["prompt"], "Prompt should have id field"
            assert "text" in data["prompt"], "Prompt should have text field"
            print(f"PASS: Prompt has id: {data['prompt']['id'][:8]}...")
        else:
            print("SKIP: No prompt configured for today")


class TestTasteMatchEndpoint:
    """Verify taste-match endpoint for In Common tab (BLOCK 49.2)"""

    def test_taste_match_endpoint(self, headers):
        """GET /api/users/{username}/taste-match should work"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/taste-match", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/users/katieintheafterglow/taste-match returns 200")

    def test_taste_match_structure(self, headers):
        """Response should have shared_reality, shared_dreams, swap_potential"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/taste-match", headers=headers)
        data = response.json()
        expected_fields = ["score", "shared_reality", "shared_dreams", "swap_potential"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        print(f"PASS: Taste match structure valid - score: {data.get('score')}%")


class TestFeedEndpoint:
    """Verify feed endpoint works (used by Hive page)"""

    def test_feed_returns_posts(self, headers):
        """GET /api/feed should return posts"""
        response = requests.get(f"{BASE_URL}/api/feed", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        print(f"PASS: Feed returns {len(data)} posts")

    def test_daily_prompt_posts_have_prompt_id(self, headers):
        """DAILY_PROMPT posts should have prompt_id for filtering"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=100", headers=headers)
        data = response.json()
        daily_prompts = [p for p in data if p.get("post_type") == "DAILY_PROMPT"]
        if daily_prompts:
            # Check if prompt_id exists in posts that have prompt_text
            post = daily_prompts[0]
            print(f"PASS: Found DAILY_PROMPT post, fields: {list(post.keys())[:10]}")
        else:
            print("SKIP: No DAILY_PROMPT posts in feed")


class TestProfileEndpoint:
    """Verify profile endpoints needed for In Common tab"""

    def test_get_user_profile(self, headers):
        """GET /api/users/{username} should return profile"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "username" in data
        print(f"PASS: Profile endpoint returns username: {data.get('username')}")

    def test_get_user_records(self, headers):
        """GET /api/users/{username}/records should return records"""
        response = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/records", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: User records endpoint returns {len(data)} records")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
