"""
Tests for PromptModifierTool protocol - Epic 1: Core Agent System.
"""

import pytest
from chat_shell.tools.base import PromptModifierTool
from chat_shell.agent.agent import AgentState


pytestmark = [pytest.mark.unit, pytest.mark.epic_1]


class TestPromptModifierTool:
    """Test cases for PromptModifierTool protocol."""

    def test_protocol_interface(self):
        """Test that PromptModifierTool defines the expected interface."""

        class ValidModifier:
            def modify_prompt(self, current_prompt: str, state: AgentState) -> str:
                return current_prompt + " modified"

        # Should be able to instantiate
        modifier = ValidModifier()
        result = modifier.modify_prompt("test", AgentState())
        assert result == "test modified"

    def test_protocol_with_multiple_modifications(self):
        """Test protocol with multiple modifications."""

        class ContextModifier:
            def __init__(self, context):
                self.context = context

            def modify_prompt(self, current_prompt: str, state: AgentState) -> str:
                return f"{current_prompt}\n\nContext: {self.context}"

        modifier = ContextModifier("Important context")
        result = modifier.modify_prompt("You are helpful.", AgentState())

        assert "You are helpful." in result
        assert "Context: Important context" in result

    def test_protocol_state_access(self):
        """Test that modifier can access agent state."""

        class StateAwareModifier:
            def modify_prompt(self, current_prompt: str, state: AgentState) -> str:
                iteration_info = f"\n\nIteration: {state.iteration_count}"
                return current_prompt + iteration_info

        modifier = StateAwareModifier()
        state = AgentState(iteration_count=5)
        result = modifier.modify_prompt("Base prompt", state)

        assert "Iteration: 5" in result

    def test_protocol_conditional_modification(self):
        """Test conditional prompt modification based on state."""

        class ConditionalModifier:
            def modify_prompt(self, current_prompt: str, state: AgentState) -> str:
                if state.iteration_count > 3:
                    return current_prompt + "\n\nBe concise."
                return current_prompt

        modifier = ConditionalModifier()

        # Should not modify when iteration count is low
        state_low = AgentState(iteration_count=2)
        result_low = modifier.modify_prompt("Base", state_low)
        assert result_low == "Base"

        # Should modify when iteration count is high
        state_high = AgentState(iteration_count=5)
        result_high = modifier.modify_prompt("Base", state_high)
        assert "Be concise." in result_high
