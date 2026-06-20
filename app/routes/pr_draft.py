"""
DevFlow Agent — PR Draft Route
POST /api/pr-draft — Streams generated PR descriptions
"""

from flask import Blueprint, request, Response, stream_with_context
from app.agents.pr_draft_agent import PRDraftAgent

pr_draft_bp = Blueprint("pr_draft", __name__)


@pr_draft_bp.route("/api/pr-draft", methods=["POST"])
def pr_draft_route():
    """Generate a PR description from a git diff."""
    data = request.get_json(silent=True) or {}
    diff_text = data.get("diff", "").strip()
    issue_number = data.get("issue_number")

    if not diff_text:
        def error_stream():
            yield "⚠️ diff is required.\n"
            yield "Paste the output of: git diff HEAD\n"
        return Response(
            stream_with_context(error_stream()),
            mimetype="text/plain",
            headers={"X-Accel-Buffering": "no"},
        )

    # Ensure issue_number is an int or None
    if issue_number is not None:
        try:
            issue_number = int(issue_number)
        except (ValueError, TypeError):
            issue_number = None

    agent = PRDraftAgent()
    return Response(
        stream_with_context(agent.run(diff_text, issue_number=issue_number)),
        mimetype="text/plain",
        headers={"X-Accel-Buffering": "no"},
    )
