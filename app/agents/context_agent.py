"""
DevFlow Agent — Context Agent
Analyzes a GitHub issue and identifies relevant files to start working on.

Input:  GitHub issue URL, optional flags
Output: Streamed developer brief — summary, relevant files, starting point,
        open questions
"""

import logging
import re
from typing import Generator

from app.agents.base_agent import BaseAgent
from app.utils.github_client import GitHubClient

logger = logging.getLogger(__name__)

# Hard cap on files scored per request — prevents O(n) blocking on giant repos
_MAX_FILES_SCORED = 2_000
_TOP_N_FILES = 5


class ContextAgent(BaseAgent):
    """Generates a ready-to-code developer brief from a GitHub issue URL."""

    def __init__(self) -> None:
        super().__init__()
        self.github = GitHubClient()

    def run(
        self,
        issue_url: str,
        include_comments: bool = True,
        show_file_tree: bool = True,
    ) -> Generator[str, None, None]:
        """
        Fetch the issue, rank relevant files, and stream an LLM-generated brief.

        Args:
            issue_url:        Full GitHub issue URL.
            include_comments: Whether to fetch and include issue comments.
            show_file_tree:   Whether to fetch and rank the repo file tree.

        Yields:
            Text chunks for streaming to the frontend.
        """
        # ── Step 1: Fetch issue data ───────────────────────────────────
        logger.info("ContextAgent: fetching issue %s", issue_url)
        try:
            issue = self.github.fetch_issue(
                issue_url, include_comments=include_comments
            )
        except ValueError as exc:
            yield f"⚠️ {exc}\n"
            return
        except Exception as exc:
            yield self._github_error_message(exc)
            return

        yield f"📋 Fetched issue #{issue['number']}: {issue['title']}\n\n"

        # ── Step 2: Fetch repo file tree (optional) ────────────────────
        relevant_files: list[tuple[str, int]] = []

        if show_file_tree:
            try:
                file_tree = self.github.fetch_file_tree(issue["owner"], issue["repo"])
                yield f"📂 Repository has {len(file_tree)} files\n\n"
                relevant_files = self._rank_files_by_keyword(issue["body"], file_tree)
                if relevant_files:
                    yield "🔍 Top relevant files identified:\n"
                    for path, score in relevant_files:
                        yield f"   • {path} (relevance: {score})\n"
                    yield "\n"
            except Exception as exc:
                yield f"⚠️ Could not fetch file tree: {exc}\n"

        # ── Step 3: Build prompt and stream LLM response ───────────────
        prompt = self._build_prompt(issue, relevant_files)
        yield "---\n\n"
        yield from self._stream_llm(prompt)

    def _rank_files_by_keyword(
        self, issue_body: str, file_tree: list[str], top_n: int = _TOP_N_FILES
    ) -> list[tuple[str, int]]:
        """
        Score each file path by keyword overlap with the issue body.

        Uses pure string matching (no LLM) for deterministic, fast results.
        Caps the number of files scored to avoid blocking the Flask thread
        on very large repositories.

        Returns:
            List of (file_path, score) tuples sorted by score descending.
        """
        if not issue_body or not file_tree:
            return []

        keywords = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", issue_body.lower()))
        scored: list[tuple[str, int]] = []

        for path in file_tree[:_MAX_FILES_SCORED]:
            path_parts = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", path.lower()))
            overlap = len(keywords & path_parts)
            if overlap > 0:
                scored.append((path, overlap))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def _build_prompt(self, issue: dict, relevant_files: list[tuple[str, int]]) -> str:
        """Build the LLM prompt from issue data and ranked file list."""
        comments_text = ""
        if issue.get("comments"):
            comments_text = "\n\n## Issue Comments\n"
            for comment in issue["comments"][:10]:
                author = comment.get("author", "unknown")
                body = comment.get("body", "")[:500]
                comments_text += f"\n**@{author}:** {body}\n"

        files_text = ""
        if relevant_files:
            files_text = "\n\n## Potentially Relevant Files\n"
            for path, _score in relevant_files:
                files_text += f"- {path}\n"

        labels_text = ", ".join(issue.get("labels", [])) or "none"
        issue_body = (issue.get("body") or "")[:3_000]

        return f"""Analyze this GitHub issue and provide a developer brief.

## Issue #{issue['number']}: {issue['title']}

**Labels:** {labels_text}

**Issue Body:**
{issue_body}
{comments_text}
{files_text}

## Your Task

Provide a structured developer brief with these sections:

### 📝 Issue Summary
A concise 2–3 sentence summary of what this issue is about.

### 📁 Relevant Files
List the files most likely to need changes, with a brief note on why each is relevant.

### 🚀 Suggested Starting Point
Which file/function to look at first and why.

### ❓ Open Questions
Any ambiguities or questions that should be clarified before starting work.

Be specific and actionable. Reference file paths and function names where possible."""

    def _system_prompt(self) -> str:
        return (
            "You are a senior software engineer helping a developer understand a "
            "GitHub issue. Provide clear, actionable analysis. Be concise but "
            "thorough. Use markdown formatting for readability."
        )

    @staticmethod
    def _github_error_message(exc: Exception) -> str:
        err = str(exc).lower()
        if "rate" in err or "limit" in err or "403" in str(exc):
            return (
                "⚠️ GitHub API rate limit reached. "
                "Add GITHUB_TOKEN to .env for 5,000 requests/hour (free).\n"
            )
        if "404" in str(exc):
            return (
                "⚠️ Repository or issue not found. "
                "Check that the URL points to a public GitHub issue.\n"
            )
        return f"⚠️ Could not fetch issue: {exc}\n"
