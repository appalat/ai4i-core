"""
Async repository for feature flag operations.

Following the pattern from services/asr-service/repositories/asr_repository.py
"""

import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database_models import FeatureFlagDB
from repositories.configuration_repository import DatabaseError

logger = logging.getLogger(__name__)


class FeatureFlagRepository:
    """Async repository for feature flag operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db
    
    async def create(
        self,
        name: str,
        description: Optional[str],
        is_enabled: bool,
        rollout_percentage: float,
        target_users: Optional[List[str]],
        environment: str
    ) -> FeatureFlagDB:
        """Create new feature flag."""
        try:
            flag = FeatureFlagDB(
                name=name,
                description=description,
                is_enabled=is_enabled,
                rollout_percentage=rollout_percentage,
                target_users=target_users,
                environment=environment
            )
            
            self.db.add(flag)
            await self.db.commit()
            await self.db.refresh(flag)
            
            logger.info(f"Created feature flag {flag.id} (name={name})")
            return flag
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create feature flag: {e}")
            raise DatabaseError(f"Failed to create feature flag: {e}")
    
    async def get_by_name(
        self,
        name: str,
        environment: str
    ) -> Optional[FeatureFlagDB]:
        """Retrieve specific feature flag by name."""
        try:
            result = await self.db.execute(
                select(FeatureFlagDB).where(
                    FeatureFlagDB.name == name,
                    FeatureFlagDB.environment == environment
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get feature flag by name: {e}")
            raise DatabaseError(f"Failed to get feature flag: {e}")
    
    async def get_all(
        self,
        environment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FeatureFlagDB]:
        """Get paginated list of feature flags."""
        try:
            query = select(FeatureFlagDB)
            if environment:
                query = query.where(FeatureFlagDB.environment == environment)
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get all feature flags: {e}")
            raise DatabaseError(f"Failed to get feature flags: {e}")
    
    async def update(
        self,
        id: int,
        is_enabled: Optional[bool] = None,
        rollout_percentage: Optional[float] = None,
        target_users: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> Optional[FeatureFlagDB]:
        """Update feature flag settings."""
        try:
            result = await self.db.execute(
                select(FeatureFlagDB).where(FeatureFlagDB.id == id)
            )
            flag = result.scalar_one_or_none()
            
            if not flag:
                logger.warning(f"Feature flag {id} not found")
                return None
            
            # Update fields
            if is_enabled is not None:
                flag.is_enabled = is_enabled
            if rollout_percentage is not None:
                flag.rollout_percentage = rollout_percentage
            if target_users is not None:
                flag.target_users = target_users
            if description is not None:
                flag.description = description
            
            await self.db.commit()
            await self.db.refresh(flag)
            
            logger.info(f"Updated feature flag {id}")
            return flag
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update feature flag {id}: {e}")
            raise DatabaseError(f"Failed to update feature flag: {e}")
    
    async def delete(
        self,
        id: int
    ) -> bool:
        """Delete feature flag."""
        try:
            result = await self.db.execute(
                select(FeatureFlagDB).where(FeatureFlagDB.id == id)
            )
            flag = result.scalar_one_or_none()
            
            if not flag:
                logger.warning(f"Feature flag {id} not found")
                return False
            
            await self.db.delete(flag)
            await self.db.commit()
            
            logger.info(f"Deleted feature flag {id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete feature flag {id}: {e}")
            raise DatabaseError(f"Failed to delete feature flag: {e}")
    
    async def get_enabled_flags(
        self,
        environment: str
    ) -> List[FeatureFlagDB]:
        """Get all enabled feature flags for an environment."""
        try:
            result = await self.db.execute(
                select(FeatureFlagDB).where(
                    FeatureFlagDB.environment == environment,
                    FeatureFlagDB.is_enabled == True
                )
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get enabled feature flags: {e}")
            raise DatabaseError(f"Failed to get enabled flags: {e}")
    
    async def get_flags_for_user(
        self,
        user_id: str,
        environment: str
    ) -> List[FeatureFlagDB]:
        """Get feature flags applicable to a specific user."""
        try:
            # Get flags where user is in target_users list or rollout percentage > 0
            result = await self.db.execute(
                select(FeatureFlagDB).where(
                    FeatureFlagDB.environment == environment
                )
            )
            all_flags = result.scalars().all()
            
            # Filter flags that apply to this user
            applicable_flags = []
            for flag in all_flags:
                if flag.target_users and user_id in flag.target_users:
                    applicable_flags.append(flag)
                elif flag.rollout_percentage > 0:
                    applicable_flags.append(flag)
            
            return applicable_flags
            
        except Exception as e:
            logger.error(f"Failed to get feature flags for user {user_id}: {e}")
            raise DatabaseError(f"Failed to get flags for user: {e}")

