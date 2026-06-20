"""
DevFlow Agent — Flask Application Factory
"""

import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import Config
from app.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create, configure, and return the Flask application."""
    setup_logging(Config.LOG_LEVEL)

    app = Flask(__name__)

    # ── Security: request body size cap ────────────────────────────────
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    # ── CORS ────────────────────────────────────────────────────────────
    CORS(app, origins=Config.ALLOWED_ORIGINS)
    logger.info("CORS enabled for origins: %s", Config.ALLOWED_ORIGINS)

    # ── Rate limiting ────────────────────────────────────────────────────
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["300 per hour", "2000 per day"],
        storage_uri="memory://",
    )

    # ── Register blueprints ──────────────────────────────────────────────
    from app.routes.context import context_bp
    from app.routes.boilerplate import boilerplate_bp
    from app.routes.docs import docs_bp
    from app.routes.pr_draft import pr_draft_bp

    app.register_blueprint(context_bp)
    app.register_blueprint(boilerplate_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(pr_draft_bp)

    # Apply tighter per-endpoint limits where GitHub API is involved
    limiter.limit("30 per hour")(
        app.view_functions.get("context.context_route")
        or _noop  # guard for test environments where blueprints may differ
    )

    # ── Health endpoint ──────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        """Return provider availability based on configured API keys."""
        return jsonify(
            {
                "status": "ok",
                "providers": {
                    "groq": bool(os.environ.get("GROQ_API_KEY")),
                    "gemini": bool(os.environ.get("GEMINI_API_KEY")),
                    "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
                    "github_token": bool(os.environ.get("GITHUB_TOKEN")),
                },
            }
        )

    logger.info("DevFlow Agent application created successfully.")
    return app


def _noop(*args, **kwargs):
    """No-op placeholder — used as a safe fallback for limiter.limit()."""
    pass
