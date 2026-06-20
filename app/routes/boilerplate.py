"""
DevFlow Agent — Boilerplate Route
POST /api/boilerplate — Streams generated Python boilerplate.
"""

import logging

from flask import Blueprint, request

from app.agents.boilerplate_agent import BoilerplateAgent
from app.utils.stream_utils import agent_stream_response, error_stream_response

logger = logging.getLogger(__name__)
boilerplate_bp = Blueprint("boilerplate", __name__)


@boilerplate_bp.route("/api/boilerplate", methods=["POST"])
def boilerplate_route():
    """Generate Python boilerplate from a natural language description."""
    data = request.get_json(silent=True) or {}

    description = data.get("description", "").strip()
    if not description:
        return error_stream_response(
            '⚠️ description is required.\n',
            'Send: {"description": "Flask route for user registration"}\n',
        )

    style_ref: str | None = data.get("style_ref", "").strip() or None

    logger.info("Boilerplate Agent request (style_ref=%s)", bool(style_ref))
    agent = BoilerplateAgent()
    return agent_stream_response(agent.run(description, style_ref=style_ref))
