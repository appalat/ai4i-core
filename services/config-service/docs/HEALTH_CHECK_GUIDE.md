# Service Registry Health Check Guide

## Overview

Services in the registry start with "unknown" status. This guide explains how to update their health status.

## Automatic Health Checking

### Using the Health Check Script

The `update_service_health.py` script automatically checks all registered services and updates their health status.

```bash
cd services/config-service

# Check all services once
python3 update_service_health.py

# Check a specific service
python3 update_service_health.py asr-service

# Run continuous health checks every 30 seconds
python3 update_service_health.py --interval 30
```

### How It Works

1. **Retrieves all services** from the registry
2. **Checks health endpoint** for each service:
   - Uses `health_check_url` if available
   - Falls back to standard health endpoints per service type
   - Times out after 5 seconds
3. **Updates status**:
   - ✅ `healthy` - Service responds with HTTP 200
   - ❌ `unhealthy` - Service doesn't respond or returns error
4. **Records response time** in milliseconds

### Health Endpoints

The script knows the correct health endpoints for each service:

| Service | Health Endpoint |
|---------|----------------|
| api-gateway-service | `/health` |
| auth-service | `/health` |
| config-service | `/health` |
| metrics-service | `/health` |
| telemetry-service | `/health` |
| alerting-service | `/health` |
| dashboard-service | `/health` |
| asr-service | `/api/v1/asr/health` |
| tts-service | `/health` |
| nmt-service | `/api/v1/nmt/health` |
| pipeline-service | `/health` |
| simple-ui-frontend | `/health` |

## Manual Health Updates

### Via API

Update a service's health status manually:

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

### Via Python

```python
import requests

BASE_URL = "http://localhost:8082/api/v1"
API_KEY = "admin"

headers = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json"
}

# Update service health
update_data = {
    "service_name": "asr-service",
    "status": "healthy",
    "response_time": 150.5
}

response = requests.put(
    f"{BASE_URL}/registry/health",
    headers=headers,
    json=update_data
)
print(response.json())
```

## Service Status Values

- **unknown** - Initial status, hasn't been checked yet
- **healthy** - Service is responding and working correctly
- **unhealthy** - Service is not responding or returning errors

## Continuous Monitoring

For production, set up a cron job or scheduled task to run health checks:

```bash
# Run every 30 seconds via cron (not recommended for high frequency)
*/1 * * * * cd /path/to/config-service && python3 update_service_health.py
```

Or use the built-in interval option:

```bash
# Run continuous checks every 30 seconds
python3 update_service_health.py --interval 30
```

## Troubleshooting

### All services showing as unhealthy

- **Services not running**: Start the services first
  ```bash
  docker-compose up -d
  ```

- **Wrong URLs**: Check if service URLs are correct
  ```bash
  curl "http://localhost:8082/api/v1/registry/asr-service" \
    -H "Authorization: ApiKey admin"
  ```

- **Network issues**: Verify services are accessible
  ```bash
  curl http://localhost:8082/health  # Check config-service
  curl http://localhost:8080/health  # Check api-gateway
  ```

### Service shows healthy but returns errors

The health check only verifies HTTP connectivity. You may need custom health check logic for more detailed status.

### Health check script can't connect to services

- Ensure services are running
- Check Docker network connectivity
- Verify service URLs use correct hostnames
- Check firewall/network settings

## Integration with CI/CD

You can integrate health checks into your deployment pipeline:

```yaml
# Example GitHub Actions step
- name: Update service health
  run: |
    cd services/config-service
    python3 update_service_health.py
```

## Best Practices

1. **Run health checks regularly** - At least every 30-60 seconds
2. **Set up alerts** - Monitor for services transitioning to unhealthy
3. **Log health changes** - Track status transitions for debugging
4. **Use response times** - Monitor service performance over time
5. **Automate** - Use the health check script in monitoring loops

## Related Documentation

- [Service Registry API](../../docs/SEED_SERVICES_README.md)
- [Config Service README](../README.md)

