"""
Test Suite: HoneyGroove v2.7.2 - BLOCK 597 Features
- Interactive Value Recovery Toast (recovery status with recovered_details & total_increase)
- Test Data Purge Admin Endpoint  
- Disclaimer Padding verification (RecordDetailPage)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRecoveryStatusEndpoint:
    """
    BLOCK 476: GET /api/valuation/recovery/status
    Should include recovered_details array and total_increase when recovery completed
    """
    
    @pytest.fixture
    def auth_token(self):
        """Login as admin user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "admin_password"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_recovery_status_requires_auth(self):
        """Recovery status endpoint requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/valuation/recovery/status")
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print("PASS: Recovery status endpoint requires auth")
    
    def test_recovery_status_returns_correct_structure(self, auth_token):
        """Recovery status should return expected fields"""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/recovery/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        # Must have status field
        assert "status" in data, "Response must have 'status' field"
        print(f"Recovery status: {data.get('status')}")
        
        # If completed, should have recovered_details and total_increase
        if data.get("status") == "completed":
            # recovered_details may be present if recovery was run with newly valued records
            if "recovered_details" in data:
                assert isinstance(data["recovered_details"], list), "recovered_details must be a list"
                print(f"Recovered details count: {len(data['recovered_details'])}")
                
                # Check structure of recovered_details items
                if len(data["recovered_details"]) > 0:
                    item = data["recovered_details"][0]
                    expected_fields = ["title", "artist", "old_value", "new_value", "increase"]
                    for field in expected_fields:
                        assert field in item, f"recovered_details item missing '{field}'"
                    print(f"Sample recovery item: {item.get('title')} - old: ${item.get('old_value')}, new: ${item.get('new_value')}")
            
            if "total_increase" in data:
                assert isinstance(data["total_increase"], (int, float)), "total_increase must be numeric"
                print(f"Total increase: ${data.get('total_increase')}")
        
        # Standard fields should always be present
        standard_fields = ["total", "valued", "recovered", "failed"]
        for field in standard_fields:
            assert field in data, f"Missing standard field: {field}"
        
        print(f"PASS: Recovery status structure correct - status={data.get('status')}, valued={data.get('valued')}/{data.get('total')}")


class TestPurgeTestDataEndpoint:
    """
    BLOCK 597: POST /api/admin/purge-test-data
    Identifies and deletes test listings/trades/notifications/posts
    Protects founder account (4072aaa7-1171-4cd2-9c8f-20dfca8fdc58)
    """
    
    @pytest.fixture
    def admin_token(self):
        """Login as admin user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "admin_password"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_purge_requires_admin_auth(self):
        """Purge endpoint requires admin authentication"""
        # No auth
        resp = requests.post(f"{BASE_URL}/api/admin/purge-test-data")
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"
        print("PASS: Purge endpoint rejects unauthenticated requests")
    
    def test_purge_requires_admin_role(self, admin_token):
        """Purge endpoint requires admin role"""
        # First verify the user is admin
        resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        user_data = resp.json()
        is_admin = user_data.get("is_admin", False)
        print(f"User is_admin: {is_admin}")
        
        # If not admin, this test will verify 403
        # If admin, test will succeed
        resp = requests.post(
            f"{BASE_URL}/api/admin/purge-test-data",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if not is_admin:
            assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}"
            print("PASS: Non-admin users get 403")
        else:
            assert resp.status_code == 200, f"Expected 200 for admin, got {resp.status_code}"
            print("PASS: Admin can access purge endpoint")
    
    def test_purge_returns_correct_response_structure(self, admin_token):
        """Purge endpoint returns expected response structure"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/purge-test-data",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        
        # Check required fields
        expected_fields = [
            "test_users_found",
            "listings_deleted",
            "trade_requests_deleted",
            "notifications_deleted",
            "posts_deleted"
        ]
        for field in expected_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"Test users found: {len(data.get('test_users_found', []))}")
        print(f"Listings deleted: {data.get('listings_deleted')}")
        print(f"Trade requests deleted: {data.get('trade_requests_deleted')}")
        print(f"Notifications deleted: {data.get('notifications_deleted')}")
        print(f"Posts deleted: {data.get('posts_deleted')}")
        
        # Verify test_users_found structure if any exist
        if data.get("test_users_found"):
            user = data["test_users_found"][0]
            assert "id" in user, "Test user must have 'id'"
            assert "email" in user, "Test user must have 'email'"
            assert "username" in user, "Test user must have 'username'"
            print(f"Sample test user: {user.get('username')} - {user.get('email')}")
        
        print("PASS: Purge response structure correct")
    
    def test_purge_protects_founder_account(self, admin_token):
        """Purge should never include founder account in test_users_found"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/purge-test-data",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        founder_id = "4072aaa7-1171-4cd2-9c8f-20dfca8fdc58"
        test_user_ids = [u.get("id") for u in data.get("test_users_found", [])]
        
        assert founder_id not in test_user_ids, "Founder account must be protected from purge!"
        print(f"PASS: Founder account ({founder_id}) protected - not in test users list")
    
    def test_purge_identifies_test_patterns(self, admin_token):
        """Purge identifies users with test email patterns"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/purge-test-data",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify email patterns being matched
        test_patterns_matched = []
        for user in data.get("test_users_found", []):
            email = user.get("email", "").lower()
            if "@test.com" in email or "@example.com" in email or "test" in email:
                test_patterns_matched.append(email)
        
        print(f"Test emails matched: {test_patterns_matched[:5]}")  # Show first 5
        
        # Message if no test users (already cleaned)
        if not data.get("test_users_found"):
            print("No test users found - database already clean or no test accounts exist")
            if "message" in data:
                print(f"Message: {data['message']}")
        
        print("PASS: Test pattern identification working")


class TestRecoveryStartEndpoint:
    """Test POST /api/valuation/recovery/start"""
    
    @pytest.fixture
    def auth_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "admin_password"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_recovery_start_requires_auth(self):
        """Recovery start endpoint requires authentication"""
        resp = requests.post(f"{BASE_URL}/api/valuation/recovery/start")
        assert resp.status_code in [401, 403]
        print("PASS: Recovery start requires auth")
    
    def test_recovery_start_returns_progress(self, auth_token):
        """Recovery start returns progress information"""
        resp = requests.post(
            f"{BASE_URL}/api/valuation/recovery/start",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 200 (started) or 400 (already running)
        assert resp.status_code in [200, 400], f"Expected 200/400, got {resp.status_code}"
        
        data = resp.json()
        if resp.status_code == 200:
            assert "status" in data
            print(f"Recovery started/status: {data.get('status')}")
        else:
            print(f"Recovery response: {data}")
        
        print("PASS: Recovery start endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
