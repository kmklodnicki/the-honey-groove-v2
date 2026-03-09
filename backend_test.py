#!/usr/bin/env python3
import requests
import sys
import json
from datetime import datetime
import time
import uuid

class HoneyGrooveAPITester:
    def __init__(self, base_url="https://wax-collector-dev.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.test_records = []
        self.tests_run = 0
        self.tests_passed = 0

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name} - {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200, auth=True):
        """Make HTTP request with error handling"""
        url = f"{self.api_base}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"

            if response.status_code != expected_status:
                return False, f"Status {response.status_code}, expected {expected_status}. Response: {response.text[:200]}"
            
            return True, response.json() if response.status_code != 204 else {}
        
        except requests.RequestException as e:
            return False, f"Request failed: {str(e)}"
        except json.JSONDecodeError:
            return False, f"Invalid JSON response: {response.text[:200]}"

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, result = self.make_request('GET', '/', auth=False)
        return self.log_result("Root API endpoint", success and "HoneyGroove" in str(result))

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"testuser{timestamp}@example.com"
        test_username = f"testuser{timestamp}"
        
        user_data = {
            "email": test_email,
            "password": "TestPass123!",
            "username": test_username
        }
        
        success, result = self.make_request('POST', '/auth/register', data=user_data, auth=False)
        
        if success:
            self.token = result.get('access_token')
            self.user_data = result.get('user')
        
        return self.log_result("User registration", success and self.token is not None)

    def test_user_login(self):
        """Test user login with registered credentials"""
        if not self.user_data:
            return self.log_result("User login", False, "No user data available")
        
        login_data = {
            "email": self.user_data['email'],
            "password": "TestPass123!"
        }
        
        success, result = self.make_request('POST', '/auth/login', data=login_data, auth=False)
        
        if success:
            self.token = result.get('access_token')
        
        return self.log_result("User login", success and 'access_token' in result)

    def test_get_user_profile(self):
        """Test getting current user profile"""
        success, result = self.make_request('GET', '/auth/me')
        return self.log_result("Get user profile", success and 'username' in result)

    def test_discogs_search(self):
        """Test Discogs API search integration"""
        success, result = self.make_request('GET', '/discogs/search?q=Pink Floyd')
        
        if success and isinstance(result, list) and len(result) > 0:
            # Store first result for later use
            self.test_record_data = result[0]
            return self.log_result("Discogs search", True)
        
        return self.log_result("Discogs search", False, f"Expected list with results, got: {type(result)}")

    def test_add_record_to_collection(self):
        """Test adding a record to collection"""
        if not hasattr(self, 'test_record_data'):
            # Fallback record data
            record_data = {
                "title": "The Dark Side of the Moon",
                "artist": "Pink Floyd", 
                "year": 1973,
                "format": "Vinyl",
                "notes": "Test record"
            }
        else:
            record_data = {
                "discogs_id": self.test_record_data.get('discogs_id'),
                "title": self.test_record_data.get('title', 'Test Album'),
                "artist": self.test_record_data.get('artist', 'Test Artist'),
                "cover_url": self.test_record_data.get('cover_url'),
                "year": self.test_record_data.get('year'),
                "format": "Vinyl",
                "notes": "Added via API test"
            }
        
        success, result = self.make_request('POST', '/records', data=record_data, expected_status=200)
        
        if success and 'id' in result:
            self.test_records.append(result)
            return self.log_result("Add record to collection", True)
        
        return self.log_result("Add record to collection", False, f"Failed to add record: {result}")

    def test_get_collection(self):
        """Test getting user's collection"""
        success, result = self.make_request('GET', '/records')
        
        if success and isinstance(result, list):
            return self.log_result("Get collection", len(result) > 0, f"Collection has {len(result)} records")
        
        return self.log_result("Get collection", False, "Expected list of records")

    def test_log_spin(self):
        """Test logging a spin"""
        if not self.test_records:
            return self.log_result("Log spin", False, "No records in collection to spin")
        
        record_id = self.test_records[0]['id']
        spin_data = {
            "record_id": record_id,
            "notes": "Great listening session!"
        }
        
        success, result = self.make_request('POST', '/spins', data=spin_data)
        return self.log_result("Log spin", success and 'id' in result)

    def test_get_spins(self):
        """Test getting user's spin history"""
        success, result = self.make_request('GET', '/spins')
        return self.log_result("Get spins", success and isinstance(result, list))

    def test_activity_feed(self):
        """Test getting activity feed (The Hive)"""
        success, result = self.make_request('GET', '/feed')
        
        if success and isinstance(result, list):
            return self.log_result("Activity feed (The Hive)", True, f"Feed has {len(result)} posts")
        
        return self.log_result("Activity feed (The Hive)", False, "Expected list of posts")

    def test_explore_feed(self):
        """Test getting explore feed"""
        success, result = self.make_request('GET', '/explore', auth=False)
        return self.log_result("Explore feed", success and isinstance(result, list))

    def test_buzzing_now(self):
        """Test getting trending/buzzing records"""
        success, result = self.make_request('GET', '/buzzing', auth=False)
        return self.log_result("Buzzing Now (trending)", success and isinstance(result, list))

    def test_weekly_summary(self):
        """Test weekly summary generation"""
        success, result = self.make_request('GET', '/weekly-summary')
        
        if success and 'total_spins' in result:
            return self.log_result("Weekly summary generation", True)
        
        return self.log_result("Weekly summary generation", False, "Expected summary data")

    def test_user_stats(self):
        """Test user profile stats"""
        success, result = self.make_request('GET', '/auth/me')
        
        if success:
            required_fields = ['collection_count', 'spin_count', 'followers_count', 'following_count']
            has_stats = all(field in result for field in required_fields)
            return self.log_result("User profile stats", has_stats)
        
        return self.log_result("User profile stats", False)

    def test_global_stats(self):
        """Test global stats endpoint"""
        success, result = self.make_request('GET', '/stats', auth=False)
        
        if success and all(key in result for key in ['users', 'records', 'spins', 'hauls']):
            return self.log_result("Global stats", True)
        
        return self.log_result("Global stats", False, "Expected stats object")

    def test_search_users(self):
        """Test user search"""
        if not self.user_data:
            return self.log_result("Search users", False, "No user data")
        
        # Search for current user
        query = self.user_data['username'][:3]  # Search partial username
        success, result = self.make_request('GET', f'/users/search/{query}')
        return self.log_result("Search users", success and isinstance(result, list))

    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test records
        for record in self.test_records:
            try:
                self.make_request('DELETE', f"/records/{record['id']}")
            except:
                pass

    def run_all_tests(self):
        """Run all API tests"""
        print("🍯 Starting HoneyGroove API Tests")
        print("=" * 50)
        
        # Basic connectivity
        self.test_root_endpoint()
        
        # Authentication flow
        self.test_user_registration()
        self.test_user_login() 
        self.test_get_user_profile()
        
        # Record management
        self.test_discogs_search()
        self.test_add_record_to_collection()
        self.test_get_collection()
        
        # Spin logging
        self.test_log_spin()
        self.test_get_spins()
        
        # Social features
        self.test_activity_feed()
        self.test_explore_feed()
        self.test_buzzing_now()
        
        # Analytics
        self.test_weekly_summary()
        self.test_user_stats()
        self.test_global_stats()
        
        # Search
        self.test_search_users()
        
        # Cleanup
        self.cleanup()
        
        # Results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            failed = self.tests_run - self.tests_passed
            print(f"❌ {failed} tests failed")
            return 1

if __name__ == "__main__":
    tester = HoneyGrooveAPITester()
    sys.exit(tester.run_all_tests())