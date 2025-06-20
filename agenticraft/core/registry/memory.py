"""
In-memory implementation of service registry.

This module provides a simple in-memory registry suitable
for single-process applications and testing.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import httpx

from .base import (
    ServiceRegistry,
    ServiceInfo,
    ServiceStatus,
    ServiceNotFoundError,
    ServiceAlreadyExistsError
)

logger = logging.getLogger(__name__)


class InMemoryRegistry(ServiceRegistry):
    """In-memory service registry implementation."""
    
    def __init__(self):
        """Initialize in-memory registry."""
        super().__init__()
        self._services: Dict[str, ServiceInfo] = {}
        self._lock = asyncio.Lock()
        
    async def register(
        self,
        name: str,
        service_type: str,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
        health_check_url: Optional[str] = None
    ) -> ServiceInfo:
        """Register a service."""
        async with self._lock:
            if name in self._services:
                raise ServiceAlreadyExistsError(name)
                
            service = ServiceInfo(
                id=str(uuid4()),
                name=name,
                type=service_type,
                status=ServiceStatus.ACTIVE,
                endpoint=endpoint,
                metadata=metadata or {},
                tags=tags or set(),
                health_check_url=health_check_url
            )
            
            self._services[name] = service
            logger.info(f"Registered service: {name} (type: {service_type})")
            
            # Notify watchers
            await self._notify_watchers(service, "registered")
            
            return service
            
    async def unregister(self, name: str) -> bool:
        """Unregister a service."""
        async with self._lock:
            if name not in self._services:
                return False
                
            service = self._services[name]
            del self._services[name]
            
            logger.info(f"Unregistered service: {name}")
            
            # Notify watchers
            await self._notify_watchers(service, "unregistered")
            
            return True
            
    async def discover(
        self,
        service_type: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        status: Optional[ServiceStatus] = None
    ) -> List[ServiceInfo]:
        """Discover services."""
        async with self._lock:
            services = []
            
            for service in self._services.values():
                # Apply filters
                if service_type and service.type != service_type:
                    continue
                    
                if tags and not tags.issubset(service.tags):
                    continue
                    
                if status and service.status != status:
                    continue
                    
                services.append(service)
                
            return services
            
    async def get(self, name: str) -> Optional[ServiceInfo]:
        """Get service by name."""
        async with self._lock:
            return self._services.get(name)
            
    async def update_status(self, name: str, status: ServiceStatus) -> bool:
        """Update service status."""
        async with self._lock:
            if name not in self._services:
                return False
                
            service = self._services[name]
            old_status = service.status
            service.status = status
            service.updated_at = datetime.utcnow()
            
            if old_status != status:
                logger.info(f"Service {name} status: {old_status.value} -> {status.value}")
                
                # Notify watchers
                await self._notify_watchers(service, "updated")
                
            return True
            
    async def update_metadata(
        self,
        name: str,
        metadata: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """Update service metadata."""
        async with self._lock:
            if name not in self._services:
                return False
                
            service = self._services[name]
            
            if merge:
                service.metadata.update(metadata)
            else:
                service.metadata = metadata
                
            service.updated_at = datetime.utcnow()
            
            # Notify watchers
            await self._notify_watchers(service, "updated")
            
            return True
            
    async def health_check(self, name: str) -> bool:
        """Check service health."""
        service = await self.get(name)
        if not service:
            raise ServiceNotFoundError(name)
            
        # If no health check URL, assume healthy if status is active
        if not service.health_check_url:
            return service.status == ServiceStatus.ACTIVE
            
        # Perform HTTP health check
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(service.health_check_url)
                
                is_healthy = response.status_code == 200
                
                # Update status based on health
                new_status = ServiceStatus.ACTIVE if is_healthy else ServiceStatus.ERROR
                await self.update_status(name, new_status)
                
                return is_healthy
                
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            await self.update_status(name, ServiceStatus.ERROR)
            return False
            
    async def list_types(self) -> List[str]:
        """List all service types."""
        async with self._lock:
            types = set()
            for service in self._services.values():
                types.add(service.type)
            return sorted(list(types))
            
    async def list_tags(self) -> Set[str]:
        """List all tags."""
        async with self._lock:
            all_tags = set()
            for service in self._services.values():
                all_tags.update(service.tags)
            return all_tags
            
    async def clear(self) -> None:
        """Clear all services."""
        async with self._lock:
            # Notify watchers about each service being removed
            for service in list(self._services.values()):
                await self._notify_watchers(service, "unregistered")
                
            self._services.clear()
            logger.info("Cleared all services from registry")
            
    def __len__(self) -> int:
        """Get number of registered services."""
        return len(self._services)
        
    def __contains__(self, name: str) -> bool:
        """Check if service is registered."""
        return name in self._services
        
    async def export(self) -> Dict[str, Any]:
        """Export registry state."""
        async with self._lock:
            return {
                "services": [
                    service.to_dict()
                    for service in self._services.values()
                ]
            }
            
    async def import_data(self, data: Dict[str, Any]) -> None:
        """Import registry state."""
        async with self._lock:
            self._services.clear()
            
            for service_data in data.get("services", []):
                service = ServiceInfo.from_dict(service_data)
                self._services[service.name] = service
                
                # Notify watchers
                await self._notify_watchers(service, "registered")
