"""
DevFlow Agent — Pytest Configuration and Shared Fixtures

Environment variables are set before any app imports so that Config
class-level attributes are evaluated with test values, not production keys.
"""

import os

# Set test credentials BEFORE importing any app module.
# Config class attributes are evaluated at import time, so these must
# be in place first.
os.environ.setdefault("GROQ_API_KEY", "test-groq-key-for-pytest")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key-for-pytest")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key-for-pytest")
os.environ.setdefault("GITHUB_TOKEN", "test-github-token-for-pytest")
os.environ.setdefault("FLASK_DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")  # quiet during tests

import pytest

from app import create_app


@pytest.fixture(scope="session")
def app():
    """Create a Flask app instance for the test session."""
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    # Disable rate limiting during tests
    flask_app.config["RATELIMIT_ENABLED"] = False
    return flask_app


@pytest.fixture
def client(app):
    """Return a Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_llm_stream(mocker):
    """
    Patch LLMClient.stream() to return a predictable sequence of chunks
    without making any real API calls.
    """
    def _stream(prompt, system=""):
        yield "Test "
        yield "LLM "
        yield "response."

    mocker.patch("app.utils.llm_client.LLMClient.stream", side_effect=_stream)
    return _stream
