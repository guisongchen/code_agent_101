"""
Unit tests for CalculatorTool.
"""
import pytest
import math

from chat_shell_101.tools.calculator import CalculatorTool, CalculatorInput
from chat_shell_101.tools.base import ToolOutput


class TestCalculatorTool:
    """Test suite for CalculatorTool."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create calculator tool instance."""
        return CalculatorTool()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "expression, expected",
        [
            # Basic arithmetic
            ("2 + 2", "4"),
            ("10 - 5", "5"),
            ("3 * 4", "12"),
            ("8 / 2", "4.0"),
            ("7 // 2", "3"),
            ("7 % 3", "1"),
            ("2 ** 3", "8"),
            # Negative numbers
            ("-5 + 3", "-2"),
            ("5 + -3", "2"),
            ("-5 * -3", "15"),
            # Floating point
            ("3.14 + 2.86", "6.0"),
            ("10.5 / 2", "5.25"),
            ("5.5 * 2", "11.0"),
            # Zero handling
            ("0 + 5", "5"),
            ("5 * 0", "0"),
            ("0 / 5", "0.0"),
        ]
    )
    async def test_basic_arithmetic(
        self, calculator: CalculatorTool, expression: str, expected: str
    ) -> None:
        """Test basic arithmetic operations."""
        input_data = CalculatorInput(expression=expression)
        result = await calculator.execute(input_data)

        assert result.error == ""
        assert result.result == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "expression, expected",
        [
            # Operator precedence
            ("2 + 3 * 4", "14"),  # Multiplication before addition
            ("(2 + 3) * 4", "20"),  # Parentheses override precedence
            ("2 * 3 + 4 * 5", "26"),  # Multiple operations
            ("2 ** 3 * 4", "32"),  # Exponentiation before multiplication
            ("2 * 3 ** 2", "18"),  # Exponentiation before multiplication
            # Complex expressions
            ("(1 + 2) * (3 + 4)", "21"),
            ("10 - (2 + 3) * 2", "0"),
            ("(5 + 3) // 2 + 1", "5"),
            ("2 * (3 + 4) / 2", "7.0"),
            # Nested parentheses
            ("((1 + 2) * 3) + 4", "13"),
            ("1 + (2 * (3 + 4))", "15"),
            ("(1 + (2 * 3)) * 4", "28"),
        ]
    )
    async def test_complex_expressions(
        self, calculator: CalculatorTool, expression: str, expected: str
    ) -> None:
        """Test complex expressions with parentheses and operator precedence."""
        input_data = CalculatorInput(expression=expression)
        result = await calculator.execute(input_data)

        assert result.error == ""
        assert result.result == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "expression, expected_error_contains",
        [
            # Division by zero
            ("5 / 0", "division by zero"),
            ("10 // 0", "integer division"),
            ("5 % 0", "integer division"),
            # Invalid syntax
            ("2 +", "Invalid expression"),
            ("* 5", "Invalid expression"),
            ("2 & 3", "Unsupported binary operator"),
            ("~5", "Unsupported unary operator"),
            # Empty or whitespace-only
            ("", "Invalid expression"),
            ("   ", "Invalid expression"),
            # Non-arithmetic expressions
            ("import os", "Invalid expression"),
            ("__import__('os')", "Invalid expression"),
            ("eval('2+2')", "Invalid expression"),
            # Malformed expressions
            ("2 + * 3", "Invalid expression"),
            ("(2 + 3", "Invalid expression"),
            ("2 + 3)", "Invalid expression"),
        ]
    )
    async def test_error_handling(
        self, calculator: CalculatorTool, expression: str, expected_error_contains: str
    ) -> None:
        """Test error handling for invalid expressions."""
        input_data = CalculatorInput(expression=expression)
        result = await calculator.execute(input_data)

        assert result.result == ""
        assert expected_error_contains in result.error

    @pytest.mark.asyncio
    async def test_large_numbers(self, calculator: CalculatorTool) -> None:
        """Test handling of large numbers."""
        input_data = CalculatorInput(expression="999999999 * 999999999")
        result = await calculator.execute(input_data)

        assert result.error == ""
        assert result.result == "999999998000000001"

    @pytest.mark.asyncio
    async def test_floating_point_precision(self, calculator: CalculatorTool) -> None:
        """Test floating point precision handling."""
        input_data = CalculatorInput(expression="0.1 + 0.2")
        result = await calculator.execute(input_data)

        assert result.error == ""
        # Note: 0.1 + 0.2 = 0.30000000000000004 in floating point
        assert abs(float(result.result) - 0.3) < 1e-10

    @pytest.mark.asyncio
    async def test_unary_operators(self, calculator: CalculatorTool) -> None:
        """Test unary operators."""
        test_cases = [
            ("+5", "5"),
            ("-5", "-5"),
            ("-(-5)", "5"),
            ("+(-5)", "-5"),
            ("-(2 + 3)", "-5"),
        ]

        for expression, expected in test_cases:
            input_data = CalculatorInput(expression=expression)
            result = await calculator.execute(input_data)

            assert result.error == ""
            assert result.result == expected

    @pytest.mark.asyncio
    async def test_safe_eval_security(self, calculator: CalculatorTool) -> None:
        """Test that safe_eval prevents dangerous operations."""
        dangerous_expressions = [
            "__import__('os').system('ls')",
            "eval('2+2')",
            "exec('import os')",
            "open('/etc/passwd').read()",
            "().__class__.__base__.__subclasses__()",
            "import os",
            "from os import system",
            "lambda: os.system('ls')",
        ]

        for expression in dangerous_expressions:
            input_data = CalculatorInput(expression=expression)
            result = await calculator.execute(input_data)

            assert result.result == ""
            assert "Invalid expression" in result.error

    def test_tool_metadata(self, calculator: CalculatorTool) -> None:
        """Test tool metadata (name, description, input schema)."""
        assert calculator.name == "calculator"
        assert "arithmetic expressions" in calculator.description.lower()
        assert calculator.input_schema == CalculatorInput

    @pytest.mark.asyncio
    async def test_tool_output_structure(self, calculator: CalculatorTool) -> None:
        """Test that tool output follows expected structure."""
        input_data = CalculatorInput(expression="2 + 2")
        result = await calculator.execute(input_data)

        assert isinstance(result, ToolOutput)
        assert hasattr(result, "result")
        assert hasattr(result, "error")
        assert result.result == "4"
        assert result.error == ""

    @pytest.mark.asyncio
    async def test_whitespace_handling(self, calculator: CalculatorTool) -> None:
        """Test that whitespace is handled correctly."""
        test_cases = [
            ("2+2", "4"),  # No spaces
            ("2 + 2", "4"),  # Normal spacing
            ("  2  +  2  ", "4"),  # Extra spaces
            ("\t2\t+\t2\t", "4"),  # Tabs
        ]

        for expression, expected in test_cases:
            input_data = CalculatorInput(expression=expression)
            result = await calculator.execute(input_data)

            assert result.error == ""
            assert result.result == expected

    @pytest.mark.asyncio
    async def test_mixed_number_types(self, calculator: CalculatorTool) -> None:
        """Test mixing integers and floats in expressions."""
        test_cases = [
            ("2 + 3.5", "5.5"),
            ("3.5 * 2", "7.0"),
            ("10 // 3.0", "3.0"),  # Floor division with float
            ("10.5 // 2", "5.0"),  # Floor division with float result
        ]

        for expression, expected in test_cases:
            input_data = CalculatorInput(expression=expression)
            result = await calculator.execute(input_data)

            assert result.error == ""
            assert result.result == expected