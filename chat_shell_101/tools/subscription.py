"""
Subscription management tools for task creation and control.
"""

import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class CreateSubscriptionInput(ToolInput):
    """Input schema for create subscription tool."""
    task_description: str = Field(..., description="Description of the task to be performed")
    schedule: Optional[str] = Field(default=None, description="Schedule expression (cron format) or 'once'/'daily'/'weekly'")
    priority: str = Field(default="normal", description="Task priority: 'low', 'normal', 'high', 'urgent'")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional task metadata")


class SubscriptionInfo(BaseModel):
    """Subscription/task information."""
    id: str
    task_description: str
    status: str  # pending, running, completed, failed, cancelled
    created_at: str
    schedule: Optional[str] = None
    priority: str = "normal"
    result: Optional[str] = None
    error: Optional[str] = None


class CreateSubscriptionOutput(ToolOutput):
    """Output schema for create subscription tool."""
    subscription_id: str = ""
    status: str = ""
    message: str = ""


class SilentExitInput(ToolInput):
    """Input schema for silent exit tool.

    This tool allows the agent to gracefully exit a subscription task
    without producing visible output to the user.
    """
    reason: Optional[str] = Field(default=None, description="Reason for silent exit")
    status: str = Field(default="completed", description="Exit status: 'completed', 'failed', 'cancelled'")
    result_data: Optional[Dict[str, Any]] = Field(default=None, description="Result data to store")


class SilentExitOutput(ToolOutput):
    """Output schema for silent exit tool."""
    exit_code: int = 0
    message: str = ""


class CreateSubscriptionTool(BaseTool):
    """Tool for creating subscription tasks.

    Subscriptions are background tasks that can be scheduled
    to run periodically or executed once.

    Example:
        tool = CreateSubscriptionTool()
        result = await tool.execute(CreateSubscriptionInput(
            task_description="Daily report generation",
            schedule="daily",
            priority="normal"
        ))
    """

    name = "create_subscription"
    description = (
        "Create a new subscription or scheduled task. "
        "Use this to set up recurring tasks like daily reports, "
        "monitoring, or background processing. "
        "Returns a subscription ID for later reference."
    )
    input_schema = CreateSubscriptionInput

    def __init__(self, subscription_manager: Optional[Any] = None):
        """Initialize subscription tool.

        Args:
            subscription_manager: Optional subscription manager instance
        """
        self._manager = subscription_manager
        self._subscriptions: Dict[str, SubscriptionInfo] = {}

    async def execute(self, input_data: CreateSubscriptionInput) -> ToolOutput:
        """Execute create subscription."""
        try:
            # Generate subscription ID
            sub_id = str(uuid.uuid4())[:8]

            # Create subscription info
            subscription = SubscriptionInfo(
                id=sub_id,
                task_description=input_data.task_description,
                status="pending",
                created_at=datetime.now().isoformat(),
                schedule=input_data.schedule,
                priority=input_data.priority
            )

            self._subscriptions[sub_id] = subscription

            # If manager is available, register with it
            if self._manager:
                await self._register_with_manager(subscription, input_data)

            logger.info(f"Created subscription {sub_id}: {input_data.task_description}")

            message = f"Created subscription {sub_id}"
            if input_data.schedule:
                message += f" (scheduled: {input_data.schedule})"

            return CreateSubscriptionOutput(
                result=message,
                subscription_id=sub_id,
                status="pending",
                message=message
            )

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return ToolOutput(
                result="",
                error=f"Failed to create subscription: {str(e)}"
            )

    async def _register_with_manager(
        self, subscription: SubscriptionInfo, input_data: CreateSubscriptionInput
    ):
        """Register subscription with external manager."""
        # Placeholder for external manager integration
        pass

    def get_subscription(self, sub_id: str) -> Optional[SubscriptionInfo]:
        """Get subscription by ID."""
        return self._subscriptions.get(sub_id)

    def list_subscriptions(self, status: Optional[str] = None) -> List[SubscriptionInfo]:
        """List all subscriptions, optionally filtered by status."""
        subs = list(self._subscriptions.values())
        if status:
            subs = [s for s in subs if s.status == status]
        return subs


class SilentExitTool(BaseTool):
    """Tool for silently exiting a subscription task.

    This tool allows the agent to gracefully complete a subscription
    task without generating visible output. The result is stored but
    not shown to the user.

    Example:
        tool = SilentExitTool()
        result = await tool.execute(SilentExitInput(
            reason="Task completed successfully",
            status="completed",
            result_data={"processed": 100}
        ))
    """

    name = "silent_exit"
    description = (
        "Silently exit the current subscription task. "
        "Use this when a background task completes without "
        "needing to notify the user. Stores results internally."
    )
    input_schema = SilentExitInput

    def __init__(self, on_exit: Optional[callable] = None):
        """Initialize silent exit tool.

        Args:
            on_exit: Optional callback to call on exit
        """
        self._on_exit = on_exit

    async def execute(self, input_data: SilentExitInput) -> ToolOutput:
        """Execute silent exit."""
        try:
            exit_code = 0 if input_data.status == "completed" else 1

            # Prepare result
            result = {
                "status": input_data.status,
                "reason": input_data.reason,
                "result_data": input_data.result_data,
                "exited_at": datetime.now().isoformat()
            }

            # Call exit handler if provided
            if self._on_exit:
                await self._on_exit(result)

            logger.info(f"Silent exit with status: {input_data.status}")

            message = f"Task {input_data.status}"
            if input_data.reason:
                message += f": {input_data.reason}"

            return SilentExitOutput(
                result=message,
                exit_code=exit_code,
                message=message
            )

        except Exception as e:
            logger.error(f"Silent exit failed: {e}")
            return ToolOutput(
                result="",
                error=f"Exit failed: {str(e)}"
            )
