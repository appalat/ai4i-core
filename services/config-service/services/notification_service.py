"""
Kafka event publishing for configuration changes.

Following the pattern from services/telemetry-service/main.py and services/alerting-service/main.py
"""

import logging
import json
import os
from datetime import datetime
from typing import Optional
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


class NotificationService:
    """Kafka event publishing for configuration changes."""
    
    def __init__(self, kafka_producer: Optional[AIOKafkaProducer]):
        """Initialize notification service with Kafka producer."""
        self.producer = kafka_producer
    
    async def publish_config_update(
        self,
        action: str,
        key: str,
        environment: str,
        service_name: str,
        value: Optional[str] = None
    ) -> bool:
        """Publish configuration change event."""
        if not self.producer:
            logger.debug("Kafka producer not available - skipping config-update event")
            return False
        try:
            event = {
                "action": action,
                "resource_type": "configuration",
                "resource_id": key,
                "data": {
                    "key": key,
                    "environment": environment,
                    "service_name": service_name,
                    "value": value  # Only include if not sensitive
                },
                "timestamp": datetime.utcnow().isoformat(),
                "environment": environment
            }
            
            topic = os.getenv('KAFKA_TOPIC_CONFIG_UPDATES', 'config-updates')
            message = json.dumps(event)
            
            await self.producer.send(topic, value=message)
            logger.info(f"Published config-update event: {action} {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish config-update event: {e}")
            return False
    
    async def publish_feature_flag_update(
        self,
        action: str,
        name: str,
        environment: str,
        is_enabled: bool
    ) -> bool:
        """Publish feature flag change event."""
        if not self.producer:
            logger.debug("Kafka producer not available - skipping feature-flag-update event")
            return False
        try:
            event = {
                "action": action,
                "resource_type": "feature_flag",
                "resource_id": name,
                "data": {
                    "name": name,
                    "environment": environment,
                    "is_enabled": is_enabled
                },
                "timestamp": datetime.utcnow().isoformat(),
                "environment": environment
            }
            
            topic = os.getenv('KAFKA_TOPIC_FEATURE_FLAG_UPDATES', 'feature-flag-updates')
            message = json.dumps(event)
            
            await self.producer.send(topic, value=message)
            logger.info(f"Published feature-flag-update event: {action} {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish feature-flag-update event: {e}")
            return False
    
    async def publish_service_registry_update(
        self,
        action: str,
        service_name: str,
        status: str
    ) -> bool:
        """Publish service registry change event."""
        if not self.producer:
            logger.debug("Kafka producer not available - skipping service-registry-update event")
            return False
        try:
            event = {
                "action": action,
                "resource_type": "service",
                "resource_id": service_name,
                "data": {
                    "service_name": service_name,
                    "status": status
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            topic = os.getenv('KAFKA_TOPIC_SERVICE_REGISTRY_UPDATES', 'service-registry-updates')
            message = json.dumps(event)
            
            await self.producer.send(topic, value=message)
            logger.info(f"Published service-registry-update event: {action} {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish service-registry-update event: {e}")
            return False

