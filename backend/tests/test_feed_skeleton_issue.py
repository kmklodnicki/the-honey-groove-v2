"""
Test suite for feed skeleton issue fixes - iteration 241
Tests:
1. GET /api/prompts/today - Daily Prompt card data with buzz_count and streak
2. POST /api/prompts/buzz-in - Buzz-in endpoint with prompt_id
3. GET /api/feed - Feed returns hydrated record data (no ghost records)
4. Admin Panel button layout - not an API test, tested via Playwright
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "HoneyGroove2026!"

class TestFeedSkeletonFixes:
    """Tests for feed skeleton and daily prompt fixes"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Note: API returns 'access_token' not 'token'
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_health_check(self):
        """Test backend health"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("Health check: PASS")
    
    def test_login_returns_token(self):
        """Test login returns access_token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify token field name
        assert "access_token" in data or "token" in data, f"Missing token field: {data.keys()}"
        print(f"Login successful, token field: {'access_token' if 'access_token' in data else 'token'}")
    
    def test_daily_prompt_today(self, auth_headers):
        """Test GET /api/prompts/today returns prompt with buzz_count and streak"""
        response = requests.get(f"{BASE_URL}/api/prompts/today", headers=auth_headers)
        assert response.status_code == 200, f"Prompts/today failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "prompt" in data, f"Missing 'prompt' field: {data.keys()}"
        assert "has_buzzed_in" in data, f"Missing 'has_buzzed_in' field"
        assert "streak" in data, f"Missing 'streak' field"
        assert "buzz_count" in data, f"Missing 'buzz_count' field"
        
        prompt = data.get("prompt")
        if prompt:
            assert "id" in prompt, f"Prompt missing 'id': {prompt.keys()}"
            assert "text" in prompt, f"Prompt missing 'text': {prompt.keys()}"
            print(f"Today's prompt: '{prompt['text'][:50]}...'")
            print(f"Buzz count: {data['buzz_count']}, Streak: {data['streak']}, Buzzed in: {data['has_buzzed_in']}")
        else:
            print("No prompt scheduled for today")
        
        return data
    
    def test_feed_returns_hydrated_posts(self, auth_headers):
        """Test GET /api/feed returns posts with hydrated record data (no ghost records)"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=20", headers=auth_headers)
        assert response.status_code == 200, f"Feed failed: {response.text}"
        posts = response.json()
        
        assert isinstance(posts, list), f"Feed should be a list, got: {type(posts)}"
        
        ghost_records = []
        valid_posts = 0
        
        for post in posts:
            post_type = post.get("post_type", "")
            post_id = post.get("id", "?")
            
            # Check for ghost records (posts with record_id but missing title/cover)
            if post.get("record_id"):
                record_title = post.get("record_title") or (post.get("record", {}) or {}).get("title")
                cover_url = post.get("cover_url") or (post.get("record", {}) or {}).get("cover_url")
                
                if not record_title:
                    ghost_records.append({
                        "id": post_id,
                        "type": post_type,
                        "record_id": post.get("record_id"),
                        "issue": "missing_title"
                    })
                else:
                    valid_posts += 1
            else:
                # Posts without record_id (like ISO, NOTE) are valid if they have content
                if post.get("caption") or post.get("content") or post.get("iso"):
                    valid_posts += 1
        
        print(f"Feed returned {len(posts)} posts, {valid_posts} valid, {len(ghost_records)} ghost records")
        
        if ghost_records:
            print(f"WARNING: Ghost records found: {ghost_records[:5]}")
        
        # Feed should not have ghost records after the fix
        assert len(ghost_records) == 0, f"Feed contains {len(ghost_records)} ghost records with missing titles"
        
        return posts
    
    def test_feed_post_types(self, auth_headers):
        """Verify feed only contains allowed post types"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=50", headers=auth_headers)
        assert response.status_code == 200
        posts = response.json()
        
        ALLOWED_TYPES = {"NOW_SPINNING", "NEW_HAUL", "ISO", "RANDOMIZER", "DAILY_PROMPT", "NOTE"}
        
        invalid_types = []
        type_counts = {}
        
        for post in posts:
            pt = (post.get("post_type") or "").upper()
            type_counts[pt] = type_counts.get(pt, 0) + 1
            if pt and pt not in ALLOWED_TYPES:
                invalid_types.append({"id": post.get("id"), "type": pt})
        
        print(f"Post type distribution: {type_counts}")
        
        if invalid_types:
            print(f"WARNING: Invalid post types: {invalid_types[:5]}")
        
        assert len(invalid_types) == 0, f"Feed contains {len(invalid_types)} posts with invalid types"
    
    def test_daily_prompt_responses_structure(self, auth_headers):
        """Test daily prompt response structure if user has buzzed in"""
        # First get today's prompt
        today_resp = requests.get(f"{BASE_URL}/api/prompts/today", headers=auth_headers)
        assert today_resp.status_code == 200
        data = today_resp.json()
        
        if not data.get("prompt"):
            pytest.skip("No prompt scheduled for today")
        
        prompt_id = data["prompt"]["id"]
        
        # If user has buzzed in, we can fetch responses
        if data.get("has_buzzed_in"):
            responses_resp = requests.get(
                f"{BASE_URL}/api/prompts/{prompt_id}/responses",
                headers=auth_headers
            )
            assert responses_resp.status_code == 200, f"Failed to get responses: {responses_resp.text}"
            responses = responses_resp.json()
            
            print(f"Prompt has {len(responses)} responses")
            
            # Verify response structure
            if responses:
                sample = responses[0]
                required_fields = ["id", "user_id", "prompt_id", "record_id"]
                for field in required_fields:
                    assert field in sample, f"Response missing '{field}'"
                
                # Check for color_variant field (added in fix)
                if "color_variant" in sample:
                    print(f"Sample response has color_variant: {sample.get('color_variant')}")
        else:
            print("User has not buzzed in today - skipping responses test")
    
    def test_feed_iso_posts_have_data(self, auth_headers):
        """Test that ISO posts in feed have proper data structure"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=100", headers=auth_headers)
        assert response.status_code == 200
        posts = response.json()
        
        iso_posts = [p for p in posts if p.get("post_type") == "ISO"]
        
        if not iso_posts:
            print("No ISO posts found in feed")
            return
        
        valid_iso = 0
        empty_iso = []
        
        for post in iso_posts:
            iso_data = post.get("iso")
            caption = post.get("caption") or post.get("content")
            
            # ISO post should have iso data OR caption
            if iso_data and (iso_data.get("artist") or iso_data.get("album")):
                valid_iso += 1
            elif caption:
                valid_iso += 1
            else:
                empty_iso.append({"id": post.get("id"), "iso_id": post.get("iso_id")})
        
        print(f"Found {len(iso_posts)} ISO posts, {valid_iso} valid, {len(empty_iso)} empty")
        
        if empty_iso:
            print(f"WARNING: Empty ISO posts: {empty_iso[:3]}")
    
    def test_now_spinning_posts_have_records(self, auth_headers):
        """Test that NOW_SPINNING posts have record data"""
        response = requests.get(f"{BASE_URL}/api/feed?limit=100", headers=auth_headers)
        assert response.status_code == 200
        posts = response.json()
        
        spinning_posts = [p for p in posts if p.get("post_type") == "NOW_SPINNING"]
        
        if not spinning_posts:
            print("No NOW_SPINNING posts found in feed")
            return
        
        valid_spinning = 0
        ghost_spinning = []
        
        for post in spinning_posts:
            record_title = post.get("record_title") or (post.get("record", {}) or {}).get("title")
            caption = post.get("caption")
            
            if record_title and caption:
                valid_spinning += 1
            elif not record_title:
                ghost_spinning.append({
                    "id": post.get("id"),
                    "record_id": post.get("record_id"),
                    "caption": caption[:30] if caption else None
                })
        
        print(f"Found {len(spinning_posts)} NOW_SPINNING posts, {valid_spinning} valid, {len(ghost_spinning)} ghost")
        
        # NOW_SPINNING posts should not have empty record titles after fix
        assert len(ghost_spinning) == 0, f"Found {len(ghost_spinning)} NOW_SPINNING posts without record titles"


class TestBuzzInEndpoint:
    """Tests for buzz-in functionality with prompt_id"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        return data.get("access_token") or data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_buzz_in_requires_prompt_id(self, auth_headers):
        """Test that buzz-in requires prompt_id and record_id"""
        response = requests.post(
            f"{BASE_URL}/api/prompts/buzz-in",
            json={},
            headers=auth_headers
        )
        # Should fail with 400 or 422 for missing fields
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("Buzz-in correctly requires prompt_id and record_id")
    
    def test_buzz_in_validates_prompt_exists(self, auth_headers):
        """Test that buzz-in validates prompt exists"""
        response = requests.post(
            f"{BASE_URL}/api/prompts/buzz-in",
            json={"prompt_id": "nonexistent-id", "record_id": "some-record"},
            headers=auth_headers
        )
        # Should fail with 404 for nonexistent prompt
        assert response.status_code in [400, 404], f"Expected 400/404, got {response.status_code}"
        print("Buzz-in correctly validates prompt exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
