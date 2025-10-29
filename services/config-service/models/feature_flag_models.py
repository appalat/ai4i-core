"""
Pydantic models for feature flag management.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

# Supported environments
SUPPORTED_ENVIRONMENTS = ["development", "staging", "production"]


class FeatureFlagRequest(BaseModel):
    """Request model for creating a feature flag."""
    name: str = Field(..., description="Feature flag name", max_length=255)
    description: Optional[str] = Field(None, description="Feature flag description")
    is_enabled: bool = Field(False, description="Whether the feature is globally enabled")
    rollout_percentage: float = Field(0.00, ge=0.00, le=100.00, description="Rollout percentage (0-100)")
    target_users: Optional[List[str]] = Field(None, description="List of user IDs to target")
    environment: str = Field(..., description="Environment name")
    
    @validator("environment")
    def validate_environment(cls, v):
        if v not in SUPPORTED_ENVIRONMENTS:
            raise ValueError(f"Environment must be one of {SUPPORTED_ENVIRONMENTS}")
        return v
    
    @validator("name")
    def validate_name(cls, v):
        if not v or len(v) > 255:
            raise ValueError("Name must be between 1 and 255 characters")
        # Lowercase with underscores only
        if not v.lower() == v.replace(' ', '_'):
            raise ValueError("Name must be lowercase with underscores")
        return v.lower()


class FeatureFlagUpdate(BaseModel):
    """Request model for updating a feature flag."""
    description: Optional[str] = Field(None, description="Feature flag description")
    is_enabled: Optional[bool] = Field(None, description="Whether the feature is globally enabled")
    rollout_percentage: Optional[float] = Field(None, ge=0.00, le=100.00, description="Rollout percentage")
    target_users: Optional[List[str]] = Field(None, description="List of user IDs to target")


class FeatureFlagEvaluationRequest(BaseModel):
    """Request model for evaluating a feature flag."""
    flag_name: str = Field(..., description="Feature flag name")
    environment: str = Field(..., description="Environment name")
    user_id: Optional[str] = Field(None, description="User ID for evaluation")
    
    @validator("environment")
    def validate_environment(cls, v):
        if v not in SUPPORTED_ENVIRONMENTS:
            raise ValueError(f"Environment must be one of {SUPPORTED_ENVIRONMENTS}")
        return v


class FeatureFlagEvaluationResponse(BaseModel):
    """Response model for feature flag evaluation."""
    enabled: bool = Field(..., description="Whether the feature is enabled for the user")
    reason: str = Field(..., description="Reason for the evaluation result")
    flag_name: str = Field(..., description="Feature flag name")
    environment: str = Field(..., description="Environment name")


class FeatureFlagResponse(BaseModel):
    """Response model for feature flag."""
    id: int
    name: str
    description: Optional[str]
    is_enabled: bool
    rollout_percentage: float
    target_users: Optional[List[str]]
    environment: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FeatureFlagListResponse(BaseModel):
    """Response model for list of feature flags."""
    flags: List[FeatureFlagResponse]
    total: int
    limit: int
    offset: int

