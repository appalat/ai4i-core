"""
Configuration management router with CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from services.configuration_service import ConfigurationService
from models.config_models import (
    ConfigurationRequest,
    ConfigurationUpdate,
    ConfigurationResponse,
    ConfigurationListResponse,
    ConfigurationQuery,
    ConfigurationHistoryResponse
)
from repositories.configuration_repository import ConfigurationRepository
from middleware.auth_provider import AuthProvider, require_admin_permissions

# Create router
config_router = APIRouter(prefix="/api/v1/config", tags=["configurations"])


async def get_db_session():
    """Dependency to get database session."""
    from main import app
    session_factory = app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_configuration_service(db: AsyncSession = Depends(get_db_session)) -> ConfigurationService:
    """Dependency to get configuration service."""
    from main import app
    cache_service = app.state.cache_service
    notification_service = app.state.notification_service
    
    repository = ConfigurationRepository(db)
    return ConfigurationService(repository, cache_service, notification_service)




@config_router.post("/", response_model=ConfigurationResponse)
async def create_configuration(
    request: ConfigurationRequest,
    service: ConfigurationService = Depends(get_configuration_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Create a new configuration."""
    try:
        config = await service.create_configuration(
            request=request,
            changed_by=auth["user_email"]
        )
        return ConfigurationResponse.model_validate(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@config_router.get("/{key}", response_model=ConfigurationResponse)
async def get_configuration(
    key: str,
    environment: str = Query(..., description="Environment name"),
    service_name: str = Query(..., description="Service name"),
    config_service: ConfigurationService = Depends(get_configuration_service)
):
    """Get a configuration by key, environment, and service."""
    try:
        config = await config_service.get_configuration(key, environment, service_name)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return ConfigurationResponse.model_validate(config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@config_router.get("/", response_model=ConfigurationListResponse)
async def list_configurations(
    query: ConfigurationQuery = Depends(),
    config_service: ConfigurationService = Depends(get_configuration_service)
):
    """List configurations with filtering and pagination."""
    try:
        configs = await config_service.search_configurations(
            pattern=query.key_pattern,
            environment=query.environment,
            service_name=query.service_name,
            limit=query.limit,
            offset=query.offset
        )
        
        # Convert to response models
        config_responses = [ConfigurationResponse.model_validate(config) for config in configs]
        
        return ConfigurationListResponse(
            configurations=config_responses,
            total=len(config_responses),
            limit=query.limit,
            offset=query.offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@config_router.get("/service/{service_name}", response_model=List[ConfigurationResponse])
async def get_configurations_by_service(
    service_name: str,
    environment: str = Query(..., description="Environment name"),
    config_service: ConfigurationService = Depends(get_configuration_service)
):
    """Get all configurations for a specific service."""
    try:
        configs = await config_service.get_configurations_by_service(service_name, environment)
        return [ConfigurationResponse.model_validate(config) for config in configs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@config_router.put("/{config_id}", response_model=ConfigurationResponse)
async def update_configuration(
    config_id: int,
    update: ConfigurationUpdate,
    config_service: ConfigurationService = Depends(get_configuration_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Update a configuration."""
    try:
        config = await config_service.update_configuration(
            id=config_id,
            update=update,
            changed_by=auth["user_email"]
        )
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return ConfigurationResponse.model_validate(config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@config_router.delete("/{config_id}")
async def delete_configuration(
    config_id: int,
    config_service: ConfigurationService = Depends(get_configuration_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Delete a configuration."""
    try:
        success = await config_service.delete_configuration(
            id=config_id,
            changed_by=auth["user_email"]
        )
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return {"message": "Configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@config_router.get("/{config_id}/history", response_model=List[ConfigurationHistoryResponse])
async def get_configuration_history(
    config_id: int,
    config_service: ConfigurationService = Depends(get_configuration_service)
):
    """Get configuration change history."""
    try:
        history = await config_service.get_configuration_history(config_id)
        return [ConfigurationHistoryResponse.model_validate(h) for h in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
