"""Tests for calculator tools."""

import pytest
import math

from agenticraft.tools.calculator import (
    simple_calculate,
    scientific_calculate,
    SAFE_FUNCTIONS,
    SAFE_OPERATORS
)
from agenticraft.core.exceptions import ToolExecutionError


class TestSimpleCalculateTool:
    """Test the basic simple_calculate tool."""
    
    def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        assert simple_calculate.run(expression="2 + 2") == 4.0
        assert simple_calculate.run(expression="10 - 3") == 7.0
        assert simple_calculate.run(expression="5 * 6") == 30.0
        assert simple_calculate.run(expression="20 / 4") == 5.0
        assert simple_calculate.run(expression="10 % 3") == 1.0
        assert simple_calculate.run(expression="2 ** 3") == 8.0
    
    def test_order_of_operations(self):
        """Test correct order of operations."""
        assert simple_calculate.run(expression="2 + 3 * 4") == 14.0
        assert simple_calculate.run(expression="(2 + 3) * 4") == 20.0
        assert simple_calculate.run(expression="10 / 2 + 3") == 8.0
        assert simple_calculate.run(expression="10 / (2 + 3)") == 2.0
    
    def test_float_operations(self):
        """Test floating point operations."""
        assert simple_calculate.run(expression="3.14 * 2") == 6.28
        assert simple_calculate.run(expression="10.5 / 2.5") == 4.2
        assert abs(simple_calculate.run(expression="0.1 + 0.2") - 0.3) < 0.0001
    
    def test_safe_functions(self):
        """Test safe mathematical functions."""
        assert simple_calculate.run(expression="abs(-5)") == 5.0
        assert simple_calculate.run(expression="round(3.7)") == 4.0
        assert simple_calculate.run(expression="min(5, 3, 8)") == 3.0
        assert simple_calculate.run(expression="max(5, 3, 8)") == 8.0
        assert simple_calculate.run(expression="sum([1, 2, 3, 4])") == 10.0
        assert simple_calculate.run(expression="pow(2, 3)") == 8.0
    
    def test_math_functions(self):
        """Test math module functions."""
        assert simple_calculate.run(expression="sqrt(16)") == 4.0
        assert simple_calculate.run(expression="sqrt(2)") == pytest.approx(1.4142, rel=0.001)
        
        # Trigonometric functions
        assert simple_calculate.run(expression="sin(0)") == 0.0
        assert simple_calculate.run(expression="cos(0)") == 1.0
        assert abs(simple_calculate.run(expression="sin(pi/2)") - 1.0) < 0.0001
        
        # Logarithmic functions
        assert simple_calculate.run(expression="log(e)") == 1.0
        assert simple_calculate.run(expression="log10(100)") == 2.0
        assert simple_calculate.run(expression="exp(1)") == pytest.approx(math.e, rel=0.001)
    
    def test_constants(self):
        """Test mathematical constants."""
        assert simple_calculate.run(expression="pi") == pytest.approx(math.pi)
        assert simple_calculate.run(expression="e") == pytest.approx(math.e)
        assert simple_calculate.run(expression="2 * pi") == pytest.approx(2 * math.pi)
    
    def test_complex_expressions(self):
        """Test complex mathematical expressions."""
        # Pythagorean theorem
        assert simple_calculate.run(expression="sqrt(3**2 + 4**2)") == 5.0
        
        # Circle area
        radius = 5
        expected_area = math.pi * radius ** 2
        assert simple_calculate.run(expression=f"pi * {radius}**2") == pytest.approx(expected_area)
        
        # Compound expression
        result = simple_calculate.run(expression="(sin(pi/4)**2 + cos(pi/4)**2)")
        assert result == pytest.approx(1.0, rel=0.0001)
    
    def test_invalid_expressions(self):
        """Test invalid expression handling."""
        with pytest.raises((ToolExecutionError, ValueError), match="Failed to evaluate"):
            simple_calculate.run(expression="2 +")
        
        with pytest.raises((ToolExecutionError, ValueError), match="Failed to evaluate"):
            simple_calculate.run(expression="invalid")
        
        with pytest.raises((ToolExecutionError, ValueError), match="Failed to evaluate"):
            simple_calculate.run(expression="(2 + 3")
        
        # Unsafe operations should fail
        with pytest.raises((ToolExecutionError, ValueError), match="Failed to evaluate"):
            simple_calculate.run(expression="__import__('os')")
        
        with pytest.raises((ToolExecutionError, ValueError), match="Failed to evaluate"):
            simple_calculate.run(expression="open('file.txt')")
    
    def test_non_numeric_result(self):
        """Test handling of non-numeric results."""
        with pytest.raises((ToolExecutionError, ValueError), match="Result must be numeric"):
            simple_calculate.run(expression="'hello'")
        
        with pytest.raises((ToolExecutionError, ValueError), match="Result must be numeric"):
            simple_calculate.run(expression="[1, 2, 3]")
    
    def test_tool_metadata(self):
        """Test tool metadata."""
        assert simple_calculate.name == "simple_calculator"
        assert "math" in simple_calculate.description.lower()
        assert hasattr(simple_calculate, 'run')


class TestScientificCalculateTool:
    """Test the scientific calculator tool."""
    
    @pytest.mark.asyncio
    async def test_basic_calculation(self):
        """Test basic scientific calculation."""
        result = await scientific_calculate.arun(expression="2 + 2")
        
        assert result['result'] == 4.0
        assert result['expression'] == "2 + 2"
        assert 'explanation' not in result
    
    @pytest.mark.asyncio
    async def test_with_explanation(self):
        """Test calculation with explanation."""
        result = await scientific_calculate.arun(expression="sqrt(16)", explain=True)
        
        assert result['result'] == 4.0
        assert result['expression'] == "sqrt(16)"
        assert 'explanation' in result
        assert "square root" in result['explanation'].lower()
    
    @pytest.mark.asyncio
    async def test_precision_control(self):
        """Test precision control."""
        # Default precision (4 decimal places)
        result = await scientific_calculate.arun(expression="pi")
        assert result['result'] == round(math.pi, 4)
        
        # Custom precision
        result = await scientific_calculate.arun(expression="pi", precision=2)
        assert result['result'] == round(math.pi, 2)
        
        result = await scientific_calculate.arun(expression="sqrt(2)", precision=6)
        assert result['result'] == round(math.sqrt(2), 6)
    
    @pytest.mark.asyncio
    async def test_trigonometric_explanation(self):
        """Test trigonometric calculations with explanation."""
        result = await scientific_calculate.arun(expression="sin(pi/2)", explain=True)
        
        assert result['result'] == 1.0
        assert "trigonometric" in result['explanation'].lower()
    
    @pytest.mark.asyncio
    async def test_logarithmic_explanation(self):
        """Test logarithmic calculations with explanation."""
        result = await scientific_calculate.arun(expression="log10(100)", explain=True)
        
        assert result['result'] == 2.0
        assert "logarithmic" in result['explanation'].lower()
    
    @pytest.mark.asyncio
    async def test_complex_scientific_calculation(self):
        """Test complex scientific calculations."""
        # Calculate standard deviation manually
        expression = "sqrt((sum([1, 4, 9, 16, 25]) - 5*3**2) / 4)"
        result = await scientific_calculate.arun(expression=expression, precision=3)
        
        assert 'result' in result
        assert 'expression' in result
        # Verify it's calculated correctly (std dev of [1,2,3,4,5])
        assert result['result'] == pytest.approx(1.581, rel=0.001)
    
    @pytest.mark.asyncio
    async def test_tool_metadata(self):
        """Test scientific calculator metadata."""
        assert scientific_calculate.name == "scientific_calculator"
        assert "scientific" in scientific_calculate.description.lower()
        
        # Check parameters
        param_names = {p.name for p in scientific_calculate.parameters}
        assert "expression" in param_names
        assert "explain" in param_names
        assert "precision" in param_names


class TestSafeFunctions:
    """Test the safety of allowed functions."""
    
    def test_safe_functions_list(self):
        """Ensure only safe functions are exposed."""
        # Check that dangerous functions are not in SAFE_FUNCTIONS
        dangerous = ['eval', 'exec', 'compile', '__import__', 'open', 'file']
        for func in dangerous:
            assert func not in SAFE_FUNCTIONS
        
        # Check expected functions are present
        expected = ['abs', 'round', 'min', 'max', 'sum', 'sqrt', 'sin', 'cos']
        for func in expected:
            assert func in SAFE_FUNCTIONS
    
    def test_no_system_access(self):
        """Ensure no system access through calculator."""
        # These should all fail
        dangerous_expressions = [
            "__import__('os').system('ls')",
            "open('/etc/passwd')",
            "eval('2+2')",
            "exec('print(1)')",
            "__builtins__",
            "globals()",
            "locals()",
        ]
        
        for expr in dangerous_expressions:
            with pytest.raises((ToolExecutionError, ValueError)):
                simple_calculate.run(expression=expr)
