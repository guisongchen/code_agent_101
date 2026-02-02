"""
Unit tests for base tool interface.
"""
import pytest
from typing import Any, Dict
from pydantic import BaseModel, Field

from chat_shell_101.tools.base import BaseTool, ToolInput, ToolOutput


class TestToolInput:
    """Test suite for ToolInput base class."""

    def test_tool_input_is_pydantic_model(self) -> None:
        """Test that ToolInput is a Pydantic BaseModel."""
        assert issubclass(ToolInput, BaseModel)

    def test_tool_input_empty_by_default(self) -> None:
        """Test that ToolInput has no fields by default."""
        # Create instance
        input_data = ToolInput()

        # Should have no fields (except internal Pydantic fields)
        assert hasattr(input_data, "model_dump")
        # model_dump() should return empty dict for base ToolInput
        assert input_data.model_dump() == {}

    def test_tool_input_can_be_extended(self) -> None:
        """Test that ToolInput can be extended with fields."""
        class ExtendedToolInput(ToolInput):
            param1: str = Field(..., description="First parameter")
            param2: int = Field(default=42, description="Second parameter")

        # Create instance
        input_data = ExtendedToolInput(param1="test")

        assert input_data.param1 == "test"
        assert input_data.param2 == 42

        # Should have fields in model_dump
        dump = input_data.model_dump()
        assert dump["param1"] == "test"
        assert dump["param2"] == 42

    def test_tool_input_validation(self) -> None:
        """Test that ToolInput extensions validate data."""
        class ValidatedToolInput(ToolInput):
            value: int = Field(..., gt=0, description="Positive integer")

        # Valid input
        input_data = ValidatedToolInput(value=5)
        assert input_data.value == 5

        # Invalid input should raise validation error
        with pytest.raises(ValueError):
            ValidatedToolInput(value=-1)

    def test_tool_input_serialization(self) -> None:
        """Test ToolInput serialization to/from dict."""
        class SerializableToolInput(ToolInput):
            text: str = Field(..., description="Text parameter")
            count: int = Field(default=1, description="Count parameter")

        # Create from dict
        data = {"text": "hello", "count": 3}
        input_data = SerializableToolInput(**data)

        assert input_data.text == "hello"
        assert input_data.count == 3

        # Convert back to dict
        result = input_data.model_dump()
        assert result == data


class TestToolOutput:
    """Test suite for ToolOutput class."""

    def test_tool_output_is_pydantic_model(self) -> None:
        """Test that ToolOutput is a Pydantic BaseModel."""
        assert issubclass(ToolOutput, BaseModel)

    def test_tool_output_required_fields(self) -> None:
        """Test that ToolOutput has required fields."""
        # Create instance with only result
        output = ToolOutput(result="test result")

        assert output.result == "test result"
        assert output.error == ""  # Default value

    def test_tool_output_with_error(self) -> None:
        """Test ToolOutput with error field."""
        output = ToolOutput(result="", error="Something went wrong")

        assert output.result == ""
        assert output.error == "Something went wrong"

    def test_tool_output_with_result_and_error(self) -> None:
        """Test ToolOutput with both result and error."""
        output = ToolOutput(result="partial result", error="warning message")

        assert output.result == "partial result"
        assert output.error == "warning message"

    def test_tool_output_various_result_types(self) -> None:
        """Test ToolOutput with different result types."""
        # String result
        output1 = ToolOutput(result="string result")
        assert output1.result == "string result"

        # Integer result
        output2 = ToolOutput(result=42)
        assert output2.result == 42

        # List result
        output3 = ToolOutput(result=[1, 2, 3])
        assert output3.result == [1, 2, 3]

        # Dict result
        output4 = ToolOutput(result={"key": "value"})
        assert output4.result == {"key": "value"}

        # None result
        output5 = ToolOutput(result=None)
        assert output5.result is None

    def test_tool_output_equality(self) -> None:
        """Test ToolOutput equality comparison."""
        output1 = ToolOutput(result="test", error="")
        output2 = ToolOutput(result="test", error="")
        output3 = ToolOutput(result="different", error="")

        assert output1 == output2
        assert output1 != output3

    def test_tool_output_representation(self) -> None:
        """Test ToolOutput string representation."""
        output = ToolOutput(result="success", error="")

        repr_str = repr(output)
        assert "ToolOutput" in repr_str
        assert "result=" in repr_str
        assert "error=" in repr_str

    def test_tool_output_serialization(self) -> None:
        """Test ToolOutput serialization to/from dict."""
        output = ToolOutput(result={"data": "value"}, error="")

        # Convert to dict
        data = output.model_dump()
        assert data["result"] == {"data": "value"}
        assert data["error"] == ""

        # Create from dict
        new_output = ToolOutput(**data)
        assert new_output == output


class TestBaseTool:
    """Test suite for BaseTool abstract class."""

    def test_base_tool_is_abstract(self) -> None:
        """Test that BaseTool cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseTool()  # type: ignore

        assert "abstract" in str(exc_info.value).lower()

    def test_base_tool_abstract_methods(self) -> None:
        """Test that BaseTool has required abstract methods."""
        # Check abstract methods
        assert hasattr(BaseTool.execute, "__isabstractmethod__")
        assert BaseTool.execute.__isabstractmethod__ is True

        # Check class attributes (not abstract, but required)
        assert hasattr(BaseTool, "name")
        assert hasattr(BaseTool, "description")
        assert hasattr(BaseTool, "input_schema")

    def test_concrete_tool_implementation(self) -> None:
        """Test that a concrete BaseTool implementation works."""
        class ConcreteToolInput(ToolInput):
            input_param: str = Field(..., description="Input parameter")

        class ConcreteTool(BaseTool):
            name = "concrete_tool"
            description = "A concrete tool implementation"
            input_schema = ConcreteToolInput

            async def execute(self, input_data: ConcreteToolInput) -> ToolOutput:
                return ToolOutput(result=f"Processed: {input_data.input_param}")

        # Should be able to instantiate concrete implementation
        tool = ConcreteTool()
        assert isinstance(tool, BaseTool)

        # Check attributes
        assert tool.name == "concrete_tool"
        assert tool.description == "A concrete tool implementation"
        assert tool.input_schema == ConcreteToolInput

        # Check abstract method is implemented
        assert not hasattr(tool.execute, "__isabstractmethod__")

    def test_incomplete_tool_implementation(self) -> None:
        """Test that incomplete tool implementation raises error."""
        class IncompleteTool(BaseTool):
            name = "incomplete_tool"
            description = "Incomplete tool"
            # Missing input_schema and execute method

        with pytest.raises(TypeError) as exc_info:
            IncompleteTool()  # type: ignore

        assert "abstract" in str(exc_info.value).lower()

    def test_tool_to_dict_method(self) -> None:
        """Test to_dict method converts tool to dictionary."""
        class DictToolInput(ToolInput):
            param: str = Field(..., description="Parameter")

        class DictTool(BaseTool):
            name = "dict_tool"
            description = "Tool for testing to_dict method"
            input_schema = DictToolInput

            async def execute(self, input_data: DictToolInput) -> ToolOutput:
                return ToolOutput(result="test")

        tool = DictTool()
        tool_dict = tool.to_dict()

        assert isinstance(tool_dict, dict)
        assert tool_dict["name"] == "dict_tool"
        assert tool_dict["description"] == "Tool for testing to_dict method"
        assert tool_dict["args_schema"] == DictToolInput

    @pytest.mark.asyncio
    async def test_concrete_tool_execution(self) -> None:
        """Test executing a concrete tool."""
        class ExecutionToolInput(ToolInput):
            value: str = Field(..., description="Value to process")

        class ExecutionTool(BaseTool):
            name = "execution_tool"
            description = "Tool that processes values"
            input_schema = ExecutionToolInput

            async def execute(self, input_data: ExecutionToolInput) -> ToolOutput:
                processed = input_data.value.upper()
                return ToolOutput(result=processed)

        tool = ExecutionTool()
        input_data = ExecutionToolInput(value="hello")

        result = await tool.execute(input_data)

        assert isinstance(result, ToolOutput)
        assert result.result == "HELLO"
        assert result.error == ""

    @pytest.mark.asyncio
    async def test_tool_execution_with_error(self) -> None:
        """Test tool execution that returns an error."""
        class ErrorToolInput(ToolInput):
            cause_error: bool = Field(..., description="Whether to cause error")

        class ErrorTool(BaseTool):
            name = "error_tool"
            description = "Tool that can return errors"
            input_schema = ErrorToolInput

            async def execute(self, input_data: ErrorToolInput) -> ToolOutput:
                if input_data.cause_error:
                    return ToolOutput(result="", error="Error occurred")
                else:
                    return ToolOutput(result="Success")

        tool = ErrorTool()

        # Test error case
        input1 = ErrorToolInput(cause_error=True)
        result1 = await tool.execute(input1)
        assert result1.result == ""
        assert result1.error == "Error occurred"

        # Test success case
        input2 = ErrorToolInput(cause_error=False)
        result2 = await tool.execute(input2)
        assert result2.result == "Success"
        assert result2.error == ""

    def test_tool_inheritance(self) -> None:
        """Test tool inheritance hierarchy."""
        class ParentToolInput(ToolInput):
            base_param: str = Field(..., description="Base parameter")

        class ParentTool(BaseTool):
            name = "parent_tool"
            description = "Parent tool"
            input_schema = ParentToolInput

            async def execute(self, input_data: ParentToolInput) -> ToolOutput:
                return ToolOutput(result=f"Parent: {input_data.base_param}")

        class ChildToolInput(ParentToolInput):
            extra_param: int = Field(..., description="Extra parameter")

        class ChildTool(ParentTool):
            name = "child_tool"
            description = "Child tool"
            input_schema = ChildToolInput

            async def execute(self, input_data: ChildToolInput) -> ToolOutput:
                return ToolOutput(
                    result=f"Child: {input_data.base_param}, {input_data.extra_param}"
                )

        parent_tool = ParentTool()
        child_tool = ChildTool()

        assert isinstance(parent_tool, BaseTool)
        assert isinstance(child_tool, BaseTool)
        assert isinstance(child_tool, ParentTool)

        assert parent_tool.name == "parent_tool"
        assert child_tool.name == "child_tool"
        assert parent_tool.input_schema == ParentToolInput
        assert child_tool.input_schema == ChildToolInput

    def test_tool_with_complex_input_schema(self) -> None:
        """Test tool with complex input schema."""
        from typing import List, Optional

        class ComplexToolInput(ToolInput):
            name: str = Field(..., description="Name")
            count: int = Field(default=1, ge=1, le=100, description="Count")
            tags: List[str] = Field(default_factory=list, description="Tags")
            enabled: Optional[bool] = Field(default=None, description="Enabled flag")

        class ComplexTool(BaseTool):
            name = "complex_tool"
            description = "Tool with complex input schema"
            input_schema = ComplexToolInput

            async def execute(self, input_data: ComplexToolInput) -> ToolOutput:
                # Just return the input as string for testing
                return ToolOutput(result=str(input_data.model_dump()))

        tool = ComplexTool()

        # Test with minimal input
        input1 = ComplexToolInput(name="test")
        assert input1.name == "test"
        assert input1.count == 1
        assert input1.tags == []
        assert input1.enabled is None

        # Test with full input
        input2 = ComplexToolInput(
            name="full",
            count=5,
            tags=["tag1", "tag2"],
            enabled=True
        )
        assert input2.name == "full"
        assert input2.count == 5
        assert input2.tags == ["tag1", "tag2"]
        assert input2.enabled is True

        # Test validation
        with pytest.raises(ValueError):
            ComplexToolInput(name="test", count=0)  # count must be >= 1

        with pytest.raises(ValueError):
            ComplexToolInput(name="test", count=101)  # count must be <= 100