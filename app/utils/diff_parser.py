"""
DevFlow Agent — Git Diff Parser
Parses raw git diff text into a structured change summary.
Pure string processing — no external libraries needed.
"""


class DiffParser:
    """Parses unified diff format into structured change data."""

    def parse(self, diff_text: str) -> dict:
        """
        Parse a git diff string into a structured summary.

        Args:
            diff_text: Raw output from `git diff`

        Returns:
            dict with keys:
                files_changed: list of dicts with {path, lines_added, lines_removed}
                total_added: int
                total_removed: int
                summary: str (human-readable summary)
        """
        if not diff_text or not diff_text.strip():
            return {
                "files_changed": [],
                "total_added": 0,
                "total_removed": 0,
                "summary": "No changes detected.",
            }

        files = []
        current_file = None
        total_added = 0
        total_removed = 0

        for line in diff_text.splitlines():
            # Detect file boundaries
            if line.startswith("diff --git"):
                if current_file:
                    files.append(current_file)
                # Extract file path from "diff --git a/path b/path"
                parts = line.split(" b/")
                path = parts[-1] if len(parts) > 1 else "unknown"
                current_file = {
                    "path": path,
                    "lines_added": 0,
                    "lines_removed": 0,
                }

            elif line.startswith("--- ") or line.startswith("+++ "):
                # File header lines — skip
                continue

            elif line.startswith("+") and current_file:
                # Skip hunk headers like "+++ b/file.py"
                if not line.startswith("+++"):
                    current_file["lines_added"] += 1
                    total_added += 1

            elif line.startswith("-") and current_file:
                # Skip file headers like "--- a/file.py"
                if not line.startswith("---"):
                    current_file["lines_removed"] += 1
                    total_removed += 1

        # Don't forget the last file
        if current_file:
            files.append(current_file)

        # Build human-readable summary
        summary_parts = [
            f"{len(files)} file(s) changed",
            f"+{total_added} lines added",
            f"-{total_removed} lines removed",
        ]
        summary = ", ".join(summary_parts)

        # Per-file detail
        file_details = []
        for f in files:
            file_details.append(
                f"  • {f['path']} (+{f['lines_added']}/-{f['lines_removed']})"
            )

        if file_details:
            summary += "\n\nFiles:\n" + "\n".join(file_details)

        return {
            "files_changed": files,
            "total_added": total_added,
            "total_removed": total_removed,
            "summary": summary,
        }
