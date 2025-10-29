"""
Pydantic models for service registry management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, HttpUrl

# Supported service statuses
SUPPORTED_STATUSES = ["healthy", "unhealthy", "unknown"]


class ServiceRegistrationRequest(BaseModel):
    """Request model for registering a service."""
    service_name: str = Field(..., description="Service name", max_length=100)
    service_url: str = Field(..., description="Service URL")
    health_check_url: Optional[str] = Field(None, description="Health check URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Service metadata")
    
    @validator("service_name")
    def validate_service_name(cls, v):
        if not v or len(v) > 100:
            raise ValueError("Service name must be between 1 and 100 characters")
        # Lowercase alphanumeric with hyphens
        if not v.lower() == v.replace(' ', '-'):
            raise ValueError("Service name must be lowercase alphanumeric with hyphens")
        return v.lower()
    
    @validator("service_url", "health_check_url")
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class ServiceHealthUpdate(BaseModel):
    """Request model for updating service health."""
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Health status")
    response_time: Optional[float] = Field(None, ge=0, description="Response time in milliseconds")
    
    @validator("status")
    def validate_status(cls, v):
        if v not in SUPPORTED_STATUSES:
            raise ValueError(f"Status must be one of {SUPPORTED_STATUSES}")
        return v


class ServiceInfo(BaseModel):
    """Response model for service information."""
    id: int
    service_name: str
    service_url: str
    health_check_url: Optional[str]
    status: str
    last_health_check: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    registered_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """Response model for list of services."""
    services: List[ServiceInfo]
    total: int


class ServiceDiscoveryResponse(BaseModel):
    """Response model for service discovery."""
    services: List[ServiceInfo]
    total: int

