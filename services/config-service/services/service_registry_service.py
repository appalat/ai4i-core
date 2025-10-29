"""Business logic for service discovery."""

import logging
import os
import json
from typing import Optional, List, Dict, Any
from repositories.service_registry_repository import ServiceRegistryRepository
from services.cache_service import CacheService
from services.notification_service import NotificationService
from models.service_registry_models import ServiceRegistrationRequest, ServiceHealthUpdate
from models.database_models import ServiceRegistryDB

logger = logging.getLogger(__name__)
SERVICE_REGISTRY_TTL = int(os.getenv("SERVICE_REGISTRY_TTL", "300"))


class ServiceRegistryService:
    """Business logic for service discovery."""
    
    def __init__(self, repository, cache_service, redis_client, notification_service):
        self.repository = repository
        self.cache_service = cache_service
        self.redis_client = redis_client
        self.notification_service = notification_service
    
    def _convert_metadata(self, metadata) -> Optional[Dict[str, Any]]:
        """Convert metadata to dict or None, handling SQLAlchemy types."""
        if metadata is None:
            return None
        if isinstance(metadata, dict):
            return metadata
        # Handle SQLAlchemy types or other cases
        try:
            return dict(metadata) if metadata else None
        except (TypeError, ValueError):
            return None
    
    async def register_service(self, request: ServiceRegistrationRequest) -> ServiceRegistryDB:
        """Register or update service in DB and Redis."""
        try:
            service = await self.repository.register(request.service_name, request.service_url,
                request.health_check_url, request.metadata)
            
            # Convert service to dict for caching
            service_dict = {
                "id": service.id,
                "service_name": service.service_name,
                "service_url": service.service_url,
                "health_check_url": service.health_check_url,
                "status": service.status,
                "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None,
                "metadata": self._convert_metadata(service.service_metadata),
                "registered_at": service.registered_at.isoformat(),
                "updated_at": service.updated_at.isoformat()
            }
            
            # Write to Redis using API Gateway pattern
            instance_data = {
                "instance_id": f"{request.service_name}-1",
                "url": request.service_url,
                "health_status": service.status,
                "last_check_timestamp": service.updated_at.isoformat() if service.updated_at else None,
                "avg_response_time": service.service_metadata.get("avg_response_time", 0) if service.service_metadata else 0,
                "consecutive_failures": 0
            }
            await self.redis_client.setex(f"service:{request.service_name}:instances", SERVICE_REGISTRY_TTL, json.dumps(instance_data))
            await self.redis_client.setex(f"service:{request.service_name}:active", SERVICE_REGISTRY_TTL, "1")
            await self.cache_service.set(f"service_info:{request.service_name}", service_dict, ttl=SERVICE_REGISTRY_TTL)
            
            # Publish event
            await self.notification_service.publish_service_registry_update(
                action="register",
                service_name=request.service_name,
                status=service.status
            )
            
            return service
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            raise
    
    async def get_service(self, service_name: str) -> Optional[dict]:
        """Retrieve service from cache or DB."""
        try:
            cached = await self.cache_service.get(f"service_info:{service_name}")
            if cached:
                return cached
            
            service = await self.repository.get_by_name(service_name)
            if service:
                # Convert to dict for consistent return type
                service_dict = {
                    "id": service.id,
                    "service_name": service.service_name,
                    "service_url": service.service_url,
                    "health_check_url": service.health_check_url,
                    "status": service.status,
                    "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None,
                    "metadata": self._convert_metadata(service.service_metadata),
                    "registered_at": service.registered_at.isoformat(),
                    "updated_at": service.updated_at.isoformat()
                }
                # Cache the dict
                await self.cache_service.set(f"service_info:{service_name}", service_dict, ttl=SERVICE_REGISTRY_TTL)
                return service_dict
            
            return None
        except Exception as e:
            logger.error(f"Failed to get service: {e}")
            raise
    
    async def get_all_services(self, status_filter: Optional[str] = None) -> List[dict]:
        """List all services."""
        try:
            services = await self.repository.get_all(status_filter)
            # Convert ORM objects to dicts for consistent response
            service_dicts = []
            for service in services:
                service_dict = {
                    "id": service.id,
                    "service_name": service.service_name,
                    "service_url": service.service_url,
                    "health_check_url": service.health_check_url,
                    "status": service.status,
                    "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None,
                    "metadata": self._convert_metadata(service.service_metadata),
                    "registered_at": service.registered_at.isoformat(),
                    "updated_at": service.updated_at.isoformat()
                }
                service_dicts.append(service_dict)
            return service_dicts
        except Exception as e:
            logger.error(f"Failed to get all services: {e}")
            raise
    
    async def get_healthy_services(self) -> List[dict]:
        """Get only healthy services."""
        try:
            cached = await self.cache_service.get("healthy_services")
            if cached:
                return cached
            
            services = await self.repository.get_healthy_services()
            # Convert to list of dicts
            service_dicts = []
            for service in services:
                service_dict = {
                    "id": service.id,
                    "service_name": service.service_name,
                    "service_url": service.service_url,
                    "health_check_url": service.health_check_url,
                    "status": service.status,
                    "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None,
                    "metadata": self._convert_metadata(service.service_metadata),
                    "registered_at": service.registered_at.isoformat(),
                    "updated_at": service.updated_at.isoformat()
                }
                service_dicts.append(service_dict)
            
            await self.cache_service.set("healthy_services", service_dicts, ttl=30)
            return service_dicts
        except Exception as e:
            logger.error(f"Failed to get healthy services: {e}")
            raise
    
    async def update_health(self, service_name: str, status: str, response_time: Optional[float] = None) -> Optional[dict]:
        """Update health status in DB and Redis."""
        try:
            service = await self.repository.update_health(service_name, status, response_time)
            if service:
                # Convert to dict for consistent return type
                service_dict = {
                    "id": service.id,
                    "service_name": service.service_name,
                    "service_url": service.service_url,
                    "health_check_url": service.health_check_url,
                    "status": service.status,
                    "last_health_check": service.last_health_check.isoformat() if service.last_health_check else None,
                    "metadata": self._convert_metadata(service.service_metadata),
                    "registered_at": service.registered_at.isoformat(),
                    "updated_at": service.updated_at.isoformat()
                }
                
                instance_data = {
                    "instance_id": f"{service_name}-1", 
                    "url": service.service_url,
                    "health_status": status, 
                    "last_check_timestamp": service.last_health_check.isoformat() if service.last_health_check else None,
                    "avg_response_time": response_time or 0, 
                    "consecutive_failures": 0
                }
                await self.redis_client.setex(f"service:{service_name}:instances", SERVICE_REGISTRY_TTL, json.dumps(instance_data))
                await self.redis_client.setex(f"service:{service_name}:active", SERVICE_REGISTRY_TTL, "1" if status == "healthy" else "0")
                await self.cache_service.delete_pattern(f"service_info:{service_name}*")
                await self.cache_service.delete("healthy_services")
                
                # Publish event
                await self.notification_service.publish_service_registry_update(
                    action="health_update",
                    service_name=service_name,
                    status=status
                )
                
                return service_dict
            return None
        except Exception as e:
            logger.error(f"Failed to update health: {e}")
            raise
    
    async def deregister_service(self, service_name: str) -> bool:
        """Deregister a service."""
        try:
            success = await self.repository.deregister(service_name)
            if success:
                # Clean up cache and Redis
                await self.cache_service.delete_pattern(f"service_info:{service_name}*")
                await self.cache_service.delete("healthy_services")
                await self.redis_client.delete(f"service:{service_name}:instances")
                await self.redis_client.delete(f"service:{service_name}:active")
                
                # Publish event
                await self.notification_service.publish_service_registry_update(
                    action="deregister",
                    service_name=service_name,
                    status="deregistered"
                )
            
            return success
        except Exception as e:
            logger.error(f"Failed to deregister service: {e}")
            raise

