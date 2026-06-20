"""
DevFlow Agent — Configuration
All values loaded from environment variables via python-dotenv.
"""

import os


class Config:
    # ── Required ───────────────────────────────────────────────
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

    # ── Optional — increases GitHub rate limit ─────────────────
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

    # ── Optional — LLM fallbacks ──────────────────────────────
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

    # ── Flask ──────────────────────────────────────────────────
    FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))

    # ── Streamlit → Flask URL ─────────────────────────────────
    FLASK_URL = os.environ.get("FLASK_URL", "http://localhost:5000")
