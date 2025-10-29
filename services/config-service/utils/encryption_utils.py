"""
Encryption utilities for sensitive configuration values.
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from typing import Optional

logger = logging.getLogger(__name__)

# Check if encryption is enabled
ENABLE_ENCRYPTION = os.getenv("ENABLE_ENCRYPTION", "false").lower() == "true"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Initialize Fernet cipher if encryption is enabled
_cipher = None
if ENABLE_ENCRYPTION and ENCRYPTION_KEY:
    try:
        # Ensure the key is properly formatted for Fernet
        if len(ENCRYPTION_KEY) == 32:
            # Convert to base64 if it's raw bytes
            key = base64.urlsafe_b64encode(ENCRYPTION_KEY.encode())
        elif len(ENCRYPTION_KEY) == 44:
            # Already base64 encoded
            key = ENCRYPTION_KEY.encode()
        else:
            logger.warning("Invalid encryption key length. Encryption disabled.")
            ENABLE_ENCRYPTION = False
        
        if ENABLE_ENCRYPTION:
            _cipher = Fernet(key)
            logger.info("Encryption enabled")
    except Exception as e:
        logger.error(f"Failed to initialize encryption: {e}")
        ENABLE_ENCRYPTION = False
        _cipher = None

if ENABLE_ENCRYPTION and not _cipher:
    logger.warning("Encryption enabled but cipher not initialized. Encryption disabled.")
    ENABLE_ENCRYPTION = False


def encrypt_value(value: str) -> Optional[str]:
    """
    Encrypt a configuration value.
    
    Args:
        value: The value to encrypt
        
    Returns:
        Encrypted value as base64 string, or None if encryption is disabled
    """
    if not ENABLE_ENCRYPTION or not _cipher:
        return None
    
    try:
        encrypted_bytes = _cipher.encrypt(value.encode())
        encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode()
        logger.debug("Value encrypted successfully")
        return encrypted_str
    except Exception as e:
        logger.error(f"Failed to encrypt value: {e}")
        return None


def decrypt_value(encrypted_value: str) -> Optional[str]:
    """
    Decrypt a configuration value.
    
    Args:
        encrypted_value: The encrypted value as base64 string
        
    Returns:
        Decrypted value, or None if decryption fails
    """
    if not ENABLE_ENCRYPTION or not _cipher:
        return encrypted_value  # Return as-is if encryption is disabled
    
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted_bytes = _cipher.decrypt(encrypted_bytes)
        decrypted_str = decrypted_bytes.decode()
        logger.debug("Value decrypted successfully")
        return decrypted_str
    except Exception as e:
        logger.error(f"Failed to decrypt value: {e}")
        return None


def is_encryption_enabled() -> bool:
    """Check if encryption is enabled."""
    return ENABLE_ENCRYPTION and _cipher is not None


def redact_sensitive_value(value: str, is_encrypted: bool = False) -> str:
    """
    Redact sensitive values for logging/events.
    
    Args:
        value: The value to redact
        is_encrypted: Whether the value is encrypted
        
    Returns:
        Redacted value for safe logging
    """
    if is_encrypted or is_encryption_enabled():
        return "[REDACTED]"
    
    # For non-encrypted values, show first and last few characters
    if len(value) <= 8:
        return "[REDACTED]"
    
    return f"{value[:3]}...{value[-3:]}"


def generate_encryption_key() -> str:
    """
    Generate a new encryption key.
    
    Returns:
        Base64 encoded encryption key
    """
    key = Fernet.generate_key()
    return key.decode()
