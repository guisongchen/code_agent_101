"""
LangGraph ReAct agent for Chat Shell 101.
"""

import asyncio
from typing import Dict, List, Any, AsyncGenerator, Annotated
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from .config import config
from .tools.registry import tool_registry
from .utils import format_tool_call, format_tool_result, format_thinking


class AgentState(BaseModel):
    """State for the agent graph."""
    messages: Annotated[List[Any], add_messages] = []


class ChatAgent:
    """Chat agent with ReAct pattern using LangGraph."""

    def __init__(self):
        self.llm = None
        self.tools = []
        self.tools_by_name = {}
        self.graph = None
        self._initialized = False

    async def initialize(self):
        """Initialize the agent."""
        if self._initialized:
            return

        # Initialize LLM
        llm_kwargs = {
            "model": config.openai.model,
            "api_key": config.openai.api_key,
            "temperature": config.openai.temperature,
            "max_tokens": config.openai.max_tokens,
            "streaming": True,
        }
        if config.openai.base_url:
            llm_kwargs["base_url"] = config.openai.base_url

        self.llm = ChatOpenAI(**llm_kwargs)

        # Get internal tools from registry (for execution)
        self.internal_tools = tool_registry.get_all_tools()
        self.tools_by_name = {tool.name: tool for tool in self.internal_tools}

        # Get LangChain tools from registry (for LLM binding)
        self.tools = tool_registry.to_langchain_tools()

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph
        self.graph = self._build_graph()
        self._initialized = True

    def _build_graph(self):
        """Build the LangGraph state graph."""

        # Define nodes
        async def agent_node(state: AgentState):
            """Node that calls the agent."""
            # Call the LLM
            response = await self.llm_with_tools.ainvoke(state.messages)
            return {"messages": [response]}

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

            return {"messages": tool_messages}

        def should_continue(state: AgentState):
            """Determine whether to continue to tools or end."""
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

        # Compile the graph
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
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream agent responses."""
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

        # Initialize state
        initial_state = AgentState(messages=lc_messages)

        # Track which tool calls we've already processed
        processed_tool_calls = set()

        # Run the graph
        async for event in self.graph.astream(initial_state, stream_mode="values"):
            # Get the latest message
            if "messages" in event and event["messages"]:
                messages_list = event["messages"]
                last_message = messages_list[-1]

                if isinstance(last_message, AIMessage):
                    # Check if it's a tool call
                    if last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            tool_call_id = tool_call["id"]

                            # Skip if we've already processed this tool call
                            if tool_call_id in processed_tool_calls:
                                continue
                            processed_tool_calls.add(tool_call_id)

                            if show_thinking:
                                yield {
                                    "type": "thinking",
                                    "data": {
                                        "text": f"Calling tool {tool_call['name']} with args: {tool_call['args']}"
                                    }
                                }
                            yield {
                                "type": "tool_call",
                                "data": {
                                    "tool": tool_call["name"],
                                    "input": tool_call["args"],
                                }
                            }

                            # Find the corresponding ToolMessage in the state
                            tool_result_found = False
                            for msg in reversed(messages_list):
                                if isinstance(msg, ToolMessage) and msg.tool_call_id == tool_call_id:
                                    yield {
                                        "type": "tool_result",
                                        "data": {"result": msg.content}
                                    }
                                    tool_result_found = True
                                    break

                            if not tool_result_found:
                                # Tool hasn't been executed yet, execute it now
                                try:
                                    result = await self._execute_tool(
                                        tool_call["name"], tool_call["args"]
                                    )
                                    yield {
                                        "type": "tool_result",
                                        "data": {"result": result}
                                    }
                                except Exception as e:
                                    yield {
                                        "type": "error",
                                        "data": {"message": f"Tool execution error: {e}"}
                                    }
                    else:
                        # It's a regular response
                        if last_message.content:
                            yield {
                                "type": "content",
                                "data": {"text": last_message.content}
                            }
                elif isinstance(last_message, HumanMessage):
                    # User message, skip
                    pass

    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke the agent and return the final response."""
        full_response = ""
        async for event in self.stream(messages):
            if event["type"] == "content":
                full_response += event["data"]["text"]
        return full_response


# Global agent instance
_agent_instance = None


async def get_agent() -> ChatAgent:
    """Get or create the global agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ChatAgent()
        await _agent_instance.initialize()
    return _agent_instance
