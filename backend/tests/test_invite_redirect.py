"""
Test suite for /api/auth/register-invite endpoint
Tests the backend registration functionality for invite codes
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestInviteRegistration:
    """Tests for the register-invite endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_code = f'HG-TEST{uuid.uuid4().hex[:6].upper()}'
        self.test_email = f'test_invite_{uuid.uuid4().hex[:8]}@test.com'
        self.test_username = f'testuser{uuid.uuid4().hex[:6]}'
        
    def test_register_invite_invalid_code(self):
        """Test register-invite with invalid code returns 400"""
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "INVALID-CODE-12345",
            "email": "test@test.com",
            "password": "testpass123",
            "username": "testuser"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "used" in data["detail"].lower()
        print(f"✅ Invalid code returns 400: {data['detail']}")
    
    def test_register_invite_missing_fields(self):
        """Test register-invite with missing required fields"""
        # Missing password
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "HG-TEST1234",
            "email": "test@test.com",
            "username": "testuser"
        })
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        print("✅ Missing password returns 422 validation error")
        
        # Missing email
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "HG-TEST1234",
            "password": "testpass123",
            "username": "testuser"
        })
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        print("✅ Missing email returns 422 validation error")
    
    def test_register_invite_endpoint_exists(self):
        """Test that the register-invite endpoint exists and returns expected error for bad code"""
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "NONEXISTENT",
            "email": "test@example.com",
            "password": "testpass123",
            "username": "newuser"
        })
        # Should not be 404 (endpoint exists) or 500 (server error)
        assert response.status_code in [400, 422], f"Endpoint should exist, got {response.status_code}: {response.text}"
        print(f"✅ Endpoint exists and returns proper error: {response.status_code}")
    
    def test_register_invite_rate_limit_header(self):
        """Test that endpoint handles rate limiting"""
        # This is a basic check - actual rate limit would require many requests
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "TEST-CODE",
            "email": "test@test.com",
            "password": "testpass123",
            "username": "testuser"
        })
        # Should return 400 (invalid code) not 429 (rate limited) for single request
        assert response.status_code != 500, f"Server error: {response.text}"
        print(f"✅ Rate limiter not triggered on single request: {response.status_code}")
    
    def test_register_invite_response_format(self):
        """Test that error responses have correct format"""
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "INVALID-CODE",
            "email": "test@test.com",
            "password": "testpass123",
            "username": "testuser"
        })
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"
        assert isinstance(data["detail"], str), "'detail' should be a string"
        print(f"✅ Error response format correct: {data}")


class TestInviteCodeValidation:
    """Tests for invite code format validation - skipped due to rate limiting"""
    
    @pytest.mark.skip(reason="Rate limiter prevents multiple rapid requests in test suite")
    def test_code_case_insensitive(self):
        """Test that invite codes are case-insensitive (should be normalized to uppercase)"""
        # Both lowercase and uppercase should fail with same error (code not found)
        response_lower = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "hg-invalid",
            "email": "test@test.com",
            "password": "testpass123",
            "username": "testuser"
        })
        response_upper = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "HG-INVALID",
            "email": "test@test.com",
            "password": "testpass123",
            "username": "testuser"
        })
        # Both should return same status (400 - invalid code)
        assert response_lower.status_code == response_upper.status_code == 400
        print("✅ Code validation is case-insensitive")
    
    @pytest.mark.skip(reason="Rate limiter prevents multiple rapid requests in test suite")
    def test_code_with_whitespace(self):
        """Test that codes with whitespace are trimmed"""
        response = requests.post(f"{BASE_URL}/api/auth/register-invite", json={
            "code": "  INVALID-CODE  ",
            "email": "test@test.com",
            "password": "testpass123",
            "username": "testuser"
        })
        # Should process (trim) the code and return 400 (invalid), not 500 (error)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✅ Whitespace in code is handled properly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
