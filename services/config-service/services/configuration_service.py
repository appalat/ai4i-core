"""
Business logic for configuration management.

Following the pattern from services/asr-service/services/asr_service.py
"""

import logging
import os
from typing import Optional, List
from repositories.configuration_repository import ConfigurationRepository
from services.cache_service import CacheService
from services.notification_service import NotificationService
from models.config_models import ConfigurationRequest, ConfigurationUpdate, ConfigurationResponse
from models.database_models import ConfigurationDB, ConfigurationHistoryDB
from utils.encryption_utils import encrypt_value, decrypt_value, redact_sensitive_value

logger = logging.getLogger(__name__)

# Configuration
CONFIG_CACHE_TTL = int(os.getenv("CONFIG_CACHE_TTL", "300"))


class ConfigurationService:
    """Business logic for configuration management."""
    
    def __init__(
        self,
        repository: ConfigurationRepository,
        cache_service: CacheService,
        notification_service: NotificationService
    ):
        """Initialize configuration service with dependencies."""
        self.repository = repository
        self.cache_service = cache_service
        self.notification_service = notification_service
    
    async def create_configuration(
        self,
        request: ConfigurationRequest,
        changed_by: str
    ) -> ConfigurationDB:
        """Validate and create configuration, invalidate cache, publish event."""
        try:
            # Handle encryption if enabled and requested
            value_to_store = request.value
            is_encrypted = request.is_encrypted
            
            if request.is_encrypted:
                encrypted_value = encrypt_value(request.value)
                if encrypted_value:
                    value_to_store = encrypted_value
                    is_encrypted = True
                else:
                    logger.warning(f"Encryption failed for key {request.key}, storing unencrypted")
                    is_encrypted = False
            
            # Create configuration
            config = await self.repository.create(
                key=request.key,
                value=value_to_store,
                environment=request.environment,
                service_name=request.service_name,
                description=request.description,
                is_encrypted=is_encrypted,
                changed_by=changed_by
            )
            
            # Invalidate cache
            cache_pattern = f"config:{request.environment}:{request.service_name}:{request.key}"
            await self.cache_service.delete(cache_pattern)
            
            # Publish event with redacted value
            await self.notification_service.publish_config_update(
                action="create",
                key=request.key,
                environment=request.environment,
                service_name=request.service_name,
                value=redact_sensitive_value(request.value, is_encrypted)
            )
            
            logger.info(f"Created configuration: {request.key}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            raise
    
    async def get_configuration(
        self,
        key: str,
        environment: str,
        service_name: str
    ) -> Optional[ConfigurationResponse]:
        """Check cache first, fallback to DB, populate cache."""
        try:
            # Check cache
            cache_key = f"config:{environment}:{service_name}:{key}"
            cached = await self.cache_service.get(cache_key)
            
            if cached:
                logger.debug(f"Cache hit for configuration: {key}")
                # Handle decryption if needed
                if cached.get("is_encrypted", False):
                    decrypted_value = decrypt_value(cached["value"])
                    if decrypted_value:
                        cached["value"] = decrypted_value
                    else:
                        logger.warning(f"Decryption failed for cached key {key}")
                return ConfigurationResponse.model_validate(cached)
            
            # Query database
            config = await self.repository.get_by_key(key, environment, service_name)
            
            if config:
                # Handle decryption if needed
                value_to_return = config.value
                if config.is_encrypted:
                    decrypted_value = decrypt_value(config.value)
                    if decrypted_value:
                        value_to_return = decrypted_value
                    else:
                        logger.warning(f"Decryption failed for key {key}")
                
                # Convert to dict for caching
                config_dict = {
                    "id": config.id,
                    "key": config.key,
                    "value": value_to_return,  # Return decrypted value
                    "environment": config.environment,
                    "service_name": config.service_name,
                    "description": config.description,
                    "is_encrypted": config.is_encrypted,
                    "version": config.version,
                    "created_at": config.created_at.isoformat(),
                    "updated_at": config.updated_at.isoformat()
                }
                # Populate cache
                await self.cache_service.set(cache_key, config_dict, ttl=CONFIG_CACHE_TTL)
                return ConfigurationResponse.model_validate(config_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            raise
    
    async def get_configurations_by_service(
        self,
        service_name: str,
        environment: str
    ) -> List[ConfigurationDB]:
        """Retrieve all configs for a service with caching."""
        try:
            configs = await self.repository.get_by_service(service_name, environment)
            return configs
        except Exception as e:
            logger.error(f"Failed to get configurations by service: {e}")
            raise
    
    async def update_configuration(
        self,
        id: int,
        update: ConfigurationUpdate,
        changed_by: str
    ) -> Optional[ConfigurationDB]:
        """Update config, invalidate cache, publish event, create history."""
        try:
            # Get existing config to know the key
            from sqlalchemy import select
            result = await self.repository.db.execute(
                select(ConfigurationDB).where(ConfigurationDB.id == id)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                return None
            
            # Update configuration
            config = await self.repository.update(
                id=id,
                value=update.value,
                is_encrypted=update.is_encrypted,
                description=update.description,
                changed_by=changed_by
            )
            
            # Invalidate cache
            cache_pattern = f"config:{existing.environment}:{existing.service_name}:{existing.key}"
            await self.cache_service.delete(cache_pattern)
            
            # Publish event
            await self.notification_service.publish_config_update(
                action="update",
                key=existing.key,
                environment=existing.environment,
                service_name=existing.service_name
            )
            
            logger.info(f"Updated configuration: {existing.key}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise
    
    async def delete_configuration(
        self,
        id: int,
        changed_by: str
    ) -> bool:
        """Delete config, invalidate cache, publish event."""
        try:
            # Get existing config to know the key
            from sqlalchemy import select
            result = await self.repository.db.execute(
                select(ConfigurationDB).where(ConfigurationDB.id == id)
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                return False
            
            # Delete configuration
            success = await self.repository.delete(id, changed_by)
            
            # Invalidate cache
            if success:
                cache_pattern = f"config:{existing.environment}:{existing.service_name}:{existing.key}"
                await self.cache_service.delete(cache_pattern)
                
                # Publish event
                await self.notification_service.publish_config_update(
                    action="delete",
                    key=existing.key,
                    environment=existing.environment,
                    service_name=existing.service_name
                )
            
            logger.info(f"Deleted configuration: {existing.key}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete configuration: {e}")
            raise
    
    async def get_configuration_history(
        self,
        config_id: int
    ) -> List[ConfigurationHistoryDB]:
        """Retrieve audit trail."""
        try:
            history = await self.repository.get_history(config_id)
            return history
        except Exception as e:
            logger.error(f"Failed to get configuration history: {e}")
            raise
    
    async def search_configurations(
        self,
        pattern: Optional[str] = None,
        environment: Optional[str] = None,
        service_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConfigurationDB]:
        """Search with pattern matching."""
        try:
            configs = await self.repository.search(
                key_pattern=pattern,
                environment=environment,
                service_name=service_name,
                limit=limit,
                offset=offset
            )
            return configs
        except Exception as e:
            logger.error(f"Failed to search configurations: {e}")
            raise

