"""
Tests for Discogs valuation/market data endpoints.
Features:
- Collection Value: GET /api/valuation/collection and /api/valuation/collection/{username}
- Hidden Gems: GET /api/valuation/hidden-gems and /api/valuation/hidden-gems/{username}
- Taste Report: GET /api/valuation/taste-report
- Record Values: GET /api/valuation/record-values
- Pricing Assist: GET /api/valuation/pricing-assist/{discogs_id}
- Wantlist Price Alert: PUT /api/valuation/wantlist/{iso_id}/price-alert
- Background Refresh: POST /api/valuation/refresh
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestValuationAuth:
    """Test auth requirements for valuation endpoints."""

    def test_collection_value_requires_auth(self):
        """GET /api/valuation/collection requires authentication."""
        resp = requests.get(f"{BASE_URL}/api/valuation/collection")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    def test_hidden_gems_requires_auth(self):
        """GET /api/valuation/hidden-gems requires authentication."""
        resp = requests.get(f"{BASE_URL}/api/valuation/hidden-gems")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    def test_taste_report_requires_auth(self):
        """GET /api/valuation/taste-report requires authentication."""
        resp = requests.get(f"{BASE_URL}/api/valuation/taste-report")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    def test_record_values_requires_auth(self):
        """GET /api/valuation/record-values requires authentication."""
        resp = requests.get(f"{BASE_URL}/api/valuation/record-values")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    def test_pricing_assist_requires_auth(self):
        """GET /api/valuation/pricing-assist/{id} requires authentication."""
        resp = requests.get(f"{BASE_URL}/api/valuation/pricing-assist/249504")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    def test_price_alert_requires_auth(self):
        """PUT /api/valuation/wantlist/{id}/price-alert requires authentication."""
        resp = requests.put(f"{BASE_URL}/api/valuation/wantlist/test-id/price-alert", json={"target_price": 50})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    def test_refresh_requires_auth(self):
        """POST /api/valuation/refresh requires authentication."""
        resp = requests.post(f"{BASE_URL}/api/valuation/refresh")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


class TestValuationPublicEndpoints:
    """Test public valuation endpoints (by username)."""

    def test_collection_value_by_username(self):
        """GET /api/valuation/collection/{username} returns public collection value."""
        resp = requests.get(f"{BASE_URL}/api/valuation/collection/demo")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Validate response structure
        assert "total_value" in data, "Missing 'total_value' field"
        assert "valued_count" in data, "Missing 'valued_count' field"
        assert "total_count" in data, "Missing 'total_count' field"
        assert isinstance(data["total_value"], (int, float)), "total_value should be numeric"
        assert isinstance(data["valued_count"], int), "valued_count should be int"
        assert isinstance(data["total_count"], int), "total_count should be int"
        print(f"Demo user collection: total_value=${data['total_value']}, valued={data['valued_count']}/{data['total_count']}")

    def test_collection_value_nonexistent_user(self):
        """GET /api/valuation/collection/{username} returns 404 for non-existent user."""
        resp = requests.get(f"{BASE_URL}/api/valuation/collection/nonexistent_user_12345")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    def test_hidden_gems_by_username(self):
        """GET /api/valuation/hidden-gems/{username} returns public hidden gems."""
        resp = requests.get(f"{BASE_URL}/api/valuation/hidden-gems/demo")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"
        # Verify structure if we have any gems
        if len(data) > 0:
            gem = data[0]
            assert "id" in gem, "Gem missing 'id'"
            assert "title" in gem, "Gem missing 'title'"
            assert "artist" in gem, "Gem missing 'artist'"
            assert "median_value" in gem, "Gem missing 'median_value'"
            print(f"Demo hidden gems: {len(data)} gems, top=${data[0]['median_value'] if data else 'N/A'}")

    def test_hidden_gems_nonexistent_user(self):
        """GET /api/valuation/hidden-gems/{username} returns 404 for non-existent user."""
        resp = requests.get(f"{BASE_URL}/api/valuation/hidden-gems/nonexistent_user_12345")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


@pytest.fixture(scope="class")
def auth_token():
    """Authenticate and get token."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@example.com",
        "password": "password123"
    })
    if resp.status_code != 200:
        pytest.skip(f"Login failed: {resp.text}")
    data = resp.json()
    token = data.get("access_token")
    if not token:
        pytest.skip("No access_token in login response")
    return token


class TestValuationAuthenticated:
    """Test authenticated valuation endpoints."""

    def test_collection_value_authenticated(self, auth_token):
        """GET /api/valuation/collection returns user's collection value."""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/collection",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "total_value" in data
        assert "valued_count" in data
        assert "total_count" in data
        assert data["total_value"] >= 0, "total_value should be non-negative"
        print(f"Authenticated collection: ${data['total_value']}, {data['valued_count']}/{data['total_count']} valued")

    def test_hidden_gems_authenticated(self, auth_token):
        """GET /api/valuation/hidden-gems returns top 3 most valuable records."""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/hidden-gems",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"
        # Should return at most 3 by default
        assert len(data) <= 3, f"Expected max 3 gems, got {len(data)}"
        # Verify sorted by median_value descending
        if len(data) > 1:
            for i in range(len(data) - 1):
                assert data[i]["median_value"] >= data[i+1]["median_value"], "Gems not sorted by value descending"
        print(f"Hidden gems: {len(data)} records")

    def test_taste_report_authenticated(self, auth_token):
        """GET /api/valuation/taste-report returns value summary."""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/taste-report",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Verify structure
        assert "total_value" in data, "Missing 'total_value'"
        assert "valued_count" in data, "Missing 'valued_count'"
        assert "total_count" in data, "Missing 'total_count'"
        assert "over_100_count" in data, "Missing 'over_100_count'"
        assert "most_valuable" in data, "Missing 'most_valuable'"
        # If most_valuable exists, verify structure
        if data["most_valuable"]:
            mv = data["most_valuable"]
            assert "title" in mv, "most_valuable missing title"
            assert "artist" in mv, "most_valuable missing artist"
            assert "median_value" in mv, "most_valuable missing median_value"
        print(f"Taste report: ${data['total_value']}, {data['over_100_count']} over $100")

    def test_record_values_authenticated(self, auth_token):
        """GET /api/valuation/record-values returns record_id -> median_value map."""
        resp = requests.get(
            f"{BASE_URL}/api/valuation/record-values",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, dict), "Response should be a dict"
        # Verify values are numeric
        for key, val in data.items():
            assert isinstance(val, (int, float)), f"Value for {key} should be numeric"
        print(f"Record values map: {len(data)} records with values")

    def test_pricing_assist_cached_release(self, auth_token):
        """GET /api/valuation/pricing-assist/{discogs_id} returns price range for known release."""
        # Rumours by Fleetwood Mac - should be in cache
        resp = requests.get(
            f"{BASE_URL}/api/valuation/pricing-assist/249504",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "low" in data, "Missing 'low'"
        assert "high" in data, "Missing 'high'"
        assert "median" in data, "Missing 'median'"
        assert "stale" in data, "Missing 'stale'"
        # At least one value should be present
        print(f"Pricing assist for 249504: low=${data['low']}, median=${data['median']}, high=${data['high']}")

    def test_refresh_triggers_background_task(self, auth_token):
        """POST /api/valuation/refresh triggers background refresh."""
        resp = requests.post(
            f"{BASE_URL}/api/valuation/refresh",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "message" in data, "Missing 'message'"
        assert "queued" in data, "Missing 'queued'"
        print(f"Refresh response: {data['message']}, queued={data['queued']}")


class TestWantlistPriceAlerts:
    """Test wantlist price alert functionality."""

    def test_set_price_alert_requires_valid_iso(self, auth_token):
        """PUT /api/valuation/wantlist/{iso_id}/price-alert returns 404 for invalid ISO."""
        resp = requests.put(
            f"{BASE_URL}/api/valuation/wantlist/nonexistent-iso-id/price-alert",
            json={"target_price": 50},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    def test_set_price_alert_on_valid_iso(self, auth_token):
        """Test setting price alert on a valid ISO item (if exists)."""
        # First get user's ISOs
        isos_resp = requests.get(
            f"{BASE_URL}/api/iso",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if isos_resp.status_code != 200:
            pytest.skip("Could not fetch ISOs")
        isos = isos_resp.json()
        if not isos:
            pytest.skip("No ISO items to test with")
        
        # Find an OPEN ISO
        test_iso = None
        for iso in isos:
            if iso.get("status") == "OPEN":
                test_iso = iso
                break
        if not test_iso:
            pytest.skip("No OPEN ISO items found")

        # Set price alert
        resp = requests.put(
            f"{BASE_URL}/api/valuation/wantlist/{test_iso['id']}/price-alert",
            json={"target_price": 75.50},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "message" in data
        assert "target_price" in data
        assert data["target_price"] == 75.50
        print(f"Set price alert on ISO {test_iso['id']}: ${data['target_price']}")

        # Clear the alert
        clear_resp = requests.put(
            f"{BASE_URL}/api/valuation/wantlist/{test_iso['id']}/price-alert",
            json={"target_price": None},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert clear_resp.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
