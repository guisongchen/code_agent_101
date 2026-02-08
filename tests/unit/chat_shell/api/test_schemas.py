"""
Tests for API schema models.
"""

import pytest

from chat_shell.api.schemas import (
    ChatRequest,
    ChatResponse,
    ChatEvent,
    ChatMessage,
    MessageRole,
    SessionStatus,
    HealthResponse,
    ErrorResponse,
)


@pytest.mark.epic_4
@pytest.mark.unit
class TestChatSchemas:
    """Test API schema models."""

    def test_chat_message_creation(self):
        """Test ChatMessage creation."""
        msg = ChatMessage(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.timestamp is None

    def test_chat_request_creation(self):
        """Test ChatRequest creation."""
        request = ChatRequest(
            messages=[ChatMessage(role=MessageRole.USER, content="Hello")],
            session_id="test-session",
            model="gpt-4",
            temperature=0.7,
        )
        assert len(request.messages) == 1
        assert request.session_id == "test-session"
        assert request.model == "gpt-4"
        assert request.temperature == 0.7
        assert request.stream is True  # default

    def test_chat_request_defaults(self):
        """Test ChatRequest default values."""
        request = ChatRequest(
            messages=[ChatMessage(role=MessageRole.USER, content="Hello")],
        )
        assert request.temperature == 0.7
        assert request.max_tokens == 4096
        assert request.stream is True
        assert request.session_id is None

    def test_chat_response_creation(self):
        """Test ChatResponse creation."""
        response = ChatResponse(
            subtask_id="task-123",
            session_id="session-456",
            status="created",
        )
        assert response.subtask_id == "task-123"
        assert response.session_id == "session-456"
        assert response.status == "created"

    def test_chat_event_creation(self):
        """Test ChatEvent creation."""
        event = ChatEvent(
            event_type="content",
            data={"text": "Hello"},
        )
        assert event.event_type == "content"
        assert event.data == {"text": "Hello"}
        assert event.timestamp is not None

    def test_session_status_creation(self):
        """Test SessionStatus creation."""
        from datetime import datetime
        now = datetime.now()
        status = SessionStatus(
            subtask_id="task-123",
            session_id="session-456",
            status="running",
            created_at=now,
            message_count=5,
        )
        assert status.subtask_id == "task-123"
        assert status.session_id == "session-456"
        assert status.status == "running"
        assert status.message_count == 5

    def test_health_response_creation(self):
        """Test HealthResponse creation."""
        response = HealthResponse(
            status="healthy",
            version="0.1.0",
            uptime_seconds=60.5,
            active_sessions=3,
            models_available=["gpt-4", "gpt-3.5-turbo"],
        )
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.uptime_seconds == 60.5
        assert response.active_sessions == 3
        assert response.models_available == ["gpt-4", "gpt-3.5-turbo"]

    def test_error_response_creation(self):
        """Test ErrorResponse creation."""
        error = ErrorResponse(
            error_code="INVALID_REQUEST",
            message="Invalid request parameters",
            details={"field": "temperature"},
        )
        assert error.error_code == "INVALID_REQUEST"
        assert error.message == "Invalid request parameters"
        assert error.details == {"field": "temperature"}

    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"


pytestmark = [pytest.mark.unit, pytest.mark.chat_shell]
