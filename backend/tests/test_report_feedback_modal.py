"""
Test Report Modal and Feedback Admin Features
- Bug report / General feedback toggle
- GET /api/reports/admin/feedback with mode filters
- Report submission for both bug and feedback modes
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
TEST_USER = {"email": "testexplore@test.com", "password": "testpass123"}
ADMIN_USER = {"email": "admin@thehoneygroove.com", "password": "admin123"}


class TestReportReasons:
    """Test /api/reports/reasons endpoint for bug and feedback types"""
    
    def test_get_bug_reasons(self):
        """Bug mode should return valid reasons list"""
        response = requests.get(f"{BASE_URL}/api/reports/reasons/bug")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "reasons" in data
        assert len(data["reasons"]) > 0
        expected = ["UI / display issue", "Feature not working", "Performance problem", "Other"]
        assert data["reasons"] == expected, f"Got: {data['reasons']}"
        print(f"PASS: Bug reasons returned: {data['reasons']}")
    
    def test_get_feedback_reasons(self):
        """Feedback mode should return General Feedback reason"""
        response = requests.get(f"{BASE_URL}/api/reports/reasons/feedback")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "reasons" in data
        assert "General Feedback" in data["reasons"]
        print(f"PASS: Feedback reasons returned: {data['reasons']}")


class TestReportSubmission:
    """Test /api/reports/submit endpoint for bug and feedback modes"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Auth failed: {response.status_code} - {response.text}")
    
    def test_submit_bug_report(self, auth_token):
        """Submit a bug report with target_type='bug'"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "target_type": "bug",
            "reason": "UI / display issue",
            "notes": "TEST_BUG_REPORT: Testing bug report submission",
            "page_url": "https://test.com/test-page",
            "browser_info": "Test Browser"
        }
        response = requests.post(f"{BASE_URL}/api/reports/submit", json=payload, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "report_id" in data
        assert data["status"] == "OPEN"
        print(f"PASS: Bug report submitted with ID: {data['report_id']}")
        return data["report_id"]
    
    def test_submit_general_feedback(self, auth_token):
        """Submit general feedback with target_type='feedback'"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "target_type": "feedback",
            "reason": "General Feedback",
            "notes": "TEST_FEEDBACK: Testing general feedback submission - great platform!",
            "page_url": "https://test.com/feedback-page",
            "browser_info": "Test Browser"
        }
        response = requests.post(f"{BASE_URL}/api/reports/submit", json=payload, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "report_id" in data
        assert data["status"] == "OPEN"
        print(f"PASS: General feedback submitted with ID: {data['report_id']}")
        return data["report_id"]


class TestAdminFeedbackEndpoint:
    """Test /api/reports/admin/feedback endpoint with mode filters"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin auth failed: {response.status_code} - {response.text}")
    
    def test_get_all_feedback_entries(self, admin_token):
        """GET /api/reports/admin/feedback returns all bug and feedback entries"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/reports/admin/feedback", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "entries" in data
        print(f"PASS: All feedback entries returned: {len(data['entries'])} entries")
        
        # Verify entries have reporter info
        if data["entries"]:
            entry = data["entries"][0]
            assert "reporter" in entry, "Entry missing 'reporter' field"
            assert "target_type" in entry
            assert entry["target_type"] in ["bug", "feedback"]
            print(f"PASS: Entry has reporter info: {entry.get('reporter', {}).get('username', 'N/A')}")
    
    def test_filter_by_bug_mode(self, admin_token):
        """GET /api/reports/admin/feedback?mode=bug returns only bug reports"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/reports/admin/feedback?mode=bug", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "entries" in data
        
        # All entries should be bug type
        for entry in data["entries"]:
            assert entry["target_type"] == "bug", f"Expected bug, got {entry['target_type']}"
        print(f"PASS: Bug mode filter works - {len(data['entries'])} bug reports")
    
    def test_filter_by_feedback_mode(self, admin_token):
        """GET /api/reports/admin/feedback?mode=feedback returns only feedback"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/reports/admin/feedback?mode=feedback", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "entries" in data
        
        # All entries should be feedback type
        for entry in data["entries"]:
            assert entry["target_type"] == "feedback", f"Expected feedback, got {entry['target_type']}"
        print(f"PASS: Feedback mode filter works - {len(data['entries'])} feedback entries")
    
    def test_admin_required_for_feedback_endpoint(self):
        """Non-admin should get 403 on /api/reports/admin/feedback"""
        # Login as regular user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        if login_resp.status_code != 200:
            pytest.skip("Could not log in as test user")
        user_token = login_resp.json().get("access_token")
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{BASE_URL}/api/reports/admin/feedback", headers=headers)
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print("PASS: Non-admin correctly gets 403 on admin endpoint")


class TestEntryStructure:
    """Verify structure of feedback entries"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin auth failed: {response.status_code}")
    
    def test_entry_contains_required_fields(self, admin_token):
        """Each entry should have type, reporter info, reason (if bug), message, timestamp, status"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/reports/admin/feedback", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        if not data["entries"]:
            pytest.skip("No entries to validate")
        
        entry = data["entries"][0]
        
        # Required fields
        required_fields = ["report_id", "target_type", "notes", "created_at", "status", "reporter"]
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"
        
        # Reporter should have username
        if entry.get("reporter"):
            assert "username" in entry["reporter"] or entry["reporter"] == {}, "Reporter missing username"
        
        # Bug reports should have reason
        if entry["target_type"] == "bug":
            assert "reason" in entry, "Bug report missing reason field"
        
        print(f"PASS: Entry structure validated - has all required fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
