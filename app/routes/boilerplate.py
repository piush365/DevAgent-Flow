"""
DevFlow Agent — Boilerplate Route
POST /api/boilerplate — Streams generated Python boilerplate
"""

from flask import Blueprint, request, Response, stream_with_context
from app.agents.boilerplate_agent import BoilerplateAgent

boilerplate_bp = Blueprint("boilerplate", __name__)


@boilerplate_bp.route("/api/boilerplate", methods=["POST"])
def boilerplate_route():
    """Generate Python boilerplate from a description."""
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    style_ref = data.get("style_ref", "").strip() or None

    if not description:
        def error_stream():
            yield "⚠️ description is required.\n"
            yield 'Send: {"description": "Flask route for user registration"}\n'
        return Response(
            stream_with_context(error_stream()),
            mimetype="text/plain",
            headers={"X-Accel-Buffering": "no"},
        )

    agent = BoilerplateAgent()
    return Response(
        stream_with_context(agent.run(description, style_ref=style_ref)),
        mimetype="text/plain",
        headers={"X-Accel-Buffering": "no"},
    )
