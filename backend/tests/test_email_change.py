"""
Test suite for email change feature in HoneyGroove
Tests:
- POST /api/auth/change-email: same email, invalid email, valid new email
- GET /api/auth/confirm-email-change: invalid token, valid token
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "vinylcollector@honey.io"
TEST_PASSWORD = "password123"


class TestEmailChangeFeature:
    """Tests for the email change endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Token field 'access_token' not found in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_change_email_same_as_current(self, auth_headers):
        """POST /api/auth/change-email should fail when new email is same as current"""
        response = requests.post(
            f"{BASE_URL}/api/auth/change-email",
            json={"new_email": TEST_EMAIL},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        assert "current email" in data["detail"].lower() or "already" in data["detail"].lower(), \
            f"Error message should mention it's the current email. Got: {data['detail']}"
        print(f"✓ Same email rejection works: {data['detail']}")
    
    def test_change_email_invalid_format(self, auth_headers):
        """POST /api/auth/change-email should fail for invalid email format"""
        # Test with no @ symbol
        response = requests.post(
            f"{BASE_URL}/api/auth/change-email",
            json={"new_email": "notanemail"},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid email, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        print(f"✓ Invalid email rejection works: {data['detail']}")
        
    def test_change_email_empty(self, auth_headers):
        """POST /api/auth/change-email should fail for empty email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/change-email",
            json={"new_email": ""},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for empty email, got {response.status_code}"
        print(f"✓ Empty email rejection works")

    def test_change_email_valid_new_email(self, auth_headers):
        """POST /api/auth/change-email should succeed for valid new email"""
        # Generate unique test email
        test_email = f"test_email_change_{uuid.uuid4().hex[:8]}@test.example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/change-email",
            json={"new_email": test_email},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got: {data}"
        assert "message" in data, "Response should have 'message' field"
        assert "confirmation" in data["message"].lower() or "sent" in data["message"].lower(), \
            f"Message should mention confirmation email sent. Got: {data['message']}"
        print(f"✓ Valid email change request works: {data['message']}")

    def test_change_email_requires_auth(self):
        """POST /api/auth/change-email should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auth/change-email",
            json={"new_email": "new@test.com"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✓ Authentication requirement works")


class TestEmailConfirmation:
    """Tests for email confirmation endpoint"""
    
    def test_confirm_email_invalid_token(self):
        """GET /api/auth/confirm-email-change should fail for invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/confirm-email-change",
            params={"token": "invalid-token-12345"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid token, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower(), \
            f"Error message should mention invalid/expired. Got: {data['detail']}"
        print(f"✓ Invalid token rejection works: {data['detail']}")

    def test_confirm_email_missing_token(self):
        """GET /api/auth/confirm-email-change should fail without token"""
        response = requests.get(f"{BASE_URL}/api/auth/confirm-email-change")
        # FastAPI returns 422 for missing required query params
        assert response.status_code in [400, 422], f"Expected 400/422 for missing token, got {response.status_code}"
        print(f"✓ Missing token rejection works")


class TestEmailConfirmationEndToEnd:
    """End-to-end test for email confirmation flow using MongoDB directly"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def user_id(self, auth_token):
        """Get user ID from /auth/me"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        return response.json()["id"]

    def test_full_email_change_flow(self, auth_headers, user_id):
        """
        Test full email change flow:
        1. Request email change
        2. Get token from MongoDB
        3. Confirm the change
        4. Revert the change back to original
        """
        from pymongo import MongoClient
        
        # Connect to MongoDB
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        client = MongoClient(mongo_url)
        db = client[db_name]
        
        # Use a unique test email
        new_test_email = f"e2e_test_{uuid.uuid4().hex[:8]}@test.example.com"
        
        try:
            # Step 1: Request email change
            response = requests.post(
                f"{BASE_URL}/api/auth/change-email",
                json={"new_email": new_test_email},
                headers=auth_headers
            )
            assert response.status_code == 200, f"Email change request failed: {response.text}"
            print(f"✓ Step 1: Email change requested for {new_test_email}")
            
            # Step 2: Get token from MongoDB
            request_doc = db.email_change_requests.find_one({"user_id": user_id})
            assert request_doc is not None, "Email change request not found in database"
            token = request_doc["token"]
            assert token, "Token not found in email change request"
            print(f"✓ Step 2: Found token in MongoDB")
            
            # Step 3: Confirm the email change
            response = requests.get(
                f"{BASE_URL}/api/auth/confirm-email-change",
                params={"token": token}
            )
            assert response.status_code == 200, f"Email confirmation failed: {response.text}"
            data = response.json()
            assert data.get("status") == "ok", f"Expected status 'ok', got: {data}"
            print(f"✓ Step 3: Email change confirmed: {data.get('message')}")
            
            # Step 4: Verify user email was updated
            user = db.users.find_one({"id": user_id}, {"_id": 0, "email": 1})
            assert user["email"] == new_test_email, f"User email not updated. Expected {new_test_email}, got {user['email']}"
            print(f"✓ Step 4: User email verified as {new_test_email}")
            
            # Step 5: Revert the email back to original
            db.users.update_one({"id": user_id}, {"$set": {"email": TEST_EMAIL}})
            user_after = db.users.find_one({"id": user_id}, {"_id": 0, "email": 1})
            assert user_after["email"] == TEST_EMAIL, "Failed to revert email"
            print(f"✓ Step 5: Email reverted back to {TEST_EMAIL}")
            
        finally:
            # Cleanup: ensure email is reverted and any pending requests are cleaned
            db.users.update_one({"id": user_id}, {"$set": {"email": TEST_EMAIL}})
            db.email_change_requests.delete_many({"user_id": user_id})
            client.close()
            print("✓ Cleanup complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
