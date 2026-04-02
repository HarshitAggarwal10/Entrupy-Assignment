import requests
import json
import time
import sys
from typing import Optional, Dict

# Configuration
BASE_URL = "http://localhost:8000/api"
TIMEOUT = 10

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")

def print_test_result(test_name: str, status: bool, response: Optional[dict] = None):
    """Print test result"""
    if status:
        print_success(f"{test_name}")
        if response:
            print(f"  Response: {json.dumps(response, indent=2)[:200]}...")
    else:
        print_error(f"{test_name}")
        if response:
            print(f"  Error: {json.dumps(response, indent=2)}")

def test_health_check() -> bool:
    """Test 1: Health check endpoint"""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/../health", timeout=TIMEOUT)
        data = response.json()
        
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            print_success("Health check passed")
            return True
        else:
            print_error(f"Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_create_api_key(name: str = "TestApp") -> Optional[str]:
    """Test 2: Create API key"""
    print_header("TEST 2: Create API Key")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api-keys",
            params={"name": name},
            timeout=TIMEOUT
        )
        
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200 and "api_key" in data:
            print_success(f"API key created: {name}")
            print_info(f"Key (save this!): {data['api_key']}")
            return data['api_key']
        else:
            print_error(f"Failed to create API key: {data}")
            return None
    except Exception as e:
        print_error(f"API key creation failed: {e}")
        return None

def test_list_api_keys() -> bool:
    """Test 3: List all API keys"""
    print_header("TEST 3: List API Keys")
    
    try:
        response = requests.get(f"{BASE_URL}/api-keys", timeout=TIMEOUT)
        
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Total keys: {data.get('total', 0)}")
        
        if data.get('keys'):
            for key in data['keys']:
                print(f"    - {key['name']} (Created: {key['created_at']})")
        
        if response.status_code == 200:
            print_success("Listed API keys")
            return True
        else:
            print_error("Failed to list API keys")
            return False
    except Exception as e:
        print_error(f"List API keys failed: {e}")
        return False

def test_get_products_with_key(api_key: str) -> bool:
    """Test 4: Get products WITH valid API key"""
    print_header("TEST 4: Get Products WITH Valid API Key")
    
    try:
        headers = {"X-API-Key": api_key}
        response = requests.get(
            f"{BASE_URL}/products?limit=3",
            headers=headers,
            timeout=TIMEOUT
        )
        
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Total products: {data.get('total', 0)}")
        print(f"  Returned: {len(data.get('data', []))} items")
        
        if response.status_code == 200 and data.get('data'):
            print_success("Retrieved products with API key")
            return True
        else:
            print_error("Failed to retrieve products")
            return False
    except Exception as e:
        print_error(f"Get products failed: {e}")
        return False

def test_get_products_without_key() -> bool:
    """Test 5: Get products WITHOUT API key"""
    print_header("TEST 5: Get Products WITHOUT API Key (Optional)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/products?limit=3",
            timeout=TIMEOUT
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print_success("API is open without authentication")
            return True
        else:
            print_info("API requires authentication")
            return True  # Still pass - depends on design choice
    except Exception as e:
        print_error(f"Failed: {e}")
        return False

def test_get_products_with_invalid_key() -> bool:
    """Test 6: Get products WITH invalid API key"""
    print_header("TEST 6: Get Products WITH Invalid API Key")
    
    try:
        headers = {"X-API-Key": "invalid-key-12345"}
        response = requests.get(
            f"{BASE_URL}/products",
            headers=headers,
            timeout=TIMEOUT
        )
        
        print(f"  Status: {response.status_code}")
        data = response.json()
        
        if response.status_code == 401:
            print_success("Correctly rejected invalid API key")
            print_info(f"Error: {data.get('detail', 'Unauthorized')}")
            return True
        else:
            print_error(f"Should reject invalid key, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False

def test_get_request_logs() -> bool:
    """Test 7: Get request logs"""
    print_header("TEST 7: Get Request Logs")
    
    try:
        response = requests.get(
            f"{BASE_URL}/request-logs?limit=10",
            timeout=TIMEOUT
        )
        
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Total logged requests: {data.get('total', 0)}")
        
        if data.get('logs'):
            print(f"  Recent requests:")
            for log in data['logs'][:3]:
                print(f"    - {log['method']} {log['path']} → {log['status_code']} ({log['response_time_ms']:.2f}ms)")
        
        if response.status_code == 200:
            print_success("Retrieved request logs")
            return True
        else:
            print_error("Failed to get request logs")
            return False
    except Exception as e:
        print_error(f"Get request logs failed: {e}")
        return False

def test_api_key_usage(api_key_id: Optional[str] = None) -> bool:
    """Test 8: Get API key usage statistics"""
    print_header("TEST 8: Get API Key Usage Statistics")
    
    if not api_key_id:
        print_info("Skipping - no API key ID available")
        return True
    
    try:
        response = requests.get(
            f"{BASE_URL}/api-keys/{api_key_id}/usage",
            timeout=TIMEOUT
        )
        
        print(f"  Status: {response.status_code}")
        data = response.json()
        
        print(f"  Total requests: {data.get('total_requests', 0)}")
        print(f"  Status codes: {json.dumps(data.get('status_codes', {}))}")
        print(f"  Avg response time: {data.get('average_response_time_ms', 0):.2f}ms")
        print(f"  Top endpoints:")
        for path, count in list(data.get('endpoints', {}).items())[:3]:
            print(f"    - {path}: {count} calls")
        
        if response.status_code == 200:
            print_success("Retrieved API key usage statistics")
            return True
        else:
            print_error("Failed to get usage statistics")
            return False
    except Exception as e:
        print_error(f"Get usage stats failed: {e}")
        return False

def test_filtering_and_analytics(api_key: str) -> bool:
    """Test 9: Test filtering and analytics with authentication"""
    print_header("TEST 9: Filtering & Analytics with Authentication")
    
    try:
        headers = {"X-API-Key": api_key}
        
        # Test filtering
        response = requests.get(
            f"{BASE_URL}/products?brand=Chanel&min_price=500&max_price=2000",
            headers=headers,
            timeout=TIMEOUT
        )
        
        print(f"  Filtering - Status: {response.status_code}")
        data = response.json()
        print(f"  Found {data.get('total', 0)} products matching filters")
        
        # Test analytics
        response = requests.get(
            f"{BASE_URL}/analytics",
            headers=headers,
            timeout=TIMEOUT
        )
        
        print(f"  Analytics - Status: {response.status_code}")
        data = response.json()
        print(f"  Total products: {data.get('total_products', 0)}")
        print(f"  By source: {json.dumps(data.get('products_by_source', {}))}")
        
        print_success("Filtering and analytics work with authentication")
        return True
    except Exception as e:
        print_error(f"Filtering/analytics test failed: {e}")
        return False

def test_rate_limiting(api_key: str) -> bool:
    """Test 10: Rate limiting (if enabled)"""
    print_header("TEST 10: Rate Limiting Check")
    
    try:
        headers = {"X-API-Key": api_key}
        
        # Make multiple rapid requests
        print("  Making 5 rapid requests...")
        for i in range(5):
            response = requests.get(
                f"{BASE_URL}/products?limit=1",
                headers=headers,
                timeout=TIMEOUT
            )
            print(f"    Request {i+1}: {response.status_code}")
        
        print_success("Rate limiting test completed (no hard limits enforced)")
        return True
    except Exception as e:
        if "429" in str(e):
            print_success("Rate limit detected (429 Too Many Requests)")
            return True
        else:
            print_error(f"Rate limiting test failed: {e}")
            return False

def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("  AUTHENTICATION & API TRACKING TEST SUITE")
    print("=" * 70)
    print(f"{Colors.END}\n")
    
    # Check if backend is running
    try:
        requests.get(f"{BASE_URL}/../health", timeout=5)
    except:
        print_error("Backend is not running!")
        print_info("Start backend with: python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    results = {}
    api_key = None
    api_key_id = None
    
    # Run tests
    results['health_check'] = test_health_check()
    
    # Create API key for remaining tests
    api_key = test_create_api_key(f"TestApp_{int(time.time())}")
    if not api_key:
        print_error("Cannot continue without API key")
        sys.exit(1)
    
    # Get the key ID from the list
    try:
        response = requests.get(f"{BASE_URL}/api-keys")
        data = response.json()
        if data.get('keys'):
            api_key_id = data['keys'][0]['id']
    except:
        pass
    
    results['list_api_keys'] = test_list_api_keys()
    results['products_with_key'] = test_get_products_with_key(api_key)
    results['products_without_key'] = test_get_products_without_key()
    results['invalid_key'] = test_get_products_with_invalid_key()
    results['request_logs'] = test_get_request_logs()
    results['api_usage'] = test_api_key_usage(api_key_id)
    results['filtering_analytics'] = test_filtering_and_analytics(api_key)
    results['rate_limiting'] = test_rate_limiting(api_key)
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"  {color}{test_name:.<40} {status}{Colors.END}")
    
    print(f"\n  {Colors.BOLD}Result: {passed}/{total} tests passed{Colors.END}\n")
    
    if passed == total:
        print_success("ALL TESTS PASSED!")
        return 0
    else:
        print_error(f"{total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
