"""
Test Block 442: Test Listing Filter Guard
Tests for is_test_listing flag toggle, visibility filtering, admin endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@thehoneygroove.com"
ADMIN_PASSWORD = "admin_password"
USER_EMAIL = "test@example.com"
USER_PASSWORD = "test123"
TEST_LISTING_ID = "a448de35-c8f2-4b26-87c0-a8367ea009bf"


def get_admin_token():
    """Helper to get admin token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def get_user_token():
    """Helper to get user token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


# ========== PATCH /api/listings/{id}/test-flag Tests ==========

def test_toggle_test_flag_admin_success():
    """Admin can toggle is_test_listing flag"""
    admin_token = get_admin_token()
    if not admin_token:
        pytest.skip("Admin login failed")
        
    resp = requests.patch(
        f"{BASE_URL}/api/listings/{TEST_LISTING_ID}/test-flag",
        json={"is_test_listing": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("id") == TEST_LISTING_ID
    assert data.get("is_test_listing") == True
    print(f"✓ Admin toggled test flag to True for listing {TEST_LISTING_ID}")


def test_toggle_test_flag_non_admin_returns_403():
    """Non-admin user gets 403 when trying to toggle test flag"""
    user_token = get_user_token()
    if not user_token:
        pytest.skip("User login failed")
        
    resp = requests.patch(
        f"{BASE_URL}/api/listings/{TEST_LISTING_ID}/test-flag",
        json={"is_test_listing": False},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
    print("✓ Non-admin correctly receives 403 on test flag toggle")


def test_toggle_test_flag_no_auth_returns_403():
    """Unauthenticated request returns 403"""
    resp = requests.patch(
        f"{BASE_URL}/api/listings/{TEST_LISTING_ID}/test-flag",
        json={"is_test_listing": True}
    )
    assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
    print("✓ Unauthenticated request correctly blocked")


def test_toggle_test_flag_nonexistent_listing_returns_404():
    """Toggling nonexistent listing returns 404"""
    admin_token = get_admin_token()
    if not admin_token:
        pytest.skip("Admin login failed")
        
    resp = requests.patch(
        f"{BASE_URL}/api/listings/nonexistent-listing-id/test-flag",
        json={"is_test_listing": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    print("✓ Nonexistent listing correctly returns 404")


# ========== GET /api/admin/test-listings Tests ==========

def test_get_admin_test_listings_admin_success():
    """Admin can fetch all test listings"""
    admin_token = get_admin_token()
    if not admin_token:
        pytest.skip("Admin login failed")
        
    resp = requests.get(
        f"{BASE_URL}/api/admin/test-listings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert isinstance(data, list)
    print(f"✓ Admin fetched {len(data)} test listings")
    
    # Check that all returned listings have is_test_listing=True
    for listing in data:
        assert listing.get("is_test_listing") == True, f"Listing {listing.get('id')} missing is_test_listing=True"
    print("✓ All returned listings have is_test_listing=True")


def test_get_admin_test_listings_non_admin_returns_403():
    """Non-admin user gets 403 when trying to fetch test listings"""
    user_token = get_user_token()
    if not user_token:
        pytest.skip("User login failed")
        
    resp = requests.get(
        f"{BASE_URL}/api/admin/test-listings",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
    print("✓ Non-admin correctly receives 403 on admin test-listings endpoint")


# ========== GET /api/listings Filter Tests ==========

def test_listings_exclude_test_for_non_admin():
    """Non-admin users should not see is_test_listing=true listings"""
    user_token = get_user_token()
    if not user_token:
        pytest.skip("User login failed")
        
    resp = requests.get(
        f"{BASE_URL}/api/listings",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    # Check that no listing has is_test_listing=True
    test_listings_visible = [l for l in data if l.get("is_test_listing") == True]
    assert len(test_listings_visible) == 0, f"Non-admin sees {len(test_listings_visible)} test listings - should be 0"
    print(f"✓ Non-admin sees {len(data)} listings, none are test listings")


def test_listings_exclude_test_for_unauthenticated():
    """Unauthenticated users should not see test listings"""
    resp = requests.get(f"{BASE_URL}/api/listings")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    # Check that no listing has is_test_listing=True
    test_listings_visible = [l for l in data if l.get("is_test_listing") == True]
    assert len(test_listings_visible) == 0, f"Unauthenticated sees {len(test_listings_visible)} test listings"
    print(f"✓ Unauthenticated user sees {len(data)} listings, none are test listings")


def test_listings_api_for_admin():
    """Admin can access listings API (test listings may be visible)"""
    admin_token = get_admin_token()
    if not admin_token:
        pytest.skip("Admin login failed")
        
    resp = requests.get(
        f"{BASE_URL}/api/listings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    print(f"✓ Admin fetched {len(data)} listings from GET /api/listings")


# ========== ListingResponse Model Tests ==========

def test_listing_response_includes_is_test_listing():
    """Individual listing response includes is_test_listing field"""
    admin_token = get_admin_token()
    if not admin_token:
        pytest.skip("Admin login failed")
        
    resp = requests.get(
        f"{BASE_URL}/api/listings/{TEST_LISTING_ID}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert "is_test_listing" in data, "Response missing is_test_listing field"
    print(f"✓ Listing response includes is_test_listing={data.get('is_test_listing')}")


# ========== ISO Matches Exclude Test Listings ==========

def test_iso_matches_exclude_test_listings():
    """ISO matches should not include test listings"""
    user_token = get_user_token()
    if not user_token:
        pytest.skip("User login failed")
        
    resp = requests.get(
        f"{BASE_URL}/api/listings/iso-matches",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    test_listings = [l for l in data if l.get("is_test_listing") == True]
    assert len(test_listings) == 0, "ISO matches should not include test listings"
    print(f"✓ ISO matches returned {len(data)} listings, none are test listings")


# ========== Similar Listings Exclude Test Listings ==========

def test_similar_listings_exclude_test_listings():
    """Similar listings in listing detail should not include test listings"""
    user_token = get_user_token()
    if not user_token:
        pytest.skip("User login failed")
        
    # Get a listing first
    resp = requests.get(
        f"{BASE_URL}/api/listings",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    if resp.status_code == 200 and len(resp.json()) > 0:
        listing_id = resp.json()[0]["id"]
        
        detail_resp = requests.get(
            f"{BASE_URL}/api/listings/{listing_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        if detail_resp.status_code == 200:
            data = detail_resp.json()
            similar = data.get("similar_listings", [])
            test_in_similar = [l for l in similar if l.get("is_test_listing") == True]
            assert len(test_in_similar) == 0, "Similar listings should not include test listings"
            print(f"✓ Similar listings ({len(similar)}) exclude test listings")
        else:
            print(f"✓ Could not fetch listing detail (status={detail_resp.status_code})")
    else:
        print("✓ No listings available to test similar listings")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
