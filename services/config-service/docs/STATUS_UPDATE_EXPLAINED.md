# How Service Registry Status Updates After Deployment

## Quick Answer

**Status updates automatically** - No manual intervention needed!

When you deploy services, the Config Service runs a **background health monitor** that:
1. **Starts automatically** when Config Service starts (after 10 second delay)
2. **Checks all services** every 30 seconds
3. **Updates status** in the database automatically:
   - `unknown` → `healthy` (when service responds)
   - `unknown` → `unhealthy` (when service doesn't respond)
   - `healthy` → `unhealthy` (when service goes down)
   - `unhealthy` → `healthy` (when service recovers)

## Detailed Explanation

### Automatic Background Monitoring

The Config Service includes a **`HealthMonitorService`** that runs as a background task:

```python
# Automatically starts when config-service starts
HealthMonitorService.start_monitoring(
    interval_seconds=30,      # Check every 30 seconds
    startup_delay=10          # Wait 10 seconds before first check
)
```

### How Status Gets Updated

```
┌─────────────────────────────────────────────────────────┐
│              Config Service Startup                     │
│  1. Initialize connections (Redis, PostgreSQL, etc.)     │
│  2. Create HealthMonitorService                          │
│  3. Start background health monitoring task              │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│         Health Monitor (Every 30 seconds)                │
│                                                          │
│  1. Query database → Get all registered services         │
│  2. For each service:                                    │
│     ├─ Call health endpoint (e.g., /health)             │
│     ├─ Measure response time                            │
│     ├─ Determine status (healthy/unhealthy)             │
│     └─ Update database:                                 │
│        - status column                                  │
│        - last_health_check timestamp                    │
│        - response_time in metadata                       │
│  3. Invalidate cache                                    │
│  4. Publish Kafka event (optional)                      │
└─────────────────────────────────────────────────────────┘
```

### Status Transitions

```
Initial State:    unknown
                        │
                        ▼
           ┌─────────────────────┐
           │  Health Check Cycle  │
           └─────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
   Service responds               Service doesn't respond
        │                               │
        ▼                               ▼
    healthy                         unhealthy
        │                               │
        └───────────────┬───────────────┘
                        │
           Next health check cycle (30s)
```

### Database Updates

Every health check cycle updates:

- **`status`** column: `healthy` | `unhealthy` | `unknown`
- **`last_health_check`** column: Current timestamp
- **`metadata.avg_response_time`**: Response time in milliseconds
- **`updated_at`**: Last update timestamp

### Configuration

Control health monitoring via environment variables:

```bash
# In .env or docker-compose.yml
HEALTH_CHECK_INTERVAL=30          # Check every 30 seconds
HEALTH_CHECK_STARTUP_DELAY=10     # Wait 10s before first check
```

### Verification

After deployment, check status updates:

```bash
# Watch logs to see health checks
docker logs -f config-service | grep "Health check"

# Query current status
curl "http://localhost:8082/api/v1/registry/" \
  -H "Authorization: ApiKey admin"
```

You'll see:
- Services transition from `unknown` to `healthy`/`unhealthy`
- `last_health_check` timestamps updating every 30 seconds
- Status changes logged in config-service logs

### Summary

**You don't need to do anything!** 

1. ✅ Deploy services
2. ✅ Services register (status = "unknown")
3. ✅ Config Service health monitor automatically:
   - Waits 10 seconds
   - Starts checking every 30 seconds
   - Updates status automatically
4. ✅ Status reflects actual service health

The status column updates **automatically** after deployment - no manual scripts or API calls needed!

## Related Documentation

- [Health Check Guide](HEALTH_CHECK_GUIDE.md) - Manual health checking (optional)
- [Deployment Health Status](DEPLOYMENT_HEALTH_STATUS.md) - Full deployment guide
- [Service Registry Seeding](SEED_SERVICES_README.md) - Service registration

