"""
DevFlow Agent — PR Draft Agent
Generates pull request descriptions from git diffs.

Input:  Git diff text + optional issue number
Output: Streamed PR description — title, summary, changes, testing checklist
"""

import logging
from typing import Generator

from app.agents.base_agent import BaseAgent
from app.utils.diff_parser import DiffParser

logger = logging.getLogger(__name__)

# Characters of raw diff included in the LLM prompt
_DIFF_CHAR_LIMIT = 6_000


class PRDraftAgent(BaseAgent):
    """Generates structured PR descriptions from git diffs."""

    def __init__(self) -> None:
        super().__init__()
        self.parser = DiffParser()

    def run(
        self,
        diff_text: str,
        issue_number: int | None = None,
    ) -> Generator[str, None, None]:
        """
        Parse a git diff and stream an LLM-generated PR description.

        Args:
            diff_text:    Raw output from ``git diff`` or ``git diff HEAD``.
            issue_number: Optional GitHub issue number to reference.

        Yields:
            Text chunks for streaming to the frontend.
        """
        # ── Step 1: Parse diff ─────────────────────────────────────────
        parsed = self.parser.parse(diff_text)

        if not parsed["files_changed"]:
            yield "⚠️ No file changes detected in the diff.\n"
            yield "Make sure you're pasting the full output of `git diff` or `git diff HEAD`.\n"
            return

        first_line = parsed["summary"].split("\n")[0]
        yield f"📊 {first_line}\n\n"

        for file_info in parsed["files_changed"]:
            added = file_info["lines_added"]
            removed = file_info["lines_removed"]
            yield f"   • {file_info['path']} (+{added}/-{removed})\n"
        yield "\n"

        # ── Step 2: Build prompt and stream LLM response ───────────────
        logger.info(
            "PRDraftAgent: drafting PR for %d file(s)", len(parsed["files_changed"])
        )
        prompt = self._build_prompt(diff_text, parsed, issue_number)
        yield "---\n\n"
        yield from self._stream_llm(prompt)

    def _build_prompt(
        self,
        diff_text: str,
        parsed: dict,
        issue_number: int | None,
    ) -> str:
        """Build the LLM prompt for PR description generation."""
        issue_section = ""
        if issue_number is not None:
            issue_section = (
                f"\n\n**Related Issue:** #{issue_number}\n"
                f"Include 'Closes #{issue_number}' in the Related Issues section."
            )

        truncated_diff = diff_text[:_DIFF_CHAR_LIMIT]
        if len(diff_text) > _DIFF_CHAR_LIMIT:
            truncated_diff += "\n\n[... diff truncated for length ...]"

        return f"""Generate a pull request description based on this git diff.

## Diff Summary
{parsed['summary']}
{issue_section}

## Raw Diff
```diff
{truncated_diff}
```

## Instructions
Generate a well-structured PR description with these exact sections:

**Title**
A concise conventional-commit style title (feat:, fix:, refactor:, docs:, etc.)

**Summary**
A 2–4 sentence overview of what this PR does and why.

**Changes**
A bullet-point list of specific changes grouped by file. Be specific about what
was added, modified, or removed.

**Testing**
A checkbox-style testing checklist relevant to the actual changes:
- [ ] Test item 1
- [ ] Test item 2

**Related Issues**
Reference any related issues.

Be specific. Reference actual file names and code changes from the diff."""

    def _system_prompt(self) -> str:
        return (
            "You are a senior developer writing PR descriptions. Be clear, specific, "
            "and concise. Reference actual file names and code changes. Use "
            "conventional commit format for titles. Write testing checklists that "
            "are actionable and relevant to the specific changes."
        )
