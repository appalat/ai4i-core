# Service Registry Health Status - Deployment Guide

## How Status Updates After Deployment

The service registry `status` column is **automatically updated** through a **background health monitoring service** that runs within the Config Service. After deployment, you don't need to manually update status - it happens automatically!

## Automatic Health Monitoring

### How It Works

1. **Config Service Startup**
   - On startup, the Config Service initializes a `HealthMonitorService`
   - The health monitor starts after a configurable delay (default: 10 seconds)
   - This delay allows other services time to start up

2. **Periodic Health Checks**
   - Every 30 seconds (configurable), the health monitor:
     - Retrieves all registered services from the database
     - Calls each service's health endpoint
     - Updates the status in the database:
       - ✅ `healthy` - Service responds with HTTP 200
       - ❌ `unhealthy` - Service doesn't respond or returns error
     - Records response time and last check timestamp

3. **Status Transitions**
   - **unknown** → **healthy** when service becomes available
   - **unknown** → **unhealthy** when service check fails
   - **healthy** → **unhealthy** when service goes down
   - **unhealthy** → **healthy** when service recovers

## Configuration

### Environment Variables

Add these to your `.env` file or `docker-compose.yml`:

```bash
# Health check interval in seconds (default: 30)
HEALTH_CHECK_INTERVAL=30

# Delay before starting health checks (default: 10)
# Gives services time to start up
HEALTH_CHECK_STARTUP_DELAY=10
```

### Docker Compose Example

```yaml
services:
  config-service:
    environment:
      - HEALTH_CHECK_INTERVAL=30
      - HEALTH_CHECK_STARTUP_DELAY=10
```

## Deployment Flow

### 1. Initial Deployment

```bash
# Start services
docker-compose up -d

# Services register themselves or get seeded:
# - Status starts as "unknown" in database
# - Config Service starts and initializes health monitor
# - Health monitor waits 10 seconds (startup delay)
# - First health check cycle runs after 10 seconds
```

### 2. Status Update Timeline

```
Time    | Event
--------|--------------------------------------------------
0s      | Services start, status = "unknown" in DB
0s      | Config Service starts, initializes health monitor
10s     | Health monitor delay expires, first check cycle begins
10s     | Health monitor calls each service's health endpoint
10-15s  | Status updates in database:
        | - Running services → "healthy" ✅
        | - Not running services → "unhealthy" ❌
        | - last_health_check timestamp updated
40s     | Second health check cycle (every 30s)
70s     | Third health check cycle
...     | Continuous monitoring every 30 seconds
```

### 3. What Happens Automatically

- ✅ **No manual intervention needed** - Status updates happen automatically
- ✅ **Continuous monitoring** - Health checks run every 30 seconds
- ✅ **Status transitions tracked** - Changes logged with timestamps
- ✅ **Database updated** - Status, last_health_check, and response_time all updated
- ✅ **Cache invalidated** - Service info cache cleared on status change

### 3. After Service Starts

When a service starts:
- It may self-register or already be in registry
- Next health check cycle (within 30s) will detect it
- Status updates: `unknown/unhealthy` → `healthy`

### 4. Service Goes Down

When a service stops:
- Next health check (within 30s) will fail
- Status updates: `healthy` → `unhealthy`
- `last_health_check` timestamp is updated

## Health Endpoints

Each service type has a specific health endpoint:

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

## Monitoring Health Monitor

### Check Health Monitor Status

The health monitor logs its activity:

```bash
# View config service logs
docker logs -f config-service

# Look for:
# "Starting health monitor (interval: 30s, startup delay: 10s)"
# "Health check: service-name unknown → healthy (45.2ms)"
```

### Verify Status Updates

```bash
# Check current status
curl "http://localhost:8082/api/v1/registry/" \
  -H "Authorization: ApiKey admin" | jq '.services[] | {name: .service_name, status: .status, last_check: .last_health_check}'

# Should see updated statuses within 30-40 seconds after deployment
```

## Manual Updates (Optional)

While automatic monitoring handles status updates, you can also update manually:

### Via API

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

### Via Script

```bash
cd services/config-service
python3 update_service_health.py
```

## Troubleshooting

### Status Stays "unknown"

**Issue**: Services remain "unknown" after deployment

**Solutions**:
1. Check if health monitor is running:
   ```bash
   docker logs config-service | grep -i "health monitor"
   ```

2. Verify health check interval is configured:
   ```bash
   docker exec config-service env | grep HEALTH_CHECK
   ```

3. Check for errors:
   ```bash
   docker logs config-service | grep -i error
   ```

### Status Stuck on "unhealthy"

**Issue**: Service is running but shows "unhealthy"

**Solutions**:
1. Verify service health endpoint works:
   ```bash
   curl http://asr-service:8087/api/v1/asr/health
   ```

2. Check Docker network connectivity:
   ```bash
   docker exec config-service ping asr-service
   ```

3. Verify health endpoint URL in registry:
   ```bash
   curl "http://localhost:8082/api/v1/registry/asr-service" \
     -H "Authorization: ApiKey admin"
   ```

### Health Monitor Not Starting

**Issue**: No health check logs appear

**Solutions**:
1. Ensure config-service is running:
   ```bash
   docker ps | grep config-service
   ```

2. Check startup delay - wait at least 10 seconds
3. Check logs for initialization errors:
   ```bash
   docker logs config-service
   ```

## Best Practices

1. **Set Appropriate Interval**
   - Too frequent (e.g., 5s): High load, unnecessary checks
   - Too infrequent (e.g., 120s): Slow status updates
   - **Recommended**: 30-60 seconds

2. **Configure Startup Delay**
   - Give services time to start before first check
   - **Recommended**: 10-30 seconds

3. **Monitor Health Monitor**
   - Include health monitor logs in monitoring
   - Alert if health monitor stops

4. **Service Health Endpoints**
   - Ensure all services have working `/health` endpoints
   - Standardize health response format

## Related Documentation

- [Health Check Guide](HEALTH_CHECK_GUIDE.md)
- [Service Registry Seeding](SEED_SERVICES_README.md)
- [Config Service README](../README.md)

