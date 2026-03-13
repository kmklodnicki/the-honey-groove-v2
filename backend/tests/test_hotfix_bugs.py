"""
Test suite for production hotfix bugs:
1. Admin prompts API returns sorted prompts (descending by scheduled_date)
2. FRONTEND_URL is hard-coded to production domain
3. Password reset generates correct URL
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vinyl-shield-prod.preview.emergentagent.com')

class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Verify API health check works"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"SUCCESS: Health check passed - {data}")
    
    def test_admin_login(self):
        """Verify admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["is_admin"] is True
        print(f"SUCCESS: Admin login successful - username: {data['user']['username']}")
        return data["access_token"]


class TestAdminPromptsSorting:
    """Test that admin prompts endpoint returns prompts sorted by scheduled_date descending"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026!"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_prompts_sorted_descending(self, admin_token):
        """FIX #1: Admin prompts should be sorted by scheduled_date descending (newest first)"""
        response = requests.get(
            f"{BASE_URL}/api/prompts/admin/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        prompts = response.json()
        
        assert len(prompts) > 0, "Should have at least one prompt"
        print(f"Total prompts returned: {len(prompts)}")
        
        # Extract scheduled_dates and verify descending order
        dates = []
        for p in prompts:
            if p.get("scheduled_date"):
                dates.append(p["scheduled_date"])
        
        assert len(dates) >= 2, "Need at least 2 prompts with dates to verify sorting"
        
        # Check each consecutive pair is in descending order
        for i in range(len(dates) - 1):
            assert dates[i] >= dates[i+1], f"Dates should be descending: {dates[i]} should be >= {dates[i+1]}"
        
        print(f"SUCCESS: Prompts are sorted in descending order")
        print(f"  First 3 dates: {dates[:3]}")
        print(f"  Last 3 dates: {dates[-3:]}")


class TestFrontendURLHardcoded:
    """Test that FRONTEND_URL is correctly configured for password reset emails"""
    
    def test_forgot_password_endpoint_exists(self):
        """Verify forgot password endpoint works (doesn't reveal if email exists)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "test-nonexistent@example.com"}
        )
        # Should return 200 even for non-existent emails (security best practice)
        assert response.status_code == 200
        data = response.json()
        assert "ok" in str(data.get("status", "")).lower() or "sent" in str(data.get("message", "")).lower()
        print(f"SUCCESS: Forgot password endpoint works correctly")
    
    def test_frontend_url_in_database_py(self):
        """FIX #2: Verify FRONTEND_URL is hard-coded to production domain in database.py"""
        # Read the database.py file to verify FRONTEND_URL
        with open('/app/backend/database.py', 'r') as f:
            content = f.read()
        
        # Check that FRONTEND_URL is hard-coded to the production domain
        assert 'FRONTEND_URL = "https://www.thehoneygroove.com"' in content, \
            "FRONTEND_URL should be hard-coded to https://www.thehoneygroove.com"
        
        print("SUCCESS: FRONTEND_URL is correctly hard-coded to https://www.thehoneygroove.com")


class TestISOPageBottomPadding:
    """Test that ISOPage.js has correct bottom padding to prevent content cutoff"""
    
    def test_isopage_has_pb32_class(self):
        """FIX #3: Verify ISOPage container has pb-32 class instead of pb-24"""
        with open('/app/frontend/src/pages/ISOPage.js', 'r') as f:
            content = f.read()
        
        # Check for pb-32 in the main container
        assert 'pb-32' in content, "ISOPage should have pb-32 class for bottom padding"
        
        # More specific check - the main container should have pb-32
        assert 'pb-32 md:pb-8' in content, \
            "ISOPage container should have 'pb-32 md:pb-8' for mobile bottom padding"
        
        print("SUCCESS: ISOPage.js has correct pb-32 bottom padding class")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
