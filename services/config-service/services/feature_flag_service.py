"""Business logic for feature flag management."""

import logging
import hashlib
import os
from typing import Optional, List
from repositories.feature_flag_repository import FeatureFlagRepository
from services.cache_service import CacheService
from services.notification_service import NotificationService
from models.feature_flag_models import FeatureFlagRequest, FeatureFlagUpdate, FeatureFlagResponse
from models.database_models import FeatureFlagDB

logger = logging.getLogger(__name__)
FEATURE_FLAG_CACHE_TTL = int(os.getenv("FEATURE_FLAG_CACHE_TTL", "300"))


class FeatureFlagService:
    """Business logic for feature flag management."""
    
    def __init__(self, repository, cache_service, notification_service):
        self.repository = repository
        self.cache_service = cache_service
        self.notification_service = notification_service
    
    async def create_feature_flag(self, request: FeatureFlagRequest) -> FeatureFlagDB:
        """Create new feature flag, cache it, publish event."""
        try:
            flag = await self.repository.create(
                name=request.name, description=request.description,
                is_enabled=request.is_enabled, rollout_percentage=request.rollout_percentage,
                target_users=request.target_users, environment=request.environment
            )
            cache_key = f"feature_flag:{request.name}:{request.environment}"
            await self.cache_service.set(cache_key, {"id": flag.id, "name": flag.name,
                "description": flag.description, "is_enabled": flag.is_enabled,
                "rollout_percentage": float(flag.rollout_percentage), "target_users": flag.target_users,
                "environment": flag.environment, "created_at": flag.created_at.isoformat(),
                "updated_at": flag.updated_at.isoformat()}, ttl=FEATURE_FLAG_CACHE_TTL)
            await self.notification_service.publish_feature_flag_update(
                action="create", name=request.name, environment=request.environment, is_enabled=request.is_enabled)
            logger.info(f"Created feature flag: {request.name}")
            return flag
        except Exception as e:
            logger.error(f"Failed to create feature flag: {e}")
            raise
    
    async def get_feature_flag(self, name: str, environment: str) -> Optional[FeatureFlagResponse]:
        """Check cache, fallback to DB, populate cache."""
        try:
            cache_key = f"feature_flag:{name}:{environment}"
            cached = await self.cache_service.get(cache_key)
            if cached:
                return FeatureFlagResponse.model_validate(cached)
            
            flag = await self.repository.get_by_name(name, environment)
            if flag:
                # Convert to dict for caching
                flag_dict = {
                    "id": flag.id,
                    "name": flag.name,
                    "description": flag.description,
                    "is_enabled": flag.is_enabled,
                    "rollout_percentage": float(flag.rollout_percentage),
                    "target_users": flag.target_users,
                    "environment": flag.environment,
                    "created_at": flag.created_at.isoformat(),
                    "updated_at": flag.updated_at.isoformat()
                }
                await self.cache_service.set(cache_key, flag_dict, ttl=FEATURE_FLAG_CACHE_TTL)
                return FeatureFlagResponse.model_validate(flag_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to get feature flag: {e}")
            raise
    
    async def get_all_feature_flags(self, environment: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[FeatureFlagDB]:
        """List all feature flags."""
        try:
            flags = await self.repository.get_all(environment, limit, offset)
            return flags
        except Exception as e:
            logger.error(f"Failed to get feature flags: {e}")
            raise
    
    async def update_feature_flag(self, id: int, update: FeatureFlagUpdate) -> Optional[FeatureFlagDB]:
        """Update flag, invalidate cache, publish event."""
        try:
            flag = await self.repository.update(id, is_enabled=update.is_enabled,
                rollout_percentage=update.rollout_percentage, target_users=update.target_users,
                description=update.description)
            if flag:
                cache_key = f"feature_flag:{flag.name}:{flag.environment}"
                await self.cache_service.delete(cache_key)
                await self.notification_service.publish_feature_flag_update(
                    action="update", name=flag.name, environment=flag.environment, is_enabled=flag.is_enabled)
            return flag
        except Exception as e:
            logger.error(f"Failed to update feature flag: {e}")
            raise
    
    async def delete_feature_flag(self, id: int) -> bool:
        """Delete flag, invalidate cache, publish event."""
        try:
            from sqlalchemy import select
            result = await self.repository.db.execute(select(FeatureFlagDB).where(FeatureFlagDB.id == id))
            existing = result.scalar_one_or_none()
            if not existing:
                return False
            success = await self.repository.delete(id)
            if success:
                cache_key = f"feature_flag:{existing.name}:{existing.environment}"
                await self.cache_service.delete(cache_key)
                await self.notification_service.publish_feature_flag_update(
                    action="delete", name=existing.name, environment=existing.environment, is_enabled=existing.is_enabled)
            return success
        except Exception as e:
            logger.error(f"Failed to delete feature flag: {e}")
            raise
    
    async def evaluate_feature_flag(self, name: str, environment: str, user_id: Optional[str] = None):
        """Evaluate feature flag for a user."""
        try:
            flag = await self.get_feature_flag(name, environment)
            if not flag:
                return {"enabled": False, "reason": "flag_not_found"}
            if not flag.is_enabled and flag.rollout_percentage == 0:
                return {"enabled": False, "reason": "globally_disabled"}
            if flag.target_users and user_id and user_id in flag.target_users:
                return {"enabled": True, "reason": "user_targeted"}
            if user_id and flag.rollout_percentage > 0:
                hash_val = int(hashlib.md5(f"{name}{user_id}".encode()).hexdigest(), 16)
                percentage = (hash_val % 100)
                if percentage < flag.rollout_percentage:
                    return {"enabled": True, "reason": f"rollout_percentage_{flag.rollout_percentage}"}
            return {"enabled": flag.is_enabled, "reason": "globally_enabled"}
        except Exception as e:
            logger.error(f"Failed to evaluate feature flag: {e}")
            raise

