"""
DevFlow Agent — Docs Route
POST /api/docs — Streams documentation-grounded answers.
"""

import logging

from flask import Blueprint, request

from app.agents.docs_agent import DocsAgent
from app.utils.stream_utils import agent_stream_response, error_stream_response

logger = logging.getLogger(__name__)
docs_bp = Blueprint("docs", __name__)


@docs_bp.route("/api/docs", methods=["POST"])
def docs_route():
    """Answer a library question using official documentation."""
    data = request.get_json(silent=True) or {}

    question = data.get("question", "").strip()
    if not question:
        return error_stream_response(
            '⚠️ question is required.\n',
            'Send: {"library": "Flask", "question": "How do I use blueprints?"}\n',
        )

    library: str = data.get("library", "").strip()
    custom_url: str | None = data.get("custom_url", "").strip() or None

    if not library and not custom_url:
        return error_stream_response(
            '⚠️ Either library or custom_url is required.\n',
            'Send: {"library": "Flask", "question": "..."}\n'
            '   or {"custom_url": "https://...", "question": "..."}\n',
        )

    logger.info("Docs Agent request: library=%r question=%r", library, question[:60])
    agent = DocsAgent()
    return agent_stream_response(agent.run(library, question, custom_url=custom_url))
