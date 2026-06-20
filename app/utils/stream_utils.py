"""
DevFlow Agent — Streaming Response Utilities
Shared helpers for building Flask streaming responses so each route
file doesn't repeat the same three-line Response(...) pattern.
"""

from typing import Generator

from flask import Response, stream_with_context

_STREAM_HEADERS = {"X-Accel-Buffering": "no"}


def agent_stream_response(generator: Generator[str, None, None]) -> Response:
    """
    Wrap an agent generator in a streamed Flask text/plain Response.

    Args:
        generator: Any generator that yields string chunks.

    Returns:
        A Flask Response that streams chunks to the client as they arrive.
    """
    return Response(
        stream_with_context(generator),
        mimetype="text/plain",
        headers=_STREAM_HEADERS,
    )


def error_stream_response(*messages: str, status: int = 400) -> Response:
    """
    Return a streaming error response containing one or more messages.

    Using a streaming response for errors keeps the frontend consistent —
    it always reads a text/plain stream regardless of success or failure.

    Args:
        *messages: One or more strings to yield in sequence.
        status:    HTTP status code (default 400).

    Returns:
        A Flask Response streaming the error messages.
    """
    def _generate() -> Generator[str, None, None]:
        for message in messages:
            yield message

    return Response(
        stream_with_context(_generate()),
        mimetype="text/plain",
        status=status,
        headers=_STREAM_HEADERS,
    )
