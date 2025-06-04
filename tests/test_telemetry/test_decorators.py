"""Tests for telemetry decorators."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from opentelemetry import trace

from agenticraft.telemetry.decorators import (
    track_metrics,
    trace,
    measure_time,
    count_calls,
    observe_value,
    trace_agent_method,
    trace_tool_execution
)


class TestTrackMetrics:
    """Test metrics tracking decorator."""
    
    @pytest.mark.asyncio
    async def test_track_metrics_async(self):
        """Test track_metrics with async function."""
        # Mock telemetry
        mock_telemetry = Mock()
        mock_counter = Mock()
        mock_histogram = Mock()
        mock_error_counter = Mock()
        
        mock_meter = Mock()
        mock_meter.create_counter.side_effect = [mock_counter, mock_error_counter]
        mock_meter.create_histogram.return_value = mock_histogram
        
        mock_telemetry.meter = mock_meter
        
        with patch('agenticraft.telemetry.decorators.get_global_telemetry', return_value=mock_telemetry):
            @track_metrics(labels=["param1"], track_duration=True, track_calls=True, track_errors=True)
            async def test_func(param1: str, param2: int):
                await asyncio.sleep(0.01)
                return param1 + str(param2)
            
            result = await test_func("test", 123)
        
        assert result == "test123"
        
        # Verify metrics were created
        assert mock_meter.create_counter.call_count == 2
        assert mock_meter.create_histogram.call_count == 1
        
        # Verify metrics were recorded
        mock_counter.add.assert_called_once()
        mock_histogram.record.assert_called_once()
    
    def test_track_metrics_sync(self):
        """Test track_metrics with sync function."""
        # Mock telemetry
        mock_telemetry = Mock()
        mock_counter = Mock()
        
        mock_meter = Mock()
        mock_meter.create_counter.return_value = mock_counter
        mock_meter.create_histogram.return_value = None
        
        mock_telemetry.meter = mock_meter
        
        with patch('agenticraft.telemetry.decorators.get_global_telemetry', return_value=mock_telemetry):
            @track_metrics(track_calls=True, track_duration=False, track_errors=False)
            def test_func(x, y):
                return x + y
            
            result = test_func(5, 3)
        
        assert result == 8
        mock_counter.add.assert_called_once_with(1, {})
    
    @pytest.mark.asyncio
    async def test_track_metrics_error(self):
        """Test track_metrics error tracking."""
        # Mock telemetry
        mock_telemetry = Mock()
        mock_error_counter = Mock()
        
        mock_meter = Mock()
        mock_meter.create_counter.return_value = mock_error_counter
        mock_meter.create_histogram.return_value = None
        
        mock_telemetry.meter = mock_meter
        
        with patch('agenticraft.telemetry.decorators.get_global_telemetry', return_value=mock_telemetry):
            @track_metrics(track_errors=True, track_calls=False, track_duration=False)
            async def test_func():
                raise ValueError("Test error")
            
            with pytest.raises(ValueError):
                await test_func()
        
        # Verify error was tracked
        mock_error_counter.add.assert_called_once()
        call_args = mock_error_counter.add.call_args[0]
        assert call_args[0] == 1
        assert "error_type" in call_args[1]
        assert call_args[1]["error_type"] == "ValueError"


class TestTrace:
    """Test trace decorator."""
    
    @pytest.mark.asyncio
    async def test_trace_async(self):
        """Test trace decorator with async function."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        with patch('agenticraft.telemetry.decorators.get_tracer', return_value=mock_tracer):
            @trace(attributes={"component": "test"})
            async def test_func(x):
                return x * 2
            
            result = await test_func(5)
        
        assert result == 10
        mock_tracer.start_as_current_span.assert_called_once()
        call_args = mock_tracer.start_as_current_span.call_args
        assert call_args[1]["attributes"] == {"component": "test"}
    
    def test_trace_sync_with_exception(self):
        """Test trace decorator exception handling."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        with patch('agenticraft.telemetry.decorators.get_tracer', return_value=mock_tracer):
            @trace(record_exception=True, set_status_on_exception=True)
            def test_func():
                raise RuntimeError("Test error")
            
            with pytest.raises(RuntimeError):
                test_func()
        
        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()


class TestUtilityDecorators:
    """Test utility decorators."""
    
    @pytest.mark.asyncio
    async def test_measure_time(self):
        """Test measure_time decorator."""
        mock_telemetry = Mock()
        mock_histogram = Mock()
        
        mock_meter = Mock()
        mock_meter.create_histogram.return_value = mock_histogram
        mock_telemetry.meter = mock_meter
        
        with patch('agenticraft.telemetry.decorators.get_global_telemetry', return_value=mock_telemetry):
            @measure_time("test.duration", {"operation": "test"})
            async def test_func():
                await asyncio.sleep(0.01)
                return "done"
            
            result = await test_func()
        
        assert result == "done"
        mock_histogram.record.assert_called_once()
        call_args = mock_histogram.record.call_args
        assert call_args[0][0] > 0  # Duration should be positive
        assert call_args[0][1] == {"operation": "test"}
    
    def test_count_calls(self):
        """Test count_calls decorator."""
        mock_telemetry = Mock()
        mock_counter = Mock()
        
        mock_meter = Mock()
        mock_meter.create_counter.return_value = mock_counter
        mock_telemetry.meter = mock_meter
        
        with patch('agenticraft.telemetry.decorators.get_global_telemetry', return_value=mock_telemetry):
            @count_calls("test.calls", {"service": "test"})
            def test_func(x):
                return x
            
            result = test_func(42)
        
        assert result == 42
        mock_counter.add.assert_called_once_with(1, {"service": "test"})
    
    @pytest.mark.asyncio
    async def test_observe_value(self):
        """Test observe_value decorator."""
        mock_telemetry = Mock()
        mock_gauge = Mock()
        
        mock_meter = Mock()
        mock_meter.create_gauge.return_value = mock_gauge
        mock_telemetry.meter = mock_meter
        
        with patch('agenticraft.telemetry.decorators.get_global_telemetry', return_value=mock_telemetry):
            @observe_value("test.size", lambda result: len(result), {"type": "list"})
            async def test_func():
                return [1, 2, 3, 4, 5]
            
            result = await test_func()
        
        assert result == [1, 2, 3, 4, 5]
        mock_gauge.set.assert_called_once_with(5, {"type": "list"})


class TestSpecializedDecorators:
    """Test specialized decorators."""
    
    @pytest.mark.asyncio
    async def test_trace_agent_method(self):
        """Test trace_agent_method decorator."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        mock_telemetry = Mock()
        mock_telemetry.meter = None
        
        class MockAgent:
            name = "TestAgent"
            id = "agent-123"
            
            @trace_agent_method("process")
            async def process(self, input_text):
                return f"Processed: {input_text}"
        
        with patch('agenticraft.telemetry.decorators.get_tracer', return_value=mock_tracer):
            with patch('agenticraft.telemetry.decorators.get_global_telemetry', return_value=mock_telemetry):
                with patch('agenticraft.telemetry.decorators.get_current_trace_id', return_value="trace-123"):
                    agent = MockAgent()
                    result = await agent.process("Hello")
        
        assert result == "Processed: Hello"
        
        # Verify span attributes were set
        mock_span.set_attribute.assert_any_call("agent.name", "TestAgent")
        mock_span.set_attribute.assert_any_call("agent.id", "agent-123")
    
    @pytest.mark.asyncio
    async def test_trace_tool_execution(self):
        """Test trace_tool_execution decorator."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        mock_telemetry = Mock()
        mock_telemetry.meter = None
        
        with patch('agenticraft.telemetry.decorators.get_tracer', return_value=mock_tracer):
            with patch('agenticraft.telemetry.decorators.get_global_telemetry', return_value=mock_telemetry):
                @trace_tool_execution("calculator")
                async def calculate(expression):
                    return eval(expression)
                
                result = await calculate("2 + 2")
        
        assert result == 4
        
        # Verify trace was created with correct attributes
        call_args = mock_tracer.start_as_current_span.call_args
        assert call_args[0][0] == "tool.calculator"
        assert call_args[1]["kind"] == trace.SpanKind.CLIENT
        assert call_args[1]["attributes"] == {"tool.name": "calculator"}


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_extract_label_values(self):
        """Test label value extraction from function parameters."""
        from agenticraft.telemetry.decorators import _extract_label_values
        
        def test_func(name: str, age: int, active: bool = True):
            pass
        
        labels = _extract_label_values(
            test_func,
            ("Alice", 30),
            {"active": False},
            ["name", "age", "active"]
        )
        
        assert labels == {
            "name": "Alice",
            "age": "30",
            "active": "False"
        }
    
    def test_add_span_attributes_from_params(self):
        """Test adding span attributes from parameters."""
        from agenticraft.telemetry.decorators import _add_span_attributes_from_params
        
        mock_span = Mock()
        
        def test_func(name: str, count: int, data: dict):
            pass
        
        _add_span_attributes_from_params(
            mock_span,
            test_func,
            ("test", 42),
            {"data": {"key": "value"}},
            "param"
        )
        
        # Only simple types should be added
        mock_span.set_attribute.assert_any_call("param.name", "test")
        mock_span.set_attribute.assert_any_call("param.count", 42)
        
        # Complex types (dict) should not be added
        assert mock_span.set_attribute.call_count == 2
