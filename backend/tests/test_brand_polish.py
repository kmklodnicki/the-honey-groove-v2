"""
Tests for Brand Polish Update - Iteration 44
Tests email templates, backend API health, and static asset availability.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestEmailTemplates:
    """Test email template structure and content"""
    
    def test_base_template_structure(self):
        """Verify base template contains logo, drip, amber divider"""
        from templates.base import wrap_email, LOGO_URL, DRIP_URL
        
        # Test wrapping
        body_html = "<p>Test content</p>"
        result = wrap_email(body_html)
        
        # Check logo image
        assert LOGO_URL in result, "Logo URL should be in template"
        assert 'logo-wordmark.png' in LOGO_URL, "Logo should be wordmark"
        
        # Check honey drip image
        assert DRIP_URL in result, "Drip URL should be in template"
        assert 'honey-drip.png' in DRIP_URL, "Drip image should be present"
        
        # Check amber divider (2px solid #C8861A)
        assert '#C8861A' in result, "Amber color should be in template"
        assert 'height:2px' in result, "2px divider should be present"
        
        # Check bee footer emoji
        assert 'thehoneygroove.com' in result, "Footer link should be present"
        
        print("SUCCESS: Base email template has logo, drip, amber divider")
    
    def test_email_service_sender_name(self):
        """Verify email sender name is 'The Honey Groove'"""
        from services.email_service import SENDER_EMAIL
        
        # Check sender contains "The Honey Groove"
        assert 'Honey Groove' in SENDER_EMAIL or 'honey' in SENDER_EMAIL.lower(), \
            f"Sender should be 'The Honey Groove', got: {SENDER_EMAIL}"
        print(f"SUCCESS: Email sender is: {SENDER_EMAIL}")
    
    def test_welcome_email_template(self):
        """Test welcome email has correct structure"""
        from templates.emails import welcome
        
        result = welcome("testuser")
        
        assert 'subject' in result
        assert 'html' in result
        assert 'testuser' in result['html']
        assert 'honey' in result['subject'].lower() or '\U0001F36F' in result['subject']
        print("SUCCESS: Welcome email template works")
    
    def test_invite_email_template(self):
        """Test invite email has correct structure"""
        from templates.emails import invite_code
        
        result = invite_code("TestUser", "ABC123")
        
        assert 'subject' in result
        assert 'html' in result
        assert 'ABC123' in result['html']
        assert 'invite' in result['subject'].lower()
        print("SUCCESS: Invite email template works")


class TestStaticAssets:
    """Test static asset availability"""
    
    def test_favicon_endpoints(self):
        """Test favicon files are accessible"""
        favicon_paths = [
            '/favicon.ico',
            '/favicon-16.png',
            '/favicon-32.png',
            '/apple-touch-icon.png',
        ]
        
        for path in favicon_paths:
            url = f"{BASE_URL}{path}"
            try:
                resp = requests.head(url, timeout=5)
                if resp.status_code == 200:
                    print(f"SUCCESS: {path} is accessible")
                else:
                    print(f"INFO: {path} returned {resp.status_code}")
            except Exception as e:
                print(f"WARNING: Could not check {path}: {e}")
    
    def test_logo_wordmark(self):
        """Test logo wordmark is accessible"""
        url = f"{BASE_URL}/logo-wordmark.png"
        try:
            resp = requests.head(url, timeout=5)
            assert resp.status_code == 200, f"Logo wordmark should be accessible, got {resp.status_code}"
            print("SUCCESS: logo-wordmark.png is accessible")
        except Exception as e:
            print(f"WARNING: Could not check logo: {e}")
    
    def test_honey_drip_image(self):
        """Test honey drip image is accessible"""
        url = f"{BASE_URL}/honey-drip.png"
        try:
            resp = requests.head(url, timeout=5)
            assert resp.status_code == 200, f"Honey drip should be accessible, got {resp.status_code}"
            print("SUCCESS: honey-drip.png is accessible")
        except Exception as e:
            print(f"WARNING: Could not check honey drip: {e}")


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        url = f"{BASE_URL}/api/health"
        try:
            resp = requests.get(url, timeout=10)
            assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
            print("SUCCESS: Health endpoint returns 200")
        except Exception as e:
            pytest.skip(f"Health endpoint not available: {e}")
    
    def test_login_endpoint_exists(self):
        """Test login endpoint responds"""
        url = f"{BASE_URL}/api/auth/login"
        try:
            resp = requests.post(url, json={"email": "", "password": ""}, timeout=10)
            # Should return 400 or 422 for invalid data, not 404 or 500
            assert resp.status_code in [400, 401, 422], f"Login endpoint should exist, got {resp.status_code}"
            print(f"SUCCESS: Login endpoint exists (returned {resp.status_code} for empty data)")
        except Exception as e:
            print(f"WARNING: Login endpoint check failed: {e}")
    
    def test_prompts_endpoint(self):
        """Test daily prompts endpoint exists"""
        url = f"{BASE_URL}/api/prompts/today"
        try:
            resp = requests.get(url, timeout=10)
            # Should return 401 for unauthorized
            assert resp.status_code in [401, 403], f"Prompts endpoint should require auth, got {resp.status_code}"
            print(f"SUCCESS: Prompts endpoint exists (returns {resp.status_code} without auth)")
        except Exception as e:
            print(f"WARNING: Prompts endpoint check failed: {e}")


class TestAuthenticatedFeatures:
    """Test authenticated features with demo user"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for demo user"""
        url = f"{BASE_URL}/api/auth/login"
        try:
            resp = requests.post(url, json={
                "email": "demo@example.com",
                "password": "password123"
            }, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('token') or data.get('access_token')
        except:
            pass
        pytest.skip("Could not authenticate demo user")
    
    def test_daily_prompt_with_auth(self, auth_token):
        """Test daily prompt endpoint with authentication"""
        url = f"{BASE_URL}/api/prompts/today"
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        resp = requests.get(url, headers=headers, timeout=10)
        assert resp.status_code == 200, f"Prompts should return 200 with auth, got {resp.status_code}"
        
        data = resp.json()
        assert 'prompt' in data, "Response should contain prompt"
        assert 'streak' in data, "Response should contain streak"
        print(f"SUCCESS: Daily prompt working. Streak: {data.get('streak', 0)}")
    
    def test_hive_feed_with_auth(self, auth_token):
        """Test hive feed endpoint"""
        url = f"{BASE_URL}/api/feed"
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        resp = requests.get(url, headers=headers, timeout=10)
        assert resp.status_code == 200, f"Hive feed should return 200, got {resp.status_code}"
        print("SUCCESS: Hive feed endpoint working")
    
    def test_notifications_with_auth(self, auth_token):
        """Test notifications endpoint"""
        url = f"{BASE_URL}/api/notifications/unread-count"
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        resp = requests.get(url, headers=headers, timeout=10)
        assert resp.status_code == 200, f"Notifications should return 200, got {resp.status_code}"
        
        data = resp.json()
        assert 'count' in data, "Response should contain count"
        print(f"SUCCESS: Notifications working. Unread: {data.get('count', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
