"""Unit tests for GitHubClient URL parser — no network calls."""

import pytest

from app.utils.github_client import GitHubClient


@pytest.fixture
def client():
    # _parse_issue_url is a static method; no API calls are made here
    return GitHubClient


class TestParseIssueUrl:
    """Tests for GitHubClient._parse_issue_url()."""

    def test_valid_https_url(self, client):
        owner, repo, number = client._parse_issue_url(
            "https://github.com/owner/repo/issues/42"
        )
        assert owner == "owner"
        assert repo == "repo"
        assert number == 42

    def test_valid_url_with_trailing_slash(self, client):
        owner, repo, number = client._parse_issue_url(
            "https://github.com/django/django/issues/1234/"
        )
        assert owner == "django"
        assert repo == "django"
        assert number == 1234

    def test_real_world_url(self, client):
        owner, repo, number = client._parse_issue_url(
            "https://github.com/psf/requests/issues/6471"
        )
        assert owner == "psf"
        assert repo == "requests"
        assert number == 6471

    def test_large_issue_number(self, client):
        _, _, number = client._parse_issue_url("https://github.com/o/r/issues/999999")
        assert number == 999999

    def test_issue_number_is_int(self, client):
        _, _, number = client._parse_issue_url("https://github.com/o/r/issues/7")
        assert isinstance(number, int)

    def test_hyphenated_repo_name(self, client):
        owner, repo, _ = client._parse_issue_url(
            "https://github.com/pallets/flask-login/issues/10"
        )
        assert owner == "pallets"
        assert repo == "flask-login"

    def test_url_with_query_params(self, client):
        """Query parameters should be tolerated (regex searches, not matches)."""
        owner, repo, number = client._parse_issue_url(
            "https://github.com/owner/repo/issues/5?ref=email"
        )
        assert owner == "owner"
        assert number == 5

    # ── Invalid URLs ────────────────────────────────────────────────────

    def test_pr_url_raises(self, client):
        with pytest.raises(ValueError, match="Invalid GitHub issue URL"):
            client._parse_issue_url("https://github.com/owner/repo/pull/42")

    def test_missing_issue_number_raises(self, client):
        with pytest.raises(ValueError):
            client._parse_issue_url("https://github.com/owner/repo/issues/")

    def test_non_github_url_raises(self, client):
        with pytest.raises(ValueError):
            client._parse_issue_url("https://gitlab.com/owner/repo/issues/1")

    def test_bare_domain_raises(self, client):
        with pytest.raises(ValueError):
            client._parse_issue_url("https://github.com")

    def test_empty_string_raises(self, client):
        with pytest.raises(ValueError):
            client._parse_issue_url("")

    def test_plain_text_raises(self, client):
        with pytest.raises(ValueError):
            client._parse_issue_url("not a url at all")
