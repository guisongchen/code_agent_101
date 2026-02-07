"""
Calculator tool for basic arithmetic operations.
"""

import ast
import operator
from typing import Any, Dict
from .base import BaseTool, ToolInput, ToolOutput
from pydantic import BaseModel, Field


class CalculatorInput(ToolInput):
    """Input schema for calculator tool."""
    expression: str = Field(..., description="Arithmetic expression to evaluate")


class CalculatorTool(BaseTool):
    """Calculator tool for basic arithmetic operations."""

    name = "calculator"
    description = "Evaluate basic arithmetic expressions. Supports +, -, *, /, //, %, **, and parentheses."
    input_schema = CalculatorInput

    # Safe operators
    _safe_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _safe_eval(self, expression: str) -> Any:
        """Safely evaluate arithmetic expression."""
        # Normalize whitespace
        expression = ' '.join(expression.split())
        try:
            # Parse expression into AST
            tree = ast.parse(expression, mode='eval')

            # Define safe evaluation function
            def _eval_node(node):
                if isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.UnaryOp):
                    operand = _eval_node(node.operand)
                    op_type = type(node.op)
                    if op_type in self._safe_operators:
                        return self._safe_operators[op_type](operand)
                    else:
                        raise ValueError(f"Unsupported unary operator: {op_type}")
                elif isinstance(node, ast.BinOp):
                    left = _eval_node(node.left)
                    right = _eval_node(node.right)
                    op_type = type(node.op)
                    if op_type in self._safe_operators:
                        return self._safe_operators[op_type](left, right)
                    else:
                        raise ValueError(f"Unsupported binary operator: {op_type}")
                elif isinstance(node, ast.Constant):
                    return node.value
                else:
                    raise ValueError(f"Unsupported node type: {type(node)}")

            result = _eval_node(tree.body)
            return result
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as e:
            raise ValueError(f"Invalid expression: {e}")

    async def execute(self, input_data: CalculatorInput) -> ToolOutput:
        """Execute calculator tool."""
        try:
            result = self._safe_eval(input_data.expression)
            return ToolOutput(result=str(result))
        except Exception as e:
            return ToolOutput(result="", error=str(e))