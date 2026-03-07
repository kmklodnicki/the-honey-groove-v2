"""Safari Bug Fix Verification Tests
Tests the backend aspects of the Safari mounting timeout fix:
- CORS expose_headers
- Login response structure for JWT client-side decode
- Auth/me endpoint for background fetch
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSafariBugFix:
    """Verify backend support for Safari bug fixes"""
    
    def test_login_returns_jwt_token(self):
        """Login should return JWT access_token for client-side decoding"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify JWT token is returned
        assert "access_token" in data, "Missing access_token in response"
        token = data["access_token"]
        
        # Verify it's a valid JWT format (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3, f"Token should have 3 parts, got {len(parts)}"
        
        # Verify user data is returned immediately with login (not requiring /me call)
        assert "user" in data, "Missing user in response"
        user = data["user"]
        assert "id" in user, "Missing user id"
        assert "email" in user, "Missing user email"
        assert user["email"] == "demo@example.com"
    
    def test_auth_me_endpoint_for_background_fetch(self):
        """Auth/me should return full user data for background fetch"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Now test /auth/me endpoint
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        user = response.json()
        
        # Verify full user profile data is returned
        assert "id" in user
        assert "email" in user
        assert "username" in user
        assert "email_verified" in user
    
    def test_cors_headers_present(self):
        """Verify CORS headers allow cross-origin requests"""
        response = requests.options(
            f"{BASE_URL}/api/auth/me",
            headers={
                "Origin": "https://collector-hive.preview.emergentagent.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # CORS preflight should succeed
        assert response.status_code in [200, 204]
        
        # Check CORS headers
        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-origin" in headers, "Missing CORS allow-origin header"
        assert "access-control-allow-methods" in headers, "Missing CORS allow-methods header"
    
    def test_jwt_contains_user_claims(self):
        """JWT should contain user claims for instant client-side hydration"""
        import base64
        import json
        
        # Login to get token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@example.com",
            "password": "password123"
        })
        token = response.json()["access_token"]
        
        # Decode JWT payload (without verification - just checking claims exist)
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        # Verify essential claims exist
        assert "sub" in payload or "user_id" in payload, "Missing user ID claim in JWT"
        assert "exp" in payload, "Missing expiration claim in JWT"
        
        # Print claims for debugging
        print(f"JWT claims: {payload}")
    
    def test_health_check(self):
        """Basic health check to verify server is running"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        # Without auth, should return 401 or 403 - not 500
        assert response.status_code in [401, 403, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
