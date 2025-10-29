"""
Async repository for service registry operations.

Following the pattern from services/asr-service/repositories/asr_repository.py
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from models.database_models import ServiceRegistryDB
from repositories.configuration_repository import DatabaseError

logger = logging.getLogger(__name__)


class ServiceRegistryRepository:
    """Async repository for service registry operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db
    
    async def register(
        self,
        service_name: str,
        service_url: str,
        health_check_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceRegistryDB:
        """Register or update service in registry."""
        try:
            # Check if service already exists
            result = await self.db.execute(
                select(ServiceRegistryDB).where(
                    ServiceRegistryDB.service_name == service_name
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing service
                existing.service_url = service_url
                existing.health_check_url = health_check_url
                if metadata is not None:
                    existing.service_metadata = metadata
                
                await self.db.commit()
                await self.db.refresh(existing)
                
                logger.info(f"Updated service registry entry for {service_name}")
                return existing
            else:
                # Create new service
                service = ServiceRegistryDB(
                    service_name=service_name,
                    service_url=service_url,
                    health_check_url=health_check_url,
                    status='unknown',
                    service_metadata=metadata
                )
                
                self.db.add(service)
                await self.db.commit()
                await self.db.refresh(service)
                
                logger.info(f"Registered service {service_name}")
                return service
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to register service: {e}")
            raise DatabaseError(f"Failed to register service: {e}")
    
    async def get_by_name(self, service_name: str) -> Optional[ServiceRegistryDB]:
        """Retrieve specific service by name."""
        try:
            result = await self.db.execute(
                select(ServiceRegistryDB).where(
                    ServiceRegistryDB.service_name == service_name
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get service by name: {e}")
            raise DatabaseError(f"Failed to get service: {e}")
    
    async def get_all(self, status_filter: Optional[str] = None) -> List[ServiceRegistryDB]:
        """Get all services, optionally filtered by status."""
        try:
            query = select(ServiceRegistryDB)
            if status_filter:
                query = query.where(ServiceRegistryDB.status == status_filter)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get all services: {e}")
            raise DatabaseError(f"Failed to get services: {e}")
    
    async def get_healthy_services(self) -> List[ServiceRegistryDB]:
        """Get only healthy services for discovery."""
        try:
            result = await self.db.execute(
                select(ServiceRegistryDB).where(
                    ServiceRegistryDB.status == 'healthy'
                )
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get healthy services: {e}")
            raise DatabaseError(f"Failed to get healthy services: {e}")
    
    async def update_health(
        self,
        service_name: str,
        status: str,
        response_time: Optional[float] = None
    ) -> Optional[ServiceRegistryDB]:
        """Update health status and last_health_check timestamp."""
        try:
            result = await self.db.execute(
                select(ServiceRegistryDB).where(
                    ServiceRegistryDB.service_name == service_name
                )
            )
            service = result.scalar_one_or_none()
            
            if not service:
                logger.warning(f"Service {service_name} not found")
                return None
            
            service.status = status
            service.last_health_check = datetime.utcnow()
            
            # Update metadata with response time if provided
            if response_time is not None:
                if service.service_metadata is None:
                    service.service_metadata = {}
                elif not isinstance(service.service_metadata, dict):
                    service.service_metadata = {}
                service.service_metadata['avg_response_time'] = response_time
            
            await self.db.commit()
            await self.db.refresh(service)
            
            logger.info(f"Updated health status for {service_name}: {status}")
            return service
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update health for {service_name}: {e}")
            raise DatabaseError(f"Failed to update health: {e}")
    
    async def deregister(self, service_name: str) -> bool:
        """Remove service from registry."""
        try:
            result = await self.db.execute(
                select(ServiceRegistryDB).where(
                    ServiceRegistryDB.service_name == service_name
                )
            )
            service = result.scalar_one_or_none()
            
            if not service:
                logger.warning(f"Service {service_name} not found")
                return False
            
            await self.db.delete(service)
            await self.db.commit()
            
            logger.info(f"Deregistered service {service_name}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to deregister service {service_name}: {e}")
            raise DatabaseError(f"Failed to deregister service: {e}")
    
    async def update_metadata(
        self,
        service_name: str,
        metadata: Dict[str, Any]
    ) -> Optional[ServiceRegistryDB]:
        """Update service metadata."""
        try:
            result = await self.db.execute(
                select(ServiceRegistryDB).where(
                    ServiceRegistryDB.service_name == service_name
                )
            )
            service = result.scalar_one_or_none()
            
            if not service:
                logger.warning(f"Service {service_name} not found")
                return None
            
            # Merge metadata if existing
            if service.service_metadata and isinstance(service.service_metadata, dict):
                service.service_metadata.update(metadata)
            else:
                service.service_metadata = metadata
            
            await self.db.commit()
            await self.db.refresh(service)
            
            logger.info(f"Updated metadata for {service_name}")
            return service
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update metadata for {service_name}: {e}")
            raise DatabaseError(f"Failed to update metadata: {e}")

