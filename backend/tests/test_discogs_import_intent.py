"""
BLOCK 585/587: Discogs Import Intent API Tests
Tests the OAuth banner relaxation and conditional banner logic
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
# Admin user credentials from test request
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "admin_password"


class TestDiscogsImportIntent:
    """Test the /api/discogs/update-import-intent endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Try to login with admin credentials
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.user = login_resp.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            self.original_intent = self.user.get("discogs_import_intent", "PENDING")
        else:
            pytest.skip(f"Could not login: {login_resp.status_code} - {login_resp.text}")
    
    def test_update_intent_to_later(self):
        """Test setting intent to LATER"""
        response = self.session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": "LATER"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("intent") == "LATER"
        print("✓ Intent set to LATER successfully")
        
        # Verify via /auth/me
        me_resp = self.session.get(f"{BASE_URL}/api/auth/me")
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data.get("discogs_import_intent") == "LATER"
        print("✓ GET /auth/me returns discogs_import_intent: LATER")
    
    def test_update_intent_to_declined(self):
        """Test setting intent to DECLINED"""
        response = self.session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": "DECLINED"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("intent") == "DECLINED"
        print("✓ Intent set to DECLINED successfully")
        
        # Verify via /auth/me
        me_resp = self.session.get(f"{BASE_URL}/api/auth/me")
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data.get("discogs_import_intent") == "DECLINED"
        assert me_data.get("discogs_migration_dismissed") == True  # Should be set to True
        print("✓ GET /auth/me returns discogs_import_intent: DECLINED and discogs_migration_dismissed: True")
    
    def test_update_intent_to_pending(self):
        """Test setting intent to PENDING"""
        response = self.session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": "PENDING"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("intent") == "PENDING"
        print("✓ Intent set to PENDING successfully")
    
    def test_update_intent_to_connected(self):
        """Test setting intent to CONNECTED"""
        response = self.session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": "CONNECTED"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("intent") == "CONNECTED"
        print("✓ Intent set to CONNECTED successfully")
        
        # Reset back to LATER
        self.session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": "LATER"})
    
    def test_invalid_intent_value(self):
        """Test that invalid intent values are rejected"""
        response = self.session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": "INVALID"})
        assert response.status_code == 400
        print("✓ Invalid intent value rejected with 400")
    
    def test_empty_intent_value(self):
        """Test that empty intent values are rejected"""
        response = self.session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": ""})
        assert response.status_code == 400
        print("✓ Empty intent value rejected with 400")
    
    def test_lowercase_intent_value(self):
        """Test that lowercase intent values are accepted (case-insensitive)"""
        response = self.session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": "later"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("intent") == "LATER"
        print("✓ Lowercase 'later' converted to 'LATER' successfully")
    
    def test_discogs_import_intent_field_in_user_response(self):
        """Verify discogs_import_intent field is included in user response"""
        me_resp = self.session.get(f"{BASE_URL}/api/auth/me")
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert "discogs_import_intent" in me_data
        assert me_data["discogs_import_intent"] in ["PENDING", "LATER", "DECLINED", "CONNECTED"]
        print(f"✓ User response includes discogs_import_intent: {me_data['discogs_import_intent']}")
    
    def test_unauthenticated_request_rejected(self):
        """Test that unauthenticated requests are rejected"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/discogs/update-import-intent", json={"intent": "LATER"})
        assert response.status_code in [401, 403]
        print("✓ Unauthenticated request properly rejected")


class TestDiscogsMigrationDismiss:
    """Test the /api/discogs/dismiss-migration endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Could not login: {login_resp.status_code}")
    
    def test_dismiss_migration(self):
        """Test dismissing the migration modal"""
        response = self.session.post(f"{BASE_URL}/api/discogs/dismiss-migration")
        assert response.status_code == 200
        data = response.json()
        assert data.get("dismissed") == True
        print("✓ Migration dismissed successfully")


class TestDiscogsStatus:
    """Test the /api/discogs/status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Could not login: {login_resp.status_code}")
    
    def test_discogs_status_endpoint(self):
        """Test that discogs status endpoint returns expected fields"""
        response = self.session.get(f"{BASE_URL}/api/discogs/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "connected" in data
        assert "discogs_username" in data
        print(f"✓ Discogs status: connected={data.get('connected')}, username={data.get('discogs_username')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
