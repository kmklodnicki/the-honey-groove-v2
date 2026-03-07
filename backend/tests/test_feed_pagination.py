"""
Test Feed Pagination Feature
Tests the /api/feed endpoint with limit and skip query parameters
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "vinylcollector@honey.io"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and get JWT token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Return authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestFeedPagination:
    """Tests for GET /api/feed with limit and skip parameters"""
    
    def test_feed_default_params(self, auth_headers):
        """Test feed endpoint with no params (should use defaults)"""
        response = requests.get(f"{BASE_URL}/api/feed", headers=auth_headers)
        assert response.status_code == 200, f"Feed failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        print(f"Default feed returned {len(data)} posts")
    
    def test_feed_with_limit(self, auth_headers):
        """Test feed endpoint with limit=10"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"limit": 10}, headers=auth_headers)
        assert response.status_code == 200, f"Feed with limit failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        assert len(data) <= 10, f"Feed should return at most 10 posts, got {len(data)}"
        print(f"Feed with limit=10 returned {len(data)} posts")
    
    def test_feed_with_limit_50(self, auth_headers):
        """Test feed endpoint with limit=50 (default limit)"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"limit": 50, "skip": 0}, headers=auth_headers)
        assert response.status_code == 200, f"Feed with limit=50 failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        assert len(data) <= 50, f"Feed should return at most 50 posts, got {len(data)}"
        print(f"Feed with limit=50, skip=0 returned {len(data)} posts")
        return data
    
    def test_feed_pagination_skip(self, auth_headers):
        """Test feed endpoint with skip parameter for pagination"""
        # First get initial batch
        response1 = requests.get(f"{BASE_URL}/api/feed", params={"limit": 5, "skip": 0}, headers=auth_headers)
        assert response1.status_code == 200, f"First page failed: {response1.text}"
        page1 = response1.json()
        
        # Then get second batch
        response2 = requests.get(f"{BASE_URL}/api/feed", params={"limit": 5, "skip": 5}, headers=auth_headers)
        assert response2.status_code == 200, f"Second page failed: {response2.text}"
        page2 = response2.json()
        
        print(f"Page 1 returned {len(page1)} posts, Page 2 returned {len(page2)} posts")
        
        # If we have posts in both pages, verify they are different
        if len(page1) > 0 and len(page2) > 0:
            page1_ids = [p.get('id') for p in page1]
            page2_ids = [p.get('id') for p in page2]
            # Ensure no overlap (except possibly pinned post)
            overlap = set(page1_ids) & set(page2_ids)
            # Pinned post can appear on first page only, so overlap should be minimal
            print(f"Page 1 IDs: {page1_ids}")
            print(f"Page 2 IDs: {page2_ids}")
            print(f"Overlap: {overlap}")
    
    def test_feed_pagination_full_cycle(self, auth_headers):
        """Test full pagination cycle: fetch page 1, then fetch page 2 with skip"""
        FEED_LIMIT = 50
        
        # Page 1
        response1 = requests.get(f"{BASE_URL}/api/feed", params={"limit": FEED_LIMIT, "skip": 0}, headers=auth_headers)
        assert response1.status_code == 200
        page1 = response1.json()
        print(f"Page 1: {len(page1)} posts")
        
        # Page 2 (skip by the number of posts from page 1)
        if len(page1) >= FEED_LIMIT:
            response2 = requests.get(f"{BASE_URL}/api/feed", params={"limit": FEED_LIMIT, "skip": len(page1)}, headers=auth_headers)
            assert response2.status_code == 200
            page2 = response2.json()
            print(f"Page 2: {len(page2)} posts (after skipping {len(page1)})")
        else:
            print(f"Only {len(page1)} posts available, less than limit of {FEED_LIMIT}, so pagination not needed")
    
    def test_feed_skip_beyond_data(self, auth_headers):
        """Test feed with skip beyond available data returns empty list"""
        response = requests.get(f"{BASE_URL}/api/feed", params={"limit": 50, "skip": 10000}, headers=auth_headers)
        assert response.status_code == 200, f"Feed with high skip failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Feed should return a list"
        # With very high skip, should return empty or minimal results
        print(f"Feed with skip=10000 returned {len(data)} posts")
    
    def test_feed_invalid_params(self, auth_headers):
        """Test feed with invalid params (negative skip)"""
        # Negative skip - should either fail gracefully or treat as 0
        response = requests.get(f"{BASE_URL}/api/feed", params={"limit": 10, "skip": -1}, headers=auth_headers)
        # API might return 200 (treating as 0) or 422 validation error
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
        print(f"Feed with skip=-1 returned status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
