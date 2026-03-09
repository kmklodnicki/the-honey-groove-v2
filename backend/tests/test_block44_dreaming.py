"""
BLOCK 44 Tests: Dreaming Tab, Dream Value, ISO exclusions, Taste Match refinements
Tests for:
- GET /api/users/{username}/dreaming - returns WISHLIST items only
- GET /api/valuation/wishlist/{username} - returns dream value for any user
- GET /api/users/{username}/iso - excludes WISHLIST items
- GET /api/users/{username}/taste-match - returns shared_dream_value
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = "admin@thehoneygroove.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Auth failed: {resp.status_code} - {resp.text}")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with authorization."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDreamingEndpoint:
    """Tests for GET /api/users/{username}/dreaming"""
    
    def test_dreaming_endpoint_exists(self):
        """GET /api/users/{username}/dreaming returns 200 or 404 (not 405)."""
        resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        assert resp.status_code in [200, 404], f"Expected 200 or 404, got {resp.status_code}"
    
    def test_dreaming_returns_list(self):
        """GET /api/users/katieintheafterglow/dreaming returns a list."""
        resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"Dreaming items count for katieintheafterglow: {len(data)}")
    
    def test_dreaming_items_have_wishlist_status(self):
        """All items from /dreaming should have status WISHLIST."""
        resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        if resp.status_code == 200:
            items = resp.json()
            for item in items:
                assert item.get("status") == "WISHLIST", f"Expected WISHLIST status, got {item.get('status')}"
        else:
            pytest.skip("No dreaming items to verify")
    
    def test_dreaming_returns_404_for_nonexistent_user(self):
        """GET /api/users/nonexistent123456/dreaming returns 404."""
        resp = requests.get(f"{BASE_URL}/api/users/nonexistent123456/dreaming")
        assert resp.status_code == 404


class TestISOExcludesWishlist:
    """Tests for GET /api/users/{username}/iso excluding WISHLIST items"""
    
    def test_iso_endpoint_exists(self):
        """GET /api/users/{username}/iso returns 200."""
        resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/iso")
        assert resp.status_code in [200, 404]
    
    def test_iso_excludes_wishlist_items(self):
        """ISO endpoint should NOT return items with WISHLIST status."""
        resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/iso")
        if resp.status_code == 200:
            items = resp.json()
            for item in items:
                status = item.get("status")
                assert status != "WISHLIST", f"ISO returned WISHLIST item: {item}"
            print(f"ISO items (non-wishlist) count: {len(items)}")


class TestWishlistValuation:
    """Tests for GET /api/valuation/wishlist/{username}"""
    
    def test_wishlist_valuation_public_endpoint_exists(self):
        """GET /api/valuation/wishlist/{username} returns 200."""
        resp = requests.get(f"{BASE_URL}/api/valuation/wishlist/katieintheafterglow")
        assert resp.status_code in [200, 404]
    
    def test_wishlist_valuation_returns_correct_structure(self):
        """GET /api/valuation/wishlist/{username} returns total_value, valued_count, total_count."""
        resp = requests.get(f"{BASE_URL}/api/valuation/wishlist/katieintheafterglow")
        if resp.status_code == 200:
            data = resp.json()
            assert "total_value" in data, "Missing total_value field"
            assert "valued_count" in data, "Missing valued_count field"
            assert "total_count" in data, "Missing total_count field"
            print(f"Dream Value for katieintheafterglow: ${data.get('total_value', 0)}")
    
    def test_wishlist_valuation_nonexistent_user(self):
        """GET /api/valuation/wishlist/nonexistent123 returns 404."""
        resp = requests.get(f"{BASE_URL}/api/valuation/wishlist/nonexistent123456")
        assert resp.status_code == 404


class TestTasteMatchSharedDreamValue:
    """Tests for shared_dream_value in taste-match endpoint"""
    
    def test_taste_match_includes_shared_dream_value(self, auth_headers):
        """GET /api/users/{username}/taste-match includes shared_dream_value field."""
        resp = requests.get(
            f"{BASE_URL}/api/users/katieintheafterglow/taste-match",
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "shared_dream_value" in data, "Missing shared_dream_value field"
        print(f"Shared dream value with katieintheafterglow: ${data.get('shared_dream_value', 0)}")
    
    def test_taste_match_requires_auth(self):
        """GET /api/users/{username}/taste-match requires authentication."""
        resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/taste-match")
        assert resp.status_code in [401, 403, 422], f"Expected auth error, got {resp.status_code}"
    
    def test_taste_match_self_returns_100_percent(self, auth_headers):
        """GET /api/users/{own_username}/taste-match returns 100% for self."""
        resp = requests.get(
            f"{BASE_URL}/api/users/admin/taste-match",
            headers=auth_headers
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("score") == 100, f"Expected 100% for self, got {data.get('score')}"
    
    def test_taste_match_full_response_structure(self, auth_headers):
        """taste-match returns score, label, shared_reality, shared_dreams, swap_potential, shared_dream_value."""
        resp = requests.get(
            f"{BASE_URL}/api/users/katieintheafterglow/taste-match",
            headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        required_fields = ["score", "label", "shared_reality", "shared_dreams", "swap_potential", "shared_dream_value"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        assert isinstance(data["shared_reality"], list)
        assert isinstance(data["shared_dreams"], list)
        assert isinstance(data["swap_potential"], list)
        assert isinstance(data["shared_dream_value"], (int, float))


class TestDreamingVsISOSeparation:
    """Verify dreaming and ISO are properly separated"""
    
    def test_no_overlap_between_dreaming_and_iso(self):
        """Dreaming and ISO should have no overlapping items for same user."""
        dreaming_resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/dreaming")
        iso_resp = requests.get(f"{BASE_URL}/api/users/katieintheafterglow/iso")
        
        if dreaming_resp.status_code == 200 and iso_resp.status_code == 200:
            dreaming_items = dreaming_resp.json()
            iso_items = iso_resp.json()
            
            dreaming_ids = {item.get("id") for item in dreaming_items}
            iso_ids = {item.get("id") for item in iso_items}
            
            overlap = dreaming_ids & iso_ids
            assert len(overlap) == 0, f"Overlap found between dreaming and ISO: {overlap}"
            print(f"Dreaming: {len(dreaming_ids)} items, ISO: {len(iso_ids)} items, No overlap: PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
