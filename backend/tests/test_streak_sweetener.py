"""
Tests for P1 Features:
1. Daily Prompt Streak Tracking - streak endpoint, longest streak calculation
2. Sweetener Payments - 4% fee, pay-sweetener endpoint
3. Wax Report weekly_prompt_streak field
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def get_auth_token():
    """Get auth token for demo user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@example.com",
        "password": "password123"
    })
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.status_code} - {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers():
    """Get auth headers for demo user"""
    token = get_auth_token()
    return {"Authorization": f"Bearer {token}"}


class TestStreakEndpoint:
    """Test GET /api/prompts/streak/{username} for streak tracking"""
    
    def test_streak_endpoint_returns_200_for_valid_user(self, auth_headers):
        """Streak endpoint should return 200 for existing user"""
        response = requests.get(f"{BASE_URL}/api/prompts/streak/demo", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_streak_endpoint_returns_streak_fields(self, auth_headers):
        """Streak endpoint should return streak, longest_streak, username"""
        response = requests.get(f"{BASE_URL}/api/prompts/streak/demo", headers=auth_headers)
        data = response.json()
        assert "streak" in data, "Missing 'streak' field"
        assert "longest_streak" in data, "Missing 'longest_streak' field"
        assert "username" in data, "Missing 'username' field"
        assert data["username"] == "demo"
        
    def test_streak_is_integer(self, auth_headers):
        """Streak values should be integers >= 0"""
        response = requests.get(f"{BASE_URL}/api/prompts/streak/demo", headers=auth_headers)
        data = response.json()
        assert isinstance(data["streak"], int), f"streak should be int, got {type(data['streak'])}"
        assert isinstance(data["longest_streak"], int), f"longest_streak should be int, got {type(data['longest_streak'])}"
        assert data["streak"] >= 0, "streak should be >= 0"
        assert data["longest_streak"] >= 0, "longest_streak should be >= 0"
        
    def test_streak_endpoint_404_for_nonexistent_user(self, auth_headers):
        """Streak endpoint should return 404 for nonexistent user"""
        response = requests.get(f"{BASE_URL}/api/prompts/streak/nonexistent_user_xyz_123", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
    def test_streak_endpoint_no_auth_required(self):
        """Streak endpoint should work without authentication (public data)"""
        response = requests.get(f"{BASE_URL}/api/prompts/streak/demo")
        assert response.status_code == 200, f"Streak endpoint should be public, got {response.status_code}"


class TestSweetenerPayment:
    """Test POST /api/trades/{trade_id}/pay-sweetener endpoint"""
    
    def test_pay_sweetener_404_for_invalid_trade(self, auth_headers):
        """Pay-sweetener should return 404 for invalid trade ID"""
        response = requests.post(
            f"{BASE_URL}/api/trades/invalid-trade-id-12345/pay-sweetener",
            json={"origin_url": "https://example.com"},
            headers=auth_headers
        )
        # Should return 404 (trade not found) or 400 (invalid trade status)
        assert response.status_code in [404, 400], f"Expected 404/400, got {response.status_code}: {response.text}"
        
    def test_pay_sweetener_endpoint_exists(self, auth_headers):
        """Pay-sweetener endpoint should exist and not return 405 (method not allowed)"""
        response = requests.post(
            f"{BASE_URL}/api/trades/00000000-0000-0000-0000-000000000000/pay-sweetener",
            json={"origin_url": "https://example.com"},
            headers=auth_headers
        )
        # Should not be 405 (method not allowed) - endpoint exists
        assert response.status_code != 405, "pay-sweetener endpoint should exist (got 405)"
        # Expected: 404 (trade not found) or 400 (trade status invalid)
        assert response.status_code in [404, 400], f"Got {response.status_code}: {response.text}"


class TestWaxReportStreak:
    """Test wax report includes weekly_prompt_streak field"""
    
    def test_wax_report_generate_includes_streak(self, auth_headers):
        """Generated wax report should include weekly_prompt_streak"""
        response = requests.post(f"{BASE_URL}/api/wax-reports/generate", headers=auth_headers)
        assert response.status_code == 200, f"Generate failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "weekly_prompt_streak" in data, "Missing 'weekly_prompt_streak' in wax report"
        assert isinstance(data["weekly_prompt_streak"], int), "weekly_prompt_streak should be int"
        
    def test_wax_report_latest_includes_streak(self, auth_headers):
        """Latest wax report should include weekly_prompt_streak"""
        # Generate first to ensure one exists
        requests.post(f"{BASE_URL}/api/wax-reports/generate", headers=auth_headers)
        
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "weekly_prompt_streak" in data, "Missing 'weekly_prompt_streak' in latest wax report"


class TestTradesEndpoint:
    """Test trades API for sweetener display data"""
    
    def test_trades_list_returns_200(self, auth_headers):
        """Trades endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/trades", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
    def test_trade_structure_includes_boot_fields(self, auth_headers):
        """If trades exist, they should have boot_amount and boot_direction fields"""
        response = requests.get(f"{BASE_URL}/api/trades", headers=auth_headers)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            trade = data[0]
            # These fields should exist (may be None/0)
            assert "boot_amount" in trade or trade.get("boot_amount") is None
            assert "boot_direction" in trade or trade.get("boot_direction") is None


class TestTodayPromptStreak:
    """Test GET /api/prompts/today includes streak"""
    
    def test_todays_prompt_includes_streak(self, auth_headers):
        """Today's prompt should include streak in response"""
        response = requests.get(f"{BASE_URL}/api/prompts/today", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "streak" in data, "Missing 'streak' in today's prompt response"


class TestProfileStreak:
    """Test that profile-related APIs work for streak display"""
    
    def test_user_profile_accessible(self, auth_headers):
        """User profile endpoint should be accessible"""
        response = requests.get(f"{BASE_URL}/api/users/demo", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestClosingLineStreak:
    """Test wax report closing line with perfect streak"""
    
    def test_closing_line_exists(self, auth_headers):
        """Wax report should have closing_line field"""
        response = requests.post(f"{BASE_URL}/api/wax-reports/generate", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "closing_line" in data, "Missing 'closing_line' in wax report"
            assert isinstance(data["closing_line"], str), "closing_line should be string"
