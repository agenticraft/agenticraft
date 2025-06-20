"""
JSON serialization implementation.
"""
import json
from typing import Any
from datetime import datetime, date
from uuid import UUID

from .base import Serializer, SerializationError


class JSONEncoder(json.JSONEncoder):
    """Enhanced JSON encoder with support for common types."""
    
    def default(self, obj):
        """Handle additional types."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
            
        return super().default(obj)


class JSONSerializer(Serializer):
    """JSON serializer implementation."""
    
    def __init__(self, indent: int = None, sort_keys: bool = False):
        """
        Initialize JSON serializer.
        
        Args:
            indent: JSON indentation (None for compact)
            sort_keys: Whether to sort object keys
        """
        self.indent = indent
        self.sort_keys = sort_keys
        self.encoder = JSONEncoder(
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=False
        )
        
    def serialize(self, data: Any) -> bytes:
        """Serialize data to JSON bytes."""
        try:
            json_str = self.encoder.encode(data)
            return json_str.encode('utf-8')
        except Exception as e:
            raise SerializationError(f"Failed to serialize to JSON: {e}")
            
    def deserialize(self, data: bytes) -> Any:
        """Deserialize JSON bytes to data."""
        try:
            json_str = data.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            raise SerializationError(f"Failed to deserialize from JSON: {e}")
