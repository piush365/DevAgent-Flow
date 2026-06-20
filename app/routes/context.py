"""
DevFlow Agent — Context Route
POST /api/context — Streams a developer brief for a GitHub issue.
"""

import logging

from flask import Blueprint, request

from app.agents.context_agent import ContextAgent
from app.utils.stream_utils import agent_stream_response, error_stream_response

logger = logging.getLogger(__name__)
context_bp = Blueprint("context", __name__)


@context_bp.route("/api/context", methods=["POST"])
def context_route():
    """Analyze a GitHub issue and stream a ready-to-code developer brief."""
    data = request.get_json(silent=True) or {}

    issue_url = data.get("issue_url", "").strip()
    if not issue_url:
        return error_stream_response(
            '⚠️ issue_url is required.\n',
            'Send: {"issue_url": "https://github.com/owner/repo/issues/N"}\n',
        )

    include_comments: bool = bool(data.get("include_comments", True))
    show_file_tree: bool = bool(data.get("show_file_tree", True))

    logger.info("Context Agent request: %s", issue_url)
    agent = ContextAgent()
    return agent_stream_response(
        agent.run(
            issue_url,
            include_comments=include_comments,
            show_file_tree=show_file_tree,
        )
    )
