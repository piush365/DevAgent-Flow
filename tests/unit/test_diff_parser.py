"""Unit tests for DiffParser — pure string processing, no mocking needed."""

import pytest

from app.utils.diff_parser import DiffParser


@pytest.fixture
def parser():
    return DiffParser()


# ── Empty / null input ────────────────────────────────────────────────


class TestEmptyInput:
    def test_empty_string(self, parser):
        result = parser.parse("")
        assert result["files_changed"] == []
        assert result["total_added"] == 0
        assert result["total_removed"] == 0
        assert "No changes" in result["summary"]

    def test_whitespace_only(self, parser):
        result = parser.parse("   \n\n\t  ")
        assert result["files_changed"] == []

    def test_none_equivalent_via_empty(self, parser):
        result = parser.parse("")
        assert isinstance(result["files_changed"], list)


# ── Single-file diffs ─────────────────────────────────────────────────

SINGLE_FILE_DIFF = """\
diff --git a/src/foo.py b/src/foo.py
index abc..def 100644
--- a/src/foo.py
+++ b/src/foo.py
@@ -1,3 +1,5 @@
 context line
+added line 1
+added line 2
-removed line
 another context
"""


class TestSingleFile:
    def test_one_file_detected(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert len(result["files_changed"]) == 1

    def test_correct_path(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert result["files_changed"][0]["path"] == "src/foo.py"

    def test_lines_added(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert result["files_changed"][0]["lines_added"] == 2

    def test_lines_removed(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert result["files_changed"][0]["lines_removed"] == 1

    def test_total_added(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert result["total_added"] == 2

    def test_total_removed(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert result["total_removed"] == 1

    def test_header_lines_not_counted_as_additions(self, parser):
        """The +++ b/file.py line must NOT be counted as an added line."""
        result = parser.parse(SINGLE_FILE_DIFF)
        # If +++ were counted, lines_added would be 3 not 2
        assert result["files_changed"][0]["lines_added"] == 2

    def test_header_lines_not_counted_as_removals(self, parser):
        """The --- a/file.py line must NOT be counted as a removed line."""
        result = parser.parse(SINGLE_FILE_DIFF)
        assert result["files_changed"][0]["lines_removed"] == 1


# ── Multi-file diffs ──────────────────────────────────────────────────

MULTI_FILE_DIFF = """\
diff --git a/app/routes.py b/app/routes.py
--- a/app/routes.py
+++ b/app/routes.py
@@ -1,2 +1,3 @@
+new import
 existing line
-old line
diff --git a/tests/test_routes.py b/tests/test_routes.py
--- a/tests/test_routes.py
+++ b/tests/test_routes.py
@@ -0,0 +1,4 @@
+def test_one():
+    pass
+
+def test_two():
"""


class TestMultipleFiles:
    def test_two_files_detected(self, parser):
        result = parser.parse(MULTI_FILE_DIFF)
        assert len(result["files_changed"]) == 2

    def test_first_file_path(self, parser):
        result = parser.parse(MULTI_FILE_DIFF)
        assert result["files_changed"][0]["path"] == "app/routes.py"

    def test_second_file_path(self, parser):
        result = parser.parse(MULTI_FILE_DIFF)
        assert result["files_changed"][1]["path"] == "tests/test_routes.py"

    def test_totals_aggregated(self, parser):
        result = parser.parse(MULTI_FILE_DIFF)
        assert result["total_added"] == 5  # 1 + 4
        assert result["total_removed"] == 1

    def test_per_file_counts_correct(self, parser):
        result = parser.parse(MULTI_FILE_DIFF)
        first = result["files_changed"][0]
        second = result["files_changed"][1]
        assert first["lines_added"] == 1
        assert first["lines_removed"] == 1
        assert second["lines_added"] == 4
        assert second["lines_removed"] == 0


# ── Summary format ────────────────────────────────────────────────────


class TestSummaryFormat:
    def test_summary_mentions_file_count(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert "1 file" in result["summary"]

    def test_summary_mentions_additions(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert "+2" in result["summary"]

    def test_summary_mentions_removals(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert "-1" in result["summary"]

    def test_summary_contains_file_path(self, parser):
        result = parser.parse(SINGLE_FILE_DIFF)
        assert "src/foo.py" in result["summary"]

    def test_empty_summary(self, parser):
        result = parser.parse("")
        assert result["summary"] == "No changes detected."


# ── Edge cases ────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_additions_only(self, parser):
        diff = (
            "diff --git a/new.py b/new.py\n"
            "--- /dev/null\n"
            "+++ b/new.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+line one\n"
            "+line two\n"
        )
        result = parser.parse(diff)
        assert result["total_added"] == 2
        assert result["total_removed"] == 0

    def test_deletions_only(self, parser):
        diff = (
            "diff --git a/old.py b/old.py\n"
            "--- a/old.py\n"
            "+++ /dev/null\n"
            "@@ -1,2 +0,0 @@\n"
            "-line one\n"
            "-line two\n"
        )
        result = parser.parse(diff)
        assert result["total_added"] == 0
        assert result["total_removed"] == 2

    def test_path_with_spaces(self, parser):
        diff = "diff --git a/my file.py b/my file.py\n--- a/my file.py\n+++ b/my file.py\n+x\n"
        result = parser.parse(diff)
        assert result["files_changed"][0]["path"] == "my file.py"

    def test_context_lines_not_counted(self, parser):
        """Lines without + or - prefix (context lines) must be ignored."""
        diff = (
            "diff --git a/f.py b/f.py\n"
            "--- a/f.py\n"
            "+++ b/f.py\n"
            "@@ -1,3 +1,3 @@\n"
            " context\n"
            " context\n"
            "+added\n"
            "-removed\n"
        )
        result = parser.parse(diff)
        assert result["total_added"] == 1
        assert result["total_removed"] == 1
