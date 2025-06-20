"""
Base registry interface for all protocols.

This module defines protocol-agnostic service registry abstractions
that can be used by MCP, A2A, and other protocols.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable
import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status in registry."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """Information about a registered service."""
    id: str
    name: str
    type: str
    status: ServiceStatus
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    health_check_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status.value,
            "endpoint": self.endpoint,
            "metadata": self.metadata,
            "tags": list(self.tags),
            "registered_at": self.registered_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "health_check_url": self.health_check_url
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceInfo":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid4())),
            name=data["name"],
            type=data["type"],
            status=ServiceStatus(data.get("status", "unknown")),
            endpoint=data.get("endpoint"),
            metadata=data.get("metadata", {}),
            tags=set(data.get("tags", [])),
            registered_at=datetime.fromisoformat(data.get("registered_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            health_check_url=data.get("health_check_url")
        )


class ServiceRegistry(ABC):
    """Abstract base class for service registries."""
    
    def __init__(self):
        """Initialize registry."""
        self._watchers: Dict[str, List[Callable[[ServiceInfo, str], Awaitable[None]]]] = {}
        
    @abstractmethod
    async def register(
        self,
        name: str,
        service_type: str,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
        health_check_url: Optional[str] = None
    ) -> ServiceInfo:
        """
        Register a service.
        
        Args:
            name: Service name (must be unique)
            service_type: Type of service (e.g., "mcp", "a2a", "tool")
            endpoint: Service endpoint URL
            metadata: Additional service metadata
            tags: Service tags for discovery
            health_check_url: URL for health checks
            
        Returns:
            Service information
        """
        pass
        
    @abstractmethod
    async def unregister(self, name: str) -> bool:
        """
        Unregister a service.
        
        Args:
            name: Service name
            
        Returns:
            True if unregistered successfully
        """
        pass
        
    @abstractmethod
    async def discover(
        self,
        service_type: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        status: Optional[ServiceStatus] = None
    ) -> List[ServiceInfo]:
        """
        Discover services.
        
        Args:
            service_type: Filter by service type
            tags: Filter by tags (services must have all specified tags)
            status: Filter by status
            
        Returns:
            List of matching services
        """
        pass
        
    @abstractmethod
    async def get(self, name: str) -> Optional[ServiceInfo]:
        """
        Get service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service info or None
        """
        pass
        
    @abstractmethod
    async def update_status(self, name: str, status: ServiceStatus) -> bool:
        """
        Update service status.
        
        Args:
            name: Service name
            status: New status
            
        Returns:
            True if updated successfully
        """
        pass
        
    @abstractmethod
    async def update_metadata(
        self,
        name: str,
        metadata: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """
        Update service metadata.
        
        Args:
            name: Service name
            metadata: New metadata
            merge: If True, merge with existing metadata
            
        Returns:
            True if updated successfully
        """
        pass
        
    @abstractmethod
    async def health_check(self, name: str) -> bool:
        """
        Check service health.
        
        Args:
            name: Service name
            
        Returns:
            True if healthy
        """
        pass
        
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all services.
        
        Returns:
            Dict mapping service names to health status
        """
        services = await self.discover()
        results = {}
        
        for service in services:
            try:
                results[service.name] = await self.health_check(service.name)
            except Exception:
                results[service.name] = False
                
        return results
        
    def watch(
        self,
        service_type: Optional[str] = None,
        callback: Optional[Callable[[ServiceInfo, str], Awaitable[None]]] = None
    ) -> str:
        """
        Watch for service changes.
        
        Args:
            service_type: Filter by service type (None for all)
            callback: Async callback function(service_info, event_type)
                     event_type can be: "registered", "updated", "unregistered"
                     
        Returns:
            Watcher ID for unsubscribing
        """
        watcher_id = str(uuid4())
        key = service_type or "*"
        
        if key not in self._watchers:
            self._watchers[key] = []
            
        if callback:
            self._watchers[key].append(callback)
            
        return watcher_id
        
    async def _notify_watchers(
        self,
        service: ServiceInfo,
        event_type: str
    ) -> None:
        """Notify watchers of service changes."""
        # Notify type-specific watchers
        if service.type in self._watchers:
            for callback in self._watchers[service.type]:
                try:
                    await callback(service, event_type)
                except Exception as e:
                    logger.error(f"Error in watcher callback: {e}")
                    
        # Notify general watchers
        if "*" in self._watchers:
            for callback in self._watchers["*"]:
                try:
                    await callback(service, event_type)
                except Exception as e:
                    logger.error(f"Error in watcher callback: {e}")
                    
    @abstractmethod
    async def list_types(self) -> List[str]:
        """
        List all service types.
        
        Returns:
            List of unique service types
        """
        pass
        
    @abstractmethod
    async def list_tags(self) -> Set[str]:
        """
        List all tags.
        
        Returns:
            Set of all tags used by services
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all services from registry."""
        pass
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


class RegistryError(Exception):
    """Base exception for registry errors."""
    pass


class ServiceNotFoundError(RegistryError):
    """Raised when service is not found."""
    
    def __init__(self, service_name: str):
        super().__init__(f"Service not found: {service_name}")
        self.service_name = service_name


class ServiceAlreadyExistsError(RegistryError):
    """Raised when service already exists."""
    
    def __init__(self, service_name: str):
        super().__init__(f"Service already exists: {service_name}")
        self.service_name = service_name
