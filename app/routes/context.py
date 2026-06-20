"""
DevFlow Agent — Context Route
POST /api/context — Streams GitHub issue analysis
"""

from flask import Blueprint, request, Response, stream_with_context
from app.agents.context_agent import ContextAgent

context_bp = Blueprint("context", __name__)


@context_bp.route("/api/context", methods=["POST"])
def context_route():
    """Analyze a GitHub issue and stream a developer brief."""
    data = request.get_json(silent=True) or {}
    issue_url = data.get("issue_url", "").strip()

    if not issue_url:
        def error_stream():
            yield "⚠️ issue_url is required.\n"
            yield "Send: {\"issue_url\": \"https://github.com/owner/repo/issues/N\"}\n"
        return Response(
            stream_with_context(error_stream()),
            mimetype="text/plain",
            headers={"X-Accel-Buffering": "no"},
        )

    agent = ContextAgent()
    return Response(
        stream_with_context(agent.run(issue_url)),
        mimetype="text/plain",
        headers={"X-Accel-Buffering": "no"},
    )
