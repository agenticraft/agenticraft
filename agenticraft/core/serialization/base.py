"""
Base serialization interface.

This module defines protocol-agnostic serialization abstractions.
"""
from abc import ABC, abstractmethod
from typing import Any, Union


class Serializer(ABC):
    """Abstract base class for serializers."""
    
    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        """
        Serialize data to bytes.
        
        Args:
            data: Data to serialize
            
        Returns:
            Serialized bytes
            
        Raises:
            SerializationError: If serialization fails
        """
        pass
        
    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """
        Deserialize bytes to data.
        
        Args:
            data: Bytes to deserialize
            
        Returns:
            Deserialized data
            
        Raises:
            SerializationError: If deserialization fails
        """
        pass
        
    def serialize_to_string(self, data: Any) -> str:
        """
        Serialize data to string.
        
        Args:
            data: Data to serialize
            
        Returns:
            Serialized string
        """
        return self.serialize(data).decode('utf-8')
        
    def deserialize_from_string(self, data: str) -> Any:
        """
        Deserialize string to data.
        
        Args:
            data: String to deserialize
            
        Returns:
            Deserialized data
        """
        return self.deserialize(data.encode('utf-8'))


class SerializationError(Exception):
    """Base exception for serialization errors."""
    pass
