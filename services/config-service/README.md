# Configuration Management Service

A comprehensive microservice for centralized configuration management, feature flags, and service discovery with support for multi-environment deployments, caching, encryption, and event streaming.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
  - [Configurations](#configurations)
  - [Feature Flags](#feature-flags)
  - [Service Registry](#service-registry)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [Caching](#caching)
- [Event Publishing](#event-publishing)
- [Security](#security)
- [Usage Examples](#usage-examples)
- [Development Setup](#development-setup)
- [Environment Variables](#environment-variables)

## Overview

The Configuration Management Service provides a centralized solution for managing application configurations, feature flags, and service discovery across different environments (development, staging, production). It supports:

- **Environment-specific configurations** with versioning and history
- **Feature flag management** with rollout percentages and user targeting
- **Service discovery** with health status tracking
- **Redis caching** for improved performance
- **Kafka event streaming** for configuration changes
- **Encryption** for sensitive configuration values
- **Authentication & authorization** for admin operations

## Features

### Core Capabilities

1. **Configuration Management**
   - Create, read, update, delete configurations
   - Environment and service-specific configurations
   - Version tracking and audit history
   - Optional encryption for sensitive values
   - Description field for documentation

2. **Feature Flags**
   - Global enable/disable flags
   - Gradual rollout with percentage-based targeting
   - User-specific targeting
   - Multi-environment support
   - Real-time evaluation

3. **Service Registry**
   - Service registration and discovery
   - Health status tracking
   - Response time monitoring
   - Metadata management
   - Redis-backed service instances

### Advanced Features

- **Redis Caching**: Configurable TTL for fast read operations
- **Event Streaming**: Kafka integration for change notifications
- **Authentication**: API key-based authentication with role-based access
- **Encryption**: Optional Fernet encryption for sensitive data
- **SQLAlchemy 2.0**: Modern ORM with async database operations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Config Service                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Config     │  │  Feature     │  │   Service    │     │
│  │   Router     │  │  Flag Router │  │  Registry    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │             │
│         └─────────────────┼──────────────────┘             │
│                           │                                │
│         ┌─────────────────┴──────────────────┐            │
│         │      Business Logic Layer           │            │
│         │  (Services + Repositories)          │            │
│         └─────────────────┬──────────────────┘            │
│                           │                                │
│         ┌─────────────────┼──────────────────┐            │
│         │                  │                  │            │
│    ┌────┴─────┐    ┌──────┴───────┐   ┌─────┴──────┐    │
│    │ PostgreSQL │   │    Redis     │   │   Kafka    │    │
│    │   Config   │   │   Caching    │   │   Events   │    │
│    │    DB     │   │              │   │            │    │
│    └───────────┘   └──────────────┘   └────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Layers

1. **API Layer**: FastAPI routers with authentication middleware
2. **Business Logic**: Services handle caching, encryption, and event publishing
3. **Data Access**: Repositories for database operations
4. **Storage**: PostgreSQL for persistence, Redis for caching, Kafka for events

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Base URL
```
http://localhost:8082/api/v1
```

### Configurations

**Prefix**: `/config`

#### Create Configuration
```http
POST /api/v1/config/
Authorization: ApiKey <api_key>

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
```http
GET /api/v1/config/{key}?environment={env}&service_name={service}
```

#### List Configurations
```http
GET /api/v1/config/?environment=production&limit=100&offset=0
```

#### Update Configuration
```http
PUT /api/v1/config/{config_id}
Authorization: ApiKey <api_key>

{
  "value": "postgresql://new-host:5432/mydb",
  "description": "Updated database URL"
}
```

#### Delete Configuration
```http
DELETE /api/v1/config/{config_id}
Authorization: ApiKey <api_key>
```

#### Get Configuration History
```http
GET /api/v1/config/{config_id}/history
```

### Feature Flags

**Prefix**: `/feature-flags`

#### Create Feature Flag
```http
POST /api/v1/feature-flags/
Authorization: ApiKey <api_key>

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
```http
GET /api/v1/feature-flags/{name}?environment={env}
```

#### List Feature Flags
```http
GET /api/v1/feature-flags/?environment=production&limit=100&offset=0
```

#### Evaluate Feature Flag
```http
POST /api/v1/feature-flags/evaluate

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
```http
PUT /api/v1/feature-flags/{flag_id}
Authorization: ApiKey <api_key>

{
  "is_enabled": true,
  "rollout_percentage": 75.0
}
```

#### Delete Feature Flag
```http
DELETE /api/v1/feature-flags/{flag_id}
Authorization: ApiKey <api_key>
```

### Service Registry

**Prefix**: `/registry` (also available at `/services` for compatibility)

#### Register Service
```http
POST /api/v1/registry/register
Authorization: ApiKey <api_key>

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
```http
GET /api/v1/registry/{service_name}
```

#### List Services
```http
GET /api/v1/registry/?status=healthy
```

#### Get Healthy Services
```http
GET /api/v1/registry/healthy
```

#### Update Service Health
```http
PUT /api/v1/registry/health
Authorization: ApiKey <api_key>

{
  "service_name": "user-service",
  "status": "healthy",
  "response_time": 150.5
}
```

#### Deregister Service
```http
DELETE /api/v1/registry/{service_name}
Authorization: ApiKey <api_key>
```

## Configuration

### Environment Variables

See `env.template` for all available configuration options.

#### Database Configuration
```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/config_db
```

#### Redis Configuration
```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_secure_password_2024
```

#### Kafka Configuration
```bash
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_CONFIG_UPDATES=config-updates
KAFKA_TOPIC_FEATURE_FLAG_UPDATES=feature-flag-updates
KAFKA_TOPIC_SERVICE_REGISTRY_UPDATES=service-registry-updates
```

#### Cache Configuration
```bash
CONFIG_CACHE_TTL=300           # Config cache TTL in seconds
FEATURE_FLAG_CACHE_TTL=300     # Feature flag cache TTL
SERVICE_REGISTRY_TTL=300       # Service registry cache TTL
```

#### Security Configuration
```bash
AUTH_ENABLED=true              # Enable authentication
REQUIRE_API_KEY=true           # Require API key for all requests
ALLOW_ANONYMOUS_ACCESS=false   # Allow unauthenticated access

ENCRYPTION_KEY=your-key-here   # Base64-encoded Fernet key
ENABLE_ENCRYPTION=true          # Enable encryption for sensitive values
```

## Database Schema

### Tables

#### configurations
Stores application configurations with versioning.

```sql
CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    environment VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(key, environment, service_name)
);
```

#### feature_flags
Stores feature flag definitions.

```sql
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT false,
    rollout_percentage DECIMAL(5,2) DEFAULT 0.00,
    target_users TEXT[],
    environment VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### service_registry
Stores registered services with health status.

```sql
CREATE TABLE service_registry (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) UNIQUE NOT NULL,
    service_url VARCHAR(255) NOT NULL,
    health_check_url VARCHAR(255),
    status VARCHAR(20) DEFAULT 'unknown',
    last_health_check TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### configuration_history
Audit trail for configuration changes.

```sql
CREATE TABLE configuration_history (
    id SERIAL PRIMARY KEY,
    configuration_id INTEGER REFERENCES configurations(id) ON DELETE CASCADE,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Caching

### Cache Strategy

The service uses Redis for caching to improve read performance:

- **Configuration cache**: `config:{environment}:{service_name}:{key}`
- **Feature flag cache**: `feature_flag:{name}:{environment}`
- **Service info cache**: `service_info:{service_name}`
- **Healthy services cache**: `healthy_services`

### Cache Invalidation

- Configurations: Invalidated on create, update, delete
- Feature flags: Invalidated on update, delete
- Service registry: Invalidated on health updates, deregistration

### Cache TTL

Default TTL is 300 seconds (5 minutes) for all caches, configurable via environment variables.

## Event Publishing

### Event Types

Configuration changes, feature flag updates, and service registry changes are published to Kafka topics:

- `config-updates`: Configuration create/update/delete events
- `feature-flag-updates`: Feature flag updates
- `service-registry-updates`: Service registration and health updates

### Event Format

```json
{
  "action": "create|update|delete",
  "resource_type": "configuration|feature_flag|service",
  "resource_id": "resource-identifier",
  "data": {
    "key": "config-key",
    "environment": "production",
    "service_name": "user-service"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "environment": "production"
}
```

## Security

### Authentication

Authentication is implemented via API key validation:

```http
Authorization: ApiKey your-api-key
```

Or:

```http
Authorization: Bearer your-api-key
```

### Authorization

- **Read operations**: Public or optional auth
- **Mutation operations**: Require admin permissions
  - POST, PUT, DELETE endpoints are protected
  - Admin check is based on API key validation

### Encryption

Sensitive configuration values can be encrypted using Fernet encryption:

1. Set `ENABLE_ENCRYPTION=true`
2. Configure `ENCRYPTION_KEY` (base64-encoded 32-byte key)
3. Mark configuration as encrypted when creating

**Generate encryption key**:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Use this as ENCRYPTION_KEY
```

### Value Redaction

Encrypted values and sensitive data are automatically redacted in:
- Logs
- Event publications
- Error messages

## Usage Examples

### Python Client Example

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

response = requests.post(f"{BASE_URL}/config/", headers=headers, json=config_data)
print(response.json())

# Get configuration
response = requests.get(
    f"{BASE_URL}/config/database.url",
    params={"environment": "production", "service_name": "user-service"}
)
print(response.json())

# Evaluate feature flag
eval_data = {
    "flag_name": "new_checkout_flow",
    "environment": "production",
    "user_id": "user123"
}
response = requests.post(f"{BASE_URL}/feature-flags/evaluate", json=eval_data)
print(response.json())
```

### Feature Flag Evaluation

Feature flags support multiple evaluation strategies:

1. **Global enable/disable**: All users see the same state
2. **Rollout percentage**: Users are randomly assigned based on hash
3. **Target users**: Specific users always see enabled flag

### Service Discovery

```python
# Register service
registry_data = {
    "service_name": "user-service",
    "service_url": "http://user-service:8080",
    "health_check_url": "http://user-service:8080/health"
}

response = requests.post(f"{BASE_URL}/registry/register", headers=headers, json=registry_data)

# Discover healthy services
response = requests.get(f"{BASE_URL}/registry/healthy")
services = response.json()
print(f"Found {services['total']} healthy services")
```

## Development Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Kafka (for event streaming)

### Installation

```bash
cd services/config-service
pip install -r requirements.txt
```

### Database Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE config_db;

# Run schema
\i infrastructure/postgres/02-config-schema.sql

# Seed data (optional)
\i infrastructure/postgres/07-seed-data.sql
```

### Environment Setup

```bash
cp env.template .env
# Edit .env with your configuration
```

### Running the Service

```bash
# Development
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8082 --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8082 --workers 4
```

### Docker Setup

```bash
# Build and run
docker-compose up config-service

# Or from project root
docker-compose up
```

## Environment Variables

Complete list of environment variables:

### Service Configuration
- `SERVICE_NAME`: Service identifier (default: config-service)
- `SERVICE_PORT`: Service port (default: 8082)
- `LOG_LEVEL`: Logging level (default: INFO)

### Database
- `DATABASE_URL`: PostgreSQL connection string

### Redis
- `REDIS_HOST`: Redis host (default: redis)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_PASSWORD`: Redis password

### Kafka
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka bootstrap servers
- `KAFKA_TOPIC_CONFIG_UPDATES`: Config updates topic
- `KAFKA_TOPIC_FEATURE_FLAG_UPDATES`: Feature flag updates topic
- `KAFKA_TOPIC_SERVICE_REGISTRY_UPDATES`: Service registry updates topic

### Security
- `AUTH_ENABLED`: Enable authentication (default: true)
- `REQUIRE_API_KEY`: Require API key (default: true)
- `ALLOW_ANONYMOUS_ACCESS`: Allow anonymous access (default: false)
- `ENCRYPTION_KEY`: Encryption key (base64)
- `ENABLE_ENCRYPTION`: Enable encryption (default: false)

### Cache
- `CONFIG_CACHE_TTL`: Config cache TTL in seconds (default: 300)
- `FEATURE_FLAG_CACHE_TTL`: Feature flag cache TTL (default: 300)
- `SERVICE_REGISTRY_TTL`: Service registry cache TTL (default: 300)

## Architecture Decisions

### Why PostgreSQL?
- ACID compliance for data consistency
- JSONB support for flexible metadata
- Strong ecosystem and tooling

### Why Redis?
- In-memory performance for caching
- Pub/sub support for future features
- Already in infrastructure

### Why Kafka?
- Decoupled event streaming
- Scalable for high-throughput
- Integration with other services

### Why Optional Encryption?
- Security for sensitive values (API keys, passwords)
- Flexibility for non-sensitive data
- Performance impact only when enabled

## Troubleshooting

### Common Issues

**Cache not invalidating**
- Check Redis connectivity
- Verify cache keys match pattern
- Check TTL values

**Decryption fails**
- Verify ENCRYPTION_KEY is set
- Check key format (base64-encoded)
- Ensure ENABLE_ENCRYPTION=true

**Authentication errors**
- Verify API key format in Authorization header
- Check AUTH_ENABLED and REQUIRE_API_KEY settings
- Review logs for validation errors

**Event publishing fails**
- Check Kafka connectivity
- Verify topic names match configuration
- Review Kafka producer logs

## Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8082/health

# Get configurations
curl "http://localhost:8082/api/v1/config/?environment=production"
```

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

## License

See [LICENSE](../../LICENSE) for license information.

## Related Documentation

- [API Documentation](docs/API_DOCUMENTATION.md)
- [Architecture Overview](../../docs/ARCHITECTURE.md)
- [Deployment Guide](../../docs/DEPLOYMENT.md)
- [Troubleshooting Guide](../../docs/TROUBLESHOOTING.md)

