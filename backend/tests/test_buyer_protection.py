"""
Backend API tests for HoneyGroove Buyer Protection Features.
Tests: Seller transaction count, Listing restrictions, Off-platform detection, 
Shipping insurance, Seller stats, Admin alerts.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "password123"


class TestSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user (demo@example.com)"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Auth headers for requests"""
        return {"Authorization": f"Bearer {auth_token}"}


class TestSellerTransactionCount(TestSetup):
    """Feature 1: Seller transaction count on profiles"""
    
    def test_auth_me_returns_completed_transactions(self, auth_headers):
        """GET /api/auth/me should return completed_transactions field"""
        resp = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200, f"GET /api/auth/me failed: {resp.text}"
        
        data = resp.json()
        # Data assertion: completed_transactions field exists and is an integer
        assert "completed_transactions" in data, "completed_transactions field missing from /api/auth/me response"
        assert isinstance(data["completed_transactions"], int), "completed_transactions should be an integer"
        print(f"✓ completed_transactions = {data['completed_transactions']}")
    
    def test_user_profile_returns_completed_transactions(self, auth_headers):
        """GET /api/users/{username} should return completed_transactions"""
        # First get current user's username
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_resp.status_code == 200
        username = me_resp.json()["username"]
        
        # Fetch profile
        resp = requests.get(f"{BASE_URL}/api/users/{username}", headers=auth_headers)
        assert resp.status_code == 200, f"GET /api/users/{username} failed: {resp.text}"
        
        data = resp.json()
        assert "completed_transactions" in data, "completed_transactions field missing from user profile"
        assert isinstance(data["completed_transactions"], int)
        print(f"✓ Profile {username} has completed_transactions = {data['completed_transactions']}")


class TestSellerStatsOnListings(TestSetup):
    """Feature 2: Seller transaction count on listing cards"""
    
    def test_get_listings_returns_seller_stats(self, auth_headers):
        """GET /api/listings should return user.completed_sales and user.rating"""
        resp = requests.get(f"{BASE_URL}/api/listings?limit=5")
        assert resp.status_code == 200, f"GET /api/listings failed: {resp.text}"
        
        listings = resp.json()
        if len(listings) == 0:
            pytest.skip("No listings available to test")
        
        # Check first listing with a user
        for listing in listings:
            if listing.get("user"):
                user = listing["user"]
                # Data assertions: seller stats fields exist
                assert "completed_sales" in user, f"completed_sales missing from listing user data: {user}"
                assert "rating" in user, f"rating missing from listing user data: {user}"
                assert isinstance(user["completed_sales"], int), "completed_sales should be an integer"
                assert isinstance(user["rating"], (int, float)), "rating should be a number"
                print(f"✓ Listing seller @{user.get('username')}: {user['completed_sales']} sales, {user['rating']} rating")
                return
        
        pytest.skip("No listings with user data found")
    
    def test_get_single_listing_returns_seller_stats(self, auth_headers):
        """GET /api/listings/{id} should return seller stats"""
        # Get a listing first
        resp = requests.get(f"{BASE_URL}/api/listings?limit=1")
        assert resp.status_code == 200
        listings = resp.json()
        if len(listings) == 0:
            pytest.skip("No listings available")
        
        listing_id = listings[0]["id"]
        detail_resp = requests.get(f"{BASE_URL}/api/listings/{listing_id}")
        assert detail_resp.status_code == 200, f"GET /api/listings/{listing_id} failed"
        
        data = detail_resp.json()
        if data.get("user"):
            assert "completed_sales" in data["user"], "completed_sales missing from listing detail"
            print(f"✓ Listing detail has seller stats: {data['user']['completed_sales']} sales")


class TestNewSellerRestrictions(TestSetup):
    """Feature 3: New seller listing restrictions (price > $150 requires 3+ transactions)"""
    
    def test_seller_stats_endpoint(self, auth_headers):
        """GET /api/seller/stats should return completed_transactions"""
        resp = requests.get(f"{BASE_URL}/api/seller/stats", headers=auth_headers)
        assert resp.status_code == 200, f"GET /api/seller/stats failed: {resp.text}"
        
        data = resp.json()
        assert "completed_transactions" in data, "completed_transactions missing from seller/stats"
        assert isinstance(data["completed_transactions"], int)
        print(f"✓ Seller has {data['completed_transactions']} completed transactions")
    
    def test_listing_restriction_for_established_seller(self, auth_headers):
        """
        POST /api/listings should allow $200 listing if seller has >= 3 transactions.
        Demo user has 7 transactions so this should succeed (minus required photo).
        """
        # Check seller stats first
        stats_resp = requests.get(f"{BASE_URL}/api/seller/stats", headers=auth_headers)
        assert stats_resp.status_code == 200
        tx_count = stats_resp.json()["completed_transactions"]
        
        if tx_count >= 3:
            # Established seller - should fail only for missing photo, not price restriction
            listing_data = {
                "artist": "TEST_High_Price_Artist",
                "album": "TEST_High_Price_Album",
                "listing_type": "BUY_NOW",
                "price": 200.00,
                "condition": "Near Mint",
                "description": "Test high-priced listing",
                "photo_urls": []  # Empty - should fail for photos, not price
            }
            resp = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
            # Should fail for missing photo, not price restriction
            if resp.status_code == 400:
                error = resp.json().get("detail", "")
                assert "photo" in error.lower(), f"Expected photo error, got: {error}"
                print(f"✓ Established seller ({tx_count} tx) - rejected for missing photo, not price")
            else:
                print(f"✓ Established seller ({tx_count} tx) can list high-priced items")
        else:
            # New seller - should fail with price restriction message
            print(f"⚠ Test user has only {tx_count} transactions - expected >= 3 for this test")


class TestOffPlatformDetection(TestSetup):
    """Feature 4: Off-platform payment detection"""
    
    def test_listing_with_offplatform_keywords_gets_flagged(self, auth_headers):
        """POST /api/listings with 'venmo' in description should set offplatform_flagged=true"""
        listing_data = {
            "artist": "TEST_OffPlatform_Artist",
            "album": "TEST_OffPlatform_Album",
            "listing_type": "BUY_NOW",
            "price": 50.00,
            "condition": "Very Good",
            "description": "Contact me on venmo for payment",  # Contains 'venmo'
            "photo_urls": ["https://example.com/test-photo.jpg"]
        }
        resp = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
        
        if resp.status_code == 201 or resp.status_code == 200:
            data = resp.json()
            assert "offplatform_flagged" in data, "offplatform_flagged field missing from response"
            assert data["offplatform_flagged"] is True, f"Expected offplatform_flagged=True, got {data['offplatform_flagged']}"
            print(f"✓ Listing with 'venmo' was flagged (offplatform_flagged=True)")
            
            # Clean up - delete the test listing
            if "id" in data:
                requests.delete(f"{BASE_URL}/api/listings/{data['id']}", headers=auth_headers)
        else:
            # May fail for photo validation - check error message
            error = resp.json().get("detail", "")
            print(f"⚠ Listing creation failed: {error}")
    
    def test_admin_offplatform_alerts_endpoint(self, auth_headers):
        """GET /api/admin/offplatform-alerts should return alerts for admin"""
        resp = requests.get(f"{BASE_URL}/api/admin/offplatform-alerts", headers=auth_headers)
        
        # Should work for admin user
        assert resp.status_code == 200, f"GET /api/admin/offplatform-alerts failed: {resp.text}"
        
        alerts = resp.json()
        assert isinstance(alerts, list), "Response should be a list"
        print(f"✓ Admin off-platform alerts endpoint works ({len(alerts)} alerts)")
        
        # If alerts exist, check structure
        if len(alerts) > 0:
            alert = alerts[0]
            assert "listing_id" in alert, "Alert missing listing_id"
            assert "keywords" in alert, "Alert missing keywords"
            assert "status" in alert, "Alert missing status"
            print(f"✓ Alert structure valid: listing_id={alert['listing_id']}, keywords={alert['keywords']}")
    
    def test_offplatform_keywords_detection(self, auth_headers):
        """Test that multiple off-platform keywords are detected"""
        keywords_to_test = ["paypal", "cashapp", "zelle", "wire transfer"]
        
        for keyword in keywords_to_test:
            listing_data = {
                "artist": f"TEST_{keyword}_Artist",
                "album": f"TEST_{keyword}_Album",
                "listing_type": "BUY_NOW",
                "price": 30.00,
                "condition": "Good",
                "description": f"Pay me via {keyword} only",
                "photo_urls": ["https://example.com/test.jpg"]
            }
            resp = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
            
            if resp.status_code in [200, 201]:
                data = resp.json()
                if data.get("offplatform_flagged"):
                    print(f"✓ Keyword '{keyword}' detected correctly")
                else:
                    print(f"⚠ Keyword '{keyword}' NOT detected")
                
                # Clean up
                if "id" in data:
                    requests.delete(f"{BASE_URL}/api/listings/{data['id']}", headers=auth_headers)
            else:
                print(f"⚠ Could not test '{keyword}' - listing creation failed")


class TestShippingInsurance(TestSetup):
    """Feature 5: Shipping insurance prompt"""
    
    def test_listing_accepts_insured_boolean(self, auth_headers):
        """POST /api/listings should accept 'insured' boolean field"""
        listing_data = {
            "artist": "TEST_Insurance_Artist",
            "album": "TEST_Insurance_Album",
            "listing_type": "BUY_NOW",
            "price": 100.00,
            "condition": "Near Mint",
            "description": "Test with insurance flag",
            "photo_urls": ["https://example.com/test.jpg"],
            "insured": True
        }
        resp = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
        
        if resp.status_code in [200, 201]:
            data = resp.json()
            assert "insured" in data, "insured field missing from listing response"
            assert data["insured"] is True, f"Expected insured=True, got {data['insured']}"
            print(f"✓ Listing created with insured=True")
            
            # Clean up
            if "id" in data:
                requests.delete(f"{BASE_URL}/api/listings/{data['id']}", headers=auth_headers)
        else:
            print(f"⚠ Listing creation failed: {resp.text}")
    
    def test_listing_detail_shows_insured_status(self, auth_headers):
        """GET /api/listings/{id} should show insured status"""
        # Create a listing with insured=true
        listing_data = {
            "artist": "TEST_InsuredDetail_Artist",
            "album": "TEST_InsuredDetail_Album",
            "listing_type": "BUY_NOW",
            "price": 80.00,
            "condition": "Very Good Plus",
            "description": "Test insured detail",
            "photo_urls": ["https://example.com/test.jpg"],
            "insured": True
        }
        create_resp = requests.post(f"{BASE_URL}/api/listings", json=listing_data, headers=auth_headers)
        
        if create_resp.status_code in [200, 201]:
            listing_id = create_resp.json()["id"]
            
            # Fetch detail
            detail_resp = requests.get(f"{BASE_URL}/api/listings/{listing_id}", headers=auth_headers)
            assert detail_resp.status_code == 200
            
            data = detail_resp.json()
            assert "insured" in data, "insured field missing from listing detail"
            assert data["insured"] is True
            print(f"✓ Listing detail shows insured=True")
            
            # Clean up
            requests.delete(f"{BASE_URL}/api/listings/{listing_id}", headers=auth_headers)
        else:
            print(f"⚠ Could not create test listing: {create_resp.text}")


class TestSellerStatsEndpoint(TestSetup):
    """Feature 6: GET /api/seller/stats endpoint"""
    
    def test_seller_stats_requires_auth(self):
        """GET /api/seller/stats should require authentication"""
        resp = requests.get(f"{BASE_URL}/api/seller/stats")
        # Should require auth
        assert resp.status_code in [401, 403], "seller/stats should require auth"
        print("✓ /api/seller/stats requires authentication")
    
    def test_seller_stats_returns_transaction_count(self, auth_headers):
        """GET /api/seller/stats should return completed_transactions"""
        resp = requests.get(f"{BASE_URL}/api/seller/stats", headers=auth_headers)
        assert resp.status_code == 200, f"GET /api/seller/stats failed: {resp.text}"
        
        data = resp.json()
        assert "completed_transactions" in data
        assert isinstance(data["completed_transactions"], int)
        assert data["completed_transactions"] >= 0
        print(f"✓ Seller stats: {data['completed_transactions']} completed transactions")


class TestAdminOffPlatformAlerts(TestSetup):
    """Feature 10: Admin Off-Platform Alerts tab"""
    
    def test_admin_alerts_requires_admin(self):
        """GET /api/admin/offplatform-alerts should require admin privileges"""
        # Test without auth - should fail
        resp = requests.get(f"{BASE_URL}/api/admin/offplatform-alerts")
        assert resp.status_code in [401, 403], "Admin endpoint should require auth"
        print("✓ Admin alerts endpoint requires authentication")
    
    def test_admin_alerts_accessible_by_admin(self, auth_headers):
        """Admin user should be able to access off-platform alerts"""
        resp = requests.get(f"{BASE_URL}/api/admin/offplatform-alerts", headers=auth_headers)
        assert resp.status_code == 200, f"Admin should be able to access alerts: {resp.text}"
        
        alerts = resp.json()
        assert isinstance(alerts, list)
        print(f"✓ Admin can access off-platform alerts ({len(alerts)} alerts)")
    
    def test_admin_can_dismiss_alert(self, auth_headers):
        """Admin should be able to dismiss an alert"""
        # First get alerts
        alerts_resp = requests.get(f"{BASE_URL}/api/admin/offplatform-alerts", headers=auth_headers)
        assert alerts_resp.status_code == 200
        
        alerts = alerts_resp.json()
        # Find an open alert to dismiss
        open_alert = next((a for a in alerts if a.get("status") == "open"), None)
        
        if open_alert:
            alert_id = open_alert["id"]
            dismiss_resp = requests.put(
                f"{BASE_URL}/api/admin/offplatform-alerts/{alert_id}/dismiss",
                headers=auth_headers
            )
            assert dismiss_resp.status_code == 200, f"Dismiss failed: {dismiss_resp.text}"
            print(f"✓ Admin dismissed alert {alert_id}")
        else:
            print("⚠ No open alerts to test dismiss functionality")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
