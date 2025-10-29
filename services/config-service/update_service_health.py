#!/usr/bin/env python3
"""
Script to update service registry health status by checking actual service endpoints.
This script performs health checks on all registered services and updates their status.
"""

import requests
import json
import sys
import time
from typing import Dict, List, Any

BASE_URL = "http://localhost:8082/api/v1"
API_KEY = "admin"
HEADERS = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json"
}

# Health check endpoints for different services
HEALTH_CHECK_ENDPOINTS = {
    "api-gateway-service": "/health",
    "auth-service": "/health",
    "config-service": "/health",
    "metrics-service": "/health",
    "telemetry-service": "/health",
    "alerting-service": "/health",
    "dashboard-service": "/health",
    "asr-service": "/api/v1/asr/health",
    "tts-service": "/health",
    "nmt-service": "/api/v1/nmt/health",
    "pipeline-service": "/health",
    "simple-ui-frontend": "/health",
}


def get_all_services() -> List[Dict[str, Any]]:
    """Get all registered services."""
    try:
        response = requests.get(f"{BASE_URL}/registry/", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("services", [])
        return []
    except Exception as e:
        print(f"Error getting services: {e}")
        return []


def check_service_health(service: Dict[str, Any]) -> tuple[bool, float]:
    """
    Check if a service is healthy by calling its health endpoint.
    Returns (is_healthy, response_time_ms)
    """
    service_name = service.get("service_name")
    service_url = service.get("service_url")
    health_check_url = service.get("health_check_url")
    
    if not service_url and not health_check_url:
        return False, 0.0
    
    # Use health_check_url if available, otherwise construct from service_url
    if health_check_url:
        url = health_check_url
    else:
        # Try to construct health endpoint
        endpoint = HEALTH_CHECK_ENDPOINTS.get(service_name, "/health")
        url = f"{service_url.rstrip('/')}{endpoint}"
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Check JSON status field first (more reliable than HTTP status code)
        # Some services return 200 even when unhealthy, or 503 with detailed status
        is_healthy = False
        try:
            data = response.json()
            if isinstance(data, dict):
                # Check if response has a detail wrapper (e.g., from HTTPException)
                if "detail" in data and isinstance(data["detail"], dict):
                    status_dict = data["detail"]
                    status = status_dict.get("status", "").lower()
                else:
                    status = data.get("status", "").lower()
                
                # Consider healthy if status is "healthy"
                if status == "healthy":
                    is_healthy = True
                elif status in ["unhealthy", "error", "down"]:
                    is_healthy = False
                elif response.status_code == 200:
                    # If no explicit status field but 200, consider healthy
                    is_healthy = True
        except:
            # If JSON parsing fails, fall back to HTTP status code
            is_healthy = response.status_code == 200
        
        return is_healthy, response_time
    except requests.exceptions.ConnectionError:
        return False, 0.0
    except requests.exceptions.Timeout:
        return False, 0.0
    except Exception as e:
        print(f"  ⚠️  Error checking {service_name}: {e}")
        return False, 0.0


def update_service_health(service_name: str, status: str, response_time: float = None) -> bool:
    """Update service health status."""
    try:
        data = {
            "service_name": service_name,
            "status": status,
        }
        if response_time is not None:
            data["response_time"] = response_time
        
        response = requests.put(
            f"{BASE_URL}/registry/health",
            headers=HEADERS,
            json=data,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error updating health for {service_name}: {e}")
        return False


def check_all_services():
    """Check health of all registered services and update their status."""
    print("=" * 80)
    print("Service Registry Health Check")
    print("=" * 80)
    print()
    
    services = get_all_services()
    
    if not services:
        print("No services found in registry.")
        return
    
    print(f"Found {len(services)} services. Checking health...")
    print("-" * 80)
    
    healthy_count = 0
    unhealthy_count = 0
    updated_count = 0
    
    for service in services:
        service_name = service.get("service_name")
        current_status = service.get("status", "unknown")
        
        print(f"Checking {service_name}...", end=" ")
        
        is_healthy, response_time = check_service_health(service)
        
        if is_healthy:
            new_status = "healthy"
            healthy_count += 1
            status_icon = "✅"
        else:
            new_status = "unhealthy"
            unhealthy_count += 1
            status_icon = "❌"
        
        # Update if status changed or still unknown
        if current_status != new_status or current_status == "unknown":
            if update_service_health(service_name, new_status, response_time):
                print(f"{status_icon} Updated: {current_status} → {new_status} ({response_time:.1f}ms)")
                updated_count += 1
            else:
                print(f"{status_icon} Failed to update")
        else:
            print(f"{status_icon} No change: {current_status}")
    
    print("-" * 80)
    print(f"\nSummary:")
    print(f"  ✅ Healthy: {healthy_count}")
    print(f"  ❌ Unhealthy: {unhealthy_count}")
    print(f"  📝 Updated: {updated_count}")
    print()
    print("=" * 80)


def check_single_service(service_name: str):
    """Check health of a single service."""
    services = get_all_services()
    
    service = next((s for s in services if s.get("service_name") == service_name), None)
    
    if not service:
        print(f"Service '{service_name}' not found in registry.")
        return
    
    print(f"Checking {service_name}...")
    
    is_healthy, response_time = check_service_health(service)
    new_status = "healthy" if is_healthy else "unhealthy"
    
    if update_service_health(service_name, new_status, response_time):
        print(f"✅ Updated: {new_status} ({response_time:.1f}ms)")
    else:
        print(f"❌ Failed to update")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update service registry health status")
    parser.add_argument(
        "service",
        nargs="?",
        help="Service name to check (optional, checks all if not provided)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Run health checks continuously with specified interval in seconds (0 = run once)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.service:
            check_single_service(args.service)
        elif args.interval > 0:
            print(f"Running health checks every {args.interval} seconds...")
            print("Press Ctrl+C to stop\n")
            while True:
                check_all_services()
                time.sleep(args.interval)
        else:
            check_all_services()
        
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nHealth check stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)

