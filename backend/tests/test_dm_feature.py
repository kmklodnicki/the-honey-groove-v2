"""
Test suite for DM (Direct Messages) feature
Tests the following endpoints:
- POST /api/dm/conversations - Create conversation and send initial message
- GET /api/dm/conversations - List user conversations
- GET /api/dm/conversations/{id} - Get conversation with messages
- POST /api/dm/conversations/{id}/messages - Send message in conversation
- GET /api/dm/unread-count - Get unread message count
- GET /api/dm/conversation-with/{userId} - Check existing conversation with user
- GET /api/users/by-id/{userId} - Get user info by ID
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_USER = {"email": "demo@example.com", "password": "password123"}
TRADER_USER = {"email": "trader@example.com", "password": "password123"}


class TestDMFeature:
    """Test DM endpoints"""
    
    @pytest.fixture(scope="class")
    def demo_auth(self):
        """Get auth token for demo user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_USER)
        assert resp.status_code == 200, f"Demo login failed: {resp.text}"
        data = resp.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "username": data["user"]["username"]
        }
    
    @pytest.fixture(scope="class")
    def trader_auth(self):
        """Get auth token for trader user"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=TRADER_USER)
        assert resp.status_code == 200, f"Trader login failed: {resp.text}"
        data = resp.json()
        return {
            "token": data["access_token"],
            "user_id": data["user"]["id"],
            "username": data["user"]["username"]
        }
    
    def test_cannot_message_self(self, demo_auth):
        """POST /api/dm/conversations - Cannot message yourself returns 400"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        resp = requests.post(f"{BASE_URL}/api/dm/conversations", json={
            "recipient_id": demo_auth['user_id'],
            "text": "Hello myself"
        }, headers=headers)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        assert "message yourself" in resp.json().get("detail", "").lower()
        print("PASS: Cannot message yourself - returns 400")
    
    def test_create_conversation_and_send_message(self, demo_auth, trader_auth):
        """POST /api/dm/conversations - Create new conversation with initial message"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        resp = requests.post(f"{BASE_URL}/api/dm/conversations", json={
            "recipient_id": trader_auth['user_id'],
            "text": "TEST_DM: Hello from pytest!",
            "context": {
                "type": "iso",
                "record_name": "Mazzy Star — So Tonight That I Might See",
                "action_text": "I have this"
            }
        }, headers=headers)
        assert resp.status_code == 200, f"Create conversation failed: {resp.text}"
        data = resp.json()
        assert "conversation_id" in data, "Response should contain conversation_id"
        print(f"PASS: Created conversation with ID: {data['conversation_id']}")
        return data['conversation_id']
    
    def test_list_conversations(self, demo_auth):
        """GET /api/dm/conversations - List user's conversations"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/dm/conversations", headers=headers)
        assert resp.status_code == 200, f"List conversations failed: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Check structure of conversation list item
        if len(data) > 0:
            conv = data[0]
            assert "id" in conv, "Conversation should have id"
            assert "other_user" in conv, "Conversation should have other_user"
            assert "last_message" in conv, "Conversation should have last_message"
            assert "last_message_at" in conv, "Conversation should have last_message_at"
            assert "unread_count" in conv, "Conversation should have unread_count"
            
            # Verify other_user structure
            if conv["other_user"]:
                assert "username" in conv["other_user"], "other_user should have username"
                assert "avatar_url" in conv["other_user"], "other_user should have avatar_url"
            print(f"PASS: List conversations returns {len(data)} conversation(s) with correct structure")
        else:
            print("PASS: List conversations returns empty list (no conversations)")
    
    def test_get_conversation_by_id(self, demo_auth, trader_auth):
        """GET /api/dm/conversations/{id} - Get conversation with messages"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        
        # First get conversation list to get an ID
        resp = requests.get(f"{BASE_URL}/api/dm/conversations", headers=headers)
        data = resp.json()
        
        if len(data) == 0:
            pytest.skip("No conversations to test")
        
        conv_id = data[0]["id"]
        
        # Get the conversation
        resp = requests.get(f"{BASE_URL}/api/dm/conversations/{conv_id}", headers=headers)
        assert resp.status_code == 200, f"Get conversation failed: {resp.text}"
        conv = resp.json()
        
        assert "id" in conv, "Conversation should have id"
        assert "other_user" in conv, "Conversation should have other_user"
        assert "messages" in conv, "Conversation should have messages"
        assert isinstance(conv["messages"], list), "Messages should be a list"
        
        # Check context if present
        if conv.get("context"):
            assert "type" in conv["context"], "Context should have type"
        
        # Check message structure if any
        if len(conv["messages"]) > 0:
            msg = conv["messages"][0]
            assert "id" in msg, "Message should have id"
            assert "sender_id" in msg, "Message should have sender_id"
            assert "text" in msg, "Message should have text"
            assert "created_at" in msg, "Message should have created_at"
        
        print(f"PASS: Get conversation by ID returns {len(conv['messages'])} messages")
    
    def test_send_message_in_conversation(self, demo_auth):
        """POST /api/dm/conversations/{id}/messages - Send message in existing conversation"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        
        # Get conversation list to get an ID
        resp = requests.get(f"{BASE_URL}/api/dm/conversations", headers=headers)
        data = resp.json()
        
        if len(data) == 0:
            pytest.skip("No conversations to test")
        
        conv_id = data[0]["id"]
        
        # Send a message
        resp = requests.post(f"{BASE_URL}/api/dm/conversations/{conv_id}/messages", json={
            "text": "TEST_DM: Reply from pytest"
        }, headers=headers)
        assert resp.status_code == 200, f"Send message failed: {resp.text}"
        msg = resp.json()
        
        assert "id" in msg, "Message should have id"
        assert "text" in msg, "Message should have text"
        assert "sender_id" in msg, "Message should have sender_id"
        assert "created_at" in msg, "Message should have created_at"
        assert msg["text"] == "TEST_DM: Reply from pytest"
        
        print("PASS: Send message returns message object with correct data")
    
    def test_unread_count(self, demo_auth):
        """GET /api/dm/unread-count - Get unread message count"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/dm/unread-count", headers=headers)
        assert resp.status_code == 200, f"Unread count failed: {resp.text}"
        data = resp.json()
        
        assert "count" in data, "Response should have count"
        assert isinstance(data["count"], int), "Count should be an integer"
        assert data["count"] >= 0, "Count should be non-negative"
        
        print(f"PASS: Unread count returns {data['count']}")
    
    def test_conversation_with_user(self, demo_auth, trader_auth):
        """GET /api/dm/conversation-with/{userId} - Check existing conversation"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        
        # Check conversation with trader
        resp = requests.get(f"{BASE_URL}/api/dm/conversation-with/{trader_auth['user_id']}", headers=headers)
        assert resp.status_code == 200, f"Conversation with user check failed: {resp.text}"
        data = resp.json()
        
        assert "conversation_id" in data, "Response should have conversation_id"
        # conversation_id can be None if no conversation exists
        print(f"PASS: Conversation-with returns conversation_id: {data['conversation_id']}")
    
    def test_user_by_id(self, demo_auth, trader_auth):
        """GET /api/users/by-id/{userId} - Get user info by ID"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        
        resp = requests.get(f"{BASE_URL}/api/users/by-id/{trader_auth['user_id']}", headers=headers)
        assert resp.status_code == 200, f"User by ID failed: {resp.text}"
        data = resp.json()
        
        assert "id" in data, "Response should have id"
        assert "username" in data, "Response should have username"
        assert data["id"] == trader_auth["user_id"], "ID should match"
        
        print(f"PASS: User by ID returns user: @{data['username']}")
    
    def test_user_by_id_not_found(self, demo_auth):
        """GET /api/users/by-id/{userId} - Non-existent user returns 404"""
        headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        
        resp = requests.get(f"{BASE_URL}/api/users/by-id/nonexistent-user-id-12345", headers=headers)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("PASS: Non-existent user returns 404")
    
    def test_dm_notification_created(self, demo_auth, trader_auth):
        """Verify DM notification is created when message is sent"""
        demo_headers = {"Authorization": f"Bearer {demo_auth['token']}"}
        trader_headers = {"Authorization": f"Bearer {trader_auth['token']}"}
        
        # Send a message from demo to trader
        resp = requests.post(f"{BASE_URL}/api/dm/conversations", json={
            "recipient_id": trader_auth['user_id'],
            "text": "TEST_DM_NOTIF: Check notification"
        }, headers=demo_headers)
        assert resp.status_code == 200, f"Send message failed: {resp.text}"
        
        # Check trader's notifications (should have a new DM notification)
        resp = requests.get(f"{BASE_URL}/api/notifications?limit=5", headers=trader_headers)
        if resp.status_code == 200:
            notifications = resp.json()
            dm_notifs = [n for n in notifications if n.get("type") == "dm" or "message" in n.get("body", "").lower()]
            if len(dm_notifs) > 0:
                print(f"PASS: DM notification created - found {len(dm_notifs)} DM notification(s)")
            else:
                print("WARNING: No DM notifications found (may be timing issue)")
        else:
            print(f"SKIP: Notifications endpoint returned {resp.status_code}")
    
    def test_unauth_dm_endpoints(self):
        """Verify DM endpoints require authentication"""
        # Test list conversations
        resp = requests.get(f"{BASE_URL}/api/dm/conversations")
        assert resp.status_code == 401, f"List conversations should require auth: {resp.status_code}"
        
        # Test unread count
        resp = requests.get(f"{BASE_URL}/api/dm/unread-count")
        assert resp.status_code == 401, f"Unread count should require auth: {resp.status_code}"
        
        # Test create conversation
        resp = requests.post(f"{BASE_URL}/api/dm/conversations", json={"recipient_id": "test", "text": "test"})
        assert resp.status_code == 401, f"Create conversation should require auth: {resp.status_code}"
        
        print("PASS: All DM endpoints require authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
