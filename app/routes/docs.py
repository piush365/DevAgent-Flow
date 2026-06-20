"""
DevFlow Agent — Docs Route
POST /api/docs — Streams documentation-grounded answers
"""

from flask import Blueprint, request, Response, stream_with_context
from app.agents.docs_agent import DocsAgent

docs_bp = Blueprint("docs", __name__)


@docs_bp.route("/api/docs", methods=["POST"])
def docs_route():
    """Answer a library question using official documentation."""
    data = request.get_json(silent=True) or {}
    library = data.get("library", "").strip()
    question = data.get("question", "").strip()
    custom_url = data.get("custom_url", "").strip() or None

    if not question:
        def error_stream():
            yield "⚠️ question is required.\n"
            yield 'Send: {"library": "Flask", "question": "How do I use blueprints?"}\n'
        return Response(
            stream_with_context(error_stream()),
            mimetype="text/plain",
            headers={"X-Accel-Buffering": "no"},
        )

    if not library and not custom_url:
        def error_stream():
            yield "⚠️ Either library or custom_url is required.\n"
            yield 'Send: {"library": "Flask", "question": "..."} or {"custom_url": "https://...", "question": "..."}\n'
        return Response(
            stream_with_context(error_stream()),
            mimetype="text/plain",
            headers={"X-Accel-Buffering": "no"},
        )

    agent = DocsAgent()
    return Response(
        stream_with_context(agent.run(library, question, custom_url=custom_url)),
        mimetype="text/plain",
        headers={"X-Accel-Buffering": "no"},
    )
