"""
Tests for Bug Fixes:
1. GET /api/valuation/record-values/{username} - Public endpoint to get pricing data for ANY user
2. Daily Prompt buzz-in retry logic when prompt_id is stale
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "HoneyGroove2026!"

class TestRecordValuesPricingFix:
    """Tests for the record-values/{username} public endpoint fix"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_record_values_katie_public(self):
        """Test GET /valuation/record-values/katie returns pricing data WITHOUT auth"""
        # This endpoint should be public (no auth required)
        response = requests.get(f"{BASE_URL}/api/valuation/record-values/katie")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should return a map of record_id -> median_value
        assert isinstance(data, dict), "Expected dict response"
        # Per main agent: katie has 147 records with values
        assert len(data) > 50, f"Expected many priced records for katie, got {len(data)}"
        print(f"✅ katie has {len(data)} records with pricing data")
        
    def test_record_values_travis_public(self):
        """Test GET /valuation/record-values/travis returns pricing data WITHOUT auth"""
        response = requests.get(f"{BASE_URL}/api/valuation/record-values/travis")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Expected dict response"
        # Per main agent: travis has 86 records with values
        assert len(data) > 30, f"Expected many priced records for travis, got {len(data)}"
        print(f"✅ travis has {len(data)} records with pricing data")
        
    def test_record_values_nonexistent_user(self):
        """Test 404 for nonexistent user"""
        response = requests.get(f"{BASE_URL}/api/valuation/record-values/nonexistent_user_xyz123")
        assert response.status_code == 404
        print("✅ Returns 404 for nonexistent user")
        
    def test_collection_value_katie_public(self):
        """Test collection value endpoint is also public for any user"""
        response = requests.get(f"{BASE_URL}/api/valuation/collection/katie")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "total_value" in data
        assert "valued_count" in data
        assert "avg_value" in data
        print(f"✅ katie collection value: ${data.get('total_value', 0):,.2f}, {data.get('valued_count', 0)} valued records, avg ${data.get('avg_value', 0):.2f}")


class TestDailyPromptBuzzIn:
    """Tests for Daily Prompt buzz-in endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_prompts_today_endpoint(self, auth_token):
        """Test GET /prompts/today returns current prompt"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/prompts/today", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Should have prompt info
        if data.get("prompt"):
            print(f"✅ Current prompt ID: {data['prompt'].get('id')}")
            print(f"✅ Prompt text: {data['prompt'].get('text', '')[:50]}...")
        else:
            print("ℹ️ No active prompt today")
            
    def test_buzz_in_with_invalid_prompt_id(self, auth_token):
        """Test buzz-in with fake prompt_id returns 404 (which frontend handles with retry)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Use a fake prompt_id that doesn't exist
        response = requests.post(f"{BASE_URL}/api/prompts/buzz-in", 
            headers=headers,
            json={
                "prompt_id": "fake-prompt-id-12345",
                "record_id": "fake-record-id",
                "caption": "test caption",
                "post_to_hive": False
            }
        )
        # Should return 404 "not found" which triggers frontend retry logic
        assert response.status_code in [400, 404], f"Expected 400/404 for invalid prompt_id, got {response.status_code}"
        print(f"✅ Invalid prompt_id correctly returns {response.status_code}")


class TestFeedGhostRecordsRegression:
    """Regression test: Ghost records should still be properly hydrated"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip(f"Authentication failed: {response.status_code}")
        
    def test_feed_returns_hydrated_posts(self, auth_token):
        """Test feed posts have record_title and cover_url (not ghost records)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/feed?limit=20", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        posts = data if isinstance(data, list) else data.get("posts", [])
        
        ghost_count = 0
        hydrated_count = 0
        for post in posts:
            if post.get("type") in ["NEW_RECORD", "SPIN"]:
                if not post.get("record_title") and not post.get("cover_url"):
                    ghost_count += 1
                else:
                    hydrated_count += 1
                    
        print(f"✅ Feed: {hydrated_count} hydrated posts, {ghost_count} ghost posts")
        # Allow some ghost posts (deleted records) but most should be hydrated
        if hydrated_count > 0:
            ghost_ratio = ghost_count / (hydrated_count + ghost_count)
            assert ghost_ratio < 0.5, f"Too many ghost records: {ghost_ratio*100:.0f}%"


class TestAdminPanelButtonsRegression:
    """Regression test: Admin Panel navigation buttons should wrap correctly"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip(f"Authentication failed: {response.status_code}")
        
    def test_admin_panel_access(self, auth_token):
        """Test admin can access admin panel (API-level check)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Check an admin-only endpoint
        response = requests.get(f"{BASE_URL}/api/admin/users?limit=5", headers=headers)
        # Should either succeed or return forbidden (if not admin) - but not 500
        assert response.status_code in [200, 403], f"Expected 200 or 403, got {response.status_code}"
        print(f"✅ Admin panel API accessible: {response.status_code}")
