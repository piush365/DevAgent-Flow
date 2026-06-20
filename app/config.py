"""
DevFlow Agent — Application Configuration
All values loaded from environment variables. Call Config.validate() at
startup to fail fast with a clear error if required vars are missing.
"""

import os


class Config:
    # ── Required ───────────────────────────────────────────────────────
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")

    # ── Optional — LLM fallbacks ───────────────────────────────────────
    GEMINI_API_KEY: str | None = os.environ.get("GEMINI_API_KEY")
    OPENROUTER_API_KEY: str | None = os.environ.get("OPENROUTER_API_KEY")

    # ── Optional — increases GitHub rate limit from 60 to 5,000/hr ─────
    GITHUB_TOKEN: str | None = os.environ.get("GITHUB_TOKEN")

    # ── Flask ──────────────────────────────────────────────────────────
    FLASK_PORT: int = int(os.environ.get("FLASK_PORT", 5000))
    FLASK_DEBUG: bool = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # ── Logging ───────────────────────────────────────────────────────
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()

    # ── Streamlit → Flask URL (configurable for Docker deployments) ────
    FLASK_URL: str = os.environ.get("FLASK_URL", "http://localhost:5000")

    # ── CORS ──────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        o.strip()
        for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
        if o.strip()
    ]

    # ── Request limits ────────────────────────────────────────────────
    MAX_CONTENT_LENGTH: int = 5 * 1024 * 1024  # 5 MB request body cap

    @classmethod
    def validate(cls) -> None:
        """
        Raise EnvironmentError if required configuration is missing.
        Call this once at application startup for a fast-fail with clear
        guidance instead of a cryptic error deep inside an API call.
        """
        if not cls.GROQ_API_KEY:
            raise EnvironmentError(
                "\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  DevFlow Agent — Missing Required Configuration\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  GROQ_API_KEY is not set.\n\n"
                "  Steps to fix:\n"
                "  1. Copy the template:  cp .env.example .env\n"
                "  2. Get a free key at:  https://console.groq.com → API Keys\n"
                "  3. Add it to .env:     GROQ_API_KEY=gsk_...\n"
                "  4. Restart the server.\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
