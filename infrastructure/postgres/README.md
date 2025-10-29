# PostgreSQL Database Initialization

This directory contains SQL scripts for initializing the PostgreSQL databases used by the AI4V-Core microservices platform.

## File Execution Order

The scripts are executed automatically in alphabetical order when the PostgreSQL container starts for the first time:

1. **init-databases.sql** - Creates all required databases
2. **01-auth-schema.sql** - Creates tables for auth-service
3. **02-config-schema.sql** - Creates tables for config-service
4. **03-metrics-schema.sql** - Creates tables for metrics-service
5. **04-telemetry-schema.sql** - Creates tables for telemetry-service
6. **05-alerting-schema.sql** - Creates tables for alerting-service
7. **06-dashboard-schema.sql** - Creates tables for dashboard-service
8. **07-seed-data.sql** - Seeds initial data for auth-service (roles, permissions)
9. **08-ai-services-schema.sql** - Creates tables for AI services (ASR, TTS, NMT)
10. **09-config-seed-data.sql** - Seeds initial data for config-service ⭐ **NEW**

## Config Service Seed Data

The `09-config-seed-data.sql` file includes:

### 1. Configurations
- API Gateway settings (rate limits, timeouts)
- Authentication service settings (JWT, passwords)
- ASR/TTS/NMT service configurations
- Metrics and telemetry settings
- Database connection settings
- Cache configurations

### 2. Feature Flags
- Development, staging, and production environments
- Platform features (new checkout, analytics, notifications)
- AI service features (experimental models, voice preview)
- Rollout percentages and target users

### 3. Service Registry
- All 12 AI4V-Core microservices
- Service URLs and health check endpoints
- Service metadata (version, type, description, capabilities)
- Service discovery information

## Manual Execution

If you need to manually run the seed data script:

```bash
# Connect to PostgreSQL
docker exec -it ai4v-postgres psql -U dhruva_user -d config_db

# Execute the seed data script
\i /path/to/09-config-seed-data.sql
```

Or from outside the container:

```bash
docker exec -i ai4v-postgres psql -U dhruva_user -d config_db < infrastructure/postgres/09-config-seed-data.sql
```

## Resetting Seed Data

To reset and re-seed the config service data:

```bash
# Clear existing data (be careful!)
docker exec -it ai4v-postgres psql -U dhruva_user -d config_db -c "
  TRUNCATE configurations, feature_flags, service_registry, configuration_history CASCADE;
"

# Re-run seed data
docker exec -i ai4v-postgres psql -U dhruva_user -d config_db < infrastructure/postgres/09-config-seed-data.sql
```

## Verification

Check seed data after initialization:

```sql
-- Count configurations
SELECT service_name, environment, COUNT(*) as count 
FROM configurations 
GROUP BY service_name, environment 
ORDER BY service_name, environment;

-- Count feature flags
SELECT environment, COUNT(*) as count 
FROM feature_flags 
GROUP BY environment 
ORDER BY environment;

-- Count services
SELECT COUNT(*) as total_services, 
       COUNT(*) FILTER (WHERE status = 'healthy') as healthy,
       COUNT(*) FILTER (WHERE status = 'unknown') as unknown
FROM service_registry;
```

## Notes

- All seed data uses `ON CONFLICT DO NOTHING` or `ON CONFLICT DO UPDATE` to allow safe re-execution
- Sensitive values like JWT secrets should be changed in production
- Service URLs use Docker internal network addresses
- Health statuses start as 'unknown' and are updated when services report health

