"""Validation utilities."""

import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
SUPPORTED_ENVIRONMENTS = ["development", "staging", "production"]


def validate_environment(environment: str) -> bool:
    """Check if environment is valid."""
    if environment not in SUPPORTED_ENVIRONMENTS:
        raise InvalidEnvironmentError(f"Environment must be one of {SUPPORTED_ENVIRONMENTS}")
    return True


def validate_config_key(key: str) -> bool:
    """Check key format."""
    if not key or len(key) > 255:
        raise InvalidConfigKeyError("Key must be between 1 and 255 characters")
    if not all(c.isalnum() or c in "._-" for c in key):
        raise InvalidConfigKeyError("Key can only contain alphanumeric, dots, underscores, hyphens")
    return True


def validate_url(url: str) -> bool:
    """Check if valid URL."""
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL")
        return True
    except Exception:
        raise ValueError("Invalid URL")


class ValidationError(Exception):
    """Base validation error."""
    pass

class InvalidEnvironmentError(ValidationError):
    """Invalid environment error."""
    pass

class InvalidConfigKeyError(ValidationError):
    """Invalid config key error."""
    pass

