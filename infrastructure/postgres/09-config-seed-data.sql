-- Config Service Seed Data
-- Initial default data for configuration management, feature flags, and service registry
-- This script populates the config_db with useful default values for AI4V-Core platform

\c config_db;

-- ============================================================================
-- CONFIGURATIONS
-- ============================================================================
-- Sample configurations for different services across environments

-- API Gateway configurations
INSERT INTO configurations (key, value, environment, service_name, description, is_encrypted, version) VALUES
('api.gateway.rate_limit.per_minute', '100', 'development', 'api-gateway-service', 'Rate limit per minute for API Gateway', false, 1),
('api.gateway.rate_limit.per_hour', '1000', 'development', 'api-gateway-service', 'Rate limit per hour for API Gateway', false, 1),
('api.gateway.timeout', '30', 'development', 'api-gateway-service', 'Request timeout in seconds', false, 1),
('api.gateway.enable_cors', 'true', 'development', 'api-gateway-service', 'Enable CORS for API Gateway', false, 1),
('api.gateway.rate_limit.per_minute', '200', 'staging', 'api-gateway-service', 'Rate limit per minute for API Gateway', false, 1),
('api.gateway.rate_limit.per_hour', '5000', 'staging', 'api-gateway-service', 'Rate limit per hour for API Gateway', false, 1),
('api.gateway.rate_limit.per_minute', '500', 'production', 'api-gateway-service', 'Rate limit per minute for API Gateway', false, 1),
('api.gateway.rate_limit.per_hour', '20000', 'production', 'api-gateway-service', 'Rate limit per hour for API Gateway', false, 1)
ON CONFLICT (key, environment, service_name) DO NOTHING;

-- Authentication Service configurations
INSERT INTO configurations (key, value, environment, service_name, description, is_encrypted, version) VALUES
('auth.jwt.secret_key', 'dev-secret-key-change-in-production', 'development', 'auth-service', 'JWT secret key (change in production)', true, 1),
('auth.jwt.access_token_expire_minutes', '30', 'development', 'auth-service', 'Access token expiration in minutes', false, 1),
('auth.jwt.refresh_token_expire_days', '7', 'development', 'auth-service', 'Refresh token expiration in days', false, 1),
('auth.password.min_length', '8', 'development', 'auth-service', 'Minimum password length', false, 1),
('auth.password.require_uppercase', 'true', 'development', 'auth-service', 'Require uppercase in passwords', false, 1),
('auth.password.require_numbers', 'true', 'development', 'auth-service', 'Require numbers in passwords', false, 1)
ON CONFLICT (key, environment, service_name) DO NOTHING;

-- ASR Service configurations
INSERT INTO configurations (key, value, environment, service_name, description, is_encrypted, version) VALUES
('asr.model.default', 'ai4bharat/indicwav2vec_v1', 'development', 'asr-service', 'Default ASR model identifier', false, 1),
('asr.audio.max_duration_seconds', '300', 'development', 'asr-service', 'Maximum audio duration in seconds', false, 1),
('asr.audio.supported_formats', 'wav,mp3,ogg', 'development', 'asr-service', 'Supported audio formats', false, 1),
('asr.streaming.enabled', 'true', 'development', 'asr-service', 'Enable streaming ASR', false, 1),
('asr.streaming.chunk_size', '8192', 'development', 'asr-service', 'Streaming chunk size in bytes', false, 1),
('asr.batch.max_items', '10', 'development', 'asr-service', 'Maximum items in batch request', false, 1)
ON CONFLICT (key, environment, service_name) DO NOTHING;

-- TTS Service configurations
INSERT INTO configurations (key, value, environment, service_name, description, is_encrypted, version) VALUES
('tts.model.default', 'tts-hindi-female', 'development', 'tts-service', 'Default TTS model identifier', false, 1),
('tts.audio.output_format', 'wav', 'development', 'tts-service', 'Default audio output format', false, 1),
('tts.audio.sampling_rate', '22050', 'development', 'tts-service', 'Audio sampling rate in Hz', false, 1),
('tts.text.max_length', '1000', 'development', 'tts-service', 'Maximum text length per request', false, 1),
('tts.batch.max_items', '10', 'development', 'tts-service', 'Maximum items in batch request', false, 1),
('tts.streaming.enabled', 'true', 'development', 'tts-service', 'Enable streaming TTS', false, 1)
ON CONFLICT (key, environment, service_name) DO NOTHING;

-- NMT Service configurations
INSERT INTO configurations (key, value, environment, service_name, description, is_encrypted, version) VALUES
('nmt.model.default', 'ai4bharat/indictrans-v2-all-gpu--t4', 'development', 'nmt-service', 'Default NMT model identifier', false, 1),
('nmt.text.max_length', '5000', 'development', 'nmt-service', 'Maximum text length per request', false, 1),
('nmt.batch.max_items', '90', 'development', 'nmt-service', 'Maximum items in batch request', false, 1),
('nmt.supported_languages', 'en,hi,ta,te,kn,ml,bn,gu,mr,pa,or,as,ur', 'development', 'nmt-service', 'Supported language codes', false, 1)
ON CONFLICT (key, environment, service_name) DO NOTHING;

-- Metrics Service configurations
INSERT INTO configurations (key, value, environment, service_name, description, is_encrypted, version) VALUES
('metrics.retention.days', '90', 'development', 'metrics-service', 'Metrics retention period in days', false, 1),
('metrics.collection.interval_seconds', '60', 'development', 'metrics-service', 'Metrics collection interval', false, 1),
('metrics.export.format', 'json', 'development', 'metrics-service', 'Default export format', false, 1)
ON CONFLICT (key, environment, service_name) DO NOTHING;

-- Telemetry Service configurations
INSERT INTO configurations (key, value, environment, service_name, description, is_encrypted, version) VALUES
('telemetry.log.retention.days', '30', 'development', 'telemetry-service', 'Log retention period in days', false, 1),
('telemetry.trace.sampling_rate', '0.1', 'development', 'telemetry-service', 'Trace sampling rate (0.0-1.0)', false, 1),
('telemetry.enable_distributed_tracing', 'true', 'development', 'telemetry-service', 'Enable distributed tracing', false, 1)
ON CONFLICT (key, environment, service_name) DO NOTHING;

-- Database configurations (for services using PostgreSQL)
INSERT INTO configurations (key, value, environment, service_name, description, is_encrypted, version) VALUES
('database.connection.pool_size', '10', 'development', 'config-service', 'Database connection pool size', false, 1),
('database.connection.max_overflow', '5', 'development', 'config-service', 'Database max overflow connections', false, 1),
('database.query.timeout_seconds', '30', 'development', 'config-service', 'Database query timeout', false, 1),
('cache.redis.ttl.default', '300', 'development', 'config-service', 'Default Redis cache TTL in seconds', false, 1),
('cache.redis.ttl.config', '300', 'development', 'config-service', 'Config cache TTL in seconds', false, 1),
('cache.redis.ttl.feature_flag', '300', 'development', 'config-service', 'Feature flag cache TTL in seconds', false, 1)
ON CONFLICT (key, environment, service_name) DO NOTHING;

-- ============================================================================
-- FEATURE FLAGS
-- ============================================================================
-- Sample feature flags for platform features

-- Development environment feature flags
INSERT INTO feature_flags (name, description, is_enabled, rollout_percentage, target_users, environment) VALUES
('new_checkout_flow', 'Enable new checkout UI with improved UX', true, 100.0, NULL, 'development'),
('ai_model_cache', 'Enable caching for AI model responses', true, 100.0, NULL, 'development'),
('advanced_analytics', 'Show advanced analytics dashboard', true, 100.0, NULL, 'development'),
('real_time_notifications', 'Enable real-time push notifications', false, 0.0, NULL, 'development'),
('beta_features', 'Show beta features to beta users', true, 50.0, ARRAY['beta_user_1', 'beta_user_2'], 'development'),
('experimental_asr_models', 'Enable experimental ASR models', true, 100.0, NULL, 'development'),
('tts_voice_preview', 'Allow users to preview TTS voices before synthesis', true, 100.0, NULL, 'development'),
('nmt_batch_processing', 'Enable batch processing for NMT requests', true, 100.0, NULL, 'development')
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    is_enabled = EXCLUDED.is_enabled,
    rollout_percentage = EXCLUDED.rollout_percentage,
    target_users = EXCLUDED.target_users,
    environment = EXCLUDED.environment,
    updated_at = CURRENT_TIMESTAMP;

-- Staging environment feature flags
INSERT INTO feature_flags (name, description, is_enabled, rollout_percentage, target_users, environment) VALUES
('new_checkout_flow', 'Enable new checkout UI with improved UX', true, 50.0, NULL, 'staging'),
('ai_model_cache', 'Enable caching for AI model responses', true, 100.0, NULL, 'staging'),
('advanced_analytics', 'Show advanced analytics dashboard', true, 100.0, NULL, 'staging'),
('real_time_notifications', 'Enable real-time push notifications', false, 0.0, NULL, 'staging'),
('beta_features', 'Show beta features to beta users', true, 25.0, NULL, 'staging'),
('experimental_asr_models', 'Enable experimental ASR models', false, 0.0, NULL, 'staging'),
('tts_voice_preview', 'Allow users to preview TTS voices before synthesis', true, 100.0, NULL, 'staging'),
('nmt_batch_processing', 'Enable batch processing for NMT requests', true, 100.0, NULL, 'staging')
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    is_enabled = EXCLUDED.is_enabled,
    rollout_percentage = EXCLUDED.rollout_percentage,
    target_users = EXCLUDED.target_users,
    environment = EXCLUDED.environment,
    updated_at = CURRENT_TIMESTAMP;

-- Production environment feature flags
INSERT INTO feature_flags (name, description, is_enabled, rollout_percentage, target_users, environment) VALUES
('new_checkout_flow', 'Enable new checkout UI with improved UX', false, 0.0, NULL, 'production'),
('ai_model_cache', 'Enable caching for AI model responses', true, 100.0, NULL, 'production'),
('advanced_analytics', 'Show advanced analytics dashboard', true, 100.0, NULL, 'production'),
('real_time_notifications', 'Enable real-time push notifications', true, 25.0, NULL, 'production'),
('beta_features', 'Show beta features to beta users', false, 0.0, NULL, 'production'),
('experimental_asr_models', 'Enable experimental ASR models', false, 0.0, NULL, 'production'),
('tts_voice_preview', 'Allow users to preview TTS voices before synthesis', true, 100.0, NULL, 'production'),
('nmt_batch_processing', 'Enable batch processing for NMT requests', true, 100.0, NULL, 'production')
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    is_enabled = EXCLUDED.is_enabled,
    rollout_percentage = EXCLUDED.rollout_percentage,
    target_users = EXCLUDED.target_users,
    environment = EXCLUDED.environment,
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- SERVICE REGISTRY
-- ============================================================================
-- Register all AI4V-Core microservices with default metadata

INSERT INTO service_registry (service_name, service_url, health_check_url, status, metadata) VALUES
-- Gateway Service
('api-gateway-service', 'http://api-gateway-service:8080', 'http://api-gateway-service:8080/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Central entry point with routing, rate limiting, and authentication", "port": 8080, "type": "gateway"}'),

-- Core Services
('auth-service', 'http://auth-service:8081', 'http://auth-service:8081/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Identity management with JWT and OAuth2", "port": 8081, "type": "core"}'),

('config-service', 'http://config-service:8082', 'http://config-service:8082/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Centralized configuration and feature flags", "port": 8082, "type": "core"}'),

('metrics-service', 'http://metrics-service:8083', 'http://metrics-service:8083/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "System and application metrics collection", "port": 8083, "type": "core"}'),

('telemetry-service', 'http://telemetry-service:8084', 'http://telemetry-service:8084/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Log aggregation, distributed tracing, and event correlation", "port": 8084, "type": "core"}'),

('alerting-service', 'http://alerting-service:8085', 'http://alerting-service:8085/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Proactive issue detection and notification", "port": 8085, "type": "core"}'),

('dashboard-service', 'http://dashboard-service:8086', 'http://dashboard-service:8086/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Visualization and reporting with Streamlit UI", "port": 8086, "type": "core"}'),

-- AI/ML Services
('asr-service', 'http://asr-service:8087', 'http://asr-service:8087/api/v1/asr/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Speech-to-Text with 22+ Indian languages", "port": 8087, "type": "ai", "capabilities": ["asr", "speech-recognition", "streaming"]}'),

('tts-service', 'http://tts-service:8088', 'http://tts-service:8088/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Text-to-Speech with multiple voice options", "port": 8088, "type": "ai", "capabilities": ["tts", "text-to-speech", "voice-synthesis"]}'),

('nmt-service', 'http://nmt-service:8089', 'http://nmt-service:8089/api/v1/nmt/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Neural Machine Translation for Indian languages", "port": 8089, "type": "ai", "capabilities": ["translation", "nmt", "language-processing"]}'),

('pipeline-service', 'http://pipeline-service:8090', 'http://pipeline-service:8090/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Multi-task AI pipeline orchestration (Speech-to-Speech translation)", "port": 8090, "type": "ai", "capabilities": ["pipeline", "orchestration", "multi-task"]}'),

-- Frontend
('simple-ui-frontend', 'http://simple-ui-frontend:3000', 'http://simple-ui-frontend:3000/health', 'unknown',
 '{"version": "1.0.0", "environment": "development", "description": "Web interface for testing AI services (Next.js)", "port": 3000, "type": "frontend"}')

ON CONFLICT (service_name) DO UPDATE SET
    service_url = EXCLUDED.service_url,
    health_check_url = EXCLUDED.health_check_url,
    metadata = EXCLUDED.metadata,
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- VERIFICATION QUERIES (commented out - uncomment to run)
-- ============================================================================

-- SELECT COUNT(*) as total_configs FROM configurations;
-- SELECT COUNT(*) as total_feature_flags FROM feature_flags;
-- SELECT COUNT(*) as total_services FROM service_registry;

-- SELECT service_name, environment, COUNT(*) as config_count
-- FROM configurations
-- GROUP BY service_name, environment
-- ORDER BY service_name, environment;

-- SELECT name, environment, is_enabled, rollout_percentage
-- FROM feature_flags
-- ORDER BY environment, name;

-- SELECT service_name, status, metadata->>'type' as service_type
-- FROM service_registry
-- ORDER BY service_name;

