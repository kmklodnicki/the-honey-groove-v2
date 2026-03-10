"""
Test suite for the Randomizer feature:
- GET /api/collection/random - returns random record from user's owned collection
- POST /api/composer/now-spinning - creates NOW_SPINNING post (used by both Post to Hive and Spin This Now)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')


def get_auth_session():
    """Helper to create authenticated session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@test.com",
        "password": "demouser"
    })
    
    if login_resp.status_code == 200:
        data = login_resp.json()
        # API returns access_token, not token
        token = data.get("access_token") or data.get("token")
        user_id = data.get("user", {}).get("id")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session, token, user_id
    print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
    return None, None, None


class TestRandomizerFeature:
    """Tests for the Randomizer feature in ComposerBar"""
    
    # ============== GET /api/collection/random Tests ==============
    
    def test_random_record_requires_authentication(self):
        """GET /api/collection/random returns 401 without token"""
        session_no_auth = requests.Session()
        response = session_no_auth.get(f"{BASE_URL}/api/collection/random")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: GET /api/collection/random requires authentication")
    
    def test_random_record_returns_record(self):
        """GET /api/collection/random returns a random record from user's collection"""
        session, token, user_id = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        response = session.get(f"{BASE_URL}/api/collection/random")
        
        # Note: If user has no records, expect 404
        if response.status_code == 404:
            data = response.json()
            assert "No records" in data.get("detail", ""), f"Expected 'No records' message, got: {data}"
            print("PASS: GET /api/collection/random correctly returns 404 when no records")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate required fields for randomizer modal
        assert "id" in data, "Response must include 'id'"
        assert "title" in data, "Response must include 'title'"
        assert "artist" in data, "Response must include 'artist'"
        
        print(f"PASS: GET /api/collection/random returns record: {data.get('artist')} - {data.get('title')}")
    
    def test_random_record_excludes_wantlist(self):
        """GET /api/collection/random excludes source='wantlist' records"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        for _ in range(3):
            response = session.get(f"{BASE_URL}/api/collection/random")
            if response.status_code == 404:
                print("PASS: No records to test exclusion - skipping")
                return
            
            data = response.json()
            source = data.get("source", "")
            assert source != "wantlist", f"Random record should not be from wantlist, got source: {source}"
        
        print("PASS: Random records exclude wantlist source")
    
    def test_random_record_excludes_dreamlist(self):
        """GET /api/collection/random excludes source='dreamlist' records"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        for _ in range(3):
            response = session.get(f"{BASE_URL}/api/collection/random")
            if response.status_code == 404:
                return
            
            data = response.json()
            source = data.get("source", "")
            assert source != "dreamlist", f"Random record should not be from dreamlist, got source: {source}"
        
        print("PASS: Random records exclude dreamlist source")
    
    def test_random_record_excludes_iso(self):
        """GET /api/collection/random excludes source='iso' records"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        for _ in range(3):
            response = session.get(f"{BASE_URL}/api/collection/random")
            if response.status_code == 404:
                return
            
            data = response.json()
            source = data.get("source", "")
            assert source != "iso", f"Random record should not be from iso, got source: {source}"
        
        print("PASS: Random records exclude iso source")
    
    def test_random_record_has_expected_fields(self):
        """GET /api/collection/random returns proper record structure"""
        session, _, user_id = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        response = session.get(f"{BASE_URL}/api/collection/random")
        if response.status_code == 404:
            pytest.skip("No records in collection")
        
        data = response.json()
        
        # Check expected fields exist (they may be null)
        expected_fields = ["id", "title", "artist", "cover_url", "user_id"]
        for field in expected_fields:
            assert field in data, f"Missing expected field: {field}"
        
        # Verify user_id matches logged-in user
        assert data.get("user_id") == user_id, "Random record should belong to current user"
        
        print(f"PASS: Random record has all expected fields")
        print(f"  - id: {data.get('id')[:8]}...")
        print(f"  - title: {data.get('title')}")
        print(f"  - artist: {data.get('artist')}")
        print(f"  - cover_url: {'present' if data.get('cover_url') else 'null'}")
        print(f"  - color_variant: {data.get('color_variant', 'null')}")
    
    # ============== POST /api/composer/now-spinning Tests (used by Randomizer) ==============
    
    def test_now_spinning_post_with_record(self):
        """POST /api/composer/now-spinning creates a NOW_SPINNING post"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        # First get a random record
        rand_resp = session.get(f"{BASE_URL}/api/collection/random")
        if rand_resp.status_code == 404:
            pytest.skip("No records to test now-spinning post")
        
        record = rand_resp.json()
        record_id = record.get("id")
        
        # Create now-spinning post (mimics 'Post to Hive' button)
        response = session.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record_id,
            "caption": "TEST_randomizer_post Testing randomizer feature",
            "mood": None
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data.get("post_type") == "NOW_SPINNING", f"Expected NOW_SPINNING, got {data.get('post_type')}"
        assert data.get("record_id") == record_id, "Post should reference the record"
        assert "TEST_randomizer_post" in data.get("caption", ""), "Caption should be preserved"
        
        print(f"PASS: Now spinning post created successfully")
        print(f"  - Post ID: {data.get('id')[:8]}...")
        print(f"  - Record: {record.get('artist')} - {record.get('title')}")
        
        # Cleanup - delete the test post
        if data.get("id"):
            session.delete(f"{BASE_URL}/api/posts/{data.get('id')}")
    
    def test_now_spinning_without_caption(self):
        """POST /api/composer/now-spinning works without caption (optional field)"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        rand_resp = session.get(f"{BASE_URL}/api/collection/random")
        if rand_resp.status_code == 404:
            pytest.skip("No records to test")
        
        record = rand_resp.json()
        
        response = session.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record.get("id"),
            "caption": None,
            "mood": None
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Caption can be null
        assert data.get("post_type") == "NOW_SPINNING"
        
        print("PASS: Now spinning post works without caption (optional)")
        
        # Cleanup
        if data.get("id"):
            session.delete(f"{BASE_URL}/api/posts/{data.get('id')}")
    
    def test_now_spinning_with_caption(self):
        """POST /api/composer/now-spinning correctly saves caption"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        rand_resp = session.get(f"{BASE_URL}/api/collection/random")
        if rand_resp.status_code == 404:
            pytest.skip("No records to test")
        
        record = rand_resp.json()
        test_caption = "TEST_spin Spinning this classic on a lazy afternoon!"
        
        response = session.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record.get("id"),
            "caption": test_caption,
            "track": None,
            "mood": None
        })
        
        assert response.status_code == 200
        data = response.json()
        assert test_caption in data.get("caption", ""), "Caption should be saved"
        
        print("PASS: Caption is correctly saved in now-spinning post")
        
        # Cleanup
        if data.get("id"):
            session.delete(f"{BASE_URL}/api/posts/{data.get('id')}")
    
    def test_now_spinning_invalid_record_returns_404(self):
        """POST /api/composer/now-spinning returns 404 for non-existent record"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        response = session.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": "nonexistent-record-id-12345",
            "caption": "This should fail",
            "mood": None
        })
        
        assert response.status_code == 404, f"Expected 404 for invalid record, got {response.status_code}"
        print("PASS: Now-spinning correctly returns 404 for invalid record ID")
    
    def test_now_spinning_requires_authentication(self):
        """POST /api/composer/now-spinning requires authentication"""
        session_no_auth = requests.Session()
        session_no_auth.headers.update({"Content-Type": "application/json"})
        
        response = session_no_auth.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": "any-id",
            "caption": "test"
        })
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Now-spinning endpoint requires authentication")


class TestRandomizerEdgeCases:
    """Edge case tests for randomizer feature"""
    
    def test_multiple_random_calls_work(self):
        """GET /api/collection/random can be called multiple times"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        success_count = 0
        for i in range(5):
            response = session.get(f"{BASE_URL}/api/collection/random")
            if response.status_code in [200, 404]:
                success_count += 1
        
        assert success_count == 5, "All random calls should succeed (or return 404 if empty)"
        print(f"PASS: Multiple random calls successful ({success_count}/5)")
    
    def test_random_response_no_mongodb_id(self):
        """GET /api/collection/random should not expose MongoDB _id"""
        session, _, _ = get_auth_session()
        assert session is not None, "Failed to authenticate"
        
        response = session.get(f"{BASE_URL}/api/collection/random")
        if response.status_code == 404:
            pytest.skip("No records")
        
        data = response.json()
        assert "_id" not in data, "MongoDB _id should not be exposed in response"
        print("PASS: Response does not expose MongoDB _id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
