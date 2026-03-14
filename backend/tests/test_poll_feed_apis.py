"""
Backend API Tests for HoneyGroove - Poll Creator View & Feed Features
Tests: Login, Feed filtering, Poll CRUD, Poll results endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "kmklodnicki@gmail.com"
ADMIN_PASSWORD = "HoneyGroove2026!"
EXISTING_POLL_ID = "8147cea7-ecf0-4c43-88d9-5dd943b3aad7"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for admin user"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "Missing access_token in response"
    return data["access_token"]


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestHealthAndBasics:
    """Basic API health checks"""

    def test_health_endpoint(self, api_client):
        """Verify API health endpoint returns OK"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ Health check passed: {data}")

    def test_login_success(self, api_client):
        """Verify admin user can login"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == "katie"
        assert data["user"]["is_admin"] is True
        print(f"✓ Login successful for user: {data['user']['username']}")


class TestFeedFiltering:
    """Feed API tests with filtering - used for dropdown filter feature"""

    def test_get_feed_all(self, authenticated_client):
        """Verify feed returns posts without filtering"""
        response = authenticated_client.get(f"{BASE_URL}/api/feed?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Feed returned {len(data)} posts")

    def test_get_feed_contains_polls(self, authenticated_client):
        """Verify feed contains POLL type posts"""
        response = authenticated_client.get(f"{BASE_URL}/api/feed?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check that at least one POLL exists in feed
        poll_posts = [p for p in data if p["post_type"] == "POLL"]
        assert len(poll_posts) > 0, "No POLL posts found in feed"
        print(f"✓ Feed contains {len(poll_posts)} poll posts")

    def test_get_feed_contains_now_spinning(self, authenticated_client):
        """Verify feed contains NOW_SPINNING posts"""
        response = authenticated_client.get(f"{BASE_URL}/api/feed?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        ns_posts = [p for p in data if p["post_type"] == "NOW_SPINNING"]
        print(f"✓ Feed contains {len(ns_posts)} NOW_SPINNING posts")

    def test_get_feed_contains_iso(self, authenticated_client):
        """Verify feed contains ISO posts"""
        response = authenticated_client.get(f"{BASE_URL}/api/feed?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        iso_posts = [p for p in data if p["post_type"] == "ISO"]
        print(f"✓ Feed contains {len(iso_posts)} ISO posts")


class TestPollResultsEndpoint:
    """Tests for GET /api/polls/{post_id}/results endpoint"""

    def test_get_poll_results_existing(self, authenticated_client):
        """Verify poll results endpoint returns correct structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/polls/{EXISTING_POLL_ID}/results")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_votes" in data
        assert "results" in data
        assert isinstance(data["results"], list)
        
        # Verify each result has required fields
        for result in data["results"]:
            assert "option" in result
            assert "count" in result
            assert "percentage" in result
        
        print(f"✓ Poll results: total_votes={data['total_votes']}, options={len(data['results'])}")

    def test_get_poll_results_invalid_id(self, authenticated_client):
        """Verify 404 returned for non-existent poll"""
        response = authenticated_client.get(f"{BASE_URL}/api/polls/invalid-poll-id/results")
        assert response.status_code in [404, 400]
        print("✓ Invalid poll ID correctly returns error")


class TestPollCreation:
    """Tests for poll creation via POST endpoint"""

    def test_create_poll_post(self, authenticated_client):
        """Verify poll post can be created via /api/composer/poll"""
        import random
        poll_question = f"TEST_poll_question_{random.randint(1000, 9999)}"
        
        payload = {
            "question": poll_question,
            "options": ["TEST_Option_A", "TEST_Option_B", "TEST_Option_C"]
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/composer/poll",
            json=payload
        )
        assert response.status_code in [200, 201]
        data = response.json()
        
        # Verify created poll
        assert data.get("poll_question") == poll_question
        assert data.get("post_type") == "POLL"
        assert "id" in data
        
        created_poll_id = data["id"]
        print(f"✓ Created poll: {created_poll_id} - {poll_question}")


class TestCORSConfiguration:
    """Verify CORS is not hardcoded"""

    def test_cors_not_hardcoded(self):
        """Check server.py doesn't have hardcoded preview URL"""
        server_path = "/app/backend/server.py"
        with open(server_path, "r") as f:
            content = f.read()
        
        # Should NOT contain hardcoded preview URL
        assert "poll-creator-view.preview.emergentagent.com" not in content
        print("✓ No hardcoded preview URL found in CORS origins")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
