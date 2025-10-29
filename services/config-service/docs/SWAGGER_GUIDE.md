# Config Service API - Swagger UI Guide

This guide explains how to access and use the Config Service APIs through the interactive Swagger UI.

## 📍 Accessing Swagger UI

### Direct Access (Config Service)

When running locally or in development:

- **Swagger UI**: http://localhost:8082/docs
- **ReDoc**: http://localhost:8082/redoc
- **OpenAPI JSON**: http://localhost:8082/openapi.json

### Through API Gateway

If accessing through the API Gateway:

- **Swagger UI**: http://localhost:8080/docs
- **OpenAPI JSON**: http://localhost:8080/openapi.json

> **Note**: The API Gateway aggregates docs from all services, but for best experience, access the Config Service directly at port 8082.

## 🚀 Quick Start

### 1. Start the Service

```bash
# Using Docker Compose
docker-compose up config-service

# Or directly
cd services/config-service
python main.py
```

### 2. Open Swagger UI

1. Open your browser and navigate to: **http://localhost:8082/docs**
2. You'll see all available API endpoints organized by tags:
   - **configurations**: Configuration management
   - **feature-flags**: Feature flag management
   - **service-registry**: Service discovery
   - **Health**: Health checks

### 3. Using Swagger UI

#### Authentication Setup

Most endpoints require authentication. To use them in Swagger UI:

1. Look for the **"Authorize"** button at the top right of the Swagger UI
2. Click it and enter your API key in one of these formats:
   - `ApiKey your-api-key-here`
   - `Bearer your-api-key-here`
3. Click **"Authorize"** then **"Close"**

> **Note**: For development/testing, you may need to disable authentication or use a test API key. Check your `.env` file for `AUTH_ENABLED` and `REQUIRE_API_KEY` settings.

## 📋 API Endpoints Overview

### Configuration Management (`/api/v1/config`)

#### Create Configuration
```
POST /api/v1/config/
```
Creates a new configuration entry for a service/environment combination.

**Example Request**:
```json
{
  "key": "database.url",
  "value": "postgresql://localhost:5432/mydb",
  "environment": "production",
  "service_name": "user-service",
  "description": "Database connection URL",
  "is_encrypted": false
}
```

#### Get Configuration
```
GET /api/v1/config/{key}
```
Retrieves a configuration by key. Requires `environment` and `service_name` query parameters.

**Parameters**:
- `key` (path): Configuration key
- `environment` (query): Environment name (e.g., "production", "staging")
- `service_name` (query): Service name (e.g., "user-service")

#### List Configurations
```
GET /api/v1/config/
```
Lists all configurations with optional filtering.

**Query Parameters**:
- `key_pattern` (optional): Pattern to match configuration keys
- `environment` (optional): Filter by environment
- `service_name` (optional): Filter by service name
- `limit` (default: 100): Maximum results
- `offset` (default: 0): Pagination offset

#### Update Configuration
```
PUT /api/v1/config/{config_id}
```
Updates an existing configuration.

**Example Request**:
```json
{
  "value": "postgresql://new-host:5432/mydb",
  "description": "Updated database URL"
}
```

#### Delete Configuration
```
DELETE /api/v1/config/{config_id}
```
Deletes a configuration entry.

#### Get Configuration History
```
GET /api/v1/config/{config_id}/history
```
Retrieves the change history for a configuration.

### Feature Flags (`/api/v1/feature-flags`)

#### Create Feature Flag
```
POST /api/v1/feature-flags/
```
Creates a new feature flag.

**Example Request**:
```json
{
  "name": "new_checkout_flow",
  "description": "Enable new checkout UI",
  "is_enabled": true,
  "rollout_percentage": 50.0,
  "target_users": ["user123", "user456"],
  "environment": "production"
}
```

#### Get Feature Flag
```
GET /api/v1/feature-flags/{name}
```
Gets a feature flag by name. Requires `environment` query parameter.

#### List Feature Flags
```
GET /api/v1/feature-flags/
```
Lists all feature flags with optional filtering.

**Query Parameters**:
- `environment` (optional): Filter by environment
- `limit` (default: 100): Maximum results
- `offset` (default: 0): Pagination offset

#### Evaluate Feature Flag
```
POST /api/v1/feature-flags/evaluate
```
Evaluates whether a feature flag is enabled for a user.

**Example Request**:
```json
{
  "flag_name": "new_checkout_flow",
  "environment": "production",
  "user_id": "user123"
}
```

**Response**:
```json
{
  "enabled": true,
  "reason": "user_targeted",
  "flag_name": "new_checkout_flow",
  "environment": "production"
}
```

#### Update Feature Flag
```
PUT /api/v1/feature-flags/{flag_id}
```
Updates a feature flag.

#### Delete Feature Flag
```
DELETE /api/v1/feature-flags/{flag_id}
```
Deletes a feature flag.

### Service Registry (`/api/v1/registry`)

#### Register Service
```
POST /api/v1/registry/register
```
Registers a new service or updates an existing one.

**Example Request**:
```json
{
  "service_name": "user-service",
  "service_url": "http://user-service:8080",
  "health_check_url": "http://user-service:8080/health",
  "metadata": {
    "version": "1.0.0",
    "region": "us-east-1"
  }
}
```

#### Get Service
```
GET /api/v1/registry/{service_name}
```
Gets service information by name.

#### List Services
```
GET /api/v1/registry/
```
Lists all registered services.

**Query Parameters**:
- `status` (optional): Filter by health status ("healthy", "unhealthy", "unknown")

#### Get Healthy Services
```
GET /api/v1/registry/healthy
```
Gets all healthy services for service discovery.

#### Update Service Health
```
PUT /api/v1/registry/health
```
Updates service health status.

**Example Request**:
```json
{
  "service_name": "user-service",
  "status": "healthy",
  "response_time": 150.5
}
```

#### Deregister Service
```
DELETE /api/v1/registry/{service_name}
```
Deregisters a service from the registry.

## 🧪 Interactive Testing with Swagger UI

### Step-by-Step Example: Creating a Configuration

1. **Open Swagger UI**: Navigate to http://localhost:8082/docs

2. **Authorize** (if required):
   - Click "Authorize" button
   - Enter your API key: `ApiKey your-api-key`
   - Click "Authorize"

3. **Find the Endpoint**:
   - Expand the **"configurations"** section
   - Click on `POST /api/v1/config/`

4. **Fill in the Request**:
   - Click "Try it out"
   - Fill in the request body:
     ```json
     {
       "key": "app.max_users",
       "value": "1000",
       "environment": "production",
       "service_name": "my-service",
       "description": "Maximum number of users",
       "is_encrypted": false
     }
     ```

5. **Execute**:
   - Click "Execute"
   - View the response below

6. **Use the Response**:
   - Copy the `config_id` from the response
   - Use it for update/delete operations

### Testing Feature Flag Evaluation

1. Navigate to **feature-flags** section
2. Find `POST /api/v1/feature-flags/evaluate`
3. Click "Try it out"
4. Enter request:
   ```json
   {
     "flag_name": "new_checkout_flow",
     "environment": "production",
     "user_id": "test_user_123"
   }
   ```
5. Click "Execute" to see if the flag is enabled for that user

## 🔧 Implementation Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8082/api/v1"
API_KEY = "your-api-key"

headers = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json"
}

# Create configuration
config_data = {
    "key": "database.url",
    "value": "postgresql://localhost:5432/mydb",
    "environment": "production",
    "service_name": "user-service",
    "description": "Database connection URL",
    "is_encrypted": False
}

response = requests.post(
    f"{BASE_URL}/config/",
    headers=headers,
    json=config_data
)
print(response.json())

# Get configuration
response = requests.get(
    f"{BASE_URL}/config/database.url",
    params={
        "environment": "production",
        "service_name": "user-service"
    }
)
print(response.json())
```

### cURL Examples

```bash
# Create configuration
curl -X POST "http://localhost:8082/api/v1/config/" \
  -H "Authorization: ApiKey your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "database.url",
    "value": "postgresql://localhost:5432/mydb",
    "environment": "production",
    "service_name": "user-service",
    "description": "Database connection URL",
    "is_encrypted": false
  }'

# Get configuration
curl "http://localhost:8082/api/v1/config/database.url?environment=production&service_name=user-service"

# Evaluate feature flag
curl -X POST "http://localhost:8082/api/v1/feature-flags/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "flag_name": "new_checkout_flow",
    "environment": "production",
    "user_id": "user123"
  }'
```

### JavaScript/TypeScript Client

```typescript
const BASE_URL = "http://localhost:8082/api/v1";
const API_KEY = "your-api-key";

async function createConfiguration() {
  const response = await fetch(`${BASE_URL}/config/`, {
    method: "POST",
    headers: {
      "Authorization": `ApiKey ${API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      key: "database.url",
      value: "postgresql://localhost:5432/mydb",
      environment: "production",
      service_name: "user-service",
      description: "Database connection URL",
      is_encrypted: false
    })
  });
  
  return await response.json();
}

async function evaluateFeatureFlag(flagName: string, environment: string, userId: string) {
  const response = await fetch(`${BASE_URL}/feature-flags/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      flag_name: flagName,
      environment: environment,
      user_id: userId
    })
  });
  
  return await response.json();
}
```

## 🔐 Authentication

### API Key Format

The service accepts API keys in two formats:

1. **ApiKey format**:
   ```
   Authorization: ApiKey your-api-key-here
   ```

2. **Bearer format** (also supported):
   ```
   Authorization: Bearer your-api-key-here
   ```

### Getting an API Key

API keys are typically managed by the auth service. Check your authentication setup or contact your administrator.

### Disabling Authentication (Development Only)

For local development, you can disable authentication:

```bash
# In your .env file
AUTH_ENABLED=false
REQUIRE_API_KEY=false
ALLOW_ANONYMOUS_ACCESS=true
```

**⚠️ Warning**: Never disable authentication in production!

## 🌐 Accessing Through API Gateway

The Config Service is also accessible through the API Gateway at port 8080:

```
http://localhost:8080/api/v1/config/...
http://localhost:8080/api/v1/feature-flags/...
http://localhost:8080/api/v1/registry/...
```

The API Gateway proxies requests to the Config Service, so all endpoints work the same way.

## 📊 Response Formats

### Success Response

```json
{
  "id": 1,
  "key": "database.url",
  "value": "postgresql://localhost:5432/mydb",
  "environment": "production",
  "service_name": "user-service",
  "description": "Database connection URL",
  "is_encrypted": false,
  "version": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Error Response

```json
{
  "detail": "Configuration not found"
}
```

## 🐛 Troubleshooting

### Swagger UI Not Loading

1. **Check service is running**:
   ```bash
   curl http://localhost:8082/health
   ```

2. **Check port is accessible**:
   ```bash
   netstat -tuln | grep 8082
   ```

3. **Check firewall settings** if accessing remotely

### Authentication Errors

1. **Verify API key format**: Must be `ApiKey <key>` or `Bearer <key>`
2. **Check authentication settings** in `.env` file
3. **Verify API key is valid** with auth service

### CORS Issues

If accessing from a browser, ensure CORS is configured:

```python
# Already configured in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📚 Additional Resources

- [Full API Documentation](README.md)
- [Integration Guide](INTEGRATION_GUIDE.md)
- [Quick Start Guide](QUICK_START.md)
- [Test Results](TEST_RESULTS.md)
- [Service Registry Seeding](SEED_SERVICES_README.md)
- [OpenAPI Specification](http://localhost:8082/openapi.json)

## 🔗 Related Services

- **Auth Service**: Port 8081 - Manages API keys and authentication
- **Metrics Service**: Port 8083 - Collects service metrics
- **Telemetry Service**: Port 8084 - Handles telemetry data
- **API Gateway**: Port 8080 - Routes requests to all services

---

**Need Help?** Open an issue or check the [Troubleshooting Guide](../../docs/TROUBLESHOOTING.md)

