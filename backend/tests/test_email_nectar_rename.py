"""
Test suite for iteration 67:
1. Email config - ADMIN_NOTIFY_EMAIL is now hello@thehoneygroove.com
2. Email config - SENDER_EMAIL contains 'The Honey Groove' and 'hello@thehoneygroove.com'
3. No references to contact@kathrynklodnicki.com
4. Frontend /nectar routes are working (tested via API that powers them)
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmailConfiguration:
    """Verify email configuration changes"""
    
    def test_admin_notify_email_is_hello_at_thehoneygroove(self):
        """ADMIN_NOTIFY_EMAIL in admin.py should be hello@thehoneygroove.com"""
        # Read the admin.py file
        admin_path = "/app/backend/routes/admin.py"
        with open(admin_path, 'r') as f:
            content = f.read()
        
        # Check ADMIN_NOTIFY_EMAIL
        match = re.search(r'ADMIN_NOTIFY_EMAIL\s*=\s*["\']([^"\']+)["\']', content)
        assert match is not None, "ADMIN_NOTIFY_EMAIL not found in admin.py"
        assert match.group(1) == "hello@thehoneygroove.com", f"Expected hello@thehoneygroove.com, got {match.group(1)}"
        print("PASSED: ADMIN_NOTIFY_EMAIL = hello@thehoneygroove.com")
    
    def test_sender_email_contains_honey_groove(self):
        """SENDER_EMAIL in email_service.py should contain 'The Honey Groove' and 'hello@thehoneygroove.com'"""
        email_service_path = "/app/backend/services/email_service.py"
        with open(email_service_path, 'r') as f:
            content = f.read()
        
        # Check that the fallback SENDER_EMAIL contains correct info
        assert "The Honey Groove" in content, "SENDER_EMAIL should contain 'The Honey Groove'"
        assert "hello@thehoneygroove.com" in content, "SENDER_EMAIL should contain 'hello@thehoneygroove.com'"
        print("PASSED: SENDER_EMAIL contains 'The Honey Groove' and 'hello@thehoneygroove.com'")
    
    def test_no_old_email_references_in_backend(self):
        """No references to the old email in backend source files"""
        import subprocess
        OLD_EMAIL = "contact@kathrynklodnicki.com"
        
        result = subprocess.run(
            ['grep', '-rn', OLD_EMAIL, '/app/backend/'],
            capture_output=True, text=True
        )
        
        # Filter out test files and __pycache__
        lines = [line for line in result.stdout.strip().split('\n') 
                 if line and '/tests/' not in line and '__pycache__' not in line]
        
        assert len(lines) == 0, f"Found old email reference in production code:\n{chr(10).join(lines)}"
        print("PASSED: No references to old email in backend production code")


class TestExploreAPIRoutes:
    """Verify the /api/explore routes are working (these power the renamed Nectar page)
    Note: Backend API routes remain /api/explore/* - only frontend routes changed to /nectar
    """
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        # Try existing test user from iteration 66
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test_direct_66@test.com",
            "password": "testpass123"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        
        # Try iso test user
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iso_test_1772900669@test.com", 
            "password": "testpass123"
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        
        pytest.skip("Could not authenticate to test explore endpoints")
    
    @pytest.fixture
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_explore_trending_endpoint(self, headers):
        """GET /api/explore/trending should return 200 - powers Nectar page"""
        resp = requests.get(f"{BASE_URL}/api/explore/trending", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), list)
        print("PASSED: GET /api/explore/trending returns 200")
    
    def test_explore_suggested_collectors_endpoint(self, headers):
        """GET /api/explore/suggested-collectors should return 200 - powers Nectar page"""
        resp = requests.get(f"{BASE_URL}/api/explore/suggested-collectors", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), list)
        print("PASSED: GET /api/explore/suggested-collectors returns 200")
    
    def test_explore_trending_in_collections_endpoint(self, headers):
        """GET /api/explore/trending-in-collections should return 200 - powers Nectar page"""
        resp = requests.get(f"{BASE_URL}/api/explore/trending-in-collections", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), list)
        print("PASSED: GET /api/explore/trending-in-collections returns 200")
    
    def test_explore_most_wanted_endpoint(self, headers):
        """GET /api/explore/most-wanted should return 200 - powers Nectar page"""
        resp = requests.get(f"{BASE_URL}/api/explore/most-wanted", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert isinstance(resp.json(), list)
        print("PASSED: GET /api/explore/most-wanted returns 200")
    
    def test_explore_near_you_endpoint(self, headers):
        """GET /api/explore/near-you should return 200 - powers Nectar page"""
        resp = requests.get(f"{BASE_URL}/api/explore/near-you", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "collectors" in data or "needs_location" in data
        print("PASSED: GET /api/explore/near-you returns 200")


class TestNoExploreRouteInFrontend:
    """Verify no /explore route references in frontend (user-facing routes only, not API calls)"""
    
    def test_no_explore_route_in_frontend_js(self):
        """No /explore frontend route references in frontend JS files
        Note: /api/explore/* API calls are expected and correct - only user routes should use /nectar
        """
        import subprocess
        result = subprocess.run(
            ['grep', '-rn', '/explore', '/app/frontend/src/'],
            capture_output=True, text=True
        )
        
        # Filter out API calls (/api/explore, ${API}/explore) - these are fine
        # We're looking for user-facing routes like to="/explore" or path="/explore"
        lines = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # Skip API calls (these should use /explore)
            if '/api/explore' in line or '${API}/explore' in line:
                continue
            # Looking for React Router routes and links
            if 'to="/explore' in line or 'path="/explore' in line or "to='/explore" in line:
                lines.append(line)
        
        assert len(lines) == 0, f"Found /explore user route references in frontend (should use /nectar):\n{chr(10).join(lines)}"
        print("PASSED: No /explore user route references in frontend (API calls correctly use /api/explore)")
