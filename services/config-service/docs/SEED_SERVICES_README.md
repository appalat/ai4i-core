# Service Registry Seeding

This script seeds the service registry with all AI4V-Core microservices.

## Usage

```bash
cd services/config-service
python3 seed_services.py
```

## What It Does

1. **Clears existing services** - Removes all currently registered services from the database
2. **Registers all AI4V-Core services** - Adds all 12 microservices with accurate metadata
3. **Verifies registration** - Lists all registered services to confirm success

## Registered Services

### Core Services
1. **api-gateway-service** (Port 8080) - Central entry point with routing, rate limiting, and authentication
2. **auth-service** (Port 8081) - Identity management with JWT and OAuth2
3. **config-service** (Port 8082) - Centralized configuration and feature flags
4. **metrics-service** (Port 8083) - System and application metrics collection
5. **telemetry-service** (Port 8084) - Log aggregation, distributed tracing, and event correlation
6. **alerting-service** (Port 8085) - Proactive issue detection and notification
7. **dashboard-service** (Port 8086) - Visualization and reporting with Streamlit UI

### AI/ML Services
8. **asr-service** (Port 8087) - Speech-to-Text with 22+ Indian languages
9. **tts-service** (Port 8088) - Text-to-Speech with multiple voice options
10. **nmt-service** (Port 8089) - Neural Machine Translation for Indian languages
11. **pipeline-service** (Port 8090) - Multi-task AI pipeline orchestration

### Frontend
12. **simple-ui-frontend** (Port 3000) - Web interface for testing AI services (Next.js)

## Service Metadata

Each service is registered with:
- `service_name` - Unique identifier
- `service_url` - Internal Docker network URL
- `health_check_url` - Health check endpoint
- `metadata` - Additional information:
  - `version` - Service version
  - `environment` - Deployment environment
  - `description` - Service description
  - `port` - Service port number
  - `type` - Service category (gateway, core, ai, frontend)
  - `capabilities` - Service-specific capabilities (for AI services)

## Viewing Registered Services

You can view all registered services via:

### API
```bash
# List all services
curl "http://localhost:8082/api/v1/registry/" \
  -H "Authorization: ApiKey admin"

# Get specific service
curl "http://localhost:8082/api/v1/registry/asr-service" \
  -H "Authorization: ApiKey admin"

# Get healthy services only
curl "http://localhost:8082/api/v1/registry/healthy" \
  -H "Authorization: ApiKey admin"
```

### Swagger UI
Visit http://localhost:8082/docs and navigate to the "service-registry" section.

## Updating Services

If you need to update a service's metadata, you can:

1. **Re-run the seed script** - It will clear and re-register everything
2. **Use the API directly** - Register services individually via the API
3. **Update via API** - Use PUT `/api/v1/registry/health` to update health status

## Troubleshooting

### Services not showing up
- Ensure the config-service is running: `curl http://localhost:8082/health`
- Check if authentication is required: `AUTH_ENABLED` environment variable
- Verify API key is correct: Default is `admin` for development

### Duplicate services
- The seed script clears existing services first
- If duplicates exist, delete them manually:
  ```bash
  curl -X DELETE "http://localhost:8082/api/v1/registry/{service_name}" \
    -H "Authorization: ApiKey admin"
  ```

### Health status showing as "unknown"
- Services start with "unknown" status when first registered
- To update health status automatically:
  ```bash
  # Check and update all services
  python3 update_service_health.py
  
  # Check a specific service
  python3 update_service_health.py asr-service
  
  # Run continuous health checks every 30 seconds
  python3 update_service_health.py --interval 30
  ```
- Or manually update via API:
  ```bash
  curl -X PUT "http://localhost:8082/api/v1/registry/health" \
    -H "Authorization: ApiKey admin" \
    -H "Content-Type: application/json" \
    -d '{
      "service_name": "asr-service",
      "status": "healthy",
      "response_time": 150.5
    }'
  ```

## Notes

- All services are registered with Docker internal network URLs (e.g., `http://service-name:port`)
- Health check URLs use the appropriate endpoint for each service type
- Metadata includes service descriptions and capabilities for better discovery
- Frontend service is included for completeness, though it may not have health endpoint

