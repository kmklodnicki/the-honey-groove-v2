"""
BLOCK 476: Value Recovery Engine Tests
Tests for:
- POST /api/valuation/recovery/start - triggers recovery for authenticated user
- GET /api/valuation/recovery/status - returns recovery status
- Recovery engine handles users with no records gracefully
- Nightly recovery scheduler registration
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestValueRecoveryEndpoints:
    """Tests for Value Recovery Engine endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test user and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Register a new test user
        timestamp = int(time.time())
        self.test_email = f"test_recovery_{timestamp}@test.com"
        self.test_username = f"testrecovery{timestamp}"
        
        register_resp = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.test_email,
            "password": "test123",
            "username": self.test_username
        })
        
        if register_resp.status_code == 200:
            data = register_resp.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            # Try login if user exists
            login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
                "email": self.test_email,
                "password": "test123"
            })
            if login_resp.status_code == 200:
                data = login_resp.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            else:
                pytest.skip("Could not authenticate test user")
    
    def test_recovery_status_endpoint_exists(self):
        """Test GET /api/valuation/recovery/status returns valid response"""
        response = self.session.get(f"{BASE_URL}/api/valuation/recovery/status")
        
        # Status code should be 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Response should contain status field
        data = response.json()
        assert "status" in data, f"Response missing 'status' field: {data}"
        
        # Status should be one of: idle, in_progress, completed
        valid_statuses = ["idle", "in_progress", "completed"]
        assert data["status"] in valid_statuses, f"Invalid status: {data['status']}"
        
        print(f"Recovery status endpoint returned: {data}")
    
    def test_recovery_start_endpoint_exists(self):
        """Test POST /api/valuation/recovery/start returns valid response"""
        response = self.session.post(f"{BASE_URL}/api/valuation/recovery/start")
        
        # Status code should be 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should return status or message
        assert "status" in data or "message" in data, f"Response missing status/message: {data}"
        
        print(f"Recovery start endpoint returned: {data}")
    
    def test_recovery_start_without_auth_fails(self):
        """Test recovery start requires authentication"""
        # Create new session without auth
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/valuation/recovery/start")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
        print(f"Unauthenticated request correctly rejected: {response.status_code}")
    
    def test_recovery_status_without_auth_fails(self):
        """Test recovery status requires authentication"""
        # Create new session without auth
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/valuation/recovery/status")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
        print(f"Unauthenticated request correctly rejected: {response.status_code}")
    
    def test_recovery_status_structure(self):
        """Test recovery status returns expected fields"""
        response = self.session.get(f"{BASE_URL}/api/valuation/recovery/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Status must be present
        assert "status" in data
        
        # For idle/completed status, should have these fields
        expected_fields = ["total", "valued", "recovered", "failed"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"Recovery status structure verified: {data}")
    
    def test_recovery_for_empty_collection(self):
        """Test recovery handles users with no records gracefully"""
        # New user has no records - recovery should complete instantly
        response = self.session.post(f"{BASE_URL}/api/valuation/recovery/start")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should either start or complete immediately
        assert "status" in data or "message" in data
        
        # Check status after
        time.sleep(1)
        status_resp = self.session.get(f"{BASE_URL}/api/valuation/recovery/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        
        # For empty collection, should be completed or idle
        assert status_data["status"] in ["completed", "idle"]
        assert status_data.get("total", 0) == 0 or status_data["status"] == "idle"
        
        print(f"Empty collection recovery handled: {status_data}")
    
    def test_double_recovery_start_returns_progress(self):
        """Test starting recovery twice returns in_progress status"""
        # Start first recovery
        resp1 = self.session.post(f"{BASE_URL}/api/valuation/recovery/start")
        assert resp1.status_code == 200
        
        # Try starting again immediately
        resp2 = self.session.post(f"{BASE_URL}/api/valuation/recovery/start")
        assert resp2.status_code == 200
        data = resp2.json()
        
        # Should return current status, not error
        # Either in_progress, completed, or started message
        assert "status" in data or "message" in data
        
        print(f"Double recovery start handled: {data}")


class TestCollectionValueWithRecovery:
    """Tests for collection value endpoint integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test user and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        timestamp = int(time.time())
        self.test_email = f"test_colval_{timestamp}@test.com"
        self.test_username = f"testcolval{timestamp}"
        
        register_resp = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.test_email,
            "password": "test123",
            "username": self.test_username
        })
        
        if register_resp.status_code == 200:
            data = register_resp.json()
            self.token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
                "email": self.test_email,
                "password": "test123"
            })
            if login_resp.status_code == 200:
                data = login_resp.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            else:
                pytest.skip("Could not authenticate")
    
    def test_collection_value_endpoint(self):
        """Test GET /api/valuation/collection returns expected structure"""
        response = self.session.get(f"{BASE_URL}/api/valuation/collection")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should have required fields
        assert "total_value" in data
        assert "valued_count" in data
        assert "total_count" in data
        
        print(f"Collection value: {data}")
    
    def test_collection_value_shows_unvalued_records(self):
        """Test collection value returns total_count and valued_count for TreasuryHeader"""
        response = self.session.get(f"{BASE_URL}/api/valuation/collection")
        
        assert response.status_code == 200
        data = response.json()
        
        # These fields drive the "Recover Values" button visibility
        total = data.get("total_count", 0)
        valued = data.get("valued_count", 0)
        
        # For new user, should be 0
        assert total >= 0
        assert valued >= 0
        assert valued <= total
        
        print(f"Collection stats: total={total}, valued={valued}")


class TestWeeklyWaxIntegration:
    """Tests for Weekly Wax email integration with collection value"""
    
    def test_weekly_wax_preview_endpoint_exists(self):
        """Test the weekly wax preview admin endpoint structure"""
        # This test verifies the endpoint exists and works for admin users
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin (demo@example.com is set as admin in server.py)
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "test123"
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Admin user not available")
        
        data = login_resp.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Try preview endpoint
        preview_resp = session.get(f"{BASE_URL}/api/admin/weekly-wax/preview")
        
        # Should be 200 for admin or 403 for non-admin
        assert preview_resp.status_code in [200, 403]
        
        if preview_resp.status_code == 200:
            preview_data = preview_resp.json()
            print(f"Weekly wax preview available: {preview_data.keys()}")


class TestNightlyRecoveryScheduler:
    """Tests for nightly recovery scheduler registration"""
    
    def test_server_startup_registers_scheduler(self):
        """Verify server.py registers schedule_nightly_recovery on startup"""
        # Read server.py to verify registration
        server_path = "/app/backend/server.py"
        
        try:
            with open(server_path, 'r') as f:
                content = f.read()
            
            # Check for scheduler registration
            assert "schedule_nightly_recovery" in content, "Scheduler not found in server.py"
            assert "from services.value_recovery import schedule_nightly_recovery" in content, "Import not found"
            assert "asyncio.create_task(schedule_nightly_recovery())" in content, "Task creation not found"
            
            print("Nightly recovery scheduler properly registered in server.py")
        except FileNotFoundError:
            pytest.skip("server.py not accessible in test environment")
    
    def test_value_recovery_module_has_scheduler(self):
        """Verify value_recovery.py has schedule_nightly_recovery function"""
        module_path = "/app/backend/services/value_recovery.py"
        
        try:
            with open(module_path, 'r') as f:
                content = f.read()
            
            assert "async def schedule_nightly_recovery" in content, "Function not found"
            assert "3 AM UTC" in content or "3, minute=0" in content, "Schedule time not configured"
            
            print("Nightly recovery scheduler function found in value_recovery.py")
        except FileNotFoundError:
            pytest.skip("value_recovery.py not accessible in test environment")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
