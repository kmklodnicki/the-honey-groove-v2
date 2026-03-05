"""
Tests for Now Spinning modal merged with Vinyl Mood feature.

Tests cover:
1. POST /api/composer/now-spinning with optional mood field
2. POST /api/composer/now-spinning without mood (null)
3. Feed returns posts with mood field for NOW_SPINNING
4. Verify 'Sunday Morning' renamed to 'Good Morning' in allowed moods
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Valid moods (renamed 'Sunday Morning' to 'Good Morning')
VALID_MOODS = [
    'Late Night', 'Good Morning', 'Rainy Day', 'Road Trip', 
    'Golden Hour', 'Deep Focus', 'Party Mode', 'Lazy Afternoon',
    'Melancholy', 'Upbeat Vibes', 'Cozy Evening', 'Workout'
]


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for demo user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@example.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.fail(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def user_records(auth_token):
    """Get user's record collection to pick a record_id"""
    response = requests.get(f"{BASE_URL}/api/records", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    if response.status_code == 200:
        records = response.json()
        if records:
            return records
    pytest.fail("Failed to get user records")


class TestNowSpinningWithMood:
    """Test Now Spinning composer endpoint with optional mood field"""

    def test_now_spinning_with_mood(self, auth_token, user_records):
        """POST /api/composer/now-spinning accepts optional mood field"""
        record = user_records[0]
        
        response = requests.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record["id"],
            "track": "Test Track",
            "caption": "Testing mood feature",
            "mood": "Late Night"
        }, headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response should have id"
        assert data["post_type"] == "NOW_SPINNING", "Post type should be NOW_SPINNING"
        assert data["mood"] == "Late Night", "Mood should be 'Late Night'"
        assert data["record_id"] == record["id"], "Record ID should match"
        assert data["track"] == "Test Track", "Track should match"
        assert data["caption"] == "Testing mood feature", "Caption should match"

    def test_now_spinning_with_good_morning_mood(self, auth_token, user_records):
        """POST /api/composer/now-spinning with 'Good Morning' (renamed from Sunday Morning)"""
        record = user_records[1] if len(user_records) > 1 else user_records[0]
        
        response = requests.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record["id"],
            "mood": "Good Morning",
            "caption": "Testing Good Morning mood"
        }, headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["mood"] == "Good Morning", "Mood should be 'Good Morning'"

    def test_now_spinning_without_mood(self, auth_token, user_records):
        """POST /api/composer/now-spinning works without mood (null)"""
        record = user_records[2] if len(user_records) > 2 else user_records[0]
        
        response = requests.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record["id"],
            "caption": "No mood selected"
        }, headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["post_type"] == "NOW_SPINNING", "Post type should be NOW_SPINNING"
        assert data.get("mood") is None, "Mood should be None/null"

    def test_now_spinning_with_all_fields_optional(self, auth_token, user_records):
        """POST with only record_id (all other fields optional)"""
        record = user_records[3] if len(user_records) > 3 else user_records[0]
        
        response = requests.post(f"{BASE_URL}/api/composer/now-spinning", json={
            "record_id": record["id"]
        }, headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["post_type"] == "NOW_SPINNING"
        assert data.get("mood") is None
        assert data.get("track") is None
        assert data.get("caption") is None


class TestFeedWithMood:
    """Test that feed returns posts with mood field"""

    def test_feed_returns_mood_field(self, auth_token):
        """GET /api/feed returns posts with mood field for NOW_SPINNING"""
        response = requests.get(f"{BASE_URL}/api/feed", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        posts = response.json()
        
        # Find NOW_SPINNING posts
        now_spinning_posts = [p for p in posts if p["post_type"] == "NOW_SPINNING"]
        assert len(now_spinning_posts) > 0, "Should have at least one NOW_SPINNING post"
        
        # Check that posts have mood field (can be null or string)
        for post in now_spinning_posts:
            assert "mood" in post, f"Post {post['id']} should have mood field"

    def test_explore_returns_mood_field(self, auth_token):
        """GET /api/explore returns posts with mood field"""
        response = requests.get(f"{BASE_URL}/api/explore", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        posts = response.json()
        
        # Find NOW_SPINNING posts
        now_spinning_posts = [p for p in posts if p["post_type"] == "NOW_SPINNING"]
        
        # Check that posts have mood field
        for post in now_spinning_posts:
            assert "mood" in post, f"Post {post['id']} should have mood field"


class TestNewHaulModal:
    """Test that New Haul modal still works correctly"""

    def test_new_haul_post(self, auth_token):
        """POST /api/composer/new-haul still works"""
        response = requests.post(f"{BASE_URL}/api/composer/new-haul", json={
            "store_name": "Test Record Shop",
            "caption": "Found some gems",
            "items": [
                {
                    "discogs_id": 12345,
                    "title": "Test Album",
                    "artist": "Test Artist",
                    "cover_url": "https://example.com/cover.jpg",
                    "year": 2020
                }
            ]
        }, headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["post_type"] == "NEW_HAUL"


class TestISOModal:
    """Test that ISO modal still works correctly"""

    def test_iso_post(self, auth_token):
        """POST /api/composer/iso still works"""
        response = requests.post(f"{BASE_URL}/api/composer/iso", json={
            "artist": "Test Artist ISO",
            "album": "Test Album ISO",
            "pressing_notes": "First pressing",
            "caption": "Looking for this gem"
        }, headers={"Authorization": f"Bearer {auth_token}"})
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["post_type"] == "ISO"


class TestComposerBarButtons:
    """Test that composer bar has correct buttons"""

    def test_no_vinyl_mood_endpoint_needed(self, auth_token):
        """
        Vinyl Mood endpoint still exists for backward compatibility,
        but the frontend no longer uses it (Now Spinning absorbed mood).
        """
        # The endpoint should still exist for old posts
        response = requests.post(f"{BASE_URL}/api/composer/vinyl-mood", json={
            "mood": "Cozy Evening",
            "caption": "Legacy endpoint test"
        }, headers={"Authorization": f"Bearer {auth_token}"})
        
        # Should still work (backward compatibility)
        assert response.status_code == 200, "Legacy vinyl-mood endpoint should still work"
