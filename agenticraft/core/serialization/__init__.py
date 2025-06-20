"""
Core serialization abstractions for AgentiCraft.

This module provides protocol-agnostic serialization
that can be used by any protocol implementation.
"""

from .base import Serializer, SerializationError
from .json import JSONSerializer
from .msgpack import MsgPackSerializer

__all__ = [
    "Serializer",
    "SerializationError",
    "JSONSerializer",
    "MsgPackSerializer"
]
