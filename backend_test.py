#!/usr/bin/env python3
"""
Backend API Testing for Irys Username System
Tests all API endpoints using the public URL
"""

import requests
import json
import sys
from datetime import datetime
from eth_account import Account
from eth_account.messages import encode_defunct

class IrysUsernameAPITester:
    def __init__(self, base_url="https://af7a6df2-50e4-4453-8477-423f60035a12.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        
        # Create a test account for signature testing
        self.test_account = Account.create()
        self.test_address = self.test_account.address
        self.test_private_key = self.test_account.key
        
        print(f"🔧 Test Setup:")
        print(f"   Base URL: {self.base_url}")
        print(f"   Test Address: {self.test_address}")
        print(f"   Starting tests...\n")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    print(f"   Response: {response.text}")
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def sign_message(self, message):
        """Sign a message with the test account"""
        message_hash = encode_defunct(text=message)
        signed_message = Account.sign_message(message_hash, private_key=self.test_private_key)
        return signed_message.signature.hex()

    def test_root_endpoint(self):
        """Test the root endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )

    def test_username_availability_valid(self):
        """Test username availability check with valid username"""
        return self.run_test(
            "Username Availability - Valid Username",
            "GET",
            "api/username/check/testuser123",
            200
        )

    def test_username_availability_taken(self):
        """Test username availability check with taken username"""
        return self.run_test(
            "Username Availability - Taken Username",
            "GET",
            "api/username/check/demo",
            200
        )

    def test_username_availability_invalid(self):
        """Test username availability check with invalid username"""
        return self.run_test(
            "Username Availability - Invalid Username",
            "GET",
            "api/username/check/ab",  # Too short
            400
        )

    def test_username_registration_valid(self):
        """Test username registration with valid data"""
        username = f"testuser_{int(datetime.now().timestamp())}"
        message = f"Register username: {username}"
        signature = self.sign_message(message)
        
        data = {
            "username": username,
            "address": self.test_address,
            "signature": signature,
            "metadata": {
                "test": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return self.run_test(
            "Username Registration - Valid",
            "POST",
            "api/username/register",
            200,
            data=data
        )

    def test_username_registration_taken(self):
        """Test username registration with taken username"""
        username = "demo"  # This should be taken
        message = f"Register username: {username}"
        signature = self.sign_message(message)
        
        data = {
            "username": username,
            "address": self.test_address,
            "signature": signature
        }
        
        return self.run_test(
            "Username Registration - Taken Username",
            "POST",
            "api/username/register",
            409,  # Conflict
            data=data
        )

    def test_username_registration_invalid_signature(self):
        """Test username registration with invalid signature"""
        username = f"testuser_{int(datetime.now().timestamp())}"
        
        data = {
            "username": username,
            "address": self.test_address,
            "signature": "0x" + "0" * 130  # Invalid signature
        }
        
        return self.run_test(
            "Username Registration - Invalid Signature",
            "POST",
            "api/username/register",
            401,  # Unauthorized
            data=data
        )

    def test_get_usernames_leaderboard(self):
        """Test getting usernames leaderboard"""
        return self.run_test(
            "Get Usernames Leaderboard",
            "GET",
            "api/usernames",
            200
        )

    def test_get_usernames_with_limit(self):
        """Test getting usernames with limit parameter"""
        return self.run_test(
            "Get Usernames with Limit",
            "GET",
            "api/usernames?limit=2",
            200
        )

    def test_resolve_username_existing(self):
        """Test resolving existing username"""
        return self.run_test(
            "Resolve Username - Existing",
            "GET",
            "api/resolve/demo",
            200
        )

    def test_resolve_username_nonexistent(self):
        """Test resolving non-existent username"""
        return self.run_test(
            "Resolve Username - Non-existent",
            "GET",
            "api/resolve/nonexistentuser123",
            404
        )

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Irys Username API Tests\n")
        
        # Test all endpoints
        tests = [
            self.test_root_endpoint,
            self.test_username_availability_valid,
            self.test_username_availability_taken,
            self.test_username_availability_invalid,
            self.test_username_registration_valid,
            self.test_username_registration_taken,
            self.test_username_registration_invalid_signature,
            self.test_get_usernames_leaderboard,
            self.test_get_usernames_with_limit,
            self.test_resolve_username_existing,
            self.test_resolve_username_nonexistent
        ]
        
        for test in tests:
            try:
                test()
                print()  # Add spacing between tests
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}\n")
        
        # Print final results
        print("=" * 50)
        print(f"📊 Test Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed!")
            return 1

def main():
    """Main function to run all tests"""
    tester = IrysUsernameAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())