"""
Pydantic models for configuration management.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

# Supported environments
SUPPORTED_ENVIRONMENTS = ["development", "staging", "production"]


class ConfigurationRequest(BaseModel):
    """Request model for creating a configuration."""
    key: str = Field(..., description="Configuration key", max_length=255)
    value: str = Field(..., description="Configuration value")
    environment: str = Field(..., description="Environment name")
    service_name: str = Field(..., description="Service name", max_length=100)
    description: Optional[str] = Field(None, description="Configuration description")
    is_encrypted: bool = Field(False, description="Whether the value is encrypted")
    
    @validator("environment")
    def validate_environment(cls, v):
        if v not in SUPPORTED_ENVIRONMENTS:
            raise ValueError(f"Environment must be one of {SUPPORTED_ENVIRONMENTS}")
        return v
    
    @validator("key")
    def validate_key(cls, v):
        if not v or len(v) > 255:
            raise ValueError("Key must be between 1 and 255 characters")
        # Allow alphanumeric, dots, underscores, hyphens
        if not all(c.isalnum() or c in "._-" for c in v):
            raise ValueError("Key can only contain alphanumeric characters, dots, underscores, and hyphens")
        return v


class ConfigurationUpdate(BaseModel):
    """Request model for updating a configuration."""
    value: Optional[str] = Field(None, description="New configuration value")
    is_encrypted: Optional[bool] = Field(None, description="Whether the value is encrypted")
    description: Optional[str] = Field(None, description="Configuration description")


class ConfigurationQuery(BaseModel):
    """Query parameters for filtering configurations."""
    environment: Optional[str] = Field(None, description="Environment filter")
    service_name: Optional[str] = Field(None, description="Service name filter")
    key_pattern: Optional[str] = Field(None, description="Key pattern for search")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class ConfigurationResponse(BaseModel):
    """Response model for configuration."""
    id: int
    key: str
    value: str
    environment: str
    service_name: str
    is_encrypted: bool
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConfigurationListResponse(BaseModel):
    """Response model for list of configurations."""
    configurations: List[ConfigurationResponse]
    total: int
    limit: int
    offset: int


class ConfigurationHistoryResponse(BaseModel):
    """Response model for configuration history."""
    id: int
    configuration_id: int
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: Optional[str]
    changed_at: datetime
    
    class Config:
        from_attributes = True

