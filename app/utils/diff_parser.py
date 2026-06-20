"""
DevFlow Agent — Git Diff Parser
Parses raw unified diff text into a structured change summary.
Pure string processing — no external libraries required.
"""

import logging

logger = logging.getLogger(__name__)


class DiffParser:
    """Parses unified diff format output into structured change data."""

    def parse(self, diff_text: str) -> dict:
        """
        Parse a git diff string into a structured summary.

        Args:
            diff_text: Raw output from ``git diff`` or ``git diff HEAD``.

        Returns:
            dict with keys:
                files_changed  — list of {path, lines_added, lines_removed}
                total_added    — int, total added lines across all files
                total_removed  — int, total removed lines across all files
                summary        — human-readable one-line + per-file detail
        """
        if not diff_text or not diff_text.strip():
            return {
                "files_changed": [],
                "total_added": 0,
                "total_removed": 0,
                "summary": "No changes detected.",
            }

        files: list[dict] = []
        current_file: dict | None = None
        total_added = 0
        total_removed = 0

        for line in diff_text.splitlines():
            if line.startswith("diff --git "):
                # Save the previous file before starting a new one
                if current_file is not None:
                    files.append(current_file)
                # Extract the destination path from "diff --git a/X b/X"
                parts = line.split(" b/", 1)
                path = parts[1] if len(parts) == 2 else "unknown"
                current_file = {"path": path, "lines_added": 0, "lines_removed": 0}

            elif current_file is not None:
                if line.startswith("--- ") or line.startswith("+++ "):
                    # File header markers — not content lines
                    continue
                elif line.startswith("+"):
                    current_file["lines_added"] += 1
                    total_added += 1
                elif line.startswith("-"):
                    current_file["lines_removed"] += 1
                    total_removed += 1
                # Context lines (space-prefixed) and hunk headers (@@) are ignored

        if current_file is not None:
            files.append(current_file)

        logger.debug(
            "DiffParser: %d file(s), +%d/-%d lines",
            len(files),
            total_added,
            total_removed,
        )

        summary = self._build_summary(files, total_added, total_removed)
        return {
            "files_changed": files,
            "total_added": total_added,
            "total_removed": total_removed,
            "summary": summary,
        }

    @staticmethod
    def _build_summary(files: list[dict], total_added: int, total_removed: int) -> str:
        """Build a human-readable summary string."""
        header = (
            f"{len(files)} file(s) changed, "
            f"+{total_added} lines added, "
            f"-{total_removed} lines removed"
        )
        if not files:
            return header

        file_lines = [
            f"  • {f['path']} (+{f['lines_added']}/-{f['lines_removed']})"
            for f in files
        ]
        return header + "\n\nFiles:\n" + "\n".join(file_lines)
