"""
DevFlow Agent — Context Agent
Analyzes a GitHub issue and identifies relevant files to start working on.

Input:  GitHub issue URL
Output: Streamed analysis — issue summary, relevant files, starting point, open questions
"""

import re
from app.utils.llm_client import LLMClient
from app.utils.github_client import GitHubClient


class ContextAgent:
    """Generates a ready-to-code brief from a GitHub issue URL."""

    def __init__(self):
        self.llm = LLMClient()
        self.github = GitHubClient()

    def run(self, issue_url: str):
        """
        Fetch issue, analyze relevant files, and stream an LLM-generated brief.
        Yields text chunks for streaming.
        """
        # ── Step 1: Fetch issue data ───────────────────────────
        try:
            issue = self.github.fetch_issue(issue_url)
        except ValueError as e:
            yield f"⚠️ {e}\n"
            return
        except Exception as e:
            err = str(e).lower()
            if "rate" in err or "limit" in err or "403" in str(e):
                yield "⚠️ GitHub API rate limit hit. Add GITHUB_TOKEN to .env for 5,000 requests/hour (free).\n"
            elif "404" in str(e):
                yield "⚠️ Repository or issue not found. Check that the URL points to a public GitHub issue.\n"
            else:
                yield f"⚠️ Could not fetch issue: {e}\n"
            return

        yield f"📋 Fetched issue #{issue['number']}: {issue['title']}\n\n"

        # ── Step 2: Fetch repo file tree ───────────────────────
        try:
            file_tree = self.github.fetch_file_tree(issue["owner"], issue["repo"])
            yield f"📂 Repository has {len(file_tree)} files\n\n"
        except Exception as e:
            yield f"⚠️ Could not fetch file tree: {e}\n"
            file_tree = []

        # ── Step 3: Rank relevant files ────────────────────────
        relevant_files = self._rank_files(issue["body"], file_tree)
        if relevant_files:
            yield "🔍 Top relevant files identified:\n"
            for path, score in relevant_files:
                yield f"   • {path} (relevance: {score})\n"
            yield "\n"

        # ── Step 4: Build prompt and stream LLM response ──────
        prompt = self._build_prompt(issue, relevant_files)

        yield "---\n\n"

        try:
            for chunk in self.llm.stream(prompt, system=self._system_prompt()):
                yield chunk
        except Exception as e:
            yield f"\n⚠️ LLM error: {e}"

    def _rank_files(self, issue_body: str, file_tree: list, top_n: int = 5) -> list:
        """
        Rank files by keyword overlap with issue body.
        Returns list of (file_path, score) tuples, sorted by score descending.
        """
        if not issue_body or not file_tree:
            return []

        # Extract keywords from issue body (words 3+ chars, lowercased)
        words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", issue_body.lower())
        keywords = set(words)

        scored_files = []
        for path in file_tree:
            # Score = how many keywords appear in the file path
            path_lower = path.lower()
            # Split path into components for matching
            path_parts = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", path_lower))
            overlap = len(keywords & path_parts)
            if overlap > 0:
                scored_files.append((path, overlap))

        scored_files.sort(key=lambda x: x[1], reverse=True)
        return scored_files[:top_n]

    def _build_prompt(self, issue: dict, relevant_files: list) -> str:
        """Build the LLM prompt from issue data and relevant files."""
        comments_text = ""
        if issue["comments"]:
            comments_text = "\n\n## Issue Comments\n"
            for c in issue["comments"][:10]:  # Limit to 10 comments
                comments_text += f"\n**@{c['author']}:** {c['body'][:500]}\n"

        files_text = ""
        if relevant_files:
            files_text = "\n\n## Potentially Relevant Files\n"
            for path, score in relevant_files:
                files_text += f"- {path}\n"

        labels_text = ", ".join(issue["labels"]) if issue["labels"] else "none"

        return f"""Analyze this GitHub issue and provide a developer brief.

## Issue #{issue['number']}: {issue['title']}

**Labels:** {labels_text}

**Issue Body:**
{issue['body'][:3000]}
{comments_text}
{files_text}

## Your Task

Provide a structured developer brief with these sections:

### 📝 Issue Summary
A concise 2-3 sentence summary of what this issue is about.

### 📁 Relevant Files
List the files most likely to need changes, with a brief note on why each is relevant.

### 🚀 Suggested Starting Point
Which file/function to look at first and why.

### ❓ Open Questions
Any ambiguities or questions that should be clarified before starting work.

Be specific and actionable. Reference file paths and function names where possible."""

    def _system_prompt(self) -> str:
        return (
            "You are a senior software engineer helping a developer understand a GitHub issue. "
            "Provide clear, actionable analysis. Be concise but thorough. "
            "Use markdown formatting for readability."
        )
