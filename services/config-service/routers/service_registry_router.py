"""
Service registry management router with registration, health updates, and discovery.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from services.service_registry_service import ServiceRegistryService
from models.service_registry_models import (
    ServiceRegistrationRequest,
    ServiceHealthUpdate,
    ServiceInfo,
    ServiceListResponse,
    ServiceDiscoveryResponse
)
from repositories.service_registry_repository import ServiceRegistryRepository
from middleware.auth_provider import AuthProvider, require_admin_permissions

# Create router with the new prefix
service_registry_router = APIRouter(prefix="/api/v1/registry", tags=["service-registry"])

# Create compatibility router for old path
service_registry_compat_router = APIRouter(prefix="/api/v1/services", tags=["service-registry"])


async def get_db_session():
    """Dependency to get database session."""
    from main import app
    session_factory = app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_service_registry_service(db: AsyncSession = Depends(get_db_session)) -> ServiceRegistryService:
    """Dependency to get service registry service."""
    from main import app
    cache_service = app.state.cache_service
    redis_client = app.state.redis_client
    notification_service = app.state.notification_service
    
    repository = ServiceRegistryRepository(db)
    return ServiceRegistryService(repository, cache_service, redis_client, notification_service)


# Define endpoint functions (will be registered with multiple routers)
async def register_service(
    request: ServiceRegistrationRequest,
    service: ServiceRegistryService = Depends(get_service_registry_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Register a new service or update existing service."""
    try:
        registered_service = await service.register_service(request)
        return ServiceInfo.model_validate(registered_service)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def get_service(
    service_name: str,
    service_registry: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Get service information by name."""
    try:
        service_info = await service_registry.get_service(service_name)
        if not service_info:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Handle cached dict vs ORM object
        if isinstance(service_info, dict):
            return ServiceInfo.model_validate(service_info)
        else:
            return ServiceInfo.model_validate(service_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def list_services(
    status: Optional[str] = Query(None, description="Filter by health status"),
    service_registry: ServiceRegistryService = Depends(get_service_registry_service)
):
    """List all registered services."""
    try:
        services = await service_registry.get_all_services(status)
        
        # Convert to response models
        service_responses = []
        for service in services:
            if isinstance(service, dict):
                service_responses.append(ServiceInfo.model_validate(service))
            else:
                service_responses.append(ServiceInfo.model_validate(service))
        
        return ServiceListResponse(
            services=service_responses,
            total=len(service_responses)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_healthy_services(
    service_registry: ServiceRegistryService = Depends(get_service_registry_service)
):
    """Get all healthy services for service discovery."""
    try:
        services = await service_registry.get_healthy_services()
        
        # Convert to response models
        service_responses = []
        for service in services:
            if isinstance(service, dict):
                service_responses.append(ServiceInfo.model_validate(service))
            else:
                service_responses.append(ServiceInfo.model_validate(service))
        
        return ServiceDiscoveryResponse(
            services=service_responses,
            total=len(service_responses)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def update_service_health(
    update: ServiceHealthUpdate,
    service_registry: ServiceRegistryService = Depends(get_service_registry_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Update service health status."""
    try:
        service = await service_registry.update_health(
            service_name=update.service_name,
            status=update.status,
            response_time=update.response_time
        )
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Handle cached dict vs ORM object
        if isinstance(service, dict):
            return ServiceInfo.model_validate(service)
        else:
            return ServiceInfo.model_validate(service)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def deregister_service(
    service_name: str,
    service_registry: ServiceRegistryService = Depends(get_service_registry_service),
    auth: dict = Depends(require_admin_permissions)
):
    """Deregister a service."""
    try:
        success = await service_registry.deregister_service(service_name)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
        return {"message": f"Service {service_name} deregistered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Register endpoints with main router (new path /api/v1/registry)
service_registry_router.add_api_route("/register", register_service, methods=["POST"], response_model=ServiceInfo)
service_registry_router.add_api_route("/{service_name}", get_service, methods=["GET"], response_model=ServiceInfo)
service_registry_router.add_api_route("/", list_services, methods=["GET"], response_model=ServiceListResponse)
service_registry_router.add_api_route("/healthy", get_healthy_services, methods=["GET"], response_model=ServiceDiscoveryResponse)
service_registry_router.add_api_route("/health", update_service_health, methods=["PUT"], response_model=ServiceInfo)
service_registry_router.add_api_route("/{service_name}", deregister_service, methods=["DELETE"])

# Register same endpoints with compatibility router (old path /api/v1/services)
service_registry_compat_router.add_api_route("/register", register_service, methods=["POST"], response_model=ServiceInfo)
service_registry_compat_router.add_api_route("/{service_name}", get_service, methods=["GET"], response_model=ServiceInfo)
service_registry_compat_router.add_api_route("/", list_services, methods=["GET"], response_model=ServiceListResponse)
service_registry_compat_router.add_api_route("/healthy", get_healthy_services, methods=["GET"], response_model=ServiceDiscoveryResponse)
service_registry_compat_router.add_api_route("/health", update_service_health, methods=["PUT"], response_model=ServiceInfo)
service_registry_compat_router.add_api_route("/{service_name}", deregister_service, methods=["DELETE"])
