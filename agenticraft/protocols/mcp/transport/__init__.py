"""
MCP transport implementations.

This module provides different transport mechanisms for MCP:
- HTTP/HTTPS for request-response communication
- WebSocket for bidirectional real-time communication
"""

from .base import (
    IMCPTransport,
    TransportRegistry,
    TransportError,
    ConnectionError,
    TimeoutError
)

# Import transports to register them
from .http import HTTPTransport

try:
    from .websocket import WebSocketTransport
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False

__all__ = [
    "IMCPTransport",
    "TransportRegistry",
    "TransportError",
    "ConnectionError",
    "TimeoutError",
    "HTTPTransport",
]

if HAS_WEBSOCKET:
    __all__.append("WebSocketTransport")
