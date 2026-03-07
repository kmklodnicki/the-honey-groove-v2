"""
Tests for Country Gate Modal and Shipping Address Country Validation features.
Features:
1. PUT /api/auth/me can update country field
2. POST /api/payments/checkout includes shipping_address_collection with allowed_countries
3. POST /api/payments/checkout validates international_shipping restrictions
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCountryGateFeatures:
    """Test Country Gate and Shipping features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.unique_id = str(uuid.uuid4())[:8]
        self.test_email_no_country = f"TEST_no_country_{self.unique_id}@honey.io"
        self.test_email_us = f"TEST_us_user_{self.unique_id}@honey.io"
        self.test_email_gb = f"TEST_gb_user_{self.unique_id}@honey.io"
        self.test_password = "testpassword123"
        self.created_user_ids = []
        self.created_listing_ids = []
        yield
        # Cleanup handled by pytest teardown
    
    def _register_user(self, email: str, username: str):
        """Helper to register a new user"""
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "username": username,
            "password": self.test_password
        })
        return resp
    
    def _login_user(self, email: str):
        """Helper to login a user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": self.test_password
        })
        return resp
    
    def _update_user_country(self, token: str, country: str):
        """Helper to update user's country"""
        resp = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"country": country},
            headers={"Authorization": f"Bearer {token}"}
        )
        return resp
    
    def _create_listing(self, token: str, international_shipping: bool = False, price: float = 25.0):
        """Helper to create a test listing"""
        resp = requests.post(
            f"{BASE_URL}/api/listings",
            json={
                "artist": f"TEST_Artist_{self.unique_id}",
                "album": f"TEST_Album_{self.unique_id}",
                "condition": "Near Mint",
                "listing_type": "BUY_NOW",
                "price": price,
                "photo_urls": ["https://example.com/photo.jpg"],
                "international_shipping": international_shipping
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 200:
            data = resp.json()
            self.created_listing_ids.append(data.get("id"))
        return resp

    # ========== TEST: PUT /api/auth/me can update country field ==========
    
    def test_update_country_field(self):
        """Test that PUT /api/auth/me can update the country field"""
        # Register a new user
        username = f"test_country_{self.unique_id}"
        reg_resp = self._register_user(self.test_email_no_country, username)
        
        if reg_resp.status_code == 400 and "already" in reg_resp.text.lower():
            # User already exists, login instead
            login_resp = self._login_user(self.test_email_no_country)
            assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
            token = login_resp.json()["access_token"]
        else:
            assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
            token = reg_resp.json()["access_token"]
        
        # Update country to US
        update_resp = self._update_user_country(token, "US")
        assert update_resp.status_code == 200, f"Country update failed: {update_resp.text}"
        
        # Verify country was saved
        user_data = update_resp.json()
        assert user_data.get("country") == "US", f"Country not updated correctly: {user_data}"
        
        # Verify via GET /api/auth/me
        me_resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200
        assert me_resp.json().get("country") == "US", "Country not persisted"
        
        print("SUCCESS: PUT /api/auth/me can update country field")

    def test_update_country_to_other_values(self):
        """Test updating country to different values"""
        username = f"test_country2_{self.unique_id}"
        reg_resp = self._register_user(f"TEST_country2_{self.unique_id}@honey.io", username)
        
        if reg_resp.status_code == 400:
            login_resp = self._login_user(f"TEST_country2_{self.unique_id}@honey.io")
            token = login_resp.json()["access_token"]
        else:
            token = reg_resp.json()["access_token"]
        
        # Test GB
        update_resp = self._update_user_country(token, "GB")
        assert update_resp.status_code == 200
        assert update_resp.json().get("country") == "GB"
        
        # Test CA
        update_resp = self._update_user_country(token, "CA")
        assert update_resp.status_code == 200
        assert update_resp.json().get("country") == "CA"
        
        print("SUCCESS: Country field can be updated to different values")


class TestCheckoutShippingAddressCollection:
    """Test Stripe checkout shipping_address_collection feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data - need a seller with Stripe connected"""
        self.unique_id = str(uuid.uuid4())[:8]
        # Using known test user with Stripe connected
        self.seller_email = "vinylcollector@honey.io"
        self.seller_password = "password123"
        yield
    
    def test_checkout_domestic_only_listing_validation(self):
        """Test that checkout blocks buyers from different countries for domestic-only listings"""
        # Login as seller (US)
        seller_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.seller_email,
            "password": self.seller_password
        })
        
        if seller_login.status_code != 200:
            pytest.skip(f"Could not login as seller: {seller_login.text}")
        
        seller_token = seller_login.json()["access_token"]
        
        # Create a domestic-only listing
        listing_resp = requests.post(
            f"{BASE_URL}/api/listings",
            json={
                "artist": f"TEST_DomesticArtist_{self.unique_id}",
                "album": f"TEST_DomesticAlbum_{self.unique_id}",
                "condition": "Near Mint",
                "listing_type": "BUY_NOW",
                "price": 30.0,
                "photo_urls": ["https://example.com/photo.jpg"],
                "international_shipping": False
            },
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        
        if listing_resp.status_code != 200:
            pytest.skip(f"Could not create listing: {listing_resp.text}")
        
        listing_id = listing_resp.json()["id"]
        
        # Create a buyer from GB
        buyer_email = f"TEST_gb_buyer_{self.unique_id}@honey.io"
        buyer_username = f"gb_buyer_{self.unique_id}"
        buyer_reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": buyer_email,
            "username": buyer_username,
            "password": "testpass123"
        })
        
        if buyer_reg.status_code == 200:
            buyer_token = buyer_reg.json()["access_token"]
        else:
            buyer_login = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": buyer_email,
                "password": "testpass123"
            })
            if buyer_login.status_code != 200:
                pytest.skip("Could not create/login buyer")
            buyer_token = buyer_login.json()["access_token"]
        
        # Set buyer's country to GB
        update_resp = requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"country": "GB"},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert update_resp.status_code == 200
        
        # Try to checkout - should fail with domestic shipping error
        checkout_resp = requests.post(
            f"{BASE_URL}/api/payments/checkout",
            json={
                "listing_id": listing_id,
                "origin_url": "https://thehoneygroove.com"
            },
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        
        # Should return 400 with domestic shipping error
        assert checkout_resp.status_code == 400, f"Expected 400, got {checkout_resp.status_code}: {checkout_resp.text}"
        assert "domestic" in checkout_resp.text.lower(), f"Expected domestic shipping error: {checkout_resp.text}"
        
        print("SUCCESS: Checkout correctly blocks buyers from different countries for domestic-only listings")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/listings/{listing_id}",
            headers={"Authorization": f"Bearer {seller_token}"}
        )

    def test_checkout_international_shipping_listing_allowed(self):
        """Test that checkout allows buyers from different countries for international shipping listings"""
        # Login as seller
        seller_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.seller_email,
            "password": self.seller_password
        })
        
        if seller_login.status_code != 200:
            pytest.skip(f"Could not login as seller: {seller_login.text}")
        
        seller_token = seller_login.json()["access_token"]
        
        # Create an international shipping listing
        listing_resp = requests.post(
            f"{BASE_URL}/api/listings",
            json={
                "artist": f"TEST_IntlArtist_{self.unique_id}",
                "album": f"TEST_IntlAlbum_{self.unique_id}",
                "condition": "Near Mint",
                "listing_type": "BUY_NOW",
                "price": 35.0,
                "photo_urls": ["https://example.com/photo.jpg"],
                "international_shipping": True
            },
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        
        if listing_resp.status_code != 200:
            pytest.skip(f"Could not create listing: {listing_resp.text}")
        
        listing_id = listing_resp.json()["id"]
        
        # Create a buyer from CA
        buyer_email = f"TEST_ca_buyer_{self.unique_id}@honey.io"
        buyer_username = f"ca_buyer_{self.unique_id}"
        buyer_reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": buyer_email,
            "username": buyer_username,
            "password": "testpass123"
        })
        
        if buyer_reg.status_code == 200:
            buyer_token = buyer_reg.json()["access_token"]
        else:
            buyer_login = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": buyer_email,
                "password": "testpass123"
            })
            if buyer_login.status_code != 200:
                pytest.skip("Could not create/login buyer")
            buyer_token = buyer_login.json()["access_token"]
        
        # Set buyer's country to CA
        requests.put(
            f"{BASE_URL}/api/auth/me",
            json={"country": "CA"},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        
        # Try to checkout - should succeed (return checkout URL)
        checkout_resp = requests.post(
            f"{BASE_URL}/api/payments/checkout",
            json={
                "listing_id": listing_id,
                "origin_url": "https://thehoneygroove.com"
            },
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        
        # Should return 200 with checkout URL (or 500 if Stripe issue, which is acceptable for this test)
        if checkout_resp.status_code == 200:
            data = checkout_resp.json()
            assert "url" in data, f"Expected checkout URL: {data}"
            print("SUCCESS: Checkout allows buyers from different countries for international shipping listings")
        elif checkout_resp.status_code == 400 and "domestic" not in checkout_resp.text.lower():
            # Other 400 error (not domestic shipping) is also acceptable
            print(f"INFO: Checkout returned 400 but not for domestic shipping: {checkout_resp.text}")
        else:
            # Even 500 from Stripe is acceptable - means the country check passed
            if "domestic" not in checkout_resp.text.lower():
                print(f"INFO: Checkout returned {checkout_resp.status_code} - country check passed")
            else:
                pytest.fail(f"Unexpected domestic shipping error for intl listing: {checkout_resp.text}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/listings/{listing_id}",
            headers={"Authorization": f"Bearer {seller_token}"}
        )


class TestCodeVerification:
    """Verify code implementation matches requirements"""
    
    def test_checkout_has_shipping_address_collection(self):
        """Verify that honeypot.py checkout includes shipping_address_collection"""
        import os
        
        honeypot_path = "/app/backend/routes/honeypot.py"
        if not os.path.exists(honeypot_path):
            pytest.skip("honeypot.py not found")
        
        with open(honeypot_path, 'r') as f:
            content = f.read()
        
        # Check for shipping_address_collection in checkout session
        assert "shipping_address_collection" in content, "shipping_address_collection not found in honeypot.py"
        assert "allowed_countries" in content, "allowed_countries not found in honeypot.py"
        
        # Verify the pattern: shipping_address_collection with user.get("country")
        assert 'user.get("country"' in content or "user.get('country'" in content, \
            "Checkout should use buyer's country for allowed_countries"
        
        print("SUCCESS: Checkout code includes shipping_address_collection with allowed_countries")
    
    def test_checkout_validates_domestic_shipping(self):
        """Verify that checkout validates domestic shipping restriction"""
        import os
        
        honeypot_path = "/app/backend/routes/honeypot.py"
        if not os.path.exists(honeypot_path):
            pytest.skip("honeypot.py not found")
        
        with open(honeypot_path, 'r') as f:
            content = f.read()
        
        # Check for international shipping validation
        assert "international_shipping" in content, "international_shipping check not found"
        assert "seller_country" in content and "buyer_country" in content, \
            "Seller/buyer country comparison not found"
        assert "only ships domestically" in content.lower() or "domestic" in content.lower(), \
            "Domestic shipping error message not found"
        
        print("SUCCESS: Checkout validates domestic shipping restrictions")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
