"""Test configuration and fixtures"""

import pytest
import asyncio
from typing import Generator

from agenticraft import Agent, Tool


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def agent() -> Agent:
    """Create a test agent"""
    return Agent(name="TestAgent", model="gpt-3.5-turbo")


@pytest.fixture
def calculator_tool() -> Tool:
    """Create calculator tool"""
    return Tool.Calculator()
