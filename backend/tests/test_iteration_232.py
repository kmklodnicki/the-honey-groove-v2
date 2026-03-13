"""
Iteration 232 Tests - Backend API verification for HoneyGroove features:
1. GET /api/prompts/today returns 'missed_yesterday' field
2. GET /api/auth/me returns 'first_name' field (should be 'Katie' for test user)
3. Stripe keys in .env are live mode (sk_live_...)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "katie"
TEST_PASSWORD = "HoneyGroove2026!"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


class TestPromptsAPI:
    """Tests for /api/prompts/today endpoint"""

    def test_prompts_today_returns_missed_yesterday(self, auth_token):
        """Verify GET /api/prompts/today includes missed_yesterday field"""
        response = requests.get(
            f"{BASE_URL}/api/prompts/today",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify missed_yesterday field exists and is boolean
        assert "missed_yesterday" in data, f"missed_yesterday field missing. Got keys: {data.keys()}"
        assert isinstance(data["missed_yesterday"], bool), f"missed_yesterday should be bool, got {type(data['missed_yesterday'])}"
        
        # Also verify other expected fields
        assert "prompt" in data, "prompt field missing"
        assert "has_buzzed_in" in data, "has_buzzed_in field missing"
        assert "streak" in data, "streak field missing"


class TestAuthMeAPI:
    """Tests for /api/auth/me endpoint"""

    def test_auth_me_returns_first_name(self, auth_token):
        """Verify GET /api/auth/me returns first_name field"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify first_name field exists
        assert "first_name" in data, f"first_name field missing. Got keys: {list(data.keys())}"
        
        # Verify Katie's first_name is 'Katie'
        assert data["first_name"] == "Katie", f"Expected first_name='Katie', got '{data.get('first_name')}'"


class TestStripeConfig:
    """Tests for Stripe configuration"""

    def test_stripe_key_is_live_mode(self):
        """Verify STRIPE_API_KEY starts with sk_live_"""
        # Read the .env file
        env_path = "/app/backend/.env"
        stripe_key = None
        
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('STRIPE_API_KEY='):
                    stripe_key = line.split('=', 1)[1].strip()
                    break
        
        assert stripe_key is not None, "STRIPE_API_KEY not found in .env"
        assert stripe_key.startswith('sk_live_'), f"Stripe key should start with sk_live_, got: {stripe_key[:15]}..."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
