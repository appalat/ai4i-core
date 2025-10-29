"""
Authentication provider for config-service routes with API key validation.
"""

from fastapi import Request, Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)


def get_api_key_from_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract API key from Authorization header."""
    if not authorization:
        return None
    
    # Support formats: "Bearer <key>", "<key>", "ApiKey <key>"
    if authorization.startswith("Bearer "):
        return authorization[7:]
    elif authorization.startswith("ApiKey "):
        return authorization[7:]
    else:
        return authorization


def hash_api_key(api_key: str) -> str:
    """Hash API key using SHA256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_db_session():
    """Dependency to get database session."""
    from main import app
    session_factory = app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def AuthProvider(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_auth_source: str = Header(default="API_KEY", alias="X-Auth-Source"),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Authentication provider dependency for FastAPI routes."""
    
    # Check if authentication is disabled
    auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    require_api_key = os.getenv("REQUIRE_API_KEY", "true").lower() == "true"
    allow_anonymous = os.getenv("ALLOW_ANONYMOUS_ACCESS", "false").lower() == "true"
    
    # If authentication is disabled or anonymous access is allowed, skip auth
    if not auth_enabled or (allow_anonymous and not require_api_key):
        # Populate request state with anonymous context
        request.state.user_id = None
        request.state.api_key_id = None
        request.state.api_key_name = None
        request.state.user_email = None
        request.state.is_authenticated = False
        
        return {
            "user_id": None,
            "api_key_id": None,
            "user": None,
            "api_key": None
        }
    
    try:
        # Extract API key from authorization header
        api_key = get_api_key_from_header(authorization)
        
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        
        # For now, implement a simple API key validation
        # In a real implementation, this would validate against a database
        valid_api_keys = {
            "admin": "admin@example.com",
            "service": "service@example.com"
        }
        
        if api_key not in valid_api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Populate request state with auth context
        request.state.user_id = api_key
        request.state.api_key_id = api_key
        request.state.api_key_name = api_key
        request.state.user_email = valid_api_keys[api_key]
        request.state.is_authenticated = True
        
        # Return auth context
        user_email = valid_api_keys[api_key]
        return {
            "user_id": api_key,
            "api_key_id": api_key,
            "user_email": user_email, 
            "user": {"email": user_email},
            "api_key": {"name": api_key}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def OptionalAuthProvider(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_auth_source: str = Header(default="API_KEY", alias="X-Auth-Source"),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[Dict[str, Any]]:
    """Optional authentication provider that doesn't raise exception if no auth provided."""
    try:
        return await AuthProvider(request, authorization, x_auth_source, db)
    except HTTPException:
        # Return None for optional auth
        return None


def require_admin_permissions(auth: Dict[str, Any] = Depends(AuthProvider)) -> Dict[str, Any]:
    """Require admin permissions for mutation operations."""
    if not auth or not auth.get("user_id"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Simple admin check - in real implementation, check user roles/permissions
    admin_users = ["admin"]
    if auth["user_id"] not in admin_users:
        raise HTTPException(status_code=403, detail="Admin permissions required")
    
    return auth
