"""
DevFlow Agent — Flask Application Factory
"""

from flask import Flask, jsonify
import os


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # ── Register route blueprints ──────────────────────────────
    from app.routes.context import context_bp
    from app.routes.boilerplate import boilerplate_bp
    from app.routes.docs import docs_bp
    from app.routes.pr_draft import pr_draft_bp

    app.register_blueprint(context_bp)
    app.register_blueprint(boilerplate_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(pr_draft_bp)

    # ── Health endpoint ────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        """Check which API keys are configured."""
        return jsonify({
            "status": "ok",
            "providers": {
                "groq": bool(os.environ.get("GROQ_API_KEY")),
                "gemini": bool(os.environ.get("GEMINI_API_KEY")),
                "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
                "github_token": bool(os.environ.get("GITHUB_TOKEN")),
            }
        })

    return app
