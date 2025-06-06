"""Tests for streaming functionality."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agenticraft import Agent
from agenticraft.core.streaming import (
    StreamChunk, StreamingResponse, StreamInterruptedError,
    collect_stream, stream_to_string, create_mock_stream
)


@pytest.mark.asyncio
async def test_stream_chunk():
    """Test StreamChunk dataclass."""
    chunk = StreamChunk(content="Hello", token="Hello", metadata={"test": True})
    
    assert chunk.content == "Hello"
    assert chunk.token == "Hello"
    assert chunk.metadata["test"] is True
    assert chunk.is_final is False
    assert chunk.timestamp > 0
    assert str(chunk) == "Hello"


@pytest.mark.asyncio
async def test_streaming_response():
    """Test StreamingResponse accumulation."""
    response = StreamingResponse()
    
    # Add chunks
    chunk1 = StreamChunk(content="Hello ")
    chunk2 = StreamChunk(content="world")
    chunk3 = StreamChunk(content="!", is_final=True, metadata={"total_tokens": 10})
    
    response.add_chunk(chunk1)
    response.add_chunk(chunk2)
    response.add_chunk(chunk3)
    
    assert response.complete_text == "Hello world!"
    assert response.chunk_count == 3
    assert response.total_tokens == 10
    assert response.duration is not None
    assert str(response) == "Hello world!"


@pytest.mark.asyncio
async def test_create_mock_stream():
    """Test mock stream creation."""
    text = "Hello world"
    chunks = []
    
    async for chunk in create_mock_stream(text, chunk_size=5, delay=0.01):
        chunks.append(chunk)
    
    assert len(chunks) == 2
    assert chunks[0].content == "Hello"
    assert chunks[1].content == " world"
    assert chunks[1].is_final is True


@pytest.mark.asyncio
async def test_collect_stream():
    """Test collecting a complete stream."""
    mock_stream = create_mock_stream("Test message", chunk_size=4, delay=0)
    response = await collect_stream(mock_stream)
    
    assert response.complete_text == "Test message"
    assert response.chunk_count == 3


@pytest.mark.asyncio
async def test_stream_to_string():
    """Test converting stream to string."""
    mock_stream = create_mock_stream("Test message", chunk_size=4, delay=0)
    result = await stream_to_string(mock_stream)
    
    assert result == "Test message"


@pytest.mark.asyncio
class TestAgentStreaming:
    """Test Agent streaming functionality."""
    
    async def test_agent_stream_basic(self):
        """Test basic agent streaming."""
        with patch('agenticraft.core.agent.ProviderFactory.create') as mock_factory:
            # Create mock provider with streaming support
            mock_provider = AsyncMock()
            mock_provider.supports_streaming.return_value = True
            
            # Mock the stream method
            async def mock_stream(*args, **kwargs):
                yield StreamChunk(content="Hello ", token="Hello ")
                yield StreamChunk(content="world!", token="world!")
                yield StreamChunk(content="", is_final=True)
            
            mock_provider.stream = mock_stream
            mock_factory.return_value = mock_provider
            
            # Create agent and test streaming
            agent = Agent(name="StreamTest")
            
            chunks = []
            async for chunk in agent.stream("Test prompt"):
                chunks.append(chunk)
            
            assert len(chunks) == 3
            assert chunks[0].content == "Hello "
            assert chunks[1].content == "world!"
            assert chunks[2].is_final is True
    
    async def test_agent_stream_no_support(self):
        """Test streaming with provider that doesn't support it."""
        with patch('agenticraft.core.agent.ProviderFactory.create') as mock_factory:
            # Create mock provider without streaming support
            mock_provider = AsyncMock()
            # Remove stream attribute to simulate no support
            if hasattr(mock_provider, 'stream'):
                delattr(mock_provider, 'stream')
            
            mock_factory.return_value = mock_provider
            
            # Create agent and test streaming
            agent = Agent(name="NoStreamTest")
            
            with pytest.raises(Exception) as exc_info:
                async for _ in agent.stream("Test prompt"):
                    pass
            
            assert "does not support streaming" in str(exc_info.value)
    
    async def test_agent_stream_interruption(self):
        """Test stream interruption handling."""
        with patch('agenticraft.core.agent.ProviderFactory.create') as mock_factory:
            # Create mock provider with streaming support
            mock_provider = AsyncMock()
            mock_provider.supports_streaming.return_value = True
            
            # Mock the stream method to raise interruption
            async def mock_stream(*args, **kwargs):
                yield StreamChunk(content="Hello ")
                raise StreamInterruptedError("Test interruption", partial_response="Hello ")
            
            mock_provider.stream = mock_stream
            mock_factory.return_value = mock_provider
            
            # Create agent and test streaming
            agent = Agent(name="InterruptTest")
            
            with pytest.raises(StreamInterruptedError) as exc_info:
                async for chunk in agent.stream("Test prompt"):
                    pass
            
            assert exc_info.value.partial_response == "Hello "


@pytest.mark.asyncio
class TestProviderStreaming:
    """Test provider-specific streaming."""
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--openai", default=False),
        reason="OpenAI tests require --openai flag"
    )
    async def test_openai_streaming(self):
        """Test OpenAI provider streaming."""
        from agenticraft.providers.openai import OpenAIProvider
        
        provider = OpenAIProvider(model="gpt-3.5-turbo")
        assert provider.supports_streaming() is True
        
        # Test actual streaming (requires API key)
        chunks = []
        async for chunk in provider.stream(
            messages=[{"role": "user", "content": "Say 'test' in one word"}],
            max_tokens=10
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert any(chunk.is_final for chunk in chunks)
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--anthropic", default=False),
        reason="Anthropic tests require --anthropic flag"
    )
    async def test_anthropic_streaming(self):
        """Test Anthropic provider streaming."""
        from agenticraft.providers.anthropic import AnthropicProvider
        
        provider = AnthropicProvider(model="claude-3-sonnet-20240229")
        assert provider.supports_streaming() is True
        
        # Test actual streaming (requires API key)
        chunks = []
        async for chunk in provider.stream(
            messages=[{"role": "user", "content": "Say 'test' in one word"}],
            max_tokens=10
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert any(chunk.is_final for chunk in chunks)
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--ollama", default=False),
        reason="Ollama tests require --ollama flag and running server"
    )
    async def test_ollama_streaming(self):
        """Test Ollama provider streaming."""
        from agenticraft.providers.ollama import OllamaProvider
        
        provider = OllamaProvider(model="llama2")
        assert provider.supports_streaming() is True
        
        # Test actual streaming (requires Ollama running)
        chunks = []
        async for chunk in provider.stream(
            messages=[{"role": "user", "content": "Say 'test' in one word"}],
            max_tokens=10
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert any(chunk.is_final for chunk in chunks)


@pytest.mark.asyncio
async def test_streaming_with_tools():
    """Test streaming when tools are involved."""
    with patch('agenticraft.core.agent.ProviderFactory.create') as mock_factory:
        # Create mock provider with streaming support
        mock_provider = AsyncMock()
        mock_provider.supports_streaming.return_value = True
        
        # Mock the stream method with tool calls
        async def mock_stream(*args, **kwargs):
            yield StreamChunk(content="I'll check the weather. ")
            yield StreamChunk(
                content="", 
                is_final=True,
                metadata={
                    "tool_calls": [{
                        "id": "123",
                        "name": "get_weather",
                        "arguments": {"city": "Paris"}
                    }]
                }
            )
        
        mock_provider.stream = mock_stream
        mock_factory.return_value = mock_provider
        
        # Create mock tool
        from agenticraft import tool
        
        @tool
        def get_weather(city: str) -> str:
            """Get weather for a city."""
            return f"Sunny in {city}"
        
        # Create agent with tool
        agent = Agent(name="ToolStreamTest", tools=[get_weather])
        
        chunks = []
        async for chunk in agent.stream("What's the weather in Paris?"):
            chunks.append(chunk)
        
        # Should have initial response chunks
        assert any("weather" in chunk.content.lower() for chunk in chunks)
