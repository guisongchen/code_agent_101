"""Message service for chat history management.

Provides CRUD operations for chat messages with pagination support.

Epic 15: Message History Management
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.messages import Message, MessageRole, MessageType
from backend.schemas.message import (
    MessageCreateRequest,
    MessageHistoryRequest,
    MessageHistoryResponse,
    MessageResponse,
)


class MessageService:
    """Service for message history management.

    Handles storing and retrieving chat messages for tasks with
    support for pagination, threading, and metadata tracking.
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session for database operations.
        """
        self.session = session

    async def create(self, request: MessageCreateRequest) -> MessageResponse:
        """Create a new message.

        Args:
            request: Message creation request.

        Returns:
            Created MessageResponse.
        """
        # Auto-assign sequence if not provided
        sequence = request.sequence
        if sequence is None:
            sequence = await self._get_next_sequence(request.task_id, request.thread_id or "default")

        message = Message(
            task_id=request.task_id,
            role=request.role,
            content=request.content,
            message_type=request.message_type,
            thread_id=request.thread_id or "default",
            sequence=sequence,
            tokens_used=request.tokens_used,
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens,
            model=request.model,
            tool_name=request.tool_name,
            tool_call_id=request.tool_call_id,
            meta=request.meta or {},
            generated_at=datetime.utcnow(),
        )

        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)

        return MessageResponse.from_db_model(message)

    async def create_user_message(
        self,
        task_id: UUID,
        content: str,
        thread_id: str = "default",
        metadata: Optional[dict] = None,
    ) -> MessageResponse:
        """Create a user message.

        Convenience method for creating user messages.

        Args:
            task_id: Task ID.
            content: Message content.
            thread_id: Thread ID.
            metadata: Optional metadata.

        Returns:
            Created MessageResponse.
        """
        request = MessageCreateRequest(
            task_id=task_id,
            role=MessageRole.USER,
            content=content,
            message_type=MessageType.TEXT,
            thread_id=thread_id,
            meta=metadata or {},
        )
        return await self.create(request)

    async def create_assistant_message(
        self,
        task_id: UUID,
        content: str,
        thread_id: str = "default",
        model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> MessageResponse:
        """Create an assistant message.

        Convenience method for creating assistant (AI) messages.

        Args:
            task_id: Task ID.
            content: Message content.
            thread_id: Thread ID.
            model: Model used for generation.
            tokens_used: Total tokens used.
            prompt_tokens: Prompt tokens used.
            completion_tokens: Completion tokens used.
            metadata: Optional metadata.

        Returns:
            Created MessageResponse.
        """
        request = MessageCreateRequest(
            task_id=task_id,
            role=MessageRole.ASSISTANT,
            content=content,
            message_type=MessageType.TEXT,
            thread_id=thread_id,
            model=model,
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            meta=metadata or {},
        )
        return await self.create(request)

    async def create_tool_message(
        self,
        task_id: UUID,
        content: str,
        tool_name: str,
        tool_call_id: Optional[str] = None,
        message_type: MessageType = MessageType.TOOL_RESULT,
        thread_id: str = "default",
        metadata: Optional[dict] = None,
    ) -> MessageResponse:
        """Create a tool message.

        Convenience method for creating tool call/result messages.

        Args:
            task_id: Task ID.
            content: Message content.
            tool_name: Tool name.
            tool_call_id: Tool call ID.
            message_type: Message type (tool_call or tool_result).
            thread_id: Thread ID.
            metadata: Optional metadata.

        Returns:
            Created MessageResponse.
        """
        request = MessageCreateRequest(
            task_id=task_id,
            role=MessageRole.TOOL,
            content=content,
            message_type=message_type,
            thread_id=thread_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            meta=metadata or {},
        )
        return await self.create(request)

    async def get(self, message_id: UUID) -> Optional[MessageResponse]:
        """Get a message by ID.

        Args:
            message_id: Message UUID.

        Returns:
            MessageResponse if found, None otherwise.
        """
        result = await self.session.execute(
            select(Message).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()

        return MessageResponse.from_db_model(message) if message else None

    async def get_history(
        self,
        task_id: UUID,
        request: Optional[MessageHistoryRequest] = None,
    ) -> MessageHistoryResponse:
        """Get message history for a task.

        Args:
            task_id: Task ID.
            request: History request with pagination options.

        Returns:
            MessageHistoryResponse with messages and pagination info.
        """
        if request is None:
            request = MessageHistoryRequest()

        # Build base query
        conditions = [Message.task_id == task_id]

        if request.thread_id:
            conditions.append(Message.thread_id == request.thread_id)

        if request.before_sequence is not None:
            conditions.append(Message.sequence < request.before_sequence)

        if request.after_sequence is not None:
            conditions.append(Message.sequence > request.after_sequence)

        # Get total count
        count_query = select(func.count()).where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get messages with pagination
        query = (
            select(Message)
            .where(and_(*conditions))
            .order_by(Message.sequence.asc())
            .offset(request.offset)
            .limit(request.limit)
        )

        result = await self.session.execute(query)
        messages = result.scalars().all()

        # Calculate has_more
        has_more = (request.offset + len(messages)) < total

        return MessageHistoryResponse(
            task_id=task_id,
            thread_id=request.thread_id,
            messages=[MessageResponse.from_db_model(m) for m in messages],
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
        )

    async def get_thread_messages(
        self,
        task_id: UUID,
        thread_id: str = "default",
        limit: int = 100,
    ) -> List[MessageResponse]:
        """Get all messages for a specific thread.

        Args:
            task_id: Task ID.
            thread_id: Thread ID.
            limit: Maximum number of messages.

        Returns:
            List of MessageResponse ordered by sequence.
        """
        result = await self.session.execute(
            select(Message)
            .where(
                and_(
                    Message.task_id == task_id,
                    Message.thread_id == thread_id,
                )
            )
            .order_by(Message.sequence.asc())
            .limit(limit)
        )
        messages = result.scalars().all()

        return [MessageResponse.from_db_model(m) for m in messages]

    async def get_latest_messages(
        self,
        task_id: UUID,
        thread_id: str = "default",
        count: int = 10,
    ) -> List[MessageResponse]:
        """Get the latest N messages for a thread.

        Args:
            task_id: Task ID.
            thread_id: Thread ID.
            count: Number of messages to get.

        Returns:
            List of MessageResponse ordered by sequence (oldest first).
        """
        result = await self.session.execute(
            select(Message)
            .where(
                and_(
                    Message.task_id == task_id,
                    Message.thread_id == thread_id,
                )
            )
            .order_by(Message.sequence.desc())
            .limit(count)
        )
        messages = result.scalars().all()

        # Reverse to get oldest first
        return [MessageResponse.from_db_model(m) for m in reversed(messages)]

    async def delete_task_messages(self, task_id: UUID) -> int:
        """Delete all messages for a task.

        Args:
            task_id: Task ID.

        Returns:
            Number of messages deleted.
        """
        result = await self.session.execute(
            select(Message).where(Message.task_id == task_id)
        )
        messages = result.scalars().all()

        for message in messages:
            await self.session.delete(message)

        return len(messages)

    async def delete_thread_messages(
        self,
        task_id: UUID,
        thread_id: str,
    ) -> int:
        """Delete all messages for a specific thread.

        Args:
            task_id: Task ID.
            thread_id: Thread ID.

        Returns:
            Number of messages deleted.
        """
        result = await self.session.execute(
            select(Message).where(
                and_(
                    Message.task_id == task_id,
                    Message.thread_id == thread_id,
                )
            )
        )
        messages = result.scalars().all()

        for message in messages:
            await self.session.delete(message)

        return len(messages)

    async def _get_next_sequence(self, task_id: UUID, thread_id: str) -> int:
        """Get the next sequence number for a thread.

        Args:
            task_id: Task ID.
            thread_id: Thread ID.

        Returns:
            Next sequence number (0 if no messages exist).
        """
        result = await self.session.execute(
            select(func.max(Message.sequence))
            .where(
                and_(
                    Message.task_id == task_id,
                    Message.thread_id == thread_id,
                )
            )
        )
        max_sequence = result.scalar()

        return (max_sequence + 1) if max_sequence is not None else 0

    async def count_messages(
        self,
        task_id: UUID,
        thread_id: Optional[str] = None,
    ) -> int:
        """Count messages for a task.

        Args:
            task_id: Task ID.
            thread_id: Optional thread ID filter.

        Returns:
            Number of messages.
        """
        conditions = [Message.task_id == task_id]

        if thread_id:
            conditions.append(Message.thread_id == thread_id)

        result = await self.session.execute(
            select(func.count()).where(and_(*conditions))
        )
        return result.scalar() or 0
