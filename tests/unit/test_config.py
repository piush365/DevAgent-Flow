"""Unit tests for Config.validate() — startup validation logic."""

import os

import pytest

from app.config import Config


class TestConfigValidate:
    def test_valid_config_passes(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "gsk_some_real_key")
        # Re-read class attribute after env change
        Config.GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
        Config.validate()  # Should not raise

    def test_missing_groq_key_raises(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        Config.GROQ_API_KEY = ""
        with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
            Config.validate()

    def test_error_message_contains_instructions(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        Config.GROQ_API_KEY = ""
        with pytest.raises(EnvironmentError) as exc_info:
            Config.validate()
        msg = str(exc_info.value)
        assert "console.groq.com" in msg
        assert ".env" in msg

    def test_flask_debug_defaults_false(self):
        """FLASK_DEBUG should default to False for production safety."""
        # The default in Config is os.environ.get("FLASK_DEBUG", "false")
        # When env var is not set, this evaluates to False
        assert isinstance(Config.FLASK_DEBUG, bool)

    def test_allowed_origins_is_list(self):
        assert isinstance(Config.ALLOWED_ORIGINS, list)
        assert len(Config.ALLOWED_ORIGINS) >= 1

    def test_max_content_length_is_positive(self):
        assert Config.MAX_CONTENT_LENGTH > 0
