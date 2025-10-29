"""
Feature flag management router with CRUD operations and evaluation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from services.feature_flag_service import FeatureFlagService
from models.feature_flag_models import (
    FeatureFlagRequest,
    FeatureFlagUpdate,
    FeatureFlagResponse,
    FeatureFlagListResponse,
    FeatureFlagEvaluationRequest,
    FeatureFlagEvaluationResponse
)
from repositories.feature_flag_repository import FeatureFlagRepository
from middleware.auth_provider import AuthProvider, require_admin_permissions

# Create router
feature_flag_router = APIRouter(prefix="/api/v1/feature-flags", tags=["feature-flags"])


async def get_db_session():
    """Dependency to get database session."""
    from main import app
    session_factory = app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_feature_flag_service(db: AsyncSession = Depends(get_db_session)) -> FeatureFlagService:
    """Dependency to get feature flag service."""
    from main import app
    cache_service = app.state.cache_service
    notification_service = app.state.notification_service
    
    repository = FeatureFlagRepository(db)
    return FeatureFlagService(repository, cache_service, notification_service)




@feature_flag_router.post("/", response_model=FeatureFlagResponse)
async def create_feature_flag(
    request: FeatureFlagRequest,
    service: FeatureFlagService = Depends(get_feature_flag_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Create a new feature flag."""
    try:
        flag = await service.create_feature_flag(request)
        return FeatureFlagResponse.model_validate(flag)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@feature_flag_router.get("/{name}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    name: str,
    environment: str = Query(..., description="Environment name"),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Get a feature flag by name and environment."""
    try:
        flag = await service.get_feature_flag(name, environment)
        if not flag:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        return FeatureFlagResponse.model_validate(flag)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@feature_flag_router.get("/", response_model=FeatureFlagListResponse)
async def list_feature_flags(
    environment: Optional[str] = Query(None, description="Environment filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """List feature flags with filtering and pagination."""
    try:
        flags = await service.get_all_feature_flags(environment, limit, offset)
        
        # Convert to response models
        flag_responses = [FeatureFlagResponse.model_validate(flag) for flag in flags]
        
        return FeatureFlagListResponse(
            flags=flag_responses,
            total=len(flag_responses),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@feature_flag_router.put("/{flag_id}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    flag_id: int,
    update: FeatureFlagUpdate,
    service: FeatureFlagService = Depends(get_feature_flag_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Update a feature flag."""
    try:
        flag = await service.update_feature_flag(flag_id, update)
        if not flag:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        return FeatureFlagResponse.model_validate(flag)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@feature_flag_router.delete("/{flag_id}")
async def delete_feature_flag(
    flag_id: int,
    service: FeatureFlagService = Depends(get_feature_flag_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Delete a feature flag."""
    try:
        success = await service.delete_feature_flag(flag_id)
        if not success:
            raise HTTPException(status_code=404, detail="Feature flag not found")
        return {"message": "Feature flag deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@feature_flag_router.post("/evaluate", response_model=FeatureFlagEvaluationResponse)
async def evaluate_feature_flag(
    request: FeatureFlagEvaluationRequest,
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Evaluate a feature flag for a user."""
    try:
        result = await service.evaluate_feature_flag(
            name=request.flag_name,
            environment=request.environment,
            user_id=request.user_id
        )
        
        return FeatureFlagEvaluationResponse(
            enabled=result["enabled"],
            reason=result["reason"],
            flag_name=request.flag_name,
            environment=request.environment
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@feature_flag_router.get("/{name}/evaluate", response_model=FeatureFlagEvaluationResponse)
async def evaluate_feature_flag_by_name(
    name: str,
    environment: str = Query(..., description="Environment name"),
    user_id: Optional[str] = Query(None, description="User ID for evaluation"),
    service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Evaluate a feature flag by name for a user."""
    try:
        result = await service.evaluate_feature_flag(
            name=name,
            environment=environment,
            user_id=user_id
        )
        
        return FeatureFlagEvaluationResponse(
            enabled=result["enabled"],
            reason=result["reason"],
            flag_name=name,
            environment=environment
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
