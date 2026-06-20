"""
DevFlow Agent — PR Draft Agent
Generates pull request descriptions from git diffs.

Input:  Git diff text + optional issue number
Output: Streamed PR description — title, summary, changes, testing checklist
"""

from app.utils.llm_client import LLMClient
from app.utils.diff_parser import DiffParser


class PRDraftAgent:
    """Generates structured PR descriptions from git diffs."""

    def __init__(self):
        self.llm = LLMClient()
        self.parser = DiffParser()

    def run(self, diff_text: str, issue_number: int = None):
        """
        Parse a git diff and stream an LLM-generated PR description.
        Yields text chunks for streaming.
        """
        # ── Step 1: Validate diff ──────────────────────────────
        if not diff_text or not diff_text.strip():
            yield "⚠️ No diff provided. Paste the output of: git diff HEAD\n"
            return

        # ── Step 2: Parse diff ─────────────────────────────────
        parsed = self.parser.parse(diff_text)

        if not parsed["files_changed"]:
            yield "⚠️ Diff appears to be empty — no file changes detected.\n"
            yield "Make sure you're pasting the full output of `git diff`.\n"
            return

        yield f"📊 Diff analysis: {parsed['summary'].split(chr(10))[0]}\n\n"

        # Show per-file breakdown
        for f in parsed["files_changed"]:
            yield f"   • {f['path']} (+{f['lines_added']}/-{f['lines_removed']})\n"
        yield "\n"

        # ── Step 3: Build prompt and stream LLM response ──────
        prompt = self._build_prompt(diff_text, parsed, issue_number)

        yield "---\n\n"

        try:
            for chunk in self.llm.stream(prompt, system=self._system_prompt()):
                yield chunk
        except Exception as e:
            yield f"\n⚠️ LLM error: {e}"

    def _build_prompt(self, diff_text: str, parsed: dict, issue_number: int = None) -> str:
        """Build the LLM prompt for PR description generation."""
        issue_section = ""
        if issue_number:
            issue_section = f"\n\n**Related Issue:** #{issue_number}\nInclude 'Closes #{issue_number}' in the Related Issues section."

        # Truncate the raw diff to avoid exceeding context limits
        truncated_diff = diff_text[:6000]
        if len(diff_text) > 6000:
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
A concise conventional-commit style title (e.g., feat:, fix:, refactor:, docs:)

**Summary**
A 2-4 sentence overview of what this PR does and why.

**Changes**
A bullet-point list of specific changes made, grouped by file. Be specific about what was added, modified, or removed.

**Testing**
A checkbox-style testing checklist relevant to the changes:
- [ ] Test item 1
- [ ] Test item 2

**Related Issues**
Reference any related issues.

Be specific and reference actual code changes from the diff."""

    def _system_prompt(self) -> str:
        return (
            "You are a senior developer writing PR descriptions. Be clear, specific, and concise. "
            "Reference actual file names and code changes. Use conventional commit format for titles. "
            "Write testing checklists that are actionable and relevant to the specific changes."
        )
