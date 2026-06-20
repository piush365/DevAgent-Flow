"""
DevFlow Agent — PR Draft Route
POST /api/pr-draft — Streams a generated PR description from a git diff.
"""

import logging

from flask import Blueprint, request

from app.agents.pr_draft_agent import PRDraftAgent
from app.utils.stream_utils import agent_stream_response, error_stream_response

logger = logging.getLogger(__name__)
pr_draft_bp = Blueprint("pr_draft", __name__)


@pr_draft_bp.route("/api/pr-draft", methods=["POST"])
def pr_draft_route():
    """Generate a PR description from a git diff."""
    data = request.get_json(silent=True) or {}

    diff_text = data.get("diff", "").strip()
    if not diff_text:
        return error_stream_response(
            "⚠️ diff is required.\n",
            "Paste the output of: git diff HEAD\n",
        )

    issue_number: int | None = None
    raw_issue = data.get("issue_number")
    if raw_issue is not None:
        try:
            issue_number = int(raw_issue)
        except (ValueError, TypeError):
            pass  # Optional field — ignore invalid values

    logger.info(
        "PR Draft Agent request: %d chars, issue=%s", len(diff_text), issue_number
    )
    agent = PRDraftAgent()
    return agent_stream_response(agent.run(diff_text, issue_number=issue_number))
