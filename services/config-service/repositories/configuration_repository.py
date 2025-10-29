"""
Async repository for configuration operations.

Following the pattern from services/asr-service/repositories/asr_repository.py
"""

import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from models.database_models import ConfigurationDB, ConfigurationHistoryDB

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class ConfigurationRepository:
    """Async repository for configuration operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db
    
    async def create(
        self,
        key: str,
        value: str,
        environment: str,
        service_name: str,
        description: Optional[str] = None,
        is_encrypted: bool = False,
        changed_by: Optional[str] = None
    ) -> ConfigurationDB:
        """Create new configuration or increment version if exists."""
        try:
            # Check if configuration already exists
            result = await self.db.execute(
                select(ConfigurationDB).where(
                    ConfigurationDB.key == key,
                    ConfigurationDB.environment == environment,
                    ConfigurationDB.service_name == service_name
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Increment version and update
                existing.version += 1
                old_value = existing.value
                existing.value = value
                existing.is_encrypted = is_encrypted
                if description:
                    existing.description = description
                
                # Create history entry
                history = ConfigurationHistoryDB(
                    configuration_id=existing.id,
                    old_value=old_value,
                    new_value=value,
                    changed_by=changed_by
                )
                self.db.add(history)
                
                await self.db.commit()
                await self.db.refresh(existing)
                
                logger.info(f"Updated configuration {existing.id} (key={key}) to version {existing.version}")
                return existing
            else:
                # Create new configuration
                config = ConfigurationDB(
                    key=key,
                    value=value,
                    environment=environment,
                    service_name=service_name,
                    description=description,
                    is_encrypted=is_encrypted,
                    version=1
                )
                
                self.db.add(config)
                await self.db.commit()
                await self.db.refresh(config)
                
                # Create initial history entry
                history = ConfigurationHistoryDB(
                    configuration_id=config.id,
                    old_value=None,
                    new_value=value,
                    changed_by=changed_by
                )
                self.db.add(history)
                await self.db.commit()
                
                logger.info(f"Created configuration {config.id} (key={key})")
                return config
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create configuration: {e}")
            raise DatabaseError(f"Failed to create configuration: {e}")
    
    async def get_by_key(
        self,
        key: str,
        environment: str,
        service_name: str
    ) -> Optional[ConfigurationDB]:
        """Retrieve specific configuration by key."""
        try:
            result = await self.db.execute(
                select(ConfigurationDB).where(
                    ConfigurationDB.key == key,
                    ConfigurationDB.environment == environment,
                    ConfigurationDB.service_name == service_name
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get configuration by key: {e}")
            raise DatabaseError(f"Failed to get configuration: {e}")
    
    async def get_by_service(
        self,
        service_name: str,
        environment: str
    ) -> List[ConfigurationDB]:
        """Get all configurations for a service in an environment."""
        try:
            result = await self.db.execute(
                select(ConfigurationDB).where(
                    ConfigurationDB.service_name == service_name,
                    ConfigurationDB.environment == environment
                )
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get configurations by service: {e}")
            raise DatabaseError(f"Failed to get configurations: {e}")
    
    async def get_all(
        self,
        environment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConfigurationDB]:
        """Get paginated list of configurations."""
        try:
            query = select(ConfigurationDB)
            if environment:
                query = query.where(ConfigurationDB.environment == environment)
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get all configurations: {e}")
            raise DatabaseError(f"Failed to get configurations: {e}")
    
    async def update(
        self,
        id: int,
        value: Optional[str] = None,
        is_encrypted: Optional[bool] = None,
        description: Optional[str] = None,
        changed_by: Optional[str] = None
    ) -> Optional[ConfigurationDB]:
        """Update configuration value."""
        try:
            result = await self.db.execute(
                select(ConfigurationDB).where(ConfigurationDB.id == id)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                logger.warning(f"Configuration {id} not found")
                return None
            
            old_value = config.value
            
            # Update fields
            if value is not None:
                config.value = value
                config.version += 1
            if is_encrypted is not None:
                config.is_encrypted = is_encrypted
            if description is not None:
                config.description = description
            
            # Create history entry
            history = ConfigurationHistoryDB(
                configuration_id=config.id,
                old_value=old_value,
                new_value=config.value,
                changed_by=changed_by
            )
            self.db.add(history)
            
            await self.db.commit()
            await self.db.refresh(config)
            
            logger.info(f"Updated configuration {id}")
            return config
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update configuration {id}: {e}")
            raise DatabaseError(f"Failed to update configuration: {e}")
    
    async def delete(
        self,
        id: int,
        changed_by: Optional[str] = None
    ) -> bool:
        """Delete configuration."""
        try:
            result = await self.db.execute(
                select(ConfigurationDB).where(ConfigurationDB.id == id)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                logger.warning(f"Configuration {id} not found")
                return False
            
            # Create history entry before delete
            history = ConfigurationHistoryDB(
                configuration_id=config.id,
                old_value=config.value,
                new_value=None,
                changed_by=changed_by
            )
            self.db.add(history)
            
            await self.db.delete(config)
            await self.db.commit()
            
            logger.info(f"Deleted configuration {id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete configuration {id}: {e}")
            raise DatabaseError(f"Failed to delete configuration: {e}")
    
    async def get_history(
        self,
        configuration_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConfigurationHistoryDB]:
        """Retrieve audit trail for a configuration."""
        try:
            result = await self.db.execute(
                select(ConfigurationHistoryDB)
                .where(ConfigurationHistoryDB.configuration_id == configuration_id)
                .order_by(ConfigurationHistoryDB.changed_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get configuration history: {e}")
            raise DatabaseError(f"Failed to get history: {e}")
    
    async def search(
        self,
        key_pattern: Optional[str] = None,
        environment: Optional[str] = None,
        service_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConfigurationDB]:
        """Search configurations with pattern matching."""
        try:
            query = select(ConfigurationDB)
            
            if key_pattern:
                query = query.where(ConfigurationDB.key.like(f"%{key_pattern}%"))
            if environment:
                query = query.where(ConfigurationDB.environment == environment)
            if service_name:
                query = query.where(ConfigurationDB.service_name == service_name)
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to search configurations: {e}")
            raise DatabaseError(f"Failed to search configurations: {e}")

