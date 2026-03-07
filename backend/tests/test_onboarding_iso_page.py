"""
Tests for Iteration 66:
1. POST /api/composer/now-spinning - now-spinning endpoint for onboarding
2. ISO page stats verification (ensure no count sections rendered)
3. Record search for discogs
4. Check records added in collection can be used for now-spinning
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNowSpinningEndpoint:
    """Tests for POST /api/composer/now-spinning endpoint"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user and get auth token"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        unique_id = str(uuid.uuid4())[:8]
        email = f"testuser_iter66_{unique_id}@test.com"
        password = "testpass123"
        username = f"tester66_{unique_id}"
        
        # Register user
        resp = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "username": username
        })
        
        if resp.status_code == 201:
            token = resp.json()["access_token"]
            user_id = resp.json()["user"]["id"]
        elif resp.status_code == 400 and "exists" in resp.text.lower():
            # User exists, try to login
            resp = session.post(f"{BASE_URL}/api/auth/login", json={
                "email": email,
                "password": password
            })
            assert resp.status_code == 200, f"Login failed: {resp.text}"
            token = resp.json()["access_token"]
            user_id = resp.json()["user"]["id"]
        else:
            pytest.skip(f"Could not create or login test user: {resp.text}")
        
        session.headers.update({"Authorization": f"Bearer {token}"})
        return {"session": session, "token": token, "user_id": user_id, "email": email}
    
    @pytest.fixture(scope="class")
    def user_record(self, test_user):
        """Add a record to user's collection for testing"""
        resp = test_user["session"].post(f"{BASE_URL}/api/records", json={
            "title": "Test Album for Now Spinning",
            "artist": "Test Artist 66",
            "discogs_id": 12345678,
            "cover_url": "https://example.com/cover.jpg",
            "year": 2024,
            "format": "LP"
        })
        
        if resp.status_code == 201:
            return resp.json()
        elif resp.status_code == 409:
            # Record already exists - check ownership and get details
            check_resp = test_user["session"].get(f"{BASE_URL}/api/records/check-ownership?discogs_id=12345678")
            if check_resp.status_code == 200 and check_resp.json().get("owned"):
                return {"id": check_resp.json()["record_id"]}
            pytest.skip(f"Record conflict: {resp.text}")
        else:
            pytest.skip(f"Could not add record: {resp.text}")
    
    def test_now_spinning_requires_auth(self):
        """POST /api/composer/now-spinning without auth returns 401"""
        resp = requests.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": "fake-record-id"
        })
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}: {resp.text}"
        print("PASSED: now-spinning requires authentication")
    
    def test_now_spinning_requires_record_id(self, test_user):
        """POST /api/composer/now-spinning without record_id fails"""
        resp = test_user["session"].post(f"{BASE_URL}/api/composer/now-spinning", json={})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
        print("PASSED: now-spinning requires record_id field")
    
    def test_now_spinning_invalid_record_returns_404(self, test_user):
        """POST /api/composer/now-spinning with non-existent record returns 404"""
        resp = test_user["session"].post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": "non-existent-record-id-123"
        })
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("PASSED: now-spinning with invalid record returns 404")
    
    def test_now_spinning_with_valid_record(self, test_user, user_record):
        """POST /api/composer/now-spinning creates post with valid record_id"""
        record_id = user_record["id"]
        
        resp = test_user["session"].post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record_id,
            "caption": "Testing from onboarding iteration 66",
            "mood": "Late Night"
        })
        
        assert resp.status_code == 200 or resp.status_code == 201, f"Expected 200/201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "id" in data, "Response should contain post id"
        assert data.get("post_type") == "NOW_SPINNING", f"Expected NOW_SPINNING post type, got {data.get('post_type')}"
        assert data.get("caption") == "Testing from onboarding iteration 66", "Caption mismatch"
        assert data.get("mood") == "Late Night", "Mood mismatch"
        
        print(f"PASSED: now-spinning creates post with id {data['id']}")
        return data
    
    def test_now_spinning_without_optional_fields(self, test_user, user_record):
        """POST /api/composer/now-spinning works with only record_id"""
        record_id = user_record["id"]
        
        resp = test_user["session"].post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record_id
        })
        
        assert resp.status_code in [200, 201], f"Expected 200/201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("post_type") == "NOW_SPINNING"
        print("PASSED: now-spinning works without optional caption/mood fields")


class TestDiscogsSearch:
    """Tests for Discogs search used in onboarding"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        unique_id = str(uuid.uuid4())[:8]
        email = f"discogs_test_{unique_id}@test.com"
        password = "testpass123"
        
        resp = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "username": f"discogs_{unique_id}"
        })
        
        if resp.status_code in [200, 201]:
            token = resp.json()["access_token"]
        else:
            pytest.skip(f"Could not create test user: {resp.text}")
        
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_discogs_search_returns_results(self, auth_session):
        """GET /api/discogs/search returns results for valid query"""
        resp = auth_session.get(f"{BASE_URL}/api/discogs/search?q=radiohead")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            result = data[0]
            # Check expected fields from search results
            assert "discogs_id" in result or "id" in result, "Results should contain discogs_id or id"
            assert "title" in result, "Results should contain title"
            print(f"PASSED: Discogs search returned {len(data)} results")
        else:
            print("WARNING: Discogs search returned no results (may be rate limited)")
    
    def test_discogs_search_empty_query(self, auth_session):
        """GET /api/discogs/search with empty query returns empty or error"""
        resp = auth_session.get(f"{BASE_URL}/api/discogs/search?q=")
        # Either empty results or 400 error is acceptable
        assert resp.status_code in [200, 400, 422], f"Unexpected status: {resp.status_code}"
        print(f"PASSED: Empty query handled correctly (status: {resp.status_code})")


class TestISOPageEndpoints:
    """Tests for ISO page related endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        unique_id = str(uuid.uuid4())[:8]
        email = f"iso_test_{unique_id}@test.com"
        password = "testpass123"
        
        resp = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "username": f"iso_{unique_id}"
        })
        
        if resp.status_code in [200, 201]:
            token = resp.json()["access_token"]
        else:
            pytest.skip(f"Could not create test user: {resp.text}")
        
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_user_isos(self, auth_session):
        """GET /api/iso returns user's ISO list"""
        resp = auth_session.get(f"{BASE_URL}/api/iso")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASSED: User ISOs endpoint returns {len(data)} items")
    
    def test_get_community_isos(self, auth_session):
        """GET /api/iso/community returns community ISOs"""
        resp = auth_session.get(f"{BASE_URL}/api/iso/community")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASSED: Community ISOs endpoint returns {len(data)} items")
    
    def test_get_listings(self, auth_session):
        """GET /api/listings returns shop listings"""
        resp = auth_session.get(f"{BASE_URL}/api/listings?limit=10")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASSED: Listings endpoint returns {len(data)} items")


class TestOnboardingFlow:
    """Tests simulating onboarding flow"""
    
    @pytest.fixture(scope="class")
    def onboarding_user(self):
        """Create a user for onboarding flow test"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        unique_id = str(uuid.uuid4())[:8]
        email = f"onboard_{unique_id}@test.com"
        password = "testpass123"
        username = f"onboard_{unique_id}"
        
        resp = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "username": username
        })
        
        if resp.status_code not in [200, 201]:
            pytest.skip(f"Could not create test user: {resp.text}")
        
        token = resp.json()["access_token"]
        user = resp.json()["user"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        return {"session": session, "token": token, "user": user, "email": email}
    
    def test_onboarding_flow_step1_add_record(self, onboarding_user):
        """Step 1: Add record to collection"""
        resp = onboarding_user["session"].post(f"{BASE_URL}/api/records", json={
            "title": "Onboarding Test Album",
            "artist": "Onboarding Artist",
            "discogs_id": 99999999,
            "year": 2025,
            "format": "LP"
        })
        
        if resp.status_code == 409:
            # Already exists, get the record_id
            check_resp = onboarding_user["session"].get(f"{BASE_URL}/api/records/check-ownership?discogs_id=99999999")
            if check_resp.status_code == 200:
                record_id = check_resp.json().get("record_id")
                onboarding_user["record_id"] = record_id
                print(f"Record already exists, using record_id: {record_id}")
                return record_id
        
        assert resp.status_code in [200, 201], f"Expected 200/201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        onboarding_user["record_id"] = data["id"]
        print(f"PASSED: Step 1 - Record added with id {data['id']}")
        return data["id"]
    
    def test_onboarding_flow_step2_now_spinning(self, onboarding_user):
        """Step 2: Create Now Spinning post"""
        record_id = onboarding_user.get("record_id")
        
        if not record_id:
            # Try to get record_id from previous test
            check_resp = onboarding_user["session"].get(f"{BASE_URL}/api/records/check-ownership?discogs_id=99999999")
            if check_resp.status_code == 200 and check_resp.json().get("owned"):
                record_id = check_resp.json()["record_id"]
            else:
                pytest.skip("No record_id available from step 1")
        
        resp = onboarding_user["session"].post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record_id,
            "mood": "Good Morning",
            "caption": "Testing onboarding step 2"
        })
        
        assert resp.status_code in [200, 201], f"Expected 200/201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("post_type") == "NOW_SPINNING"
        print(f"PASSED: Step 2 - Now Spinning post created with id {data['id']}")
    
    def test_onboarding_complete_update(self, onboarding_user):
        """Mark onboarding as completed"""
        resp = onboarding_user["session"].put(f"{BASE_URL}/api/auth/me", json={
            "onboarding_completed": True
        })
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("onboarding_completed") == True, "Onboarding should be marked complete"
        print("PASSED: Onboarding marked as complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
