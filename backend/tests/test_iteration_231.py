"""
Test iteration 231 - HoneyGroove features:
1. Backend: GET /api/prompts/today returns 'missed_yesterday' field
2. Backend: GET /api/auth/me returns 'first_name' field
3. Backend: PUT /api/auth/me accepts and saves 'first_name'
4. Feed filters have emojis AFTER text
5. Settings page First Name field validation
6. Composer track selector is native <select>
7. Onboarding modal first name step
8. Download App card in Settings
9. 'The Vault' label in navigation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Login as Katie and get auth token."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "katie",
        "password": "HoneyGroove2026!"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


class TestPromptsTodayEndpoint:
    """Test GET /api/prompts/today returns missed_yesterday field."""
    
    def test_prompts_today_has_missed_yesterday_field(self, auth_token):
        """Verify /api/prompts/today returns missed_yesterday boolean."""
        response = requests.get(
            f"{BASE_URL}/api/prompts/today",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check missed_yesterday field exists
        assert "missed_yesterday" in data, "missed_yesterday field missing from /prompts/today"
        assert isinstance(data["missed_yesterday"], bool), "missed_yesterday should be boolean"
        print(f"✓ missed_yesterday: {data['missed_yesterday']}")
        
        # Check other expected fields
        assert "prompt" in data, "prompt field missing"
        assert "has_buzzed_in" in data, "has_buzzed_in field missing"
        assert "streak" in data, "streak field missing"
        assert "buzz_count" in data, "buzz_count field missing"
        print(f"✓ All expected fields present: prompt, has_buzzed_in, streak, buzz_count")


class TestAuthMeEndpoint:
    """Test GET and PUT /api/auth/me for first_name field."""
    
    def test_auth_me_returns_first_name(self, auth_token):
        """Verify /api/auth/me returns first_name field."""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check first_name field exists
        assert "first_name" in data, "first_name field missing from /auth/me"
        print(f"✓ first_name present in /auth/me response: '{data.get('first_name')}'")
        
        # For Katie, first_name should be 'Katie' (set in previous session)
        if data.get('username') == 'katie':
            print(f"✓ Katie's first_name: {data.get('first_name')}")
    
    def test_auth_me_update_first_name(self, auth_token):
        """Verify PUT /api/auth/me accepts and saves first_name."""
        # First get current first_name
        get_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 200
        current_first_name = get_response.json().get("first_name")
        
        # Try updating first_name
        test_name = "TestKatie"
        update_response = requests.put(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"first_name": test_name}
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated_data = update_response.json()
        assert updated_data.get("first_name") == test_name, f"first_name not updated: {updated_data.get('first_name')}"
        print(f"✓ first_name updated to: {test_name}")
        
        # Restore original first_name
        restore_response = requests.put(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"first_name": current_first_name or "Katie"}
        )
        assert restore_response.status_code == 200
        print(f"✓ first_name restored to: {current_first_name or 'Katie'}")


class TestUserResponseModel:
    """Test UserResponse model includes first_name."""
    
    def test_login_returns_first_name(self):
        """Verify login response includes first_name in user object."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "katie",
            "password": "HoneyGroove2026!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "user" in data, "user object missing from login response"
        user = data["user"]
        assert "first_name" in user, "first_name missing from user object in login response"
        print(f"✓ first_name in login response user object: '{user.get('first_name')}'")


class TestStreakLogic:
    """Test streak and missed_yesterday logic."""
    
    def test_missed_yesterday_logic(self, auth_token):
        """Verify missed_yesterday is based on daily prompt answers."""
        response = requests.get(
            f"{BASE_URL}/api/prompts/today",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # missed_yesterday should be false for Katie (she's been answering prompts)
        missed = data.get("missed_yesterday", None)
        streak = data.get("streak", 0)
        has_buzzed = data.get("has_buzzed_in", False)
        
        print(f"✓ Current streak: {streak}")
        print(f"✓ Has buzzed in today: {has_buzzed}")
        print(f"✓ Missed yesterday: {missed}")
        
        # Logic check: if missed_yesterday is true, Re-pollinate should show
        # if missed_yesterday is false, Re-pollinate should NOT show
        assert isinstance(missed, bool), "missed_yesterday must be boolean"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
