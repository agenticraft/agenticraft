"""Comprehensive tests for calculator tool."""

import math
import pytest
from unittest.mock import patch, Mock

from agenticraft.tools.calculator import (
    simple_calculate, scientific_calculate,
    _calculate_expression, SAFE_FUNCTIONS, SAFE_OPERATORS
)
from agenticraft.core.tool import FunctionTool


class TestCalculatorFunctions:
    """Test calculator functions."""
    
    def test_safe_functions_available(self):
        """Test that safe functions are properly defined."""
        assert 'abs' in SAFE_FUNCTIONS
        assert 'round' in SAFE_FUNCTIONS
        assert 'sqrt' in SAFE_FUNCTIONS
        assert 'sin' in SAFE_FUNCTIONS
        assert 'pi' in SAFE_FUNCTIONS
        assert 'e' in SAFE_FUNCTIONS
        
        # Check actual functions
        assert SAFE_FUNCTIONS['abs'] is abs
        assert SAFE_FUNCTIONS['sqrt'] is math.sqrt
        assert SAFE_FUNCTIONS['pi'] == math.pi
    
    def test_safe_operators_available(self):
        """Test that safe operators are properly defined."""
        assert 'add' in SAFE_OPERATORS
        assert 'sub' in SAFE_OPERATORS
        assert 'mul' in SAFE_OPERATORS
        assert 'div' in SAFE_OPERATORS
        assert 'pow' in SAFE_OPERATORS
    
    def test_calculate_expression_basic(self):
        """Test basic mathematical expressions."""
        assert _calculate_expression("2 + 2") == 4.0
        assert _calculate_expression("10 - 3") == 7.0
        assert _calculate_expression("4 * 5") == 20.0
        assert _calculate_expression("15 / 3") == 5.0
        assert _calculate_expression("2 ** 3") == 8.0
    
    def test_calculate_expression_with_functions(self):
        """Test expressions with mathematical functions."""
        assert _calculate_expression("abs(-5)") == 5.0
        assert _calculate_expression("round(3.7)") == 4.0
        assert _calculate_expression("min(1, 2, 3)") == 1.0
        assert _calculate_expression("max(1, 2, 3)") == 3.0
        assert _calculate_expression("sqrt(16)") == 4.0
        assert _calculate_expression("pow(2, 3)") == 8.0
    
    def test_calculate_expression_with_trig(self):
        """Test trigonometric functions."""
        # sin(pi/2) = 1
        result = _calculate_expression("sin(pi/2)")
        assert abs(result - 1.0) < 0.0001
        
        # cos(0) = 1
        assert _calculate_expression("cos(0)") == 1.0
        
        # tan(0) = 0
        assert _calculate_expression("tan(0)") == 0.0
    
    def test_calculate_expression_with_log(self):
        """Test logarithmic functions."""
        assert _calculate_expression("log(e)") == 1.0
        assert _calculate_expression("log10(100)") == 2.0
        assert _calculate_expression("exp(1)") == math.e
    
    def test_calculate_expression_complex(self):
        """Test complex expressions."""
        # Order of operations
        assert _calculate_expression("2 + 3 * 4") == 14.0
        
        # Parentheses
        assert _calculate_expression("(2 + 3) * 4") == 20.0
        
        # Mixed functions and operators
        result = _calculate_expression("sqrt(16) + sin(pi/2)")
        assert abs(result - 5.0) < 0.0001
    
    def test_calculate_expression_errors(self):
        """Test error handling in calculate_expression."""
        # Invalid syntax
        with pytest.raises(ValueError, match="Failed to evaluate expression"):
            _calculate_expression("2 + + 3")
        
        # Undefined function
        with pytest.raises(ValueError, match="Failed to evaluate expression"):
            _calculate_expression("undefined_func(5)")
        
        # Division by zero
        with pytest.raises(ValueError, match="Failed to evaluate expression"):
            _calculate_expression("1 / 0")
    
    def test_calculate_expression_security(self):
        """Test that dangerous operations are blocked."""
        # Should not allow imports
        with pytest.raises(ValueError):
            _calculate_expression("__import__('os')")
        
        # Should not allow attribute access
        with pytest.raises(ValueError):
            _calculate_expression("().__class__")
    
    def test_calculate_expression_non_numeric_result(self):
        """Test error when result is not numeric."""
        # Mock eval to return a string
        with patch('builtins.eval', return_value="not a number"):
            with pytest.raises(ValueError, match="Result must be numeric"):
                _calculate_expression("2 + 2")


class TestCalculateTool:
    """Test the calculate tool function."""
    
    def test_calculate_tool_is_function_tool(self):
        """Test that calculate is properly decorated as a tool."""
        # The decorated function should be a FunctionTool
        assert hasattr(simple_calculate, 'name')
        assert simple_calculate.name == "simple_calculator"
        assert hasattr(simple_calculate, 'description')
    
    def test_calculate_basic_operations(self):
        """Test basic calculator operations."""
        assert simple_calculate("5 + 3") == 8.0
        assert simple_calculate("10 - 4") == 6.0
        assert simple_calculate("3 * 7") == 21.0
        assert simple_calculate("20 / 4") == 5.0
    
    def test_calculate_with_functions(self):
        """Test calculator with mathematical functions."""
        assert simple_calculate("sqrt(25)") == 5.0
        assert simple_calculate("abs(-10)") == 10.0
        assert simple_calculate("max(5, 10, 3)") == 10.0
    
    def test_calculate_error_propagation(self):
        """Test that errors are properly propagated."""
        with pytest.raises(ValueError):
            simple_calculate("invalid expression")


class TestScientificCalculate:
    """Test the scientific calculator async function."""
    
    @pytest.mark.asyncio
    async def test_scientific_calculate_basic(self):
        """Test basic scientific calculation."""
        result = await scientific_calculate("2 + 2")
        
        assert isinstance(result, dict)
        assert result['result'] == 4.0
        assert result['expression'] == "2 + 2"
        assert 'explanation' not in result  # No explanation by default
    
    @pytest.mark.asyncio
    async def test_scientific_calculate_with_precision(self):
        """Test scientific calculation with precision."""
        result = await scientific_calculate("pi", precision=2)
        
        assert result['result'] == 3.14
        assert result['expression'] == "pi"
    
    @pytest.mark.asyncio
    async def test_scientific_calculate_with_explanation(self):
        """Test scientific calculation with explanation."""
        result = await scientific_calculate("sqrt(16)", explain=True)
        
        assert result['result'] == 4.0
        assert result['expression'] == "sqrt(16)"
        assert 'explanation' in result
        assert "square root" in result['explanation'].lower()
    
    @pytest.mark.asyncio
    async def test_scientific_calculate_trig_explanation(self):
        """Test trigonometric calculation with explanation."""
        result = await scientific_calculate("sin(pi/2)", explain=True)
        
        assert abs(result['result'] - 1.0) < 0.0001
        assert 'explanation' in result
        assert "trigonometric" in result['explanation'].lower()
    
    @pytest.mark.asyncio
    async def test_scientific_calculate_log_explanation(self):
        """Test logarithmic calculation with explanation."""
        result = await scientific_calculate("log(100)", explain=True, precision=1)
        
        # Natural log of 100
        assert 'explanation' in result
        assert "logarithmic" in result['explanation'].lower()
    
    @pytest.mark.asyncio
    async def test_scientific_calculate_error(self):
        """Test scientific calculation error handling."""
        with pytest.raises(ValueError):
            await scientific_calculate("1 / 0")
    
    @pytest.mark.asyncio
    async def test_scientific_calculate_complex_expression(self):
        """Test complex scientific calculation."""
        result = await scientific_calculate(
            "sqrt(16) + sin(pi/2) + log10(100)",
            explain=True,
            precision=3
        )
        
        # 4 + 1 + 2 = 7
        assert abs(result['result'] - 7.0) < 0.001
        assert result['expression'] == "sqrt(16) + sin(pi/2) + log10(100)"
        assert 'explanation' in result


class TestToolDecorators:
    """Test that tools are properly decorated."""
    
    def test_calculate_tool_metadata(self):
        """Test calculate tool metadata."""
        assert hasattr(simple_calculate, 'name')
        assert simple_calculate.name == "simple_calculator"
        assert hasattr(simple_calculate, 'description')
        assert "mathematical expressions" in simple_calculate.description
    
    def test_scientific_calculate_tool_metadata(self):
        """Test scientific calculator tool metadata."""
        assert hasattr(scientific_calculate, 'name')
        assert scientific_calculate.name == "scientific_calculator"
        assert hasattr(scientific_calculate, 'description')
        assert "scientific" in scientific_calculate.description
        assert "explanation" in scientific_calculate.description
    
    def test_tools_are_function_tools(self):
        """Test that decorated functions are FunctionTool instances."""
        from agenticraft.core.tool import FunctionTool
        
        # After decoration, they should be FunctionTool instances
        # or have tool-like properties
        assert hasattr(simple_calculate, 'run')
        assert hasattr(scientific_calculate, 'arun')
