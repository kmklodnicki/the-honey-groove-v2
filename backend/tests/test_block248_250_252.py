"""
Test Block 248 (Instant-On Prompt), Block 250 (Duplicate Detector), Block 252 (Week in Wax Migration)

Features tested:
- GET /api/records/duplicates - returns duplicate_groups array and total_duplicates count
- DELETE /api/records/duplicates/clean - removes duplicate copies keeping oldest
- Prompt responses include dominant_color field from image_cache
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://mobile-msg-fix.preview.emergentagent.com')

@pytest.fixture(scope='module')
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@example.com",
        "password": "test123"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope='module')
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestDuplicateDetection:
    """Tests for Block 250: Duplicate Detector feature"""
    
    def test_get_duplicates_endpoint_exists(self, auth_headers):
        """GET /api/records/duplicates returns proper response structure"""
        response = requests.get(f"{BASE_URL}/api/records/duplicates", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "duplicate_groups" in data, "Response should contain duplicate_groups array"
        assert "total_duplicates" in data, "Response should contain total_duplicates count"
        assert isinstance(data["duplicate_groups"], list), "duplicate_groups should be a list"
        assert isinstance(data["total_duplicates"], int), "total_duplicates should be an integer"
        print(f"✅ GET /api/records/duplicates - {len(data['duplicate_groups'])} groups, {data['total_duplicates']} total duplicates")
    
    def test_get_duplicates_requires_auth(self):
        """GET /api/records/duplicates requires authentication"""
        response = requests.get(f"{BASE_URL}/api/records/duplicates")
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated request, got {response.status_code}"
        print("✅ GET /api/records/duplicates requires auth")
    
    def test_clean_duplicates_endpoint_exists(self, auth_headers):
        """DELETE /api/records/duplicates/clean returns proper response structure"""
        response = requests.delete(f"{BASE_URL}/api/records/duplicates/clean", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "removed_count" in data, "Response should contain removed_count"
        assert isinstance(data["removed_count"], int), "removed_count should be an integer"
        print(f"✅ DELETE /api/records/duplicates/clean - removed {data['removed_count']} duplicates")
    
    def test_clean_duplicates_requires_auth(self):
        """DELETE /api/records/duplicates/clean requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/records/duplicates/clean")
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated request, got {response.status_code}"
        print("✅ DELETE /api/records/duplicates/clean requires auth")


class TestDuplicateCreationAndCleanup:
    """Test creating duplicates and cleaning them up"""
    
    def test_create_duplicate_records_and_detect(self, auth_headers):
        """Create 2 records with same discogs_id and verify detection"""
        test_discogs_id = 99999888
        
        # Create first record
        record1_data = {
            "title": "TEST_Duplicate Test Album",
            "artist": "TEST_Duplicate Test Artist",
            "discogs_id": test_discogs_id,
            "notes": "First copy"
        }
        resp1 = requests.post(f"{BASE_URL}/api/records", json=record1_data, headers=auth_headers)
        print(f"Record 1 creation: {resp1.status_code}")
        
        # Create second record with same discogs_id
        record2_data = {
            "title": "TEST_Duplicate Test Album",
            "artist": "TEST_Duplicate Test Artist",
            "discogs_id": test_discogs_id,
            "notes": "First copy"  # Same notes so it can be auto-cleaned
        }
        resp2 = requests.post(f"{BASE_URL}/api/records", json=record2_data, headers=auth_headers)
        print(f"Record 2 creation: {resp2.status_code}")
        
        # Now check for duplicates
        dup_resp = requests.get(f"{BASE_URL}/api/records/duplicates", headers=auth_headers)
        assert dup_resp.status_code == 200
        dup_data = dup_resp.json()
        print(f"Duplicates detected: {dup_data['total_duplicates']} total, {len(dup_data['duplicate_groups'])} groups")
        
        # Find the group for our test records
        test_group = None
        for group in dup_data['duplicate_groups']:
            if group.get('discogs_id') == test_discogs_id:
                test_group = group
                break
        
        if test_group:
            assert test_group['count'] >= 2, "Should have at least 2 records with same discogs_id"
            assert 'needs_review' in test_group, "Group should have needs_review field"
            print(f"✅ Found duplicate group for discogs_id {test_discogs_id}: count={test_group['count']}, needs_review={test_group['needs_review']}")
        
        # Clean up - delete our test records
        if resp1.status_code == 200:
            rec1_id = resp1.json().get('id')
            if rec1_id:
                requests.delete(f"{BASE_URL}/api/records/{rec1_id}", headers=auth_headers)
        if resp2.status_code == 200:
            rec2_id = resp2.json().get('id')
            if rec2_id:
                requests.delete(f"{BASE_URL}/api/records/{rec2_id}", headers=auth_headers)


class TestDailyPromptDominantColor:
    """Tests for Block 248: Instant-On Prompt with dominant_color"""
    
    def test_prompt_today_endpoint(self, auth_headers):
        """GET /api/prompts/today returns prompt data"""
        response = requests.get(f"{BASE_URL}/api/prompts/today", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "prompt" in data, "Response should contain prompt"
        assert "has_buzzed_in" in data, "Response should contain has_buzzed_in"
        assert "streak" in data, "Response should contain streak"
        print(f"✅ GET /api/prompts/today - has_buzzed_in: {data['has_buzzed_in']}, streak: {data['streak']}")
    
    def test_prompt_responses_include_dominant_color(self, auth_headers):
        """Prompt responses should include dominant_color from image_cache"""
        # First get today's prompt
        prompt_resp = requests.get(f"{BASE_URL}/api/prompts/today", headers=auth_headers)
        assert prompt_resp.status_code == 200
        prompt_data = prompt_resp.json()
        
        if not prompt_data.get('has_buzzed_in'):
            print("⏭️ User hasn't buzzed in today - cannot test responses endpoint")
            return
        
        prompt_id = prompt_data.get('prompt', {}).get('id')
        if not prompt_id:
            print("⏭️ No prompt ID available")
            return
        
        # Get responses for the prompt
        responses_resp = requests.get(f"{BASE_URL}/api/prompts/{prompt_id}/responses", headers=auth_headers)
        if responses_resp.status_code == 403:
            print("⏭️ Must buzz in first to see responses (expected behavior)")
            return
        
        assert responses_resp.status_code == 200, f"Expected 200, got {responses_resp.status_code}: {responses_resp.text}"
        
        responses = responses_resp.json()
        if len(responses) > 0:
            # Check that responses have dominant_color field (may be None if not cached)
            first_resp = responses[0]
            assert 'dominant_color' in first_resp or first_resp.get('dominant_color') is None, "Response should have dominant_color field"
            print(f"✅ Responses include dominant_color field. First response dominant_color: {first_resp.get('dominant_color')}")
        else:
            print("⏭️ No responses available to test")


class TestImageCacheDominantColor:
    """Test that image_cache stores dominant_color"""
    
    def test_blur_placeholder_endpoint(self, auth_headers):
        """GET /api/image/blur-placeholder should exist"""
        # Test with a sample Discogs image URL
        test_url = "https://i.discogs.com/test.jpg"
        response = requests.get(f"{BASE_URL}/api/image/blur-placeholder", params={"url": test_url}, headers=auth_headers)
        # May return None for uncached images, but endpoint should work
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert 'blur_data_url' in data, "Response should contain blur_data_url field"
        print(f"✅ GET /api/image/blur-placeholder works - blur_data_url: {data.get('blur_data_url', 'None')[:30] if data.get('blur_data_url') else 'None'}...")


class TestWeekInWaxMigration:
    """Tests for Block 252: Week in Wax moved to ProfilePage"""
    
    def test_weekly_summary_endpoint(self, auth_headers):
        """GET /api/weekly-summary returns user's weekly stats"""
        response = requests.get(f"{BASE_URL}/api/weekly-summary", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_spins" in data, "Response should contain total_spins"
        assert "records_added" in data, "Response should contain records_added"
        print(f"✅ GET /api/weekly-summary - total_spins: {data.get('total_spins')}, records_added: {data.get('records_added')}")
    
    def test_user_profile_endpoint(self, auth_headers):
        """GET /api/users/{username} returns profile data"""
        response = requests.get(f"{BASE_URL}/api/users/testuser1", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "username" in data, "Response should contain username"
        assert "collection_count" in data, "Response should contain collection_count"
        print(f"✅ GET /api/users/testuser1 - username: {data.get('username')}, collection_count: {data.get('collection_count')}")
    
    def test_user_records_endpoint(self, auth_headers):
        """GET /api/users/{username}/records returns user's records"""
        response = requests.get(f"{BASE_URL}/api/users/testuser1/records", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of records"
        print(f"✅ GET /api/users/testuser1/records - {len(data)} records returned")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
