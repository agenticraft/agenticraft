"""
Core registry abstractions for AgentiCraft.

This module provides protocol-agnostic service registry
that can be used by any protocol implementation.
"""

from .base import (
    ServiceRegistry,
    ServiceInfo,
    ServiceStatus,
    RegistryError,
    ServiceNotFoundError,
    ServiceAlreadyExistsError
)

from .memory import InMemoryRegistry
from .distributed import DistributedRegistry

__all__ = [
    # Base classes
    "ServiceRegistry",
    "ServiceInfo",
    "ServiceStatus",
    "RegistryError",
    "ServiceNotFoundError",
    "ServiceAlreadyExistsError",
    
    # Implementations
    "InMemoryRegistry",
    "DistributedRegistry"
]
