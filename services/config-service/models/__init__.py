"""
Models package for config-service.
Exports all Pydantic models and database models.
"""

from .config_models import (
    ConfigurationRequest,
    ConfigurationResponse,
    ConfigurationUpdate,
    ConfigurationQuery,
    ConfigurationListResponse,
    ConfigurationHistoryResponse
)

from .feature_flag_models import (
    FeatureFlagRequest,
    FeatureFlagResponse,
    FeatureFlagUpdate,
    FeatureFlagEvaluationRequest,
    FeatureFlagEvaluationResponse,
    FeatureFlagListResponse
)

from .service_registry_models import (
    ServiceRegistrationRequest,
    ServiceHealthUpdate,
    ServiceInfo,
    ServiceListResponse,
    ServiceDiscoveryResponse
)

from .database_models import (
    ConfigurationDB,
    FeatureFlagDB,
    ServiceRegistryDB,
    ConfigurationHistoryDB,
    Base
)

__all__ = [
    # Config models
    "ConfigurationRequest",
    "ConfigurationResponse",
    "ConfigurationUpdate",
    "ConfigurationQuery",
    "ConfigurationListResponse",
    "ConfigurationHistoryResponse",
    # Feature flag models
    "FeatureFlagRequest",
    "FeatureFlagResponse",
    "FeatureFlagUpdate",
    "FeatureFlagEvaluationRequest",
    "FeatureFlagEvaluationResponse",
    "FeatureFlagListResponse",
    # Service registry models
    "ServiceRegistrationRequest",
    "ServiceHealthUpdate",
    "ServiceInfo",
    "ServiceListResponse",
    "ServiceDiscoveryResponse",
    # Database models
    "ConfigurationDB",
    "FeatureFlagDB",
    "ServiceRegistryDB",
    "ConfigurationHistoryDB",
    "Base"
]

