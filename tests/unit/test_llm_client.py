"""
Unit tests for LLMClient fallback chain logic.
All provider calls are mocked — no real API keys needed.
"""

import pytest

from app.utils.llm_client import LLMClient


def _collect(gen) -> str:
    """Drain a generator and return the concatenated string."""
    return "".join(gen)


@pytest.fixture
def client():
    return LLMClient()


class TestGroqPrimaryPath:
    def test_groq_success_returns_content(self, client, mocker):
        mocker.patch.object(
            client, "_stream_groq", return_value=iter(["Hello ", "world"])
        )
        mocker.patch.object(client, "_groq_client", new=object())  # non-None
        result = _collect(client.stream("prompt"))
        assert result == "Hello world"

    def test_groq_not_called_when_no_key(self, mocker):
        c = LLMClient()
        c.groq_key = ""
        c._groq_client = None
        c.gemini_key = None
        c.openrouter_key = None
        result = _collect(c.stream("prompt"))
        assert "unavailable" in result.lower()


class TestFallbackChain:
    def test_groq_rate_limit_falls_to_gemini(self, client, mocker):
        mocker.patch.object(
            client,
            "_stream_groq",
            side_effect=Exception("429 rate limit exceeded"),
        )
        mocker.patch.object(client, "_groq_client", new=object())
        mocker.patch.object(
            client, "_stream_gemini", return_value=iter(["Gemini response"])
        )
        client.gemini_key = "fake-key"

        result = _collect(client.stream("prompt"))
        assert "Gemini response" in result

    def test_groq_and_gemini_fail_falls_to_openrouter(self, client, mocker):
        mocker.patch.object(client, "_stream_groq", side_effect=Exception("429"))
        mocker.patch.object(client, "_groq_client", new=object())
        mocker.patch.object(
            client, "_stream_gemini", side_effect=Exception("quota exceeded")
        )
        mocker.patch.object(
            client, "_stream_openrouter", return_value=iter(["OR response"])
        )
        client.gemini_key = "fake-key"
        client.openrouter_key = "fake-key"

        result = _collect(client.stream("prompt"))
        assert "OR response" in result

    def test_all_providers_fail_yields_error(self, client, mocker):
        mocker.patch.object(client, "_stream_groq", side_effect=Exception("429"))
        mocker.patch.object(client, "_groq_client", new=object())
        mocker.patch.object(client, "_stream_gemini", side_effect=Exception("429"))
        mocker.patch.object(client, "_stream_openrouter", side_effect=Exception("500"))
        client.gemini_key = "fake-key"
        client.openrouter_key = "fake-key"

        result = _collect(client.stream("prompt"))
        assert "unavailable" in result.lower() or "error" in result.lower()

    def test_no_gemini_key_skips_gemini(self, client, mocker):
        mocker.patch.object(client, "_stream_groq", side_effect=Exception("429"))
        mocker.patch.object(client, "_groq_client", new=object())
        gemini_mock = mocker.patch.object(client, "_stream_gemini")
        mocker.patch.object(client, "_stream_openrouter", return_value=iter(["OR"]))
        client.gemini_key = None
        client.openrouter_key = "fake-key"

        _collect(client.stream("prompt"))
        gemini_mock.assert_not_called()


class TestProviderErrorMessages:
    def test_rate_limit_notice_mentions_next_provider(self, client, mocker):
        mocker.patch.object(client, "_stream_groq", side_effect=Exception("429"))
        mocker.patch.object(client, "_groq_client", new=object())
        mocker.patch.object(client, "_stream_gemini", return_value=iter(["ok"]))
        client.gemini_key = "key"

        result = _collect(client.stream("prompt"))
        # The fallback notice should appear before the Gemini response
        assert "⚡" in result or "Gemini" in result

    def test_non_rate_limit_error_still_falls_through(self, client, mocker):
        mocker.patch.object(
            client, "_stream_groq", side_effect=Exception("connection refused")
        )
        mocker.patch.object(client, "_groq_client", new=object())
        mocker.patch.object(
            client, "_stream_gemini", return_value=iter(["fallback ok"])
        )
        client.gemini_key = "key"

        result = _collect(client.stream("prompt"))
        assert "fallback ok" in result
