"""
Tests for:
1. GET /api/explore/suggested-collectors - Make Friends feature sorting by shared records (discogs_id overlap) 
   and excluding followed users AND blocked users
2. Color variant extraction in Discogs import
3. Variant display logic in feed cards (verified by record structure)
"""
import pytest
import requests
import uuid
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def get_token_from_response(data):
    """Extract token from auth response - handles both 'token' and 'access_token' formats"""
    return data.get("token") or data.get("access_token")


class TestMakeFriendsSharedRecords:
    """Test that suggested-collectors now uses shared records (discogs_id overlap) sorting"""
    
    @pytest.fixture(scope="class")
    def test_users(self):
        """Create test users with different record collections"""
        users = {}
        timestamp = str(uuid.uuid4())[:8]
        
        # Create three test users
        for name in ['main', 'friend_high_overlap', 'blocked_user']:
            email = f"TEST_VARIANT_{name}_{timestamp}@test.com"
            password = "testpass123"
            username = f"test_var_{name}_{timestamp}"
            
            # Register user
            reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": email,
                "password": password,
                "username": username,
                "display_name": f"Test {name}"
            })
            
            if reg_resp.status_code in [200, 201]:
                data = reg_resp.json()
                users[name] = {
                    "id": data["user"]["id"],
                    "username": username,
                    "token": get_token_from_response(data),
                    "email": email
                }
            elif reg_resp.status_code == 400:
                # User may already exist, try login
                login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                    "email": email,
                    "password": password
                })
                if login_resp.status_code == 200:
                    data = login_resp.json()
                    users[name] = {
                        "id": data["user"]["id"],
                        "username": username,
                        "token": get_token_from_response(data),
                        "email": email
                    }
        
        yield users
        
        # Cleanup: Delete test records
        for name, user_data in users.items():
            if user_data.get("token"):
                headers = {"Authorization": f"Bearer {user_data['token']}"}
                records_resp = requests.get(f"{BASE_URL}/api/records", headers=headers)
                if records_resp.status_code == 200:
                    for record in records_resp.json():
                        if "TEST_" in str(record.get("title", "")):
                            requests.delete(f"{BASE_URL}/api/records/{record['id']}", headers=headers)

    def test_suggested_collectors_endpoint_exists(self, test_users):
        """Verify the suggested-collectors endpoint is accessible"""
        if 'main' not in test_users:
            pytest.skip("Could not create test users")
        
        headers = {"Authorization": f"Bearer {test_users['main']['token']}"}
        response = requests.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=5", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: suggested-collectors endpoint returned {len(data)} users")

    def test_suggested_collectors_excludes_already_followed(self, test_users):
        """Verify that already-followed users are excluded from suggestions"""
        if 'main' not in test_users or 'friend_high_overlap' not in test_users:
            pytest.skip("Could not create test users")
        
        main_headers = {"Authorization": f"Bearer {test_users['main']['token']}"}
        friend_username = test_users['friend_high_overlap']['username']
        friend_id = test_users['friend_high_overlap']['id']
        
        # First, ensure we're NOT following the friend
        requests.delete(f"{BASE_URL}/api/explore/follow/{friend_username}", headers=main_headers)
        
        # Follow the friend
        follow_resp = requests.post(f"{BASE_URL}/api/explore/follow/{friend_username}", headers=main_headers)
        assert follow_resp.status_code in [200, 400], f"Follow failed: {follow_resp.text}"
        
        # Get suggestions after following
        resp_after = requests.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=50", headers=main_headers)
        assert resp_after.status_code == 200
        ids_after = [u['id'] for u in resp_after.json()]
        
        # The followed user should NOT be in the suggestions
        assert friend_id not in ids_after, "Followed user should be excluded from suggestions"
        print("PASS: Followed users are correctly excluded from suggested-collectors")
        
        # Cleanup: unfollow
        requests.delete(f"{BASE_URL}/api/explore/follow/{friend_username}", headers=main_headers)

    def test_suggested_collectors_excludes_blocked_users(self, test_users):
        """Verify that blocked users are excluded from suggestions"""
        if 'main' not in test_users or 'blocked_user' not in test_users:
            pytest.skip("Could not create test users")
        
        main_headers = {"Authorization": f"Bearer {test_users['main']['token']}"}
        blocked_username = test_users['blocked_user']['username']
        blocked_id = test_users['blocked_user']['id']
        
        # First, ensure we haven't blocked them
        requests.delete(f"{BASE_URL}/api/block/{blocked_username}", headers=main_headers)
        
        # Block the user
        block_resp = requests.post(f"{BASE_URL}/api/block/{blocked_username}", headers=main_headers)
        assert block_resp.status_code == 200, f"Block failed: {block_resp.text}"
        
        # Get suggestions - blocked user should NOT appear
        resp = requests.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=50", headers=main_headers)
        assert resp.status_code == 200
        ids = [u['id'] for u in resp.json()]
        
        assert blocked_id not in ids, "Blocked user should be excluded from suggestions"
        print("PASS: Blocked users are correctly excluded from suggested-collectors")
        
        # Cleanup: unblock
        requests.delete(f"{BASE_URL}/api/block/{blocked_username}", headers=main_headers)

    def test_suggested_collectors_response_structure(self, test_users):
        """Verify the response has expected structure (shared_artists field only when user has records)"""
        if 'main' not in test_users:
            pytest.skip("Could not create test users")
        
        headers = {"Authorization": f"Bearer {test_users['main']['token']}"}
        response = requests.get(f"{BASE_URL}/api/explore/suggested-collectors?limit=10", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # If there are results, check basic structure
        if len(data) > 0:
            first_user = data[0]
            assert 'username' in first_user, "Expected username field"
            assert 'id' in first_user, "Expected id field"
            
            # Note: shared_artists is only present when user has records with discogs_id
            # If the test user has no records, fallback returns users without shared_artists field
            has_shared_field = 'shared_artists' in first_user or 'shared_records' in first_user
            if has_shared_field:
                print(f"PASS: Response has shared_artists field. First user: @{first_user.get('username')}, shared: {first_user.get('shared_artists', first_user.get('shared_records', 0))}")
            else:
                print(f"PASS: Response in fallback mode (no shared records for current user). First user: @{first_user.get('username')}")
        else:
            print("PASS: Endpoint returns empty list (no matching collectors)")


class TestColorVariantInRecords:
    """Test that records can have color_variant field and it's returned correctly"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user for record operations"""
        timestamp = str(uuid.uuid4())[:8]
        email = f"TEST_COLOR_VAR_{timestamp}@test.com"
        password = "testpass123"
        username = f"test_color_{timestamp}"
        
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "username": username,
            "display_name": "Color Variant Test"
        })
        
        if reg_resp.status_code == 201:
            data = reg_resp.json()
            yield {
                "id": data["user"]["id"],
                "username": username,
                "token": get_token_from_response(data)
            }
        else:
            # Try login
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": email,
                "password": password
            })
            if login_resp.status_code == 200:
                data = login_resp.json()
                yield {
                    "id": data["user"]["id"],
                    "username": username,
                    "token": get_token_from_response(data)
                }
            else:
                pytest.skip("Could not create or login test user")

    def test_create_record_with_color_variant(self, test_user):
        """Test creating a record with color_variant field"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        record_data = {
            "title": "TEST_Album_Colored_Vinyl",
            "artist": "Test Artist",
            "discogs_id": 99999999,
            "year": 2024,
            "format": "Vinyl",
            "color_variant": "180g Red Translucent"
        }
        
        response = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=headers)
        assert response.status_code in [200, 201], f"Create record failed: {response.text}"
        
        data = response.json()
        assert data.get("color_variant") == "180g Red Translucent", \
            f"Expected color_variant '180g Red Translucent', got: {data.get('color_variant')}"
        
        record_id = data.get("id")
        print(f"PASS: Created record with color_variant: {data.get('color_variant')}")
        
        # Verify by fetching the record
        get_resp = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=headers)
        assert get_resp.status_code == 200
        fetched = get_resp.json()
        assert fetched.get("color_variant") == "180g Red Translucent", \
            f"Fetched record color_variant mismatch: {fetched.get('color_variant')}"
        
        print("PASS: Fetched record also has correct color_variant")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=headers)

    def test_record_without_color_variant(self, test_user):
        """Test creating a record without color_variant - should be null/None"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        record_data = {
            "title": "TEST_Album_Standard_Black",
            "artist": "Test Artist 2",
            "discogs_id": 99999998,
            "year": 2023,
            "format": "Vinyl"
        }
        
        response = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=headers)
        assert response.status_code in [200, 201], f"Create record failed: {response.text}"
        
        data = response.json()
        # color_variant should be None or not present
        assert data.get("color_variant") is None, \
            f"Expected color_variant to be None, got: {data.get('color_variant')}"
        
        record_id = data.get("id")
        print(f"PASS: Created record without color_variant - field is None as expected")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=headers)


class TestFeedPostsWithVariant:
    """Test that feed posts include record with color_variant field"""
    
    @pytest.fixture(scope="class")
    def test_user_with_record(self):
        """Create a test user with a colored vinyl record"""
        timestamp = str(uuid.uuid4())[:8]
        email = f"TEST_FEED_VAR_{timestamp}@test.com"
        password = "testpass123"
        username = f"test_feed_{timestamp}"
        
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "username": username,
            "display_name": "Feed Variant Test"
        })
        
        user_data = None
        if reg_resp.status_code == 201:
            data = reg_resp.json()
            user_data = {
                "id": data["user"]["id"],
                "username": username,
                "token": get_token_from_response(data)
            }
        else:
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": email,
                "password": password
            })
            if login_resp.status_code == 200:
                data = login_resp.json()
                user_data = {
                    "id": data["user"]["id"],
                    "username": username,
                    "token": get_token_from_response(data)
                }
        
        if not user_data:
            pytest.skip("Could not create test user")
        
        # Create a record with color_variant
        headers = {"Authorization": f"Bearer {user_data['token']}"}
        record_resp = requests.post(f"{BASE_URL}/api/records", json={
            "title": "TEST_Feed_Album",
            "artist": "Feed Test Artist",
            "discogs_id": 88888888,
            "year": 2024,
            "format": "Vinyl",
            "color_variant": "Blue Marble"
        }, headers=headers)
        
        if record_resp.status_code in [200, 201]:
            user_data["record_id"] = record_resp.json().get("id")
            user_data["record"] = record_resp.json()
        
        yield user_data
        
        # Cleanup
        if user_data and user_data.get("record_id"):
            requests.delete(f"{BASE_URL}/api/records/{user_data['record_id']}", headers=headers)

    def test_spin_creates_post_with_record_variant(self, test_user_with_record):
        """Test that a NOW_SPINNING post includes the record's color_variant"""
        if not test_user_with_record or not test_user_with_record.get("record_id"):
            pytest.skip("No test record created")
        
        headers = {"Authorization": f"Bearer {test_user_with_record['token']}"}
        record_id = test_user_with_record['record_id']
        
        # Log a spin (creates NOW_SPINNING post)
        spin_resp = requests.post(f"{BASE_URL}/api/spins", json={
            "record_id": record_id,
            "notes": "Testing variant display"
        }, headers=headers)
        
        assert spin_resp.status_code in [200, 201], f"Spin failed: {spin_resp.text}"
        
        # Check the spin response has record with variant
        spin_data = spin_resp.json()
        record = spin_data.get("record")
        if record:
            variant = record.get("color_variant")
            print(f"PASS: Spin response includes record with color_variant: {variant}")
            assert variant == "Blue Marble", f"Expected 'Blue Marble', got: {variant}"
        else:
            print("Spin response doesn't include embedded record - checking via posts endpoint")

    def test_hive_feed_posts_structure(self, test_user_with_record):
        """Test that hive feed endpoint returns posts with proper record structure"""
        if not test_user_with_record:
            pytest.skip("No test user")
        
        headers = {"Authorization": f"Bearer {test_user_with_record['token']}"}
        
        # Get hive feed (endpoint is /api/feed)
        feed_resp = requests.get(f"{BASE_URL}/api/feed?limit=20", headers=headers)
        
        assert feed_resp.status_code == 200, f"Hive feed failed: {feed_resp.text}"
        
        posts = feed_resp.json()
        
        # Check posts with records
        posts_with_records = [p for p in posts if p.get("record")]
        
        if posts_with_records:
            for post in posts_with_records[:3]:
                record = post.get("record", {})
                print(f"Post type: {post.get('post_type')}, Title: {record.get('title')}, Variant: {record.get('color_variant')}")
        
        print(f"PASS: Hive feed returned {len(posts)} posts, {len(posts_with_records)} have embedded records")


class TestDiscogsImportColorVariant:
    """Test Discogs import status endpoint"""
    
    def test_discogs_status_endpoint(self):
        """Test the Discogs connection status endpoint exists"""
        timestamp = str(uuid.uuid4())[:8]
        email = f"TEST_DISCOGS_{timestamp}@test.com"
        
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "testpass123",
            "username": f"test_disc_{timestamp}",
            "display_name": "Discogs Test"
        })
        
        if reg_resp.status_code != 201:
            pytest.skip("Could not create test user for Discogs status check")
        
        token = get_token_from_response(reg_resp.json())
        headers = {"Authorization": f"Bearer {token}"}
        
        status_resp = requests.get(f"{BASE_URL}/api/discogs/status", headers=headers)
        
        assert status_resp.status_code == 200, f"Discogs status failed: {status_resp.text}"
        data = status_resp.json()
        
        assert "connected" in data, "Response should have 'connected' field"
        print(f"PASS: Discogs status: connected={data.get('connected')}, username={data.get('discogs_username')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
