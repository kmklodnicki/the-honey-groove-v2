"""
Admin Panel API Tests - Tests all admin endpoints for the unified admin panel
Sections: Beta & Invites, Daily Prompts, Bingo Squares, Reports, Platform Settings
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "demo@example.com"
ADMIN_PASSWORD = "password123"

# Non-admin credentials
NON_ADMIN_EMAIL = "newuser@test.com"
NON_ADMIN_PASSWORD = "test1234"


@pytest.fixture(scope="module")
def admin_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.fail(f"Admin login failed: {response.text}")


@pytest.fixture(scope="module")
def non_admin_token():
    """Get authentication token for non-admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": NON_ADMIN_EMAIL,
        "password": NON_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Non-admin user not available")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture
def non_admin_headers(non_admin_token):
    return {"Authorization": f"Bearer {non_admin_token}", "Content-Type": "application/json"}


# ═══════════════════════════════════════════════
# BETA & INVITES SECTION TESTS
# ═══════════════════════════════════════════════

class TestBetaSignups:
    """Tests for beta signups management"""
    
    def test_admin_can_list_beta_signups(self, admin_headers):
        """Admin can GET /admin/beta-signups"""
        response = requests.get(f"{BASE_URL}/api/admin/beta-signups", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} beta signups")
    
    def test_admin_can_export_csv(self, admin_headers):
        """Admin can GET /admin/beta-signups/export"""
        response = requests.get(f"{BASE_URL}/api/admin/beta-signups/export", headers=admin_headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        print("CSV export successful")
    
    def test_non_admin_cannot_list_beta_signups(self, non_admin_headers):
        """Non-admin blocked from /admin/beta-signups"""
        response = requests.get(f"{BASE_URL}/api/admin/beta-signups", headers=non_admin_headers)
        assert response.status_code == 403


class TestInviteCodes:
    """Tests for invite codes management"""
    
    def test_admin_can_list_invite_codes(self, admin_headers):
        """Admin can GET /admin/invite-codes"""
        response = requests.get(f"{BASE_URL}/api/admin/invite-codes", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} invite codes")
    
    def test_admin_can_generate_single_code(self, admin_headers):
        """Admin can POST /admin/invite-codes/generate with count=1"""
        response = requests.post(
            f"{BASE_URL}/api/admin/invite-codes/generate",
            headers=admin_headers,
            json={"count": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert "code" in data[0]
        assert data[0]["code"].startswith("HG-")
        assert data[0]["status"] == "unused"
        print(f"Generated code: {data[0]['code']}")
    
    def test_non_admin_cannot_generate_codes(self, non_admin_headers):
        """Non-admin blocked from generating codes"""
        response = requests.post(
            f"{BASE_URL}/api/admin/invite-codes/generate",
            headers=non_admin_headers,
            json={"count": 1}
        )
        assert response.status_code == 403


# ═══════════════════════════════════════════════
# DAILY PROMPTS SECTION TESTS
# ═══════════════════════════════════════════════

class TestDailyPrompts:
    """Tests for daily prompts admin management"""
    
    def test_admin_can_list_all_prompts(self, admin_headers):
        """Admin can GET /prompts/admin/all"""
        response = requests.get(f"{BASE_URL}/api/prompts/admin/all", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check prompt structure
        if len(data) > 0:
            prompt = data[0]
            assert "id" in prompt
            assert "text" in prompt
            assert "scheduled_date" in prompt
            assert "active" in prompt
            assert "response_count" in prompt or prompt.get("response_count", 0) >= 0
        print(f"Found {len(data)} prompts")
    
    def test_admin_can_create_prompt(self, admin_headers):
        """Admin can POST /prompts/admin/create"""
        test_prompt = {
            "text": "TEST_prompt_what_record_defined_today",
            "scheduled_date": "2026-12-25",
            "active": True
        }
        response = requests.post(
            f"{BASE_URL}/api/prompts/admin/create",
            headers=admin_headers,
            json=test_prompt
        )
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == test_prompt["text"]
        assert "id" in data
        print(f"Created prompt: {data['id']}")
        return data["id"]
    
    def test_admin_can_update_prompt(self, admin_headers):
        """Admin can PUT /prompts/admin/{id}"""
        # First create a prompt
        create_response = requests.post(
            f"{BASE_URL}/api/prompts/admin/create",
            headers=admin_headers,
            json={"text": "TEST_update_prompt", "scheduled_date": "2026-12-26", "active": True}
        )
        prompt_id = create_response.json()["id"]
        
        # Now update it
        update_response = requests.put(
            f"{BASE_URL}/api/prompts/admin/{prompt_id}",
            headers=admin_headers,
            json={"text": "TEST_updated_prompt_text", "active": False}
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["text"] == "TEST_updated_prompt_text"
        assert data["active"] == False
        print(f"Updated prompt {prompt_id}")
    
    def test_admin_can_toggle_prompt_active(self, admin_headers):
        """Admin can toggle active state via PUT"""
        # Get existing prompts
        list_response = requests.get(f"{BASE_URL}/api/prompts/admin/all", headers=admin_headers)
        prompts = list_response.json()
        if len(prompts) == 0:
            pytest.skip("No prompts to test toggle")
        
        prompt = prompts[0]
        original_active = prompt.get("active", True)
        
        # Toggle active state
        response = requests.put(
            f"{BASE_URL}/api/prompts/admin/{prompt['id']}",
            headers=admin_headers,
            json={"active": not original_active}
        )
        assert response.status_code == 200
        
        # Toggle back
        response = requests.put(
            f"{BASE_URL}/api/prompts/admin/{prompt['id']}",
            headers=admin_headers,
            json={"active": original_active}
        )
        assert response.status_code == 200
        print(f"Toggle prompt active state verified")
    
    def test_non_admin_cannot_access_admin_prompts(self, non_admin_headers):
        """Non-admin blocked from admin prompts"""
        response = requests.get(f"{BASE_URL}/api/prompts/admin/all", headers=non_admin_headers)
        assert response.status_code == 403


# ═══════════════════════════════════════════════
# BINGO SQUARES SECTION TESTS
# ═══════════════════════════════════════════════

class TestBingoSquares:
    """Tests for bingo squares admin management"""
    
    def test_admin_can_list_bingo_squares(self, admin_headers):
        """Admin can GET /bingo/admin/squares"""
        response = requests.get(f"{BASE_URL}/api/bingo/admin/squares", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            square = data[0]
            assert "id" in square
            assert "text" in square
            assert "emoji" in square
            assert "active" in square
        print(f"Found {len(data)} bingo squares")
    
    def test_admin_can_create_square(self, admin_headers):
        """Admin can POST /bingo/admin/squares"""
        test_square = {
            "text": "TEST_square_played_a_vinyl",
            "emoji": "🎵"
        }
        response = requests.post(
            f"{BASE_URL}/api/bingo/admin/squares",
            headers=admin_headers,
            json=test_square
        )
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == test_square["text"]
        assert data["emoji"] == test_square["emoji"]
        assert data["active"] == True
        print(f"Created square: {data['id']}")
    
    def test_admin_can_toggle_square_active(self, admin_headers):
        """Admin can PUT /bingo/admin/squares/{id}"""
        # Get existing squares
        list_response = requests.get(f"{BASE_URL}/api/bingo/admin/squares", headers=admin_headers)
        squares = list_response.json()
        if len(squares) == 0:
            pytest.skip("No squares to test toggle")
        
        square = squares[0]
        original_active = square.get("active", True)
        
        # Toggle active state
        response = requests.put(
            f"{BASE_URL}/api/bingo/admin/squares/{square['id']}",
            headers=admin_headers,
            json={"active": not original_active}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["active"] == (not original_active)
        
        # Toggle back
        response = requests.put(
            f"{BASE_URL}/api/bingo/admin/squares/{square['id']}",
            headers=admin_headers,
            json={"active": original_active}
        )
        assert response.status_code == 200
        print(f"Toggle square active state verified")
    
    def test_non_admin_cannot_access_admin_squares(self, non_admin_headers):
        """Non-admin blocked from admin squares"""
        response = requests.get(f"{BASE_URL}/api/bingo/admin/squares", headers=non_admin_headers)
        assert response.status_code == 403


# ═══════════════════════════════════════════════
# REPORTS SECTION TESTS
# ═══════════════════════════════════════════════

class TestReports:
    """Tests for reports admin management"""
    
    def test_admin_can_list_reports(self, admin_headers):
        """Admin can GET /reports/admin"""
        response = requests.get(f"{BASE_URL}/api/reports/admin", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            report = data[0]
            assert "id" in report
            assert "type" in report
            assert "reason" in report
            assert "status" in report
            assert "reporter_username" in report
        print(f"Found {len(data)} reports")
    
    def test_admin_can_update_report_status(self, admin_headers):
        """Admin can PUT /reports/admin/{id}"""
        # Get existing reports
        list_response = requests.get(f"{BASE_URL}/api/reports/admin", headers=admin_headers)
        reports = list_response.json()
        if len(reports) == 0:
            pytest.skip("No reports to test update")
        
        report = reports[0]
        original_status = report.get("status", "Pending")
        new_status = "Reviewed" if original_status == "Pending" else "Pending"
        
        # Update status
        response = requests.put(
            f"{BASE_URL}/api/reports/admin/{report['id']}",
            headers=admin_headers,
            json={"status": new_status}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == new_status
        
        # Restore original
        response = requests.put(
            f"{BASE_URL}/api/reports/admin/{report['id']}",
            headers=admin_headers,
            json={"status": original_status}
        )
        assert response.status_code == 200
        print(f"Report status update verified")
    
    def test_report_status_validation(self, admin_headers):
        """Invalid status rejected"""
        list_response = requests.get(f"{BASE_URL}/api/reports/admin", headers=admin_headers)
        reports = list_response.json()
        if len(reports) == 0:
            pytest.skip("No reports to test")
        
        response = requests.put(
            f"{BASE_URL}/api/reports/admin/{reports[0]['id']}",
            headers=admin_headers,
            json={"status": "InvalidStatus"}
        )
        assert response.status_code == 400
    
    def test_non_admin_cannot_access_reports(self, non_admin_headers):
        """Non-admin blocked from admin reports"""
        response = requests.get(f"{BASE_URL}/api/reports/admin", headers=non_admin_headers)
        assert response.status_code == 403


# ═══════════════════════════════════════════════
# PLATFORM SETTINGS SECTION TESTS
# ═══════════════════════════════════════════════

class TestPlatformSettings:
    """Tests for platform settings admin management"""
    
    def test_admin_can_get_settings(self, admin_headers):
        """Admin can GET /admin/settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} settings")
    
    def test_admin_can_update_platform_fee(self, admin_headers):
        """Admin can POST /admin/settings to update fee"""
        # Get current fee
        get_response = requests.get(f"{BASE_URL}/api/admin/settings", headers=admin_headers)
        settings = get_response.json()
        current_fee = 6  # default
        for s in settings:
            if s.get("key") == "platform_fee_percent":
                current_fee = s.get("value", 6)
        
        # Update fee
        new_fee = 7.5 if current_fee != 7.5 else 8.0
        response = requests.post(
            f"{BASE_URL}/api/admin/settings",
            headers=admin_headers,
            json={"key": "platform_fee_percent", "value": new_fee}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "platform_fee_percent"
        assert data["value"] == new_fee
        
        # Restore original
        response = requests.post(
            f"{BASE_URL}/api/admin/settings",
            headers=admin_headers,
            json={"key": "platform_fee_percent", "value": current_fee}
        )
        assert response.status_code == 200
        print(f"Platform fee update verified")
    
    def test_non_admin_cannot_access_settings(self, non_admin_headers):
        """Non-admin blocked from admin settings"""
        response = requests.get(f"{BASE_URL}/api/admin/settings", headers=non_admin_headers)
        assert response.status_code == 403


# ═══════════════════════════════════════════════
# ACCESS CONTROL TESTS
# ═══════════════════════════════════════════════

class TestAccessControl:
    """Tests for admin route access control"""
    
    def test_unauthenticated_blocked_from_admin(self):
        """Unauthenticated users cannot access admin routes"""
        routes = [
            "/api/admin/beta-signups",
            "/api/admin/invite-codes",
            "/api/admin/settings",
            "/api/prompts/admin/all",
            "/api/bingo/admin/squares",
            "/api/reports/admin"
        ]
        for route in routes:
            response = requests.get(f"{BASE_URL}{route}")
            assert response.status_code in [401, 403], f"Route {route} should require auth"
        print("All admin routes require authentication")
