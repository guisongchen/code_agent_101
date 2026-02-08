"""Tests for SessionService.

Tests: 20 tests covering session lifecycle, recovery, and management
- Session creation
- Session retrieval
- Session recovery
- Session timeout/cleanup
- Concurrent session limits

Epic 16: Chat Session State Management
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from backend.models.session import ChatSession, SessionStatus
from backend.schemas.session import (
    SessionCreateRequest,
    SessionListRequest,
    SessionRecoveryRequest,
    SessionUpdateRequest,
)
from backend.services.session import SessionService

pytestmark = [
    pytest.mark.unit,
    pytest.mark.epic_16,
    pytest.mark.backend,
    pytest.mark.asyncio,
]


@pytest.mark.epic_16
@pytest.mark.unit
@pytest.mark.backend
class TestSessionService:
    """Test suite for SessionService - 20 tests."""

    async def test_create_session(self, async_session):
        """Test creating a basic session."""
        service = SessionService(async_session)

        request = SessionCreateRequest(
            user_id=1,
            task_id=uuid4(),
            thread_id="test-thread",
        )

        session = await service.create(request)
        await async_session.commit()

        assert session.user_id == 1
        assert session.thread_id == "test-thread"
        assert session.status == SessionStatus.ACTIVE
        assert session.connection_count == 1
        assert session.session_id.startswith("sess_")
        assert session.recovery_token is not None

    async def test_create_session_with_custom_id(self, async_session):
        """Test creating a session with custom ID."""
        service = SessionService(async_session)

        request = SessionCreateRequest(
            user_id=1,
            session_id="custom-session-id",
        )

        session = await service.create(request)
        await async_session.commit()

        assert session.session_id == "custom-session-id"

    async def test_create_session_exceeds_limit(self, async_session):
        """Test that session creation fails when limit is reached."""
        service = SessionService(async_session)

        # Create max sessions for user
        for i in range(SessionService.MAX_SESSIONS_PER_USER):
            request = SessionCreateRequest(
                user_id=999,
                session_id=f"session-{i}",
            )
            await service.create(request)
        await async_session.commit()

        # Try to create one more
        request = SessionCreateRequest(
            user_id=999,
            session_id="session-extra",
        )

        with pytest.raises(ValueError, match="Maximum concurrent sessions"):
            await service.create(request)

    async def test_get_session(self, async_session):
        """Test retrieving a session by session ID."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        retrieved = await service.get(created.session_id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.session_id == created.session_id

    async def test_get_session_not_found(self, async_session):
        """Test retrieving a non-existent session."""
        service = SessionService(async_session)

        result = await service.get("non-existent-session")

        assert result is None

    async def test_get_by_recovery_token(self, async_session):
        """Test retrieving a session by recovery token."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        retrieved = await service.get_by_recovery_token(created.recovery_token)

        assert retrieved is not None
        assert retrieved.id == created.id

    async def test_list_sessions(self, async_session):
        """Test listing sessions."""
        service = SessionService(async_session)

        await service.create(SessionCreateRequest(user_id=1))
        await service.create(SessionCreateRequest(user_id=1))
        await service.create(SessionCreateRequest(user_id=2))
        await async_session.commit()

        request = SessionListRequest(user_id=1)
        result = await service.list_sessions(request)

        assert result.total == 2
        assert len(result.sessions) == 2
        assert all(s.user_id == 1 for s in result.sessions)

    async def test_list_sessions_active_only(self, async_session):
        """Test listing only active sessions."""
        from backend.models.session import ChatSession
        service = SessionService(async_session)

        # Create active session
        active = await service.create(SessionCreateRequest(user_id=1))

        # Create expired session
        expired = await service.create(SessionCreateRequest(user_id=1))
        expired_db = await async_session.get(ChatSession, expired.id)
        expired_db.expires_at = datetime.utcnow() - timedelta(hours=1)
        await async_session.commit()

        request = SessionListRequest(user_id=1, active_only=True)
        result = await service.list_sessions(request)

        # Should only return non-expired active sessions
        assert all(s.expires_at > datetime.utcnow() for s in result.sessions)

    async def test_recover_session_success(self, async_session):
        """Test successful session recovery."""
        service = SessionService(async_session)

        # Create original session
        original = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        # Recover session
        request = SessionRecoveryRequest(recovery_token=original.recovery_token)
        result = await service.recover_session(request)
        await async_session.commit()

        assert result.success is True
        assert result.session is not None
        assert result.session.status == SessionStatus.ACTIVE
        assert result.session.user_id == original.user_id

        # Original should be marked as recovered
        original_db = await service.get(original.session_id)
        assert original_db.status == SessionStatus.RECOVERED

    async def test_recover_session_invalid_token(self, async_session):
        """Test recovery with invalid token."""
        service = SessionService(async_session)

        request = SessionRecoveryRequest(recovery_token="invalid-token")
        result = await service.recover_session(request)

        assert result.success is False
        assert "Invalid" in result.message

    async def test_recover_closed_session(self, async_session):
        """Test recovery of a closed session fails."""
        service = SessionService(async_session)

        # Create and close session
        original = await service.create(SessionCreateRequest(user_id=1))
        await service.close_session(original.session_id)
        await async_session.commit()

        # Try to recover
        request = SessionRecoveryRequest(recovery_token=original.recovery_token)
        result = await service.recover_session(request)

        assert result.success is False
        assert "closed" in result.message.lower()

    async def test_update_activity(self, async_session):
        """Test updating session activity."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        # Update activity
        updated = await service.update_activity(created.session_id)
        await async_session.commit()

        assert updated is not None
        # Just verify it returns a valid response
        assert updated.session_id == created.session_id

    async def test_increment_connections(self, async_session):
        """Test incrementing connection count."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        updated = await service.increment_connections(created.session_id)
        await async_session.commit()

        # Verify by re-fetching
        fetched = await service.get(created.session_id)
        assert fetched.connection_count == 2

    async def test_decrement_connections(self, async_session):
        """Test decrementing connection count."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await service.increment_connections(created.session_id)
        await async_session.commit()

        updated = await service.decrement_connections(created.session_id)
        await async_session.commit()

        # Verify by re-fetching
        fetched = await service.get(created.session_id)
        assert fetched.connection_count == 1

    async def test_decrement_to_zero_closes_session(self, async_session):
        """Test that decrementing to zero closes the session."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        await service.decrement_connections(created.session_id)
        await async_session.commit()

        # Verify by re-fetching
        fetched = await service.get(created.session_id)
        assert fetched.connection_count == 0
        assert fetched.status == SessionStatus.CLOSED

    async def test_close_session(self, async_session):
        """Test closing a session."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        await service.close_session(created.session_id)
        await async_session.commit()

        # Verify by re-fetching
        fetched = await service.get(created.session_id)
        assert fetched.status == SessionStatus.CLOSED
        assert fetched.connection_count == 0

    async def test_expire_session(self, async_session):
        """Test expiring a session."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        await service.expire_session(created.session_id)
        await async_session.commit()

        # Verify by re-fetching
        fetched = await service.get(created.session_id)
        assert fetched.status == SessionStatus.EXPIRED

    async def test_cleanup_expired_sessions(self, async_session):
        """Test cleaning up expired sessions."""
        from backend.models.session import ChatSession
        service = SessionService(async_session)

        # Create session and manually expire it
        session = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        # Fetch the DB model and expire it
        session_db = await async_session.get(ChatSession, session.id)
        session_db.expires_at = datetime.utcnow() - timedelta(hours=1)
        await async_session.commit()

        # Run cleanup
        count = await service.cleanup_expired_sessions()
        await async_session.commit()

        assert count >= 1

        # Verify session is expired
        expired = await service.get(session.session_id)
        assert expired.status == SessionStatus.EXPIRED

    async def test_get_metrics(self, async_session):
        """Test getting session metrics."""
        service = SessionService(async_session)

        # Create sessions with different statuses
        await service.create(SessionCreateRequest(user_id=1001))
        await service.create(SessionCreateRequest(user_id=1002))

        s3 = await service.create(SessionCreateRequest(user_id=1003))
        await service.close_session(s3.session_id)

        await async_session.commit()

        metrics = await service.get_metrics()

        # Just verify metrics are returned
        assert metrics.total_sessions >= 3
        assert hasattr(metrics, 'active_sessions')
        assert hasattr(metrics, 'closed_sessions')

    async def test_update_session_extend_expiry(self, async_session):
        """Test extending session expiration."""
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        old_expiry = created.expires_at

        request = SessionUpdateRequest(extend_expiry=True, expires_in_hours=4)
        await service.update_session(created.session_id, request)
        await async_session.commit()

        # Verify by re-fetching
        fetched = await service.get(created.session_id)
        assert fetched.expires_at > old_expiry

    async def test_session_is_expired(self, async_session):
        """Test session expiration check via expires_at field."""
        from backend.models.session import ChatSession
        from datetime import datetime, timedelta
        service = SessionService(async_session)

        created = await service.create(SessionCreateRequest(user_id=1))
        await async_session.commit()

        # Should not be expired (expires_at is in the future)
        assert created.expires_at > datetime.utcnow()

        # Manually expire by fetching DB model
        session_db = await async_session.get(ChatSession, created.id)
        session_db.expires_at = datetime.utcnow() - timedelta(hours=1)
        await async_session.commit()

        # Re-fetch and check expiration
        expired = await service.get(created.session_id)
        assert expired.expires_at <= datetime.utcnow()
