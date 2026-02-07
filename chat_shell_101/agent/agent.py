"""
LangGraph ReAct agent for Chat Shell 101.
"""

from typing import Dict, List, Any, AsyncGenerator, Annotated, Optional
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.base import BaseCheckpointSaver

from ..config import config as global_config
from ..tools.registry import tool_registry
from ..tools.base import PromptModifierTool
from ..utils import format_tool_call, format_tool_result, format_thinking
from ..models import ModelFactory, ModelConfig, ProviderConfig
from .config import AgentConfig
from .compressor import MessageCompressor, CompressionStrategy


class ToolIterationLimitError(Exception):
    """Raised when tool iteration limit is exceeded."""
    pass


class AgentState(BaseModel):
    """State for the agent graph."""
    messages: Annotated[List[Any], add_messages] = []
    iteration_count: int = Field(default=0, description="Number of tool execution cycles")
    system_prompt: str = Field(default="You are a helpful AI assistant.", description="Current system prompt")


class ChatAgent:
    """Chat agent with ReAct pattern using LangGraph."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.llm = None
        self.tools = []
        self.tools_by_name = {}
        self.graph = None
        self._initialized = False
        self._checkpointer: Optional[BaseCheckpointSaver] = None
        self._compressor: Optional[MessageCompressor] = None

        # Initialize compressor if context compression is enabled
        if self.config.compress_context:
            self._compressor = MessageCompressor(
                model=self.config.model or "gpt-4",
                max_tokens=self.config.max_context_tokens,
                compression_threshold=self.config.compression_threshold,
                keep_recent_messages=self.config.keep_recent_messages,
                strategy=CompressionStrategy.WINDOW,
            )

    def with_checkpointer(self, checkpointer: BaseCheckpointSaver) -> "ChatAgent":
        """Set the checkpointer for session persistence."""
        self._checkpointer = checkpointer
        return self

    async def initialize(self):
        """Initialize the agent."""
        if self._initialized:
            return

        # Initialize LLM using ModelFactory
        model_config = ModelConfig(
            model=self.config.model or global_config.openai.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            streaming=True,
            provider_config=ProviderConfig(
                api_key=global_config.openai.api_key,
                base_url=global_config.openai.base_url,
            ),
        )

        self.llm = ModelFactory.create_model_from_config(model_config)

        # Get internal tools from registry (for execution)
        all_tools = tool_registry.get_all_tools()

        # Filter tools if specific tools are requested
        if self.config.tools:
            self.internal_tools = [
                t for t in all_tools if t.name in self.config.tools
            ]
        else:
            self.internal_tools = all_tools

        self.tools_by_name = {tool.name: tool for tool in self.internal_tools}

        # Get LangChain tools from registry (for LLM binding)
        self.tools = tool_registry.to_langchain_tools()
        if self.config.tools:
            # Filter to only requested tools
            self.tools = [t for t in self.tools if t.name in self.config.tools]

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph
        self.graph = self._build_graph()
        self._initialized = True

    def _get_modified_system_prompt(self, state: AgentState) -> str:
        """Get system prompt with modifications from PromptModifierTool tools."""
        current_prompt = state.system_prompt

        # Check each tool for PromptModifierTool capability
        for tool in self.internal_tools:
            if isinstance(tool, PromptModifierTool):
                current_prompt = tool.modify_prompt(current_prompt, state)

        return current_prompt

    def _build_graph(self):
        """Build the LangGraph state graph."""

        # Define nodes
        async def agent_node(state: AgentState):
            """Node that calls the agent."""
            # Get potentially modified system prompt
            system_prompt = self._get_modified_system_prompt(state)

            # Prepare messages with system prompt
            messages = list(state.messages)

            # Replace or add system message
            has_system = False
            for i, msg in enumerate(messages):
                if isinstance(msg, SystemMessage):
                    messages[i] = SystemMessage(content=system_prompt)
                    has_system = True
                    break

            if not has_system and system_prompt:
                messages.insert(0, SystemMessage(content=system_prompt))

            # Apply context compression if enabled
            if self._compressor:
                compression_result = self._compressor.compress_if_needed(messages)
                messages = compression_result.messages

            # Call the LLM
            response = await self.llm_with_tools.ainvoke(messages)
            return {
                "messages": [response],
                "system_prompt": system_prompt,
            }

        async def tools_node(state: AgentState):
            """Node that executes tools."""
            last_message = state.messages[-1]

            tool_calls = last_message.tool_calls
            tool_messages = []

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call["id"]

                try:
                    # Execute the tool
                    result = await self._execute_tool(tool_name, tool_args)
                    tool_messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call_id,
                        )
                    )
                except Exception as e:
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: {e}",
                            tool_call_id=tool_call_id,
                        )
                    )

            # Increment iteration count
            new_count = state.iteration_count + 1

            return {
                "messages": tool_messages,
                "iteration_count": new_count,
            }

        def should_continue(state: AgentState):
            """Determine whether to continue to tools or end."""
            # Check iteration limit
            if state.iteration_count >= self.config.max_iterations:
                raise ToolIterationLimitError(
                    f"Tool iteration limit ({self.config.max_iterations}) exceeded. "
                    "The agent may be stuck in an infinite loop."
                )

            last_message = state.messages[-1]
            if last_message.tool_calls:
                return "tools"
            return END

        # Build the graph
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tools_node)

        # Define edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {"tools": "tools", END: END}
        )
        workflow.add_edge("tools", "agent")

        # Compile the graph with checkpointer if provided
        if self._checkpointer:
            return workflow.compile(checkpointer=self._checkpointer)
        else:
            return workflow.compile()

    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool by name with the given arguments."""
        if tool_name not in self.tools_by_name:
            raise ValueError(f"Tool not found: {tool_name}")

        tool = self.tools_by_name[tool_name]
        input_data = tool.input_schema(**tool_args)
        result = await tool.execute(input_data)

        if result.error:
            raise ValueError(result.error)

        return result.result

    async def stream(
        self,
        messages: List[Dict[str, str]],
        show_thinking: bool = False,
        thread_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream agent responses with token-level streaming."""
        if not self._initialized:
            await self.initialize()

        # Convert messages to LangChain format
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))

        # Prepare config for checkpointing
        run_config = {"configurable": {"thread_id": thread_id}} if thread_id else None

        # Accumulate the full response for tool call handling
        full_response = None

        # Stream from LLM
        async for chunk in self.llm_with_tools.astream(lc_messages):
            # Accumulate chunks to build the full message
            if full_response is None:
                full_response = chunk
            else:
                full_response += chunk

            # Stream content tokens as they arrive
            if chunk.content:
                yield {"type": "content", "data": {"text": chunk.content}}

        # Handle complete tool calls after streaming finishes
        if full_response and full_response.tool_calls:
            for tool_call in full_response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", "")

                # Skip incomplete tool calls
                if not tool_name or not tool_call_id:
                    continue

                if show_thinking:
                    yield {
                        "type": "thinking",
                        "data": {"text": f"Calling tool {tool_name}"}
                    }
                yield {"type": "tool_call", "data": {"tool": tool_name, "input": tool_args}}

                try:
                    result = await self._execute_tool(tool_name, tool_args)
                    yield {"type": "tool_result", "data": {"result": result}}

                    # Get follow-up response after tool execution
                    lc_messages.append(full_response)
                    lc_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))

                    # Stream the follow-up response token by token
                    async for followup in self.llm_with_tools.astream(lc_messages):
                        if followup.content:
                            yield {"type": "content", "data": {"text": followup.content}}
                except Exception as e:
                    yield {"type": "error", "data": {"message": str(e)}}

    async def invoke(
        self,
        messages: List[Dict[str, str]],
        thread_id: Optional[str] = None,
    ) -> str:
        """Invoke the agent and return the final response."""
        full_response = ""
        async for event in self.stream(messages, thread_id=thread_id):
            if event["type"] == "content":
                full_response += event["data"]["text"]
        return full_response


