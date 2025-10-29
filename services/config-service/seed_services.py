#!/usr/bin/env python3
"""
Seed script to register all AI4V-Core microservices in the service registry.
Clears existing data and registers all services with accurate information.
"""

import requests
import json
import sys
from typing import List, Dict, Any

BASE_URL = "http://localhost:8082/api/v1"
API_KEY = "admin"
HEADERS = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json"
}

# All AI4V-Core microservices
SERVICES = [
    {
        "service_name": "api-gateway-service",
        "service_url": "http://api-gateway-service:8080",
        "health_check_url": "http://api-gateway-service:8080/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Central entry point with routing, rate limiting, and authentication",
            "port": 8080,
            "type": "gateway"
        }
    },
    {
        "service_name": "auth-service",
        "service_url": "http://auth-service:8081",
        "health_check_url": "http://auth-service:8081/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Identity management with JWT and OAuth2",
            "port": 8081,
            "type": "core"
        }
    },
    {
        "service_name": "config-service",
        "service_url": "http://config-service:8082",
        "health_check_url": "http://config-service:8082/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Centralized configuration and feature flags",
            "port": 8082,
            "type": "core"
        }
    },
    {
        "service_name": "metrics-service",
        "service_url": "http://metrics-service:8083",
        "health_check_url": "http://metrics-service:8083/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "System and application metrics collection",
            "port": 8083,
            "type": "core"
        }
    },
    {
        "service_name": "telemetry-service",
        "service_url": "http://telemetry-service:8084",
        "health_check_url": "http://telemetry-service:8084/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Log aggregation, distributed tracing, and event correlation",
            "port": 8084,
            "type": "core"
        }
    },
    {
        "service_name": "alerting-service",
        "service_url": "http://alerting-service:8085",
        "health_check_url": "http://alerting-service:8085/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Proactive issue detection and notification",
            "port": 8085,
            "type": "core"
        }
    },
    {
        "service_name": "dashboard-service",
        "service_url": "http://dashboard-service:8086",
        "health_check_url": "http://dashboard-service:8086/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Visualization and reporting with Streamlit UI",
            "port": 8086,
            "type": "core"
        }
    },
    {
        "service_name": "asr-service",
        "service_url": "http://asr-service:8087",
        "health_check_url": "http://asr-service:8087/api/v1/asr/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Speech-to-Text with 22+ Indian languages",
            "port": 8087,
            "type": "ai",
            "capabilities": ["asr", "speech-recognition", "streaming"]
        }
    },
    {
        "service_name": "tts-service",
        "service_url": "http://tts-service:8088",
        "health_check_url": "http://tts-service:8088/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Text-to-Speech with multiple voice options",
            "port": 8088,
            "type": "ai",
            "capabilities": ["tts", "text-to-speech", "voice-synthesis"]
        }
    },
    {
        "service_name": "nmt-service",
        "service_url": "http://nmt-service:8089",
        "health_check_url": "http://nmt-service:8089/api/v1/nmt/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Neural Machine Translation for Indian languages",
            "port": 8089,
            "type": "ai",
            "capabilities": ["translation", "nmt", "language-processing"]
        }
    },
    {
        "service_name": "pipeline-service",
        "service_url": "http://pipeline-service:8090",
        "health_check_url": "http://pipeline-service:8090/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Multi-task AI pipeline orchestration (Speech-to-Speech translation)",
            "port": 8090,
            "type": "ai",
            "capabilities": ["pipeline", "orchestration", "multi-task"]
        }
    },
    {
        "service_name": "simple-ui-frontend",
        "service_url": "http://simple-ui-frontend:3000",
        "health_check_url": "http://simple-ui-frontend:3000/health",
        "metadata": {
            "version": "1.0.0",
            "environment": "development",
            "description": "Web interface for testing AI services (Next.js)",
            "port": 3000,
            "type": "frontend"
        }
    }
]


def get_all_services() -> List[Dict[str, Any]]:
    """Get all currently registered services."""
    try:
        response = requests.get(f"{BASE_URL}/registry/", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("services", [])
        return []
    except Exception as e:
        print(f"Error getting services: {e}")
        return []


def delete_service(service_name: str) -> bool:
    """Delete a service from registry."""
    try:
        response = requests.delete(
            f"{BASE_URL}/registry/{service_name}",
            headers=HEADERS,
            timeout=10
        )
        return response.status_code in [200, 404]  # 404 means already deleted
    except Exception as e:
        print(f"Error deleting service {service_name}: {e}")
        return False


def register_service(service_data: Dict[str, Any]) -> bool:
    """Register a service in the registry."""
    try:
        response = requests.post(
            f"{BASE_URL}/registry/register",
            headers=HEADERS,
            json=service_data,
            timeout=10
        )
        if response.status_code == 200:
            service_info = response.json()
            print(f"✅ Registered: {service_data['service_name']} (ID: {service_info.get('id')})")
            return True
        else:
            print(f"❌ Failed to register {service_data['service_name']}: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error registering {service_data['service_name']}: {e}")
        return False


def clear_all_services():
    """Clear all existing services from registry."""
    print("Clearing existing services...")
    services = get_all_services()
    
    if not services:
        print("No services to clear.")
        return
    
    print(f"Found {len(services)} existing services. Deleting...")
    for service in services:
        service_name = service.get("service_name")
        if service_name:
            if delete_service(service_name):
                print(f"  🗑️  Deleted: {service_name}")
            else:
                print(f"  ❌ Failed to delete: {service_name}")
    
    print("Clearing complete.\n")


def seed_all_services():
    """Register all AI4V-Core services."""
    print("=" * 80)
    print("AI4V-Core Service Registry Seeding")
    print("=" * 80)
    print()
    
    # Clear existing services
    clear_all_services()
    
    # Register all services
    print("Registering all AI4V-Core services...")
    print("-" * 80)
    
    success_count = 0
    failed_count = 0
    
    for service in SERVICES:
        if register_service(service):
            success_count += 1
        else:
            failed_count += 1
    
    print("-" * 80)
    print(f"\n✅ Successfully registered: {success_count}")
    if failed_count > 0:
        print(f"❌ Failed to register: {failed_count}")
    
    # Verify registration
    print("\nVerifying registrations...")
    registered_services = get_all_services()
    print(f"\nTotal services in registry: {len(registered_services)}")
    
    if registered_services:
        print("\nRegistered Services:")
        for service in registered_services:
            print(f"  • {service['service_name']:30s} | {service['status']:10s} | {service['service_url']}")
    
    print("\n" + "=" * 80)
    print("Seeding complete!")
    print("=" * 80)
    print("\nNote: All services are registered with 'unknown' status.")
    print("Run 'python3 update_service_health.py' to check and update health status.")


if __name__ == "__main__":
    try:
        seed_all_services()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)

