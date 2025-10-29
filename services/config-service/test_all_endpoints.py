#!/usr/bin/env python3
"""
Comprehensive test script for all Config Service API endpoints.
Tests all endpoints and identifies any issues.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8082"
API_KEY = "admin"  # Default test API key
HEADERS = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class EndpointTestResult:
    def __init__(self, name: str, method: str, path: str):
        self.name = name
        self.method = method
        self.path = path
        self.success = False
        self.status_code = None
        self.response = None
        self.error = None
        self.duration = None

def print_result(result: EndpointTestResult):
    """Print test result with color coding."""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result.success else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} {result.method:6s} {result.path}")
    if result.error:
        print(f"        Error: {result.error}")
    if result.status_code and not result.success:
        print(f"        Status: {result.status_code}")
        if result.response:
            print(f"        Response: {json.dumps(result.response, indent=10)}")

def test_endpoint(name: str, method: str, path: str, 
                 data: Optional[Dict] = None, 
                 params: Optional[Dict] = None,
                 headers: Optional[Dict] = None,
                 expected_status: int = 200) -> EndpointTestResult:
    """Test a single endpoint."""
    result = EndpointTestResult(name, method, path)
    
    try:
        url = f"{BASE_URL}{path}"
        test_headers = headers or HEADERS
        
        start_time = datetime.now()
        
        if method == "GET":
            response = requests.get(url, headers=test_headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=test_headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=test_headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=test_headers, timeout=10)
        else:
            result.error = f"Unsupported method: {method}"
            return result
        
        result.duration = (datetime.now() - start_time).total_seconds()
        result.status_code = response.status_code
        
        try:
            result.response = response.json()
        except:
            result.response = response.text
        
        # Consider 2xx and 3xx as success, but check if it matches expected
        if expected_status:
            result.success = response.status_code == expected_status
        else:
            result.success = 200 <= response.status_code < 400
        
        if not result.success:
            result.error = f"Expected status {expected_status}, got {result.status_code}"
            
    except requests.exceptions.ConnectionError:
        result.error = "Connection refused - is the service running?"
    except requests.exceptions.Timeout:
        result.error = "Request timeout"
    except Exception as e:
        result.error = str(e)
    
    return result

def main():
    """Run all endpoint tests."""
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}Config Service API Endpoint Testing{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    results = []
    
    # Test health endpoints
    print(f"{Colors.YELLOW}Health & Status{Colors.RESET}")
    print("-" * 80)
    results.append(test_endpoint("Root", "GET", "/"))
    results.append(test_endpoint("Health Check", "GET", "/health"))
    results.append(test_endpoint("Config Status", "GET", "/api/v1/config/status"))
    print()
    
    # Configuration endpoints
    print(f"{Colors.YELLOW}Configuration Management{Colors.RESET}")
    print("-" * 80)
    
    # Create configuration
    config_data = {
        "key": "test.database.url",
        "value": "postgresql://localhost:5432/testdb",
        "environment": "development",
        "service_name": "test-service",
        "description": "Test database URL",
        "is_encrypted": False
    }
    create_result = test_endpoint("Create Config", "POST", "/api/v1/config/", data=config_data)
    results.append(create_result)
    config_id = create_result.response.get("id") if create_result.success and create_result.response else None
    
    # List configurations
    results.append(test_endpoint("List Configs", "GET", "/api/v1/config/"))
    results.append(test_endpoint("List Configs (filtered)", "GET", "/api/v1/config/", 
                                params={"environment": "development", "service_name": "test-service"}))
    
    # Get configuration by key
    if config_id:
        results.append(test_endpoint("Get Config by Key", "GET", "/api/v1/config/test.database.url",
                                    params={"environment": "development", "service_name": "test-service"}))
        
        # Get configurations by service
        results.append(test_endpoint("Get Configs by Service", "GET", "/api/v1/config/service/test-service",
                                    params={"environment": "development"}))
        
        # Update configuration
        update_data = {
            "value": "postgresql://newhost:5432/testdb",
            "description": "Updated database URL"
        }
        results.append(test_endpoint("Update Config", "PUT", f"/api/v1/config/{config_id}", data=update_data))
        
        # Get configuration history
        results.append(test_endpoint("Get Config History", "GET", f"/api/v1/config/{config_id}/history"))
        
        # Delete configuration
        results.append(test_endpoint("Delete Config", "DELETE", f"/api/v1/config/{config_id}", expected_status=200))
    else:
        print(f"{Colors.RED}Warning: Skipping config tests - create failed{Colors.RESET}\n")
    
    print()
    
    # Feature Flag endpoints
    print(f"{Colors.YELLOW}Feature Flag Management{Colors.RESET}")
    print("-" * 80)
    
    # Create feature flag
    flag_data = {
        "name": "test_feature_flag",
        "description": "Test feature flag",
        "is_enabled": True,
        "rollout_percentage": 50.0,
        "target_users": ["user1", "user2"],
        "environment": "development"
    }
    create_flag_result = test_endpoint("Create Feature Flag", "POST", "/api/v1/feature-flags/", data=flag_data)
    results.append(create_flag_result)
    flag_id = create_flag_result.response.get("id") if create_flag_result.success and create_flag_result.response else None
    
    # List feature flags
    results.append(test_endpoint("List Feature Flags", "GET", "/api/v1/feature-flags/"))
    results.append(test_endpoint("List Feature Flags (filtered)", "GET", "/api/v1/feature-flags/",
                                 params={"environment": "development"}))
    
    # Get feature flag
    if flag_id:
        results.append(test_endpoint("Get Feature Flag", "GET", "/api/v1/feature-flags/test_feature_flag",
                                    params={"environment": "development"}))
        
        # Evaluate feature flag (POST)
        eval_data = {
            "flag_name": "test_feature_flag",
            "environment": "development",
            "user_id": "user1"
        }
        results.append(test_endpoint("Evaluate Feature Flag (POST)", "POST", "/api/v1/feature-flags/evaluate", data=eval_data))
        
        # Evaluate feature flag (GET)
        results.append(test_endpoint("Evaluate Feature Flag (GET)", "GET", "/api/v1/feature-flags/test_feature_flag/evaluate",
                                    params={"environment": "development", "user_id": "user1"}))
        
        # Update feature flag
        update_flag_data = {
            "is_enabled": False,
            "rollout_percentage": 75.0
        }
        results.append(test_endpoint("Update Feature Flag", "PUT", f"/api/v1/feature-flags/{flag_id}", data=update_flag_data))
        
        # Delete feature flag
        results.append(test_endpoint("Delete Feature Flag", "DELETE", f"/api/v1/feature-flags/{flag_id}", expected_status=200))
    else:
        print(f"{Colors.RED}Warning: Skipping feature flag tests - create failed{Colors.RESET}\n")
    
    print()
    
    # Service Registry endpoints
    print(f"{Colors.YELLOW}Service Registry{Colors.RESET}")
    print("-" * 80)
    
    # Register service
    service_data = {
        "service_name": "test-service-registry",
        "service_url": "http://test-service:8080",
        "health_check_url": "http://test-service:8080/health",
        "metadata": {
            "version": "1.0.0",
            "region": "us-east-1"
        }
    }
    register_result = test_endpoint("Register Service", "POST", "/api/v1/registry/register", data=service_data)
    results.append(register_result)
    
    # List services
    results.append(test_endpoint("List Services", "GET", "/api/v1/registry/"))
    results.append(test_endpoint("List Services (filtered)", "GET", "/api/v1/registry/",
                                params={"status": "healthy"}))
    
    # Get healthy services
    results.append(test_endpoint("Get Healthy Services", "GET", "/api/v1/registry/healthy"))
    
    # Get service
    results.append(test_endpoint("Get Service", "GET", "/api/v1/registry/test-service-registry"))
    
    # Update service health
    health_data = {
        "service_name": "test-service-registry",
        "status": "healthy",
        "response_time": 150.5
    }
    results.append(test_endpoint("Update Service Health", "PUT", "/api/v1/registry/health", data=health_data))
    
    # Deregister service
    results.append(test_endpoint("Deregister Service", "DELETE", "/api/v1/registry/test-service-registry", expected_status=200))
    
    print()
    
    # Summary
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}Test Summary{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    
    print(f"Total Tests: {len(results)}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    print()
    
    if failed > 0:
        print(f"{Colors.RED}Failed Tests:{Colors.RESET}")
        for result in results:
            if not result.success:
                print_result(result)
                print()
    
    # Exit with error if any tests failed
    sys.exit(1 if failed > 0 else 0)

if __name__ == "__main__":
    main()

