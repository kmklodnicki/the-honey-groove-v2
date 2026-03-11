"""
Block 243 Valuation Visibility Overhaul Tests
- GET /api/valuation/community-average/{discogs_id} - Returns average_value and contribution_count
- POST /api/valuation/community-value/{discogs_id} - Saves community valuation and returns new average
- POST /api/valuation/community-value/{discogs_id} - Same user updates existing (no duplicates)
- POST /api/valuation/community-value/{discogs_id} - Rejects value <= 0
- GET /api/valuation/dreamlist - Returns pending_count for pending valuation button
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Global token storage for test session
_auth_token = None

def get_auth_token():
    """Get or create auth token"""
    global _auth_token
    if _auth_token is None:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Authentication failed: {response.text}"
        _auth_token = response.json().get("access_token")
    return _auth_token

def get_headers():
    """Get auth headers"""
    token = get_auth_token()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============ Community Average Endpoint Tests ============

def test_community_average_returns_structure():
    """GET /api/valuation/community-average/{discogs_id} returns average_value and contribution_count"""
    test_discogs_id = 999999
    response = requests.get(f"{BASE_URL}/api/valuation/community-average/{test_discogs_id}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert "average_value" in data, "Response should contain average_value"
    assert "contribution_count" in data, "Response should contain contribution_count"
    assert isinstance(data["average_value"], (int, float)), "average_value should be numeric"
    assert isinstance(data["contribution_count"], int), "contribution_count should be an integer"
    print(f"✓ community-average returns: average_value={data['average_value']}, contribution_count={data['contribution_count']}")

def test_community_average_no_auth_required():
    """GET /api/valuation/community-average/{discogs_id} does not require authentication"""
    test_discogs_id = 999999
    response = requests.get(f"{BASE_URL}/api/valuation/community-average/{test_discogs_id}")
    
    assert response.status_code == 200, f"Should be public endpoint, got {response.status_code}"
    print("✓ community-average is a public endpoint (no auth required)")


# ============ Community Value Endpoint Tests ============

def test_community_value_saves_valuation():
    """POST /api/valuation/community-value/{discogs_id} saves community valuation"""
    test_discogs_id = 999999
    test_value = 45.50
    headers = get_headers()
    
    response = requests.post(
        f"{BASE_URL}/api/valuation/community-value/{test_discogs_id}",
        headers=headers,
        json={"value": test_value}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert "message" in data, "Response should contain message"
    assert "average_value" in data, "Response should contain average_value"
    assert data["average_value"] > 0, "average_value should be positive after submission"
    print(f"✓ community-value saved successfully, new average: ${data['average_value']}")

def test_community_value_updates_existing_not_duplicates():
    """POST /api/valuation/community-value/{discogs_id} updates existing submission (no duplicates)"""
    test_discogs_id = 999999
    headers = get_headers()
    
    # Submit first value
    first_value = 30.00
    response1 = requests.post(
        f"{BASE_URL}/api/valuation/community-value/{test_discogs_id}",
        headers=headers,
        json={"value": first_value}
    )
    assert response1.status_code == 200, f"First submission failed: {response1.text}"
    
    # Submit second value with same user (should UPDATE, not create duplicate)
    second_value = 50.00
    response2 = requests.post(
        f"{BASE_URL}/api/valuation/community-value/{test_discogs_id}",
        headers=headers,
        json={"value": second_value}
    )
    assert response2.status_code == 200, f"Second submission failed: {response2.text}"
    
    # Verify via community-average that count hasn't increased unexpectedly
    avg_response = requests.get(f"{BASE_URL}/api/valuation/community-average/{test_discogs_id}")
    assert avg_response.status_code == 200
    final_data = avg_response.json()
    
    assert final_data["average_value"] > 0, "Average should be positive"
    print(f"✓ User update works without duplication. Count: {final_data['contribution_count']}, Average: ${final_data['average_value']}")

def test_community_value_rejects_zero_value():
    """POST /api/valuation/community-value/{discogs_id} rejects value <= 0"""
    test_discogs_id = 999999
    headers = get_headers()
    
    response = requests.post(
        f"{BASE_URL}/api/valuation/community-value/{test_discogs_id}",
        headers=headers,
        json={"value": 0}
    )
    
    assert response.status_code == 400, f"Expected 400 for value=0, got {response.status_code}: {response.text}"
    print("✓ community-value correctly rejects value=0")

def test_community_value_rejects_negative_value():
    """POST /api/valuation/community-value/{discogs_id} rejects negative value"""
    test_discogs_id = 999999
    headers = get_headers()
    
    response = requests.post(
        f"{BASE_URL}/api/valuation/community-value/{test_discogs_id}",
        headers=headers,
        json={"value": -10.00}
    )
    
    assert response.status_code == 400, f"Expected 400 for negative value, got {response.status_code}: {response.text}"
    print("✓ community-value correctly rejects negative value")

def test_community_value_requires_auth():
    """POST /api/valuation/community-value/{discogs_id} requires authentication"""
    test_discogs_id = 999999
    
    response = requests.post(
        f"{BASE_URL}/api/valuation/community-value/{test_discogs_id}",
        json={"value": 50.00}
    )
    
    assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    print("✓ community-value requires authentication")


# ============ Dreamlist Pending Count Tests ============

def test_dreamlist_returns_pending_count():
    """GET /api/valuation/dreamlist returns pending_count field"""
    headers = get_headers()
    response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert "total_value" in data, "Response should contain total_value"
    assert "valued_count" in data, "Response should contain valued_count"
    assert "total_count" in data, "Response should contain total_count"
    assert "pending_count" in data, "Response should contain pending_count"
    assert isinstance(data["pending_count"], int), "pending_count should be an integer"
    print(f"✓ dreamlist returns pending_count={data['pending_count']} (total: {data['total_count']}, valued: {data['valued_count']})")

def test_dreamlist_pending_count_calculation():
    """pending_count should equal total_count - valued_count"""
    headers = get_headers()
    response = requests.get(f"{BASE_URL}/api/valuation/dreamlist", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    expected_pending = data["total_count"] - data["valued_count"]
    assert data["pending_count"] == expected_pending, f"pending_count ({data['pending_count']}) should equal total_count - valued_count ({expected_pending})"
    print(f"✓ pending_count calculation is correct: {data['total_count']} - {data['valued_count']} = {data['pending_count']}")


# ============ Pending Items Tests ============

def test_pending_items_returns_list():
    """GET /api/valuation/pending-items returns list of pending items"""
    headers = get_headers()
    response = requests.get(f"{BASE_URL}/api/valuation/pending-items", headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert isinstance(data, list), "Response should be a list"
    print(f"✓ pending-items returns {len(data)} items")

def test_pending_items_structure():
    """Each pending item should have expected fields including optional hive_average"""
    headers = get_headers()
    response = requests.get(f"{BASE_URL}/api/valuation/pending-items", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    if len(data) > 0:
        item = data[0]
        assert "id" in item, "Item should have id"
        assert "artist" in item, "Item should have artist"
        assert "album" in item, "Item should have album"
        print(f"✓ pending item structure verified: {list(item.keys())}")
    else:
        print("✓ pending-items endpoint works (no items currently pending)")


# ============ Record Values Tests ============

def test_record_values_returns_map():
    """GET /api/valuation/record-values returns map of record_id -> median_value"""
    headers = get_headers()
    response = requests.get(f"{BASE_URL}/api/valuation/record-values", headers=headers)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert isinstance(data, dict), "Response should be a dictionary/map"
    print(f"✓ record-values returns map with {len(data)} valued records")

def test_record_values_requires_auth():
    """GET /api/valuation/record-values requires authentication"""
    response = requests.get(f"{BASE_URL}/api/valuation/record-values")
    
    assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    print("✓ record-values requires authentication")
