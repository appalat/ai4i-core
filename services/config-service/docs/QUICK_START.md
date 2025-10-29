# Config Service - Quick Start Guide

## What is This Service?

The **Config Service** is a **three-in-one** centralized service for:
1. **Configuration Management** - Store and manage all your service settings
2. **Feature Flags** - Control features dynamically without deployment
3. **Service Discovery** - Find and connect to healthy services automatically

## The Problems It Solves

### Problem 1: Configuration Management

### ❌ Without Config Service:
```python
# In user-service/main.py
DATABASE_URL = "postgresql://localhost:5432/mydb"  # Hardcoded!
API_KEY = "secret-key-123"  # Hardcoded!
MAX_RETRIES = 3  # Hardcoded!

# Problem: Need to redeploy when settings change!
```

### ✅ With Config Service:
```python
# In user-service/main.py
from config_client import get_config

DATABASE_URL = get_config("database.url", "production", "user-service")
API_KEY = get_config("api.key", "production", "user-service")
MAX_RETRIES = int(get_config("retry.max", "production", "user-service"))

# Solution: Change configs without redeploying!
```

### Problem 2: Feature Flag Management

### ❌ Without Config Service:
```python
# In payment-service/main.py
NEW_CHECKOUT_ENABLED = False  # Hardcoded!

if NEW_CHECKOUT_ENABLED:  # Must redeploy to enable!
    use_new_checkout()
else:
    use_old_checkout()
```

### ✅ With Config Service:
```python
# In payment-service/main.py
if is_feature_enabled("new_checkout", user_id):
    use_new_checkout()  # Can enable/disable instantly!
else:
    use_old_checkout()
```

### Problem 3: Service Discovery

### ❌ Without Config Service:
```python
# In order-service/main.py
PAYMENT_SERVICE_URL = "http://payment-service:8080"  # Hardcoded!
USER_SERVICE_URL = "http://user-service:8080"  # Hardcoded!

# Problem: If service moves or fails, must update code!
```

### ✅ With Config Service:
```python
# In order-service/main.py
payment_url = discover_service("payment-service")  # Finds healthy instance!
user_url = discover_service("user-service")  # Automatically updated!

# Solution: Always connects to healthy services!
```

## Three Main Features

### 1. 📝 Configuration Storage
**Store all your settings in one place:**
- Database URLs
- API keys (encrypted)
- Timeout values
- Retry settings
- Any configurable value

**Benefits:**
- Change configs without code changes
- Different configs per environment (dev/staging/prod)
- Track who changed what and when

### 2. 🚩 Feature Flags
**Control features dynamically:**
- Enable/disable features without deployment
- Gradual rollouts (10% → 50% → 100%)
- Target specific users
- Test features safely

**Example:**
```python
if is_feature_enabled("new_payment_flow", user_id):
    use_new_payment()
else:
    use_old_payment()
```

### 3. 🔍 Service Discovery
**Find and connect to other services:**
- Register your service automatically
- Discover healthy services
- Get service URLs dynamically
- Track service health

**Example:**
```python
user_service_url = discover_service("user-service")
response = requests.get(f"{user_service_url}/api/users")
```

## How Other Services Use It

### Step 1: Store Your Configurations

```bash
# Admin creates configuration
curl -X POST http://config-service:8082/api/v1/config/ \
  -H "Authorization: ApiKey admin-key" \
  -d '{
    "key": "database.url",
    "value": "postgresql://db:5432/mydb",
    "environment": "production",
    "service_name": "user-service"
  }'
```

### Step 2: Your Service Fetches Config

```python
# In your service startup
import requests

CONFIG_SERVICE = "http://config-service:8082"

@app.on_event("startup")
async def load_configs():
    # Fetch database URL
    response = requests.get(
        f"{CONFIG_SERVICE}/api/v1/config/database.url",
        params={
            "environment": "production",
            "service_name": "user-service"
        }
    )
    db_url = response.json()["value"]
    # Use db_url for database connection
```

### Step 3: Use Feature Flags

```python
# Check if feature is enabled
response = requests.post(
    f"{CONFIG_SERVICE}/api/v1/feature-flags/evaluate",
    json={
        "flag_name": "new_ui",
        "environment": "production",
        "user_id": user.id
    }
)
enabled = response.json()["enabled"]

if enabled:
    # Show new UI
    return new_ui_response()
```

### Step 4: Register Your Service

```python
@app.on_event("startup")
async def register_service():
    requests.post(
        f"{CONFIG_SERVICE}/api/v1/registry/register",
        headers={"Authorization": "ApiKey your-key"},
        json={
            "service_name": "user-service",
            "service_url": "http://user-service:8080",
            "health_check_url": "http://user-service:8080/health"
        }
    )
```

## Common Use Cases

### Configuration Management Use Cases

**Use Case 1: Database Connection**
```python
# Get database URL from config service
db_url = get_config("database.url", "production", "user-service")
engine = create_engine(db_url)
```

**Use Case 2: External API Integration**
```python
# Get external API key (encrypted)
api_key = get_config("external.api_key", "production", "user-service")
headers = {"Authorization": f"Bearer {api_key}"}
```

**Use Case 3: Environment-Specific Settings**
```python
# Different values per environment automatically
timeout = int(get_config("request.timeout", "production", "user-service"))
max_retries = int(get_config("retry.max", "production", "user-service"))
```

### Feature Flag Use Cases

**Use Case 4: Gradual Feature Rollout**
```python
# Roll out new feature to 10% of users, then increase
if is_feature_enabled("new_payment_ui", user.id):
    render_new_ui()
else:
    render_old_ui()
```

**Use Case 5: A/B Testing**
```python
# Test new algorithm for some users
if is_feature_enabled("new_search_algorithm", user.id):
    results = new_algorithm(query)
else:
    results = old_algorithm(query)
```

**Use Case 6: Emergency Feature Disable**
```python
# Quickly disable problematic feature without deployment
if is_feature_enabled("experimental_feature", user.id):
    # Use experimental code
    pass
else:
    # Use stable code
    pass
```

### Service Discovery Use Cases

**Use Case 7: Service-to-Service Communication**
```python
# Discover where the payment service is (no hardcoded URLs!)
payment_url = discover_service("payment-service")
response = requests.post(f"{payment_url}/api/charge", json=charge_data)
```

**Use Case 8: Load Balancing**
```python
# Get all healthy instances of a service
healthy_services = get_all_healthy_services()
for service in healthy_services:
    if service["service_name"] == "user-service":
        # Distribute load across instances
        process_request(service["service_url"])
```

**Use Case 9: Health-Aware Routing**
```python
# Always route to healthy services
user_service = discover_service("user-service")
if user_service and is_service_healthy(user_service):
    response = requests.get(f"{user_service}/api/users")
else:
    # Fallback or retry logic
    handle_service_unavailable()
```

## Real Example: Complete Integration

Here's how a service uses **all three features** together:

```python
# user-service/main.py
from fastapi import FastAPI
import requests
import os

app = FastAPI()
CONFIG_URL = os.getenv("CONFIG_SERVICE_URL", "http://config-service:8082")

@app.on_event("startup")
async def startup():
    env = os.getenv("ENVIRONMENT", "production")
    service = "user-service"
    
    # 1. CONFIGURATION MANAGEMENT: Load all configs
    response = requests.get(
        f"{CONFIG_URL}/api/v1/config/service/{service}",
        params={"environment": env}
    )
    
    configs = {}
    for cfg in response.json():
        configs[cfg["key"]] = cfg["value"]
    
    app.state.configs = configs
    print(f"✅ Loaded {len(configs)} configurations")
    
    # 2. SERVICE DISCOVERY: Register this service
    requests.post(
        f"{CONFIG_URL}/api/v1/registry/register",
        headers={"Authorization": f"ApiKey {os.getenv('CONFIG_SERVICE_API_KEY')}"},
        json={
            "service_name": service,
            "service_url": f"http://{service}:8080",
            "health_check_url": f"http://{service}:8080/health",
            "metadata": {"version": "1.0.0"}
        }
    )
    print(f"✅ Registered service: {service}")

# Use configurations
@app.get("/users")
async def get_users():
    # Use database URL from config service
    db_url = app.state.configs["database.url"]
    # ... query database with db_url
    return users

@app.post("/users")
async def create_user(user_data: dict, user_id: str):
    # 3. FEATURE FLAGS: Check if auto-verify is enabled for this user
    flag_resp = requests.post(
        f"{CONFIG_URL}/api/v1/feature-flags/evaluate",
        json={
            "flag_name": "auto_verify_email",
            "environment": os.getenv("ENVIRONMENT"),
            "user_id": user_id
        }
    )
    
    auto_verify = flag_resp.json()["enabled"]
    
    if auto_verify:
        # Auto-verify email (new feature)
        send_verification_email(user_data["email"])
    else:
        # Manual verification (old feature)
        pass
    
    return created_user

@app.get("/users/{user_id}/orders")
async def get_user_orders(user_id: str):
    # 3. SERVICE DISCOVERY: Find order service dynamically
    order_service = requests.get(
        f"{CONFIG_URL}/api/v1/registry/order-service"
    ).json()
    
    if order_service["status"] == "healthy":
        orders_url = order_service["service_url"]
        orders = requests.get(f"{orders_url}/api/orders?user_id={user_id}")
        return orders.json()
    else:
        return {"error": "Order service unavailable"}
```

**What this example shows:**
- ✅ **Configuration Management**: Loads database URL and other settings at startup
- ✅ **Feature Flags**: Checks if auto-verify email feature is enabled per user
- ✅ **Service Discovery**: Registers itself and discovers other services dynamically

## Environment Variables Needed

Add to your service's environment:

```bash
# Required
CONFIG_SERVICE_URL=http://config-service:8082
ENVIRONMENT=production  # or development, staging
SERVICE_NAME=user-service  # your service name

# Optional (for admin operations)
CONFIG_SERVICE_API_KEY=your-admin-api-key
```

## Quick Checklist for Integration

### Configuration Management
- [ ] Configure `CONFIG_SERVICE_URL` environment variable
- [ ] Set `ENVIRONMENT` and `SERVICE_NAME`
- [ ] Create configurations in config service for your service
- [ ] Update service code to fetch configs instead of hardcoding
- [ ] Add error handling for config fetch failures with fallback values

### Feature Flags (if needed)
- [ ] Create feature flags in config service for features you want to control
- [ ] Update service code to check feature flags before using new features
- [ ] Test feature flag evaluation logic

### Service Discovery (if needed)
- [ ] Register service on startup using registry API
- [ ] Update health status periodically (every 30-60 seconds)
- [ ] Use service discovery to find other services instead of hardcoding URLs

### Testing & Deployment
- [ ] Test in development environment first
- [ ] Verify all three features work correctly
- [ ] Monitor config service connectivity
- [ ] Implement retry logic for config service failures

## Need More Details?

- **Full Integration Guide**: See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Swagger UI Guide**: See [SWAGGER_GUIDE.md](SWAGGER_GUIDE.md)
- **Service Registry**: See [SEED_SERVICES_README.md](SEED_SERVICES_README.md)
- **API Documentation**: See [README.md](README.md)
- **Example Code**: Check integration patterns in [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

## Common Questions

**Q: Do I have to use this service?**  
A: No, but it makes configuration management much easier in microservices.

**Q: What if config service is down?**  
A: Implement caching and fallback values. Never block on config fetches.

**Q: Can I store secrets here?**  
A: Yes! Enable encryption (`ENABLE_ENCRYPTION=true`) and mark configs as encrypted.

**Q: How do I update configs?**  
A: Use the admin API or dashboard. Changes are immediately available.

**Q: How do services know when configs change?**  
A: Config service publishes Kafka events. Services can listen and reload.

**Q: Is this like Kubernetes ConfigMaps?**  
A: Similar concept, but more flexible with versioning, history, and multi-environment support.

