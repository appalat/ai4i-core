# Config Service Integration Guide

## Purpose and Overview

The Configuration Management Service is a **centralized hub** for managing application configurations, feature flags, and service discovery across your microservices architecture. It solves critical problems in distributed systems:

### Problems It Solves

1. **Configuration Scattering**: Instead of hardcoding configs in each service, store them centrally
2. **Environment Management**: Different configs for dev/staging/prod without code changes
3. **Feature Rollouts**: Gradual feature releases with percentage-based or targeted rollouts
4. **Service Discovery**: Find and connect to healthy services dynamically
5. **Configuration Changes**: Update configs without redeploying services
6. **Secret Management**: Securely store encrypted sensitive values (API keys, passwords)

### Key Benefits

- **Single Source of Truth**: All configurations in one place
- **Dynamic Updates**: Change configs without redeployment
- **Environment Isolation**: Separate configs per environment
- **Service-Specific Configs**: Different settings per microservice
- **Audit Trail**: Track who changed what and when
- **Feature Flagging**: Control feature visibility without code changes
- **Service Discovery**: Automatic service health tracking

## How It Fits in the Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Microservices Ecosystem                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  User Service│  │  ASR Service │  │  TTS Service │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                  │            │
│         └─────────────────┼──────────────────┘            │
│                           │                                │
│         ┌─────────────────┴──────────────────┐            │
│         │     Config Service (This)          │            │
│         │  - Configuration Storage           │            │
│         │  - Feature Flags                   │            │
│         │  - Service Registry               │            │
│         └─────────────────┬──────────────────┘            │
│                           │                                │
│         ┌─────────────────┼──────────────────┐            │
│         │                 │                  │            │
│    ┌────┴─────┐    ┌──────┴───────┐   ┌─────┴──────┐    │
│    │ PostgreSQL │   │    Redis     │   │   Kafka   │    │
│    │            │   │   (Cache)     │   │  (Events) │    │
│    └────────────┘   └──────────────┘   └───────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Service Dependencies

- **Config Service** ← All microservices read from here
- **PostgreSQL** ← Config Service stores data here
- **Redis** ← Config Service caches for performance
- **Kafka** ← Config Service publishes change events

## Integration Patterns

### Pattern 1: Configuration Fetching

**Use Case**: Services need database URLs, API keys, or other settings

**Implementation**:

```python
# In your microservice (e.g., user-service)
import requests
import os

CONFIG_SERVICE_URL = os.getenv("CONFIG_SERVICE_URL", "http://config-service:8082")

def get_config(key: str, environment: str = None, service_name: str = None):
    """Fetch configuration from config service"""
    if not environment:
        environment = os.getenv("ENVIRONMENT", "development")
    if not service_name:
        service_name = os.getenv("SERVICE_NAME", "user-service")
    
    url = f"{CONFIG_SERVICE_URL}/api/v1/config/{key}"
    params = {"environment": environment, "service_name": service_name}
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        config = response.json()
        return config["value"]
    else:
        raise Exception(f"Failed to fetch config: {key}")

# Usage in your service
DATABASE_URL = get_config("database.url", "production", "user-service")
API_KEY = get_config("external.api_key", "production", "user-service")
MAX_RETRIES = int(get_config("retry.max_attempts", "production", "user-service") or "3")
```

### Pattern 2: Cached Configuration Client

**Use Case**: Reduce API calls with local caching

```python
import requests
import time
from typing import Optional

class ConfigClient:
    def __init__(self, config_service_url: str, cache_ttl: int = 300):
        self.config_service_url = config_service_url
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_times = {}
    
    def get_config(self, key: str, environment: str, service_name: str) -> Optional[str]:
        cache_key = f"{key}:{environment}:{service_name}"
        
        # Check cache
        if cache_key in self._cache:
            cache_age = time.time() - self._cache_times.get(cache_key, 0)
            if cache_age < self.cache_ttl:
                return self._cache[cache_key]
        
        # Fetch from config service
        url = f"{self.config_service_url}/api/v1/config/{key}"
        params = {"environment": environment, "service_name": service_name}
        
        try:
            response = requests.get(url, params=params, timeout=2)
            if response.status_code == 200:
                config = response.json()
                value = config["value"]
                # Cache it
                self._cache[cache_key] = value
                self._cache_times[cache_key] = time.time()
                return value
        except Exception as e:
            print(f"Config fetch failed: {e}")
            # Return cached value if available, even if expired
            return self._cache.get(cache_key)
        
        return None

# Initialize once in your service
config_client = ConfigClient("http://config-service:8082")

# Use throughout your service
db_url = config_client.get_config("database.url", "production", "user-service")
```

### Pattern 3: Startup Configuration Loading

**Use Case**: Load all configurations at service startup

```python
# In your service's startup code
async def load_configurations():
    """Load all configurations for this service at startup"""
    service_name = os.getenv("SERVICE_NAME")
    environment = os.getenv("ENVIRONMENT", "development")
    
    url = f"{CONFIG_SERVICE_URL}/api/v1/config/service/{service_name}"
    params = {"environment": environment}
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        configs = response.json()
        # Convert to dict for easy access
        config_dict = {cfg["key"]: cfg["value"] for cfg in configs}
        return config_dict
    return {}

# At service startup
@app.on_event("startup")
async def startup_event():
    configurations = await load_configurations()
    app.state.config = configurations
    logger.info(f"Loaded {len(configurations)} configurations")

# Use in your code
db_url = app.state.config.get("database.url")
```

### Pattern 4: Feature Flag Evaluation

**Use Case**: Control feature visibility dynamically

```python
def is_feature_enabled(flag_name: str, user_id: str = None) -> bool:
    """Check if a feature flag is enabled for a user"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    url = f"{CONFIG_SERVICE_URL}/api/v1/feature-flags/evaluate"
    payload = {
        "flag_name": flag_name,
        "environment": environment,
        "user_id": user_id
    }
    
    response = requests.post(url, json=payload, timeout=2)
    if response.status_code == 200:
        result = response.json()
        return result.get("enabled", False)
    return False

# Usage in your code
if is_feature_enabled("new_payment_flow", user_id="user123"):
    # Use new payment flow
    process_payment_v2()
else:
    # Use old payment flow
    process_payment_v1()
```

### Pattern 5: Service Discovery

**Use Case**: Find and connect to other services dynamically

```python
def discover_service(service_name: str) -> Optional[str]:
    """Discover the URL of a healthy service instance"""
    url = f"{CONFIG_SERVICE_URL}/api/v1/registry/{service_name}"
    
    response = requests.get(url, timeout=2)
    if response.status_code == 200:
        service = response.json()
        if service.get("status") == "healthy":
            return service.get("service_url")
    return None

def get_all_healthy_services() -> list:
    """Get all healthy services"""
    url = f"{CONFIG_SERVICE_URL}/api/v1/registry/healthy"
    
    response = requests.get(url, timeout=2)
    if response.status_code == 200:
        data = response.json()
        return data.get("services", [])
    return []

# Usage
user_service_url = discover_service("user-service")
if user_service_url:
    response = requests.get(f"{user_service_url}/api/users")
```

### Pattern 6: Event-Driven Configuration Updates

**Use Case**: Services automatically reload configs when they change

```python
from kafka import KafkaConsumer
import json

def watch_config_updates(service_name: str):
    """Watch for configuration updates via Kafka"""
    consumer = KafkaConsumer(
        'config-updates',
        bootstrap_servers='kafka:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    for message in consumer:
        event = message.value
        if (event.get("resource_type") == "configuration" and
            event.get("data", {}).get("service_name") == service_name):
            
            # Reload configuration
            config_key = event.get("data", {}).get("key")
            logger.info(f"Configuration {config_key} changed, reloading...")
            reload_config(config_key)

# In a separate thread or async task
# threading.Thread(target=watch_config_updates, args=("user-service",)).start()
```

### Pattern 7: Service Self-Registration

**Use Case**: Services register themselves in the registry

```python
@app.on_event("startup")
async def register_service():
    """Register this service in the service registry"""
    service_name = os.getenv("SERVICE_NAME", "user-service")
    service_url = os.getenv("SERVICE_URL", "http://user-service:8080")
    health_url = f"{service_url}/health"
    api_key = os.getenv("CONFIG_SERVICE_API_KEY")
    
    url = f"{CONFIG_SERVICE_URL}/api/v1/registry/register"
    headers = {"Authorization": f"ApiKey {api_key}"}
    payload = {
        "service_name": service_name,
        "service_url": service_url,
        "health_check_url": health_url,
        "metadata": {
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "region": os.getenv("REGION", "us-east-1")
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        logger.info(f"Service {service_name} registered successfully")

# Periodic health updates
async def update_health_status():
    """Update service health status periodically"""
    while True:
        await asyncio.sleep(30)  # Every 30 seconds
        
        service_name = os.getenv("SERVICE_NAME")
        response_time = measure_health_check_time()
        status = "healthy" if is_service_healthy() else "unhealthy"
        
        url = f"{CONFIG_SERVICE_URL}/api/v1/registry/health"
        headers = {"Authorization": f"ApiKey {os.getenv('CONFIG_SERVICE_API_KEY')}"}
        payload = {
            "service_name": service_name,
            "status": status,
            "response_time": response_time
        }
        
        requests.put(url, json=payload, headers=headers)

# Start health update task
# asyncio.create_task(update_health_status())
```

## Real-World Integration Examples

### Example 1: User Service Integration

```python
# user-service/main.py
from fastapi import FastAPI
import requests
import os

app = FastAPI()
CONFIG_SERVICE = os.getenv("CONFIG_SERVICE_URL", "http://config-service:8082")

# Load configs at startup
@app.on_event("startup")
async def startup():
    # Get database URL
    db_config_url = f"{CONFIG_SERVICE}/api/v1/config/database.url"
    params = {
        "environment": os.getenv("ENVIRONMENT", "production"),
        "service_name": "user-service"
    }
    response = requests.get(db_config_url, params=params)
    if response.status_code == 200:
        config = response.json()
        app.state.database_url = config["value"]
    
    # Get external API key
    api_key_url = f"{CONFIG_SERVICE}/api/v1/config/external.api_key"
    response = requests.get(api_key_url, params=params)
    if response.status_code == 200:
        config = response.json()
        app.state.external_api_key = config["value"]
    
    # Register this service
    register_service()

# Use configs in your endpoints
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    # Use database URL from config
    db_url = app.state.database_url
    # ... database operations
    
    # Check feature flag
    feature_url = f"{CONFIG_SERVICE}/api/v1/feature-flags/evaluate"
    feature_response = requests.post(feature_url, json={
        "flag_name": "enhanced_user_profile",
        "environment": os.getenv("ENVIRONMENT"),
        "user_id": user_id
    })
    
    use_enhanced = feature_response.json().get("enabled", False)
    # ... return appropriate response
```

### Example 2: ASR Service Integration

```python
# asr-service/main.py
import requests

# Get model configuration
def get_asr_model_config():
    config_key = "asr.model.path"
    url = f"{CONFIG_SERVICE}/api/v1/config/{config_key}"
    params = {
        "environment": "production",
        "service_name": "asr-service"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["value"]
    return "/default/model/path"

# Check if new ASR engine is enabled
def use_new_asr_engine(user_id: str) -> bool:
    eval_url = f"{CONFIG_SERVICE}/api/v1/feature-flags/evaluate"
    response = requests.post(eval_url, json={
        "flag_name": "new_asr_engine",
        "environment": "production",
        "user_id": user_id
    })
    return response.json().get("enabled", False)
```

### Example 3: Pipeline Service Integration

```python
# pipeline-service/main.py

def get_processing_config():
    """Get pipeline processing configuration"""
    configs = {}
    for key in ["pipeline.timeout", "pipeline.max_retries", "pipeline.queue_size"]:
        url = f"{CONFIG_SERVICE}/api/v1/config/{key}"
        params = {"environment": "production", "service_name": "pipeline-service"}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            configs[key] = response.json()["value"]
    return configs

# Use for dynamic service discovery
def get_next_service(service_type: str):
    """Find the next service in the pipeline"""
    healthy_url = f"{CONFIG_SERVICE}/api/v1/registry/healthy"
    response = requests.get(healthy_url)
    services = response.json().get("services", [])
    
    # Find service by type
    for service in services:
        if service_type in service.get("service_name", ""):
            return service.get("service_url")
    return None
```

## Configuration Management Workflow

### 1. Initial Setup

```bash
# 1. Create configuration via admin API
curl -X POST http://config-service:8082/api/v1/config/ \
  -H "Authorization: ApiKey admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "database.url",
    "value": "postgresql://db:5432/mydb",
    "environment": "production",
    "service_name": "user-service",
    "description": "Database connection URL"
  }'

# 2. Service fetches config at startup
# (See Pattern 3 above)
```

### 2. Runtime Updates

```bash
# Admin updates configuration
curl -X PUT http://config-service:8082/api/v1/config/{config_id} \
  -H "Authorization: ApiKey admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "value": "postgresql://new-db:5432/mydb"
  }'

# Service receives Kafka event
# (See Pattern 6 above)
# Service reloads configuration
```

### 3. Feature Rollout

```bash
# Create feature flag
curl -X POST http://config-service:8082/api/v1/feature-flags/ \
  -H "Authorization: ApiKey admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new_ui_design",
    "environment": "production",
    "is_enabled": true,
    "rollout_percentage": 10.0
  }'

# Gradually increase rollout
curl -X PUT http://config-service:8082/api/v1/feature-flags/{flag_id} \
  -H "Authorization: ApiKey admin-key" \
  -d '{"rollout_percentage": 50.0}'

# Services evaluate flag on each request
# (See Pattern 4 above)
```

## Best Practices

### 1. Configuration Management

✅ **DO:**
- Store all environment-specific configs in config service
- Use descriptive configuration keys
- Set up configuration templates for new services
- Use encryption for sensitive values (API keys, passwords)
- Document configuration purpose in description field

❌ **DON'T:**
- Hardcode configuration values in code
- Store sensitive data unencrypted
- Mix environment configs in same codebase
- Change configs without testing

### 2. Feature Flags

✅ **DO:**
- Use clear, descriptive flag names
- Start with low rollout percentage
- Monitor feature flag usage
- Clean up unused flags

❌ **DON'T:**
- Use flags for long-term A/B testing
- Create too many flags
- Forget to remove old flags

### 3. Service Discovery

✅ **DO:**
- Register services on startup
- Update health status regularly
- Use healthy services list for load balancing
- Deregister on shutdown

❌ **DON'T:**
- Rely on hardcoded service URLs
- Skip health check updates
- Ignore service status

### 4. Performance

✅ **DO:**
- Cache configurations locally with TTL
- Use startup configuration loading
- Implement retry logic for config fetches
- Monitor config service latency

❌ **DON'T:**
- Fetch configs on every request
- Block requests waiting for configs
- Ignore config service failures

## Error Handling

```python
def safe_get_config(key: str, default: str = None) -> str:
    """Safely get config with fallback"""
    try:
        value = get_config(key)
        return value if value else default
    except Exception as e:
        logger.warning(f"Config fetch failed for {key}: {e}")
        return default

# Usage with defaults
db_url = safe_get_config("database.url", "postgresql://localhost:5432/default")
max_retries = int(safe_get_config("retry.max", "3"))
```

## Monitoring and Observability

### Metrics to Track

1. **Config Fetch Latency**: Time to retrieve configurations
2. **Cache Hit Rate**: Percentage of configs served from cache
3. **Feature Flag Evaluation Count**: How often flags are checked
4. **Service Discovery Success Rate**: Successful service lookups
5. **Config Update Frequency**: How often configs change

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def get_config_with_logging(key: str):
    """Get config with logging"""
    logger.info(f"Fetching config: {key}")
    try:
        value = get_config(key)
        logger.debug(f"Config {key} retrieved successfully")
        return value
    except Exception as e:
        logger.error(f"Failed to fetch config {key}: {e}")
        raise
```

## Migration Guide

### Migrating from Hardcoded Configs

1. **Identify all hardcoded values** in your service
2. **Create configurations** in config service
3. **Update service code** to fetch from config service
4. **Test in development** environment first
5. **Deploy with fallback values** initially
6. **Remove hardcoded values** after validation

### Example Migration

```python
# BEFORE (Hardcoded)
DATABASE_URL = "postgresql://localhost:5432/mydb"
API_KEY = "hardcoded-key-123"

# AFTER (From Config Service)
DATABASE_URL = get_config("database.url", environment, service_name)
API_KEY = get_config("external.api_key", environment, service_name, is_encrypted=True)
```

## Troubleshooting Integration Issues

### Issue: Service can't connect to config service

**Solutions:**
- Check network connectivity
- Verify CONFIG_SERVICE_URL environment variable
- Check DNS resolution
- Verify firewall rules

### Issue: Config not found

**Solutions:**
- Verify configuration exists in config service
- Check environment and service_name parameters
- Review configuration key name
- Check permissions

### Issue: Stale configurations

**Solutions:**
- Reduce cache TTL
- Implement cache invalidation on updates
- Use event-driven updates (Kafka)
- Add cache versioning

## Summary

The Config Service is the **central nervous system** of your microservices architecture:

- **Configuration Hub**: All services get their settings from here
- **Feature Control**: Enable/disable features without deployments
- **Service Discovery**: Find and connect to other services
- **Environment Management**: Separate configs per environment
- **Dynamic Updates**: Change configs without restarting services

By following the integration patterns in this guide, your services will be:
- More flexible (configurable without redeployment)
- More resilient (service discovery)
- More controllable (feature flags)
- Easier to manage (centralized configs)

For API details, see [README.md](README.md).

