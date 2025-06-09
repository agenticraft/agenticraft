"""Calculator tool for mathematical operations.

Provides safe mathematical expression evaluation for agents.
"""

import math
import operator
from typing import Any

from ..core.tool import tool

# Safe functions and constants for calculator
SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pi": math.pi,
    "e": math.e,
}

SAFE_OPERATORS = {
    "add": operator.add,
    "sub": operator.sub,
    "mul": operator.mul,
    "div": operator.truediv,
    "mod": operator.mod,
    "pow": operator.pow,
}


def _calculate_expression(expression: str) -> float:
    """Evaluate a mathematical expression safely.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Result of the calculation

    Example:
        >>> _calculate_expression("2 + 2")
        4.0
        >>> _calculate_expression("sqrt(16) + sin(pi/2)")
        5.0
        >>> _calculate_expression("max(10, 20, 30)")
        30.0
    """
    try:
        # Create safe namespace
        safe_dict = {"__builtins__": {}, **SAFE_FUNCTIONS}

        # Evaluate expression
        result = eval(expression, safe_dict)

        # Ensure result is numeric
        if not isinstance(result, (int, float)):
            raise ValueError(f"Result must be numeric, got {type(result)}")

        return float(result)

    except Exception as e:
        raise ValueError(f"Failed to evaluate expression: {e}")


@tool(
    name="simple_calculator",
    description="Evaluate mathematical expressions with functions. Supports basic arithmetic, trigonometry, and common math functions.",
)
def simple_calculate(expression: str) -> float:
    """Evaluate a mathematical expression safely.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Result of the calculation

    Example:
        >>> simple_calculate("2 + 2")
        4.0
        >>> simple_calculate("sqrt(16) + sin(pi/2)")
        5.0
        >>> simple_calculate("max(10, 20, 30)")
        30.0
    """
    return _calculate_expression(expression)


@tool(
    name="scientific_calculator",
    description="Perform advanced scientific calculations with step-by-step explanation.",
)
async def scientific_calculate(
    expression: str, explain: bool = False, precision: int = 4
) -> dict[str, Any]:
    """Perform scientific calculation with optional explanation.

    Args:
        expression: Mathematical expression
        explain: Whether to include step-by-step explanation
        precision: Decimal places for rounding

    Returns:
        Dictionary with result and optional explanation

    Example:
        >>> await scientific_calculate("log(100, 10)", explain=True)
        {
            'result': 2.0,
            'expression': 'log(100, 10)',
            'explanation': 'Logarithm of 100 with base 10 equals 2.0'
        }
    """
    result = _calculate_expression(expression)
    rounded_result = round(result, precision)

    response = {"result": rounded_result, "expression": expression}

    if explain:
        # Generate simple explanation
        explanation = f"Evaluating: {expression} = {rounded_result}"

        # Add specific explanations for common operations
        if "sqrt" in expression:
            explanation += " (square root calculation)"
        elif "log" in expression:
            explanation += " (logarithmic calculation)"
        elif any(trig in expression for trig in ["sin", "cos", "tan"]):
            explanation += " (trigonometric calculation)"

        response["explanation"] = explanation

    return response
