#!/usr/bin/env python
"""
Comprehensive Authentication and Usage Tracking Test Suite
Tests customer registration, login, and API usage tracking
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(title):
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{title.center(70)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")

def print_test(name, passed, details=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status}  {name}")
    if details:
        print(f"     {YELLOW}→ {details}{RESET}")

def print_section(title):
    print(f"\n{BOLD}{YELLOW}{title}{RESET}")
    print(f"{YELLOW}{'-'*70}{RESET}")

print_header("COMPLETE CUSTOMER AUTHENTICATION & API USAGE TEST")

# Test Results
results = {
    "total": 0,
    "passed": 0,
    "failed": 0
}

# Sample user data
test_email = f"test_{datetime.now().timestamp()}@example.com"
test_user = {
    "username": f"testuser_{int(datetime.now().timestamp())}",
    "email": test_email,
    "password": "SecurePassword123!",
    "full_name": "Test User"
}

access_token = None


# TEST 1: Health Check
print_section("1. Health Check")
try:
    response = requests.get(f"{BASE_URL}/health")
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
    print_test("Server is running", passed, f"Status: {response.status_code}")
except Exception as e:
    print_test("Server is running", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 2: Register New Customer
print_section("2. Customer Registration")
try:
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=test_user
    )
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
        data = response.json()
        access_token = data.get("access_token")
        print_test("Register new customer account", passed, f"Username: {test_user['username']}")
        print(f"     {GREEN}→ Token received (first 20 chars): {access_token[:20]}...{RESET}")
    else:
        print_test("Register new customer account", False, response.json().get("detail", response.text))
        results["failed"] += 1
except Exception as e:
    print_test("Register new customer account", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 3: Login with Credentials
print_section("3. Customer Login")
try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": test_user["username"],
            "password": test_user["password"]
        }
    )
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
        data = response.json()
        access_token = data.get("access_token")
        user_info = data.get("user")
        print_test("Login with username/password", passed)
        print(f"     {GREEN}→ Welcome message: {data.get('message')}{RESET}")
        print(f"     {GREEN}→ User: {user_info.get('username')} ({user_info.get('email')}){RESET}")
    else:
        print_test("Login with username/password", False, response.json().get("detail"))
        results["failed"] += 1
except Exception as e:
    print_test("Login with username/password", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 4: Get User Profile
print_section("4. Fetch User Profile")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
        data = response.json()
        print_test("Retrieve authenticated user profile", passed)
        print(f"     {GREEN}→ Email: {data.get('email')}{RESET}")
        print(f"     {GREEN}→ Daily limit: {data.get('max_requests_per_day')} requests{RESET}")
        print(f"     {GREEN}→ Monthly limit: {data.get('max_requests_per_month')} requests{RESET}")
    else:
        print_test("Retrieve authenticated user profile", False, response.json().get("detail"))
        results["failed"] += 1
except Exception as e:
    print_test("Retrieve authenticated user profile", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 5: Access Public Endpoint (No Auth)
print_section("5. Public API Access")
try:
    response = requests.get(f"{BASE_URL}/products?limit=3")
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
        data = response.json()
        print_test("Access products without authentication", passed)
        print(f"     {GREEN}→ Retrieved {len(data.get('data', []))} products{RESET}")
        print(f"     {GREEN}→ Total available: {data.get('total')} products{RESET}")
    else:
        print_test("Access products without authentication", False, response.text)
        results["failed"] += 1
except Exception as e:
    print_test("Access products without authentication", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 6: Track Usage with Authenticated Request
print_section("6. API Usage Tracking")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Make 3 authenticated requests to generate usage logs
    for i in range(3):
        requests.get(f"{BASE_URL}/products?limit=2", headers=headers)
    
    # Fetch usage stats
    response = requests.get(f"{BASE_URL}/auth/usage", headers=headers)
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
        data = response.json()
        print_test("Track and retrieve API usage statistics", passed)
        print(f"     {GREEN}→ Total requests: {data.get('total_requests')}{RESET}")
        print(f"     {GREEN}→ Requests today: {data.get('requests_today')}/{data.get('limit_today')}{RESET}")
        print(f"     {GREEN}→ Requests this month: {data.get('requests_this_month')}/{data.get('limit_this_month')}{RESET}")
        print(f"     {GREEN}→ Remaining today: {data.get('requests_remaining_today')} requests{RESET}")
        print(f"     {GREEN}→ Avg response time: {data.get('average_response_time_ms'):.2f}ms{RESET}")
        
        top_endpoints = data.get('top_endpoints', [])
        if top_endpoints:
            print(f"     {GREEN}→ Top endpoints:{RESET}")
            for ep in top_endpoints:
                print(f"        • {ep.get('endpoint')}: {ep.get('requests')} requests")
    else:
        print_test("Track and retrieve API usage statistics", False, response.json().get("detail"))
        results["failed"] += 1
except Exception as e:
    print_test("Track and retrieve API usage statistics", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 7: Refresh Token
print_section("7. Token Refresh")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{BASE_URL}/auth/refresh-token", headers=headers)
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
        data = response.json()
        new_token = data.get("access_token")
        print_test("Refresh authentication token", passed)
        print(f"     {GREEN}→ New token received{RESET}")
        print(f"     {GREEN}→ Message: {data.get('message')}{RESET}")
        access_token = new_token  # Update for next tests
    else:
        print_test("Refresh authentication token", False, response.json().get("detail"))
        results["failed"] += 1
except Exception as e:
    print_test("Refresh authentication token", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 8: View Usage History
print_section("8. Detailed Usage History")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/usage/history?limit=10", headers=headers)
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
        data = response.json()
        print_test("Retrieve detailed usage history", passed)
        print(f"     {GREEN}→ Total log entries: {data.get('total')}{RESET}")
        
        logs = data.get('logs', [])
        if logs:
            print(f"     {GREEN}→ Latest requests:{RESET}")
            for log in logs[:3]:
                print(f"        • {log['method']} {log['endpoint']} → {log['status']} ({log['response_time_ms']:.2f}ms)")
    else:
        print_test("Retrieve detailed usage history", False, response.json().get("detail"))
        results["failed"] += 1
except Exception as e:
    print_test("Retrieve detailed usage history", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 9: Invalid Token Rejection
print_section("9. Security - Invalid Token Rejection")
try:
    headers = {"Authorization": "Bearer invalid-token-12345"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    passed = response.status_code == 401
    results["total"] += 1
    if passed:
        results["passed"] += 1
        print_test("Reject invalid authentication token", passed)
        print(f"     {GREEN}→ Security check passed: Unauthorized (401){RESET}")
    else:
        print_test("Reject invalid authentication token", False, f"Expected 401, got {response.status_code}")
        results["failed"] += 1
except Exception as e:
    print_test("Reject invalid authentication token", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# TEST 10: Logout
print_section("10. Customer Logout")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    passed = response.status_code == 200
    results["total"] += 1
    if passed:
        results["passed"] += 1
        data = response.json()
        print_test("Logout and invalidate session", passed)
        print(f"     {GREEN}→ Message: {data.get('message')}{RESET}")
    else:
        print_test("Logout and invalidate session", False, response.json().get("detail"))
        results["failed"] += 1
except Exception as e:
    print_test("Logout and invalidate session", False, str(e))
    results["total"] += 1
    results["failed"] += 1


# Summary
print_header("TEST SUMMARY")
print(f"{BOLD}Total Tests:{RESET} {results['total']}")
print(f"{GREEN}{BOLD}Passed:{RESET} {results['passed']}")
print(f"{RED}{BOLD}Failed:{RESET} {results['failed']}")

pass_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
status_color = GREEN if pass_rate == 100 else YELLOW if pass_rate >= 80 else RED
print(f"\n{status_color}{BOLD}Success Rate: {pass_rate:.1f}%{RESET}\n")

if results['failed'] == 0:
    print(f"{GREEN}{BOLD}✓ ALL TESTS PASSED!{RESET} 🎉\n")
else:
    print(f"{RED}{BOLD}⚠ {results['failed']} TEST(S) FAILED{RESET}\n")
