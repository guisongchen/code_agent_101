"""
Streaming-specific exceptions.
"""


class StreamingError(Exception):
    """Base exception for streaming errors."""

    def __init__(self, message: str, stream_id: str = None):
        super().__init__(message)
        self.message = message
        self.stream_id = stream_id


class StreamNotFoundError(StreamingError):
    """Raised when a stream is not found."""

    pass


class StreamAlreadyExistsError(StreamingError):
    """Raised when attempting to create a stream that already exists."""

    pass


class StreamCompletedError(StreamingError):
    """Raised when attempting to interact with a completed stream."""

    pass


class StreamCancelledError(StreamingError):
    """Raised when a stream is cancelled."""

    pass


class ClientDisconnectedError(StreamingError):
    """Raised when a client disconnects unexpectedly."""

    pass


class BufferOverflowError(StreamingError):
    """Raised when the event buffer overflows."""

    pass


class InvalidOffsetError(StreamingError):
    """Raised when an invalid offset is requested."""

    pass


class StreamRecoveryError(StreamingError):
    """Raised when stream recovery fails."""

    pass
