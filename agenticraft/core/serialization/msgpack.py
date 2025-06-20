"""
MessagePack serialization implementation.
"""
from typing import Any

try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False
    msgpack = None

from .base import Serializer, SerializationError


class MsgPackSerializer(Serializer):
    """MessagePack serializer implementation."""
    
    def __init__(self, use_bin_type: bool = True):
        """
        Initialize MessagePack serializer.
        
        Args:
            use_bin_type: Use bin type for bytes
        """
        if not HAS_MSGPACK:
            raise ImportError(
                "msgpack is required for MessagePack serialization. "
                "Install with: pip install msgpack"
            )
            
        self.use_bin_type = use_bin_type
        
    def serialize(self, data: Any) -> bytes:
        """Serialize data to MessagePack bytes."""
        try:
            return msgpack.packb(
                data,
                use_bin_type=self.use_bin_type
            )
        except Exception as e:
            raise SerializationError(f"Failed to serialize to MessagePack: {e}")
            
    def deserialize(self, data: bytes) -> Any:
        """Deserialize MessagePack bytes to data."""
        try:
            return msgpack.unpackb(
                data,
                raw=False,
                strict_map_key=False
            )
        except Exception as e:
            raise SerializationError(f"Failed to deserialize from MessagePack: {e}")
