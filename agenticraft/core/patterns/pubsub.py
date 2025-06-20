"""
Pub-Sub communication pattern.

This module provides a protocol-agnostic pub-sub pattern
that can be used by any protocol implementation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable, Awaitable, Set, List
import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Topic:
    """Pub-sub topic."""
    name: str
    metadata: Dict[str, Any] = None


@dataclass
class Message:
    """Pub-sub message."""
    id: str
    topic: str
    payload: Any
    metadata: Optional[Dict[str, Any]] = None


class Publisher(ABC):
    """Abstract publisher for pub-sub pattern."""
    
    @abstractmethod
    async def publish(
        self,
        topic: str,
        message: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Publish message to topic."""
        pass


class Subscriber(ABC):
    """Abstract subscriber for pub-sub pattern."""
    
    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: Callable[[Message], Awaitable[None]]
    ) -> str:
        """Subscribe to topic."""
        pass
        
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from topic."""
        pass


class PubSubPattern:
    """Pub-sub communication pattern."""
    
    def __init__(self):
        """Initialize pattern."""
        self._topics: Dict[str, Topic] = {}
        self._subscriptions: Dict[str, Dict[str, Callable]] = {}
        
    def create_topic(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Topic:
        """Create a topic."""
        topic = Topic(name=name, metadata=metadata or {})
        self._topics[name] = topic
        self._subscriptions[name] = {}
        return topic
        
    async def publish(
        self,
        topic_name: str,
        payload: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Publish message to topic."""
        if topic_name not in self._topics:
            raise ValueError(f"Unknown topic: {topic_name}")
            
        message = Message(
            id=str(uuid4()),
            topic=topic_name,
            payload=payload,
            metadata=metadata
        )
        
        # Notify all subscribers
        subscribers = self._subscriptions.get(topic_name, {})
        
        tasks = []
        for handler in subscribers.values():
            tasks.append(handler(message))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    def subscribe(
        self,
        topic_name: str,
        handler: Callable[[Message], Awaitable[None]]
    ) -> str:
        """Subscribe to topic."""
        if topic_name not in self._topics:
            raise ValueError(f"Unknown topic: {topic_name}")
            
        subscription_id = str(uuid4())
        self._subscriptions[topic_name][subscription_id] = handler
        
        return subscription_id
        
    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from topic."""
        for subscriptions in self._subscriptions.values():
            subscriptions.pop(subscription_id, None)
