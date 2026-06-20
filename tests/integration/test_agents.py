"""
Integration tests for agent business logic.
LLMClient.stream() and all external services (GitHub, DocFetcher) are
mocked so no real API calls are made.
"""


from app.agents.context_agent import ContextAgent
from app.agents.boilerplate_agent import BoilerplateAgent
from app.agents.docs_agent import DocsAgent
from app.agents.pr_draft_agent import PRDraftAgent


def _run(generator) -> str:
    return "".join(generator)


# ── ContextAgent ──────────────────────────────────────────────────────

class TestContextAgent:
    def test_invalid_url_yields_error(self):
        agent = ContextAgent()
        result = _run(agent.run("not-a-github-url"))
        assert "⚠️" in result

    def test_github_404_yields_error(self, mocker):
        mocker.patch(
            "app.agents.context_agent.GitHubClient.fetch_issue",
            side_effect=Exception("404 Not Found"),
        )
        agent = ContextAgent()
        result = _run(agent.run("https://github.com/o/r/issues/1"))
        assert "⚠️" in result or "not found" in result.lower()

    def test_rate_limit_error_yields_helpful_message(self, mocker):
        mocker.patch(
            "app.agents.context_agent.GitHubClient.fetch_issue",
            side_effect=Exception("403 rate limit"),
        )
        agent = ContextAgent()
        result = _run(agent.run("https://github.com/o/r/issues/1"))
        assert "rate limit" in result.lower() or "GITHUB_TOKEN" in result

    def test_successful_run_streams_brief(self, mocker):
        mocker.patch(
            "app.agents.context_agent.GitHubClient.fetch_issue",
            return_value={
                "title": "Fix the bug",
                "body": "There is a bug in parser.py",
                "labels": ["bug"],
                "comments": [],
                "owner": "org",
                "repo": "myrepo",
                "number": 42,
            },
        )
        mocker.patch(
            "app.agents.context_agent.GitHubClient.fetch_file_tree",
            return_value=["src/parser.py", "tests/test_parser.py"],
        )
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream",
            return_value=iter(["# Brief\nSome analysis"]),
        )
        agent = ContextAgent()
        result = _run(agent.run("https://github.com/org/myrepo/issues/42"))
        assert "Fix the bug" in result
        assert "42" in result

    def test_include_comments_false_skips_comment_fetch(self, mocker):
        mock_fetch = mocker.patch(
            "app.agents.context_agent.GitHubClient.fetch_issue",
            return_value={
                "title": "Issue", "body": "", "labels": [],
                "comments": [], "owner": "o", "repo": "r", "number": 1,
            },
        )
        mocker.patch(
            "app.agents.context_agent.GitHubClient.fetch_file_tree",
            return_value=[],
        )
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream", return_value=iter(["ok"])
        )
        agent = ContextAgent()
        _run(agent.run("https://github.com/o/r/issues/1", include_comments=False))
        _, kwargs = mock_fetch.call_args
        assert kwargs.get("include_comments") is False

    def test_rank_files_by_keyword_scores_correctly(self):
        agent = ContextAgent()
        tree = ["src/parser.py", "tests/test_auth.py", "docs/readme.md", "src/auth.py"]
        ranked = agent._rank_files_by_keyword("Fix the auth system login", tree)
        paths = [p for p, _ in ranked]
        # auth.py should rank higher than parser.py for "auth" issue
        assert "src/auth.py" in paths
        assert paths.index("src/auth.py") < paths.index("src/parser.py") if "src/parser.py" in paths else True

    def test_rank_files_empty_tree_returns_empty(self):
        agent = ContextAgent()
        result = agent._rank_files_by_keyword("some text", [])
        assert result == []

    def test_rank_files_empty_body_returns_empty(self):
        agent = ContextAgent()
        result = agent._rank_files_by_keyword("", ["src/foo.py"])
        assert result == []


# ── BoilerplateAgent ──────────────────────────────────────────────────

class TestBoilerplateAgent:
    def test_basic_generation(self, mocker):
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream",
            return_value=iter(["def my_func(): pass"]),
        )
        agent = BoilerplateAgent()
        result = _run(agent.run("A simple function"))
        assert "def my_func" in result

    def test_style_ref_fetch_failure_continues(self, mocker):
        mocker.patch(
            "app.agents.boilerplate_agent.DocFetcher.fetch",
            side_effect=Exception("timeout"),
        )
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream",
            return_value=iter(["fallback code"]),
        )
        agent = BoilerplateAgent()
        result = _run(
            agent.run("A function", style_ref="https://raw.example.com/f.py")
        )
        # Should warn but still produce output
        assert "⚠️" in result
        assert "fallback code" in result

    def test_ssrf_blocked_style_ref_continues(self, mocker):
        mocker.patch(
            "app.agents.boilerplate_agent.DocFetcher.fetch",
            side_effect=ValueError("private address"),
        )
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream",
            return_value=iter(["code"]),
        )
        agent = BoilerplateAgent()
        result = _run(
            agent.run("func", style_ref="http://10.0.0.1/secret")
        )
        assert "Invalid" in result or "⚠️" in result


# ── DocsAgent ─────────────────────────────────────────────────────────

class TestDocsAgent:
    def test_unknown_library_no_custom_url_yields_error(self):
        agent = DocsAgent()
        result = _run(agent.run("unknownlib9999", "how do I use it?"))
        assert "not in the built-in list" in result or "⚠️" in result

    def test_supported_library_fetches_and_answers(self, mocker):
        mocker.patch(
            "app.agents.docs_agent.DocFetcher.fetch",
            return_value=(
                "Flask is a lightweight WSGI web application framework. "
                "It is designed to make getting started quick and easy, "
                "with the ability to scale up to complex applications."
            ),
        )
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream",
            return_value=iter(["Flask answer here"]),
        )
        agent = DocsAgent()
        result = _run(agent.run("flask", "what is Flask?"))
        assert "Flask answer here" in result

    def test_custom_url_bypasses_library_lookup(self, mocker):
        mock_fetch = mocker.patch(
            "app.agents.docs_agent.DocFetcher.fetch",
            return_value="Custom docs content",
        )
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream",
            return_value=iter(["answer"]),
        )
        agent = DocsAgent()
        _run(agent.run("", "question?", custom_url="https://docs.custom.com/"))
        mock_fetch.assert_called_once_with("https://docs.custom.com/")

    def test_doc_fetch_failure_yields_error(self, mocker):
        mocker.patch(
            "app.agents.docs_agent.DocFetcher.fetch",
            side_effect=Exception("connection refused"),
        )
        agent = DocsAgent()
        result = _run(agent.run("flask", "question?"))
        assert "⚠️" in result

    def test_very_short_doc_content_yields_warning(self, mocker):
        mocker.patch(
            "app.agents.docs_agent.DocFetcher.fetch",
            return_value="x",  # less than 50 chars
        )
        agent = DocsAgent()
        result = _run(agent.run("flask", "question?"))
        assert "⚠️" in result or "little content" in result


# ── PRDraftAgent ──────────────────────────────────────────────────────

class TestPRDraftAgent:
    VALID_DIFF = (
        "diff --git a/src/foo.py b/src/foo.py\n"
        "--- a/src/foo.py\n"
        "+++ b/src/foo.py\n"
        "@@ -1,2 +1,3 @@\n"
        " existing\n"
        "+new line\n"
        "-old line\n"
    )

    def test_empty_diff_yields_error(self):
        agent = PRDraftAgent()
        result = _run(agent.run(""))
        assert "⚠️" in result

    def test_whitespace_diff_treated_as_empty(self):
        agent = PRDraftAgent()
        result = _run(agent.run("   \n  "))
        assert "⚠️" in result

    def test_valid_diff_streams_pr_description(self, mocker):
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream",
            return_value=iter(["**Title**\nfeat: add feature"]),
        )
        agent = PRDraftAgent()
        result = _run(agent.run(self.VALID_DIFF))
        assert "feat: add feature" in result

    def test_issue_number_included_in_prompt(self, mocker):
        captured_prompt = {}

        def mock_stream(prompt, system=""):
            captured_prompt["p"] = prompt
            yield "ok"

        mocker.patch(
            "app.utils.llm_client.LLMClient.stream", side_effect=mock_stream
        )
        agent = PRDraftAgent()
        _run(agent.run(self.VALID_DIFF, issue_number=101))
        assert "101" in captured_prompt.get("p", "")

    def test_no_issue_number_still_produces_output(self, mocker):
        mocker.patch(
            "app.utils.llm_client.LLMClient.stream",
            return_value=iter(["output"]),
        )
        agent = PRDraftAgent()
        result = _run(agent.run(self.VALID_DIFF))
        assert "output" in result

    def test_diff_with_no_detected_files_yields_error(self):
        agent = PRDraftAgent()
        result = _run(agent.run("this is not a valid diff format at all"))
        assert "⚠️" in result
