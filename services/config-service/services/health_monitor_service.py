"""
Background health monitoring service for automatically updating service registry status.
Runs periodic health checks on all registered services and updates their status.
"""

import asyncio
import logging
import httpx
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthMonitorService:
    """Service for monitoring and updating health status of registered services."""
    
    def __init__(
        self,
        http_client: httpx.AsyncClient
    ):
        """
        Initialize health monitor.
        
        Args:
            http_client: HTTP client for health checks
        """
        self.http_client = http_client
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Default health check endpoints for different services
        self.health_endpoints = {
            "api-gateway-service": "/health",
            "auth-service": "/health",
            "config-service": "/health",
            "metrics-service": "/health",
            "telemetry-service": "/health",
            "alerting-service": "/health",
            "dashboard-service": "/health",
            "asr-service": "/api/v1/asr/health",
            "tts-service": "/health",
            "nmt-service": "/api/v1/nmt/health",
            "pipeline-service": "/health",
            "simple-ui-frontend": "/health",
        }
    
    async def check_service_health(self, service: dict) -> tuple[bool, float]:
        """
        Check if a service is healthy by calling its health endpoint.
        Returns (is_healthy, response_time_ms)
        """
        service_name = service.get("service_name")
        service_url = service.get("service_url")
        health_check_url = service.get("health_check_url")
        
        if not service_url and not health_check_url:
            return False, 0.0
        
        # Use health_check_url if available, otherwise construct from service_url
        if health_check_url:
            url = health_check_url
        else:
            # Get health endpoint for this service type
            endpoint = self.health_endpoints.get(service_name, "/health")
            url = f"{service_url.rstrip('/')}{endpoint}"
        
        try:
            start_time = datetime.now().timestamp()
            response = await self.http_client.get(url, timeout=5.0)
            response_time = (datetime.now().timestamp() - start_time) * 1000  # ms
            
            # Check JSON status field first (more reliable than HTTP status code)
            # Some services return 200 even when unhealthy, or 503 with detailed status
            is_healthy = False
            try:
                data = response.json()
                if isinstance(data, dict):
                    # Check if response has a detail wrapper (e.g., from HTTPException)
                    if "detail" in data and isinstance(data["detail"], dict):
                        status_dict = data["detail"]
                        status = status_dict.get("status", "").lower()
                    else:
                        status = data.get("status", "").lower()
                    
                    # Consider healthy if status is "healthy"
                    if status == "healthy":
                        is_healthy = True
                    elif status in ["unhealthy", "error", "down"]:
                        is_healthy = False
                    elif response.status_code == 200:
                        # If no explicit status field but 200, consider healthy
                        is_healthy = True
            except:
                # If JSON parsing fails, fall back to HTTP status code
                is_healthy = response.status_code == 200
            
            return is_healthy, response_time
        except (httpx.ConnectError, httpx.TimeoutException):
            return False, 0.0
        except Exception as e:
            logger.debug(f"Health check error for {service_name}: {e}")
            return False, 0.0
    
    async def check_all_services(self):
        """Check health of all registered services and update their status."""
        # Use async context manager pattern like routers do for proper session management
        from main import app
        session_factory = app.state.db_session_factory
        
        async with session_factory() as db:
            from repositories.service_registry_repository import ServiceRegistryRepository
            from services.service_registry_service import ServiceRegistryService
            
            repository = ServiceRegistryRepository(db)
            service_registry_service = ServiceRegistryService(
                repository, 
                app.state.cache_service, 
                app.state.redis_client, 
                app.state.notification_service
            )
            
            try:
                services = await service_registry_service.get_all_services()
                
                if not services:
                    logger.debug("No services found for health checking")
                    return
                
                logger.debug(f"Checking health of {len(services)} services")
                
                # Check health of each service (this doesn't require DB session)
                health_results = []
                for service in services:
                    service_name = service.get("service_name")
                    current_status = service.get("status", "unknown")
                    
                    try:
                        is_healthy, response_time = await self.check_service_health(service)
                        health_results.append((service_name, current_status, is_healthy, response_time))
                    except Exception as e:
                        logger.error(f"Error checking health for {service_name}: {e}")
                        health_results.append((service_name, current_status, False, 0.0))
                
                # Update status for each service (requires DB session to stay open)
                for service_name, current_status, is_healthy, response_time in health_results:
                    try:
                        new_status = "healthy" if is_healthy else "unhealthy"
                        
                        # Only update if status changed or was unknown
                        if current_status != new_status or current_status == "unknown":
                            await service_registry_service.update_health(
                                service_name, new_status, response_time
                            )
                            logger.info(
                                f"Health check: {service_name} "
                                f"{current_status} → {new_status} ({response_time:.1f}ms)"
                            )
                    except Exception as e:
                        logger.error(f"Error updating health for {service_name}: {e}")
            except Exception as e:
                logger.error(f"Error in health check cycle: {e}")
    
    async def start_monitoring(
        self,
        interval_seconds: int = 30,
        startup_delay: int = 10
    ):
        """
        Start background health monitoring.
        
        Args:
            interval_seconds: Time between health check cycles
            startup_delay: Delay before starting first check (to let services start)
        """
        if self.is_running:
            logger.warning("Health monitor is already running")
            return
        
        self.is_running = True
        
        async def monitor_loop():
            # Wait for services to start up
            await asyncio.sleep(startup_delay)
            
            logger.info(
                f"Starting health monitor (interval: {interval_seconds}s, "
                f"startup delay: {startup_delay}s)"
            )
            
            while self.is_running:
                try:
                    await self.check_all_services()
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")
                
                await asyncio.sleep(interval_seconds)
        
        self.monitor_task = asyncio.create_task(monitor_loop())
        logger.info("Health monitor started")
    
    async def stop_monitoring(self):
        """Stop background health monitoring."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitor stopped")

