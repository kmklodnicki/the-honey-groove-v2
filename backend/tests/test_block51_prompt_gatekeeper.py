"""
Test suite for BLOCK 51.1-51.4: Daily Prompt Gatekeeper, Response Carousel, Variant Pills, In Common Tab

BLOCK 51.1: Daily Prompt gatekeeper - buzz in before seeing others
BLOCK 51.2: Response carousel with left/right navigation after buzzing in
BLOCK 51.3: Variant pills on carousel cards
BLOCK 51.4: 'In Common' tab defaults for soulmate matches, My Kinda People links to In Common tab
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - admin user
ADMIN_EMAIL = "admin@thehoneygroove.com"
ADMIN_PASSWORD = "admin123"


class TestBlock51PromptGatekeeper:
    """Tests for BLOCK 51.1-51.3: Prompt gatekeeper and response carousel"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        data = response.json()
        return data.get("access_token")
    
    @pytest.fixture(scope="class")
    def todays_prompt(self, admin_token):
        """Get today's prompt data"""
        response = requests.get(
            f"{BASE_URL}/api/prompts/today",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to get today's prompt: {response.text}")
        return response.json()
    
    # BLOCK 51.1: Gatekeeper tests
    def test_prompts_today_returns_buzz_count(self, admin_token, todays_prompt):
        """GET /api/prompts/today includes buzz_count field"""
        assert "buzz_count" in todays_prompt, "Missing buzz_count field in /prompts/today response"
        assert isinstance(todays_prompt["buzz_count"], int), "buzz_count should be an integer"
        print(f"PASSED: /api/prompts/today returns buzz_count: {todays_prompt['buzz_count']}")
    
    def test_prompts_today_returns_has_buzzed_in(self, admin_token, todays_prompt):
        """GET /api/prompts/today includes has_buzzed_in field"""
        assert "has_buzzed_in" in todays_prompt, "Missing has_buzzed_in field"
        assert isinstance(todays_prompt["has_buzzed_in"], bool), "has_buzzed_in should be boolean"
        print(f"PASSED: /api/prompts/today returns has_buzzed_in: {todays_prompt['has_buzzed_in']}")
    
    def test_prompts_today_returns_prompt(self, admin_token, todays_prompt):
        """GET /api/prompts/today includes prompt with id and text"""
        assert "prompt" in todays_prompt, "Missing prompt field"
        if todays_prompt["prompt"]:
            assert "id" in todays_prompt["prompt"], "Prompt missing id"
            assert "text" in todays_prompt["prompt"], "Prompt missing text"
            print(f"PASSED: Prompt text: {todays_prompt['prompt']['text'][:50]}...")
        else:
            print("INFO: No prompt scheduled for today")
    
    # BLOCK 51.1: Gatekeeper - responses endpoint requires buzz-in
    def test_responses_endpoint_requires_buzzin_403(self, admin_token, todays_prompt):
        """GET /api/prompts/{prompt_id}/responses returns 403 if user hasn't buzzed in"""
        if not todays_prompt.get("prompt"):
            pytest.skip("No prompt available")
        
        prompt_id = todays_prompt["prompt"]["id"]
        has_buzzed = todays_prompt.get("has_buzzed_in", False)
        
        response = requests.get(
            f"{BASE_URL}/api/prompts/{prompt_id}/responses",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if not has_buzzed:
            # If user hasn't buzzed in, should get 403
            assert response.status_code == 403, f"Expected 403 for non-buzzed user, got {response.status_code}"
            assert "buzz" in response.json().get("detail", "").lower(), "Error should mention buzzing in"
            print("PASSED: GET /api/prompts/{id}/responses returns 403 when not buzzed in")
        else:
            # If user has buzzed in, should get 200 with responses
            assert response.status_code == 200, f"Expected 200 for buzzed-in user, got {response.status_code}: {response.text}"
            print("INFO: User already buzzed in, got responses successfully")
    
    def test_responses_endpoint_requires_auth(self, todays_prompt):
        """GET /api/prompts/{prompt_id}/responses requires authentication"""
        if not todays_prompt.get("prompt"):
            pytest.skip("No prompt available")
        
        prompt_id = todays_prompt["prompt"]["id"]
        response = requests.get(f"{BASE_URL}/api/prompts/{prompt_id}/responses")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASSED: /api/prompts/{id}/responses requires authentication")
    
    # BLOCK 51.2: Response carousel structure
    def test_responses_endpoint_returns_list_after_buzzin(self, admin_token, todays_prompt):
        """GET /api/prompts/{prompt_id}/responses returns list of enriched responses after buzzing in"""
        if not todays_prompt.get("prompt"):
            pytest.skip("No prompt available")
        if not todays_prompt.get("has_buzzed_in"):
            pytest.skip("User hasn't buzzed in - can't test responses")
        
        prompt_id = todays_prompt["prompt"]["id"]
        response = requests.get(
            f"{BASE_URL}/api/prompts/{prompt_id}/responses",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"PASSED: Got {len(data)} responses")
        
        if len(data) > 0:
            # Check enriched fields in first response
            first = data[0]
            expected_fields = ["id", "user_id", "record_title", "record_artist"]
            for field in expected_fields:
                assert field in first, f"Response missing required field: {field}"
            
            # Check user enrichment fields
            user_fields = ["username", "display_name", "avatar_url", "founding_member"]
            for field in user_fields:
                assert field in first, f"Response missing user enrichment field: {field}"
            
            # BLOCK 51.3: Check variant pill field
            assert "color_variant" in first, "Response missing color_variant field for variant pill"
            
            print(f"PASSED: Response enriched with user data (username: {first.get('username')})")
            print(f"INFO: color_variant field present: {first.get('color_variant')}")


class TestBlock51TasteMatchInCommon:
    """Tests for BLOCK 51.4: In Common tab and My Kinda People links"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json().get("access_token")
    
    def test_taste_match_endpoint_exists(self, admin_token):
        """GET /api/users/{username}/taste-match endpoint exists"""
        # Find another user to check taste match
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code != 200:
            # Try specific known user
            other_username = "katieintheafterglow"
        else:
            users = response.json()
            other_user = next((u for u in users if u.get("username") != "admin"), None)
            if not other_user:
                pytest.skip("No other users found")
            other_username = other_user.get("username", "katieintheafterglow")
        
        response = requests.get(
            f"{BASE_URL}/api/users/{other_username}/taste-match",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Taste match endpoint failed: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "score" in data, "Missing score field"
        assert "shared_reality" in data, "Missing shared_reality field"
        assert "shared_dreams" in data, "Missing shared_dreams field"
        assert "swap_potential" in data, "Missing swap_potential field"
        
        print(f"PASSED: Taste match with {other_username}: {data['score']}%")
        if data.get("label"):
            print(f"INFO: Taste match label: {data['label']}")
    
    def test_my_kinda_people_endpoint(self, admin_token):
        """GET /api/discover/my-kinda-people returns matching users"""
        response = requests.get(
            f"{BASE_URL}/api/discover/my-kinda-people",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"My Kinda People endpoint failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"PASSED: My Kinda People returned {len(data)} users")
        
        if len(data) > 0:
            first = data[0]
            expected_fields = ["username", "score", "common_count"]
            for field in expected_fields:
                assert field in first, f"Missing field: {field}"
            print(f"INFO: First match: @{first['username']} ({first['score']}% match, {first['common_count']} common)")


class TestBuzzInFlow:
    """Tests for buzz-in flow that enables carousel"""
    
    @pytest.fixture(scope="class")
    def admin_auth(self):
        """Get admin auth token and user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        data = response.json()
        return {
            "token": data.get("access_token"),
            "user": data.get("user")
        }
    
    @pytest.fixture(scope="class")
    def admin_records(self, admin_auth):
        """Get admin's records"""
        response = requests.get(
            f"{BASE_URL}/api/records",
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        return response.json() if response.status_code == 200 else []
    
    def test_buzz_in_flow_complete(self, admin_auth, admin_records):
        """Full buzz-in flow: buzz in -> get responses"""
        token = admin_auth["token"]
        
        # Get today's prompt
        prompt_resp = requests.get(
            f"{BASE_URL}/api/prompts/today",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert prompt_resp.status_code == 200, f"Failed to get prompt: {prompt_resp.text}"
        prompt_data = prompt_resp.json()
        
        if not prompt_data.get("prompt"):
            pytest.skip("No prompt available today")
        
        prompt_id = prompt_data["prompt"]["id"]
        has_buzzed = prompt_data.get("has_buzzed_in", False)
        
        print(f"INFO: Prompt: {prompt_data['prompt']['text'][:50]}...")
        print(f"INFO: Has buzzed in: {has_buzzed}")
        print(f"INFO: Buzz count: {prompt_data.get('buzz_count', 0)}")
        
        if not has_buzzed:
            # User hasn't buzzed in - verify gatekeeper
            resp_check = requests.get(
                f"{BASE_URL}/api/prompts/{prompt_id}/responses",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert resp_check.status_code == 403, f"Expected 403 before buzz-in, got {resp_check.status_code}"
            print("PASSED: Gatekeeper blocked responses before buzz-in")
            
            # Now buzz in if user has records
            if not admin_records:
                pytest.skip("No records to buzz in with")
            
            buzz_resp = requests.post(
                f"{BASE_URL}/api/prompts/buzz-in",
                json={
                    "prompt_id": prompt_id,
                    "record_id": admin_records[0]["id"],
                    "caption": "TEST buzz-in for testing carousel",
                    "post_to_hive": False
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if buzz_resp.status_code == 200:
                print("PASSED: Buzz-in successful")
                buzz_data = buzz_resp.json()
                assert "id" in buzz_data, "Missing response id"
                assert "streak" in buzz_data, "Missing streak"
                print(f"INFO: New streak: {buzz_data.get('streak')}")
            elif buzz_resp.status_code == 400 and "already" in buzz_resp.json().get("detail", "").lower():
                print("INFO: Already buzzed in (race condition)")
                has_buzzed = True
            else:
                pytest.fail(f"Buzz-in failed: {buzz_resp.text}")
        
        # Now verify we can get responses
        resp_after = requests.get(
            f"{BASE_URL}/api/prompts/{prompt_id}/responses",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp_after.status_code == 200, f"Failed to get responses after buzz-in: {resp_after.text}"
        responses = resp_after.json()
        
        assert isinstance(responses, list), "Responses should be a list"
        print(f"PASSED: Got {len(responses)} responses after buzz-in")
        
        # Verify enrichment
        if len(responses) > 0:
            r = responses[0]
            assert "username" in r, "Response missing username enrichment"
            assert "color_variant" in r, "Response missing color_variant for variant pill"
            print(f"PASSED: Responses enriched with user data and color_variant")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
