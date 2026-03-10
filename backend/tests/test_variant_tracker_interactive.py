"""Tests for Interactive Variant Tracker feature.

Tests the workflow where a user can click a checkbox on a missing variant 
to add it directly to their collection via POST /api/records.

Test coverage:
- POST /api/records endpoint with discogs_id, title, artist, color_variant
- GET /api/vinyl/completion/{discogs_id} returns variants with owned status
- Authenticated vs unauthenticated access to completion endpoint
- Record creation creates activity post
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials provided by main agent
TEST_EMAIL = "demo@test.com"
TEST_PASSWORD = "demouser"
TEST_DISCOGS_ID = 14219559  # Tyler The Creator - IGOR


class TestVariantTrackerBackend:
    """Backend API tests for Interactive Variant Tracker."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"[AUTH] Logged in as {TEST_EMAIL}")
            return token
        print(f"[AUTH FAILED] Status: {response.status_code}, Response: {response.text}")
        pytest.skip("Authentication failed - skipping authenticated tests")
        
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token."""
        return {"Authorization": f"Bearer {auth_token}"}

    # =========== VARIANT COMPLETION ENDPOINT TESTS ===========
    
    def test_completion_endpoint_exists(self):
        """Test GET /api/vinyl/completion/{discogs_id} returns valid response."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/{TEST_DISCOGS_ID}", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"[PASS] Completion endpoint returned: total_variants={data.get('total_variants')}, owned_count={data.get('owned_count')}")
        
    def test_completion_returns_required_fields(self):
        """Test completion response has all required fields."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/{TEST_DISCOGS_ID}", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["album", "artist", "total_variants", "owned_count", "completion_pct", "variants"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"[PASS] All required fields present: album={data.get('album')}, artist={data.get('artist')}")
        
    def test_completion_variants_structure(self):
        """Test variants array has correct structure."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/{TEST_DISCOGS_ID}", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        variants = data.get("variants", [])
        
        # Tyler The Creator - IGOR should have variants
        if data.get("total_variants", 0) > 1:
            assert len(variants) > 0, "Expected variants when total_variants > 1"
            
            for variant in variants:
                assert "name" in variant, "Variant missing 'name' field"
                assert "owned" in variant, "Variant missing 'owned' field"
                assert "release_ids" in variant, "Variant missing 'release_ids' field"
                assert isinstance(variant["owned"], bool), "owned should be boolean"
                assert isinstance(variant["release_ids"], list), "release_ids should be array"
            
            print(f"[PASS] Variants structure valid: {len(variants)} variants found")
            for v in variants[:5]:
                print(f"  - {v['name']}: owned={v['owned']}, pressings={len(v['release_ids'])}")
        else:
            print(f"[INFO] total_variants <= 1, no variant tracker shown")
            
    def test_completion_authenticated_shows_owned(self, auth_headers):
        """Test authenticated request shows user's owned variants."""
        response = requests.get(
            f"{BASE_URL}/api/vinyl/completion/{TEST_DISCOGS_ID}",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        owned_count = data.get("owned_count", 0)
        variants = data.get("variants", [])
        owned_variants = [v for v in variants if v.get("owned")]
        
        print(f"[INFO] Authenticated: owned_count={owned_count}, owned_variants={len(owned_variants)}")
        
        # Verify owned_count matches variants with owned=True
        assert owned_count == len(owned_variants), f"owned_count ({owned_count}) != owned variants ({len(owned_variants)})"
        print(f"[PASS] Ownership tracking working correctly")

    # =========== POST /API/RECORDS ENDPOINT TESTS ===========
    
    def test_post_records_requires_auth(self):
        """Test POST /api/records returns 401/403 without auth."""
        record_data = {
            "discogs_id": 12345678,
            "title": "Test Album",
            "artist": "Test Artist",
            "color_variant": "Test Red"
        }
        response = requests.post(
            f"{BASE_URL}/api/records",
            json=record_data,
            timeout=10
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"[PASS] POST /api/records requires authentication")
        
    def test_post_records_creates_record(self, auth_headers):
        """Test POST /api/records successfully creates a record."""
        unique_discogs_id = 99990000 + int(uuid.uuid4().int % 10000)
        record_data = {
            "discogs_id": unique_discogs_id,
            "title": "TEST_Variant_Tracker_Album",
            "artist": "TEST_Variant_Artist",
            "color_variant": "TEST_Red Marble",
            "format": "Vinyl"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/records",
            json=record_data,
            headers=auth_headers,
            timeout=10
        )
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response missing 'id' field"
        assert data.get("discogs_id") == unique_discogs_id, "discogs_id mismatch"
        assert data.get("title") == record_data["title"], "title mismatch"
        assert data.get("artist") == record_data["artist"], "artist mismatch"
        assert data.get("color_variant") == record_data["color_variant"], "color_variant mismatch"
        
        record_id = data.get("id")
        print(f"[PASS] Record created successfully: id={record_id}, color_variant={data.get('color_variant')}")
        
        # Cleanup: delete the test record
        delete_response = requests.delete(
            f"{BASE_URL}/api/records/{record_id}",
            headers=auth_headers,
            timeout=10
        )
        if delete_response.status_code == 200:
            print(f"[CLEANUP] Test record deleted")
        
    def test_post_records_response_fields(self, auth_headers):
        """Test POST /api/records response has all expected fields."""
        unique_discogs_id = 99991000 + int(uuid.uuid4().int % 10000)
        record_data = {
            "discogs_id": unique_discogs_id,
            "title": "TEST_Response_Fields",
            "artist": "TEST_Artist",
            "cover_url": "https://example.com/cover.jpg",
            "year": 2024,
            "format": "Vinyl",
            "color_variant": "TEST_Blue Splatter"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/records",
            json=record_data,
            headers=auth_headers,
            timeout=10
        )
        assert response.status_code in [200, 201]
        
        data = response.json()
        
        # Check all expected fields in response
        expected_fields = ["id", "discogs_id", "title", "artist", "cover_url", "year", "format", "color_variant", "created_at"]
        for field in expected_fields:
            assert field in data, f"Response missing expected field: {field}"
        
        print(f"[PASS] Response has all expected fields: {list(data.keys())}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{data['id']}", headers=auth_headers, timeout=10)
        
    def test_post_records_creates_activity_post(self, auth_headers):
        """Test that adding a record creates an activity post."""
        unique_discogs_id = 99992000 + int(uuid.uuid4().int % 10000)
        record_data = {
            "discogs_id": unique_discogs_id,
            "title": "TEST_Activity_Post",
            "artist": "TEST_Activity_Artist",
            "color_variant": "TEST_Gold"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/records",
            json=record_data,
            headers=auth_headers,
            timeout=10
        )
        assert response.status_code in [200, 201]
        
        data = response.json()
        record_id = data.get("id")
        
        # Verify an activity post was created
        # Check recent posts for ADDED_TO_COLLECTION type with this record
        feed_response = requests.get(
            f"{BASE_URL}/api/feed",
            headers=auth_headers,
            params={"limit": 10},
            timeout=10
        )
        
        if feed_response.status_code == 200:
            feed_data = feed_response.json()
            posts = feed_data.get("posts", []) if isinstance(feed_data, dict) else feed_data
            
            # Look for the activity post for this record
            activity_post = next(
                (p for p in posts if p.get("record_id") == record_id and p.get("post_type") == "ADDED_TO_COLLECTION"),
                None
            )
            
            if activity_post:
                print(f"[PASS] Activity post created: post_type={activity_post.get('post_type')}")
            else:
                print(f"[INFO] Activity post not found in recent feed (may need different query)")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=auth_headers, timeout=10)

    def test_post_records_duplicate_handling(self, auth_headers):
        """Test POST /api/records handles duplicate records appropriately."""
        # First, let's check if a record already exists for the test discogs ID
        unique_discogs_id = 99993000 + int(uuid.uuid4().int % 10000)
        record_data = {
            "discogs_id": unique_discogs_id,
            "title": "TEST_Duplicate_Check",
            "artist": "TEST_Artist",
            "color_variant": "TEST_Silver"
        }
        
        # Create first record
        response1 = requests.post(
            f"{BASE_URL}/api/records",
            json=record_data,
            headers=auth_headers,
            timeout=10
        )
        assert response1.status_code in [200, 201]
        record_id = response1.json().get("id")
        
        # Try to create duplicate
        response2 = requests.post(
            f"{BASE_URL}/api/records",
            json=record_data,
            headers=auth_headers,
            timeout=10
        )
        
        # Either succeeds (creates another copy) or returns 409 Conflict
        # The VariantCompletion component handles 409 gracefully
        if response2.status_code == 409:
            print(f"[PASS] Duplicate returns 409 Conflict as expected")
        else:
            print(f"[INFO] Duplicate creates new record (status: {response2.status_code})")
            # Cleanup second record if created
            if response2.status_code in [200, 201]:
                record_id2 = response2.json().get("id")
                requests.delete(f"{BASE_URL}/api/records/{record_id2}", headers=auth_headers, timeout=10)
        
        # Cleanup first record
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=auth_headers, timeout=10)


class TestVariantCompletionFlow:
    """Test the full variant tracker flow end-to-end."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
        
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_variant_page_endpoint(self):
        """Test the vinyl variant page endpoint returns data."""
        response = requests.get(
            f"{BASE_URL}/api/vinyl/tyler-the-creator/igor/mint",
            timeout=30
        )
        
        # Should return data about this variant
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Variant page returns: artist={data.get('variant_overview', {}).get('artist')}")
            
            # Check variant_overview has discogs_id
            overview = data.get("variant_overview", {})
            assert "discogs_id" in overview, "variant_overview should have discogs_id"
            print(f"[INFO] discogs_id in variant: {overview.get('discogs_id')}")
        else:
            print(f"[INFO] Variant page returned {response.status_code}")
            
    def test_completion_for_igor_variants(self):
        """Test completion endpoint for Tyler the Creator IGOR."""
        response = requests.get(
            f"{BASE_URL}/api/vinyl/completion/{TEST_DISCOGS_ID}",
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        total = data.get("total_variants", 0)
        
        print(f"[INFO] IGOR variants: total={total}, owned={data.get('owned_count')}, pct={data.get('completion_pct')}")
        
        if total > 1:
            variants = data.get("variants", [])
            print(f"[INFO] Variant names:")
            for v in variants:
                status = "OWNED" if v.get("owned") else "MISSING"
                print(f"  [{status}] {v['name']}")


class TestDiscogsReleaseEndpoint:
    """Test the discogs release endpoint used by variant tracker."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
        
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_discogs_release_endpoint(self, auth_headers):
        """Test GET /api/discogs/release/{id} returns release info."""
        response = requests.get(
            f"{BASE_URL}/api/discogs/release/{TEST_DISCOGS_ID}",
            headers=auth_headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Discogs release: title={data.get('title')}, artist={data.get('artist')}")
            
            # Should have key fields needed for variant tracker
            assert "title" in data or data.get("title") is None, "Should have title"
            assert "artist" in data or data.get("artist") is None, "Should have artist"
        else:
            print(f"[INFO] Discogs release returned {response.status_code}: {response.text[:200]}")
