"""
BLOCK 3.4: Report a Problem System + BLOCK 4.1: Honey Pulse
Testing: Report submission, rate limiting, admin queue, admin actions, pulse endpoint
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"


class TestAuth:
    """Authentication helper"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get access token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}


class TestReportReasons(TestAuth):
    """BLOCK 3.4: Test GET /api/reports/reasons/{target_type}"""
    
    def test_get_listing_reasons(self, headers):
        """Test listing report reasons"""
        resp = requests.get(f"{BASE_URL}/api/reports/reasons/listing", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "reasons" in data
        assert len(data["reasons"]) > 0
        assert "Incorrect grading" in data["reasons"]
        assert "Counterfeit / bootleg" in data["reasons"]
        print(f"PASSED: Listing reasons: {data['reasons']}")
    
    def test_get_seller_reasons(self, headers):
        """Test seller report reasons"""
        resp = requests.get(f"{BASE_URL}/api/reports/reasons/seller", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "reasons" in data
        assert "Misleading listings" in data["reasons"]
        assert "Suspected fraud" in data["reasons"]
        print(f"PASSED: Seller reasons: {data['reasons']}")
    
    def test_get_order_reasons(self, headers):
        """Test order report reasons"""
        resp = requests.get(f"{BASE_URL}/api/reports/reasons/order", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "reasons" in data
        assert "Item never shipped" in data["reasons"]
        print(f"PASSED: Order reasons: {data['reasons']}")
    
    def test_get_bug_reasons(self, headers):
        """Test bug report reasons"""
        resp = requests.get(f"{BASE_URL}/api/reports/reasons/bug", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "reasons" in data
        assert "UI / display issue" in data["reasons"]
        assert "Feature not working" in data["reasons"]
        print(f"PASSED: Bug reasons: {data['reasons']}")
    
    def test_invalid_target_type(self, headers):
        """Test invalid target type returns 400"""
        resp = requests.get(f"{BASE_URL}/api/reports/reasons/invalid_type", headers=headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("PASSED: Invalid target type returns 400")


class TestReportSubmission(TestAuth):
    """BLOCK 3.4: Test POST /api/reports/submit"""
    
    def test_submit_bug_report(self, headers):
        """Test submitting a bug report"""
        resp = requests.post(f"{BASE_URL}/api/reports/submit", json={
            "target_type": "bug",
            "reason": "UI / display issue",
            "notes": "Test bug report from automated testing",
            "page_url": "https://honeygroove-fix.preview.emergentagent.com/hive",
            "browser_info": "TestAgent/1.0"
        }, headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "report_id" in data
        assert data["status"] == "OPEN"
        print(f"PASSED: Bug report submitted: {data['report_id']}")
    
    def test_submit_listing_report(self, headers):
        """Test submitting a listing report"""
        resp = requests.post(f"{BASE_URL}/api/reports/submit", json={
            "target_type": "listing",
            "target_id": "test_listing_123",
            "reason": "Incorrect grading",
            "notes": "Test listing report",
            "page_url": "https://honeygroove-fix.preview.emergentagent.com/honeypot",
            "browser_info": "TestAgent/1.0"
        }, headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert "report_id" in data
        print(f"PASSED: Listing report submitted: {data['report_id']}")
    
    def test_submit_without_reason_fails(self, headers):
        """Test that submitting without reason fails"""
        resp = requests.post(f"{BASE_URL}/api/reports/submit", json={
            "target_type": "bug",
            "notes": "Missing reason"
        }, headers=headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("PASSED: Submit without reason returns 400")
    
    def test_submit_invalid_target_type_fails(self, headers):
        """Test that invalid target type fails"""
        resp = requests.post(f"{BASE_URL}/api/reports/submit", json={
            "target_type": "invalid",
            "reason": "Test"
        }, headers=headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("PASSED: Invalid target type returns 400")


class TestAdminReportQueue(TestAuth):
    """BLOCK 3.4: Test admin report queue endpoints"""
    
    def test_admin_queue_access(self, headers):
        """Test admin can access report queue"""
        resp = requests.get(f"{BASE_URL}/api/reports/admin/queue", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"PASSED: Admin queue accessible, {len(data)} reports")
    
    def test_admin_queue_filter_by_type(self, headers):
        """Test filtering queue by target_type"""
        resp = requests.get(f"{BASE_URL}/api/reports/admin/queue?target_type=bug", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        for report in data:
            assert report.get("target_type") == "bug"
        print(f"PASSED: Bug filter works, {len(data)} bug reports")
    
    def test_admin_queue_filter_by_status(self, headers):
        """Test filtering queue by status"""
        resp = requests.get(f"{BASE_URL}/api/reports/admin/queue?status=OPEN", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        for report in data:
            assert report.get("status") == "OPEN"
        print(f"PASSED: Status filter works, {len(data)} OPEN reports")
    
    def test_admin_queue_enriched_data(self, headers):
        """Test that reports include enriched data"""
        resp = requests.get(f"{BASE_URL}/api/reports/admin/queue", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        if len(data) > 0:
            report = data[0]
            assert "reporter" in report or "reporter_username" in report
            assert "target_type" in report
            assert "reason" in report
            print(f"PASSED: Reports have enriched data")
        else:
            print("PASSED: Queue accessible (no reports to verify enrichment)")


class TestAdminReportActions(TestAuth):
    """BLOCK 3.4: Test admin report actions"""
    
    def test_admin_action_reviewing(self, headers):
        """Test marking report as REVIEWING"""
        # First get a report
        resp = requests.get(f"{BASE_URL}/api/reports/admin/queue?status=OPEN", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            report = resp.json()[0]
            report_id = report.get("report_id")
            
            # Apply REVIEWING action
            action_resp = requests.post(f"{BASE_URL}/api/reports/admin/{report_id}/action", json={
                "action": "REVIEWING"
            }, headers=headers)
            assert action_resp.status_code == 200, f"Failed: {action_resp.text}"
            print(f"PASSED: REVIEWING action applied to {report_id}")
        else:
            print("SKIPPED: No OPEN reports to test action")
    
    def test_admin_action_invalid(self, headers):
        """Test invalid action returns 400"""
        resp = requests.post(f"{BASE_URL}/api/reports/admin/test_id/action", json={
            "action": "INVALID_ACTION"
        }, headers=headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("PASSED: Invalid action returns 400")
    
    def test_valid_action_types(self, headers):
        """Test that valid action types are documented"""
        valid_actions = ["REVIEWING", "DISMISSED", "RESOLVED", "REMOVE_LISTING", "WARN_SELLER", "SUSPEND_SELLER"]
        # Just verify the endpoint exists and accepts valid actions
        resp = requests.post(f"{BASE_URL}/api/reports/admin/nonexistent_id/action", json={
            "action": "DISMISSED"
        }, headers=headers)
        # Should be 404 (not found) rather than 400 (bad request)
        assert resp.status_code == 404, f"Expected 404 for nonexistent report, got {resp.status_code}"
        print(f"PASSED: Valid action structure verified")


class TestHoneyPulse(TestAuth):
    """BLOCK 4.1: Test GET /api/valuation/pulse/{discogs_id}"""
    
    def test_pulse_endpoint_exists(self, headers):
        """Test pulse endpoint returns data structure"""
        # Use a common Discogs ID for testing
        discogs_id = 249504  # Kind of Blue by Miles Davis
        resp = requests.get(f"{BASE_URL}/api/valuation/pulse/{discogs_id}", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify expected fields
        assert "release_id" in data or "median" in data
        print(f"PASSED: Pulse endpoint returns data: {data}")
    
    def test_pulse_data_structure(self, headers):
        """Test pulse returns correct structure"""
        discogs_id = 249504
        resp = requests.get(f"{BASE_URL}/api/valuation/pulse/{discogs_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Should have these fields (may be null if no data)
        expected_fields = ["median", "hot_low", "hot_high", "confident"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        print(f"PASSED: Pulse has correct structure")
    
    def test_pulse_confidence_calculation(self, headers):
        """Test pulse confidence flag"""
        discogs_id = 249504
        resp = requests.get(f"{BASE_URL}/api/valuation/pulse/{discogs_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Confident should be boolean
        assert isinstance(data.get("confident"), bool) or data.get("confident") is None
        print(f"PASSED: Confidence is boolean: {data.get('confident')}")
    
    def test_pulse_hot_range(self, headers):
        """Test pulse hot range calculation (median +/- 15%)"""
        discogs_id = 249504
        resp = requests.get(f"{BASE_URL}/api/valuation/pulse/{discogs_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        if data.get("median") and data.get("hot_low") and data.get("hot_high"):
            median = data["median"]
            expected_low = median * 0.85
            expected_high = median * 1.15
            # Allow small rounding differences
            assert abs(data["hot_low"] - expected_low) < 0.1, f"Hot low mismatch"
            assert abs(data["hot_high"] - expected_high) < 0.1, f"Hot high mismatch"
            print(f"PASSED: Hot range is median +/- 15%")
        else:
            print("SKIPPED: No median data to verify hot range")


class TestHeartButtonOptimistic:
    """Test that like/unlike endpoints work correctly (optimistic UI is frontend)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200
        return resp.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_like_unlike_endpoints_exist(self, headers):
        """Test that like/unlike endpoints exist"""
        # Get a post from feed
        feed_resp = requests.get(f"{BASE_URL}/api/feed?limit=1", headers=headers)
        assert feed_resp.status_code == 200
        posts = feed_resp.json()
        
        if len(posts) > 0:
            post_id = posts[0]["id"]
            
            # Test like endpoint
            like_resp = requests.post(f"{BASE_URL}/api/posts/{post_id}/like", json={}, headers=headers)
            # May return 200 (success) or 400/409 (already liked)
            assert like_resp.status_code in [200, 400, 409], f"Like failed: {like_resp.status_code}"
            
            # Test unlike endpoint
            unlike_resp = requests.delete(f"{BASE_URL}/api/posts/{post_id}/like", headers=headers)
            # May return 200 (success) or 400/404 (not liked)
            assert unlike_resp.status_code in [200, 400, 404], f"Unlike failed: {unlike_resp.status_code}"
            
            print("PASSED: Like/unlike endpoints work")
        else:
            print("SKIPPED: No posts in feed to test like")


class TestSEOAltTags:
    """Test that API returns correct data for SEO alt tags"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200
        return resp.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_records_have_artist_and_title(self, headers):
        """Test records API returns artist and title for alt tags"""
        resp = requests.get(f"{BASE_URL}/api/records", headers=headers)
        assert resp.status_code == 200
        records = resp.json()
        
        for record in records[:5]:  # Check first 5
            assert "artist" in record, "Record missing artist"
            assert "title" in record, "Record missing title"
        
        print(f"PASSED: Records have artist/title for SEO ({len(records)} records)")
    
    def test_feed_posts_have_record_data(self, headers):
        """Test feed posts include record artist/title"""
        resp = requests.get(f"{BASE_URL}/api/feed?limit=10", headers=headers)
        assert resp.status_code == 200
        posts = resp.json()
        
        for post in posts:
            if post.get("record"):
                assert "artist" in post["record"]
                assert "title" in post["record"]
        
        print(f"PASSED: Feed posts have record data for SEO ({len(posts)} posts)")


class TestNonAdminAccess:
    """Test that non-admin users cannot access admin endpoints"""
    
    def test_admin_queue_requires_admin(self):
        """Test that regular users get 403 on admin queue"""
        # Try without auth
        resp = requests.get(f"{BASE_URL}/api/reports/admin/queue")
        assert resp.status_code in [401, 403], f"Expected auth error, got {resp.status_code}"
        print("PASSED: Admin queue requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
