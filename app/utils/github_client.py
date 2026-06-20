"""
DevFlow Agent — GitHub Client
Wraps PyGitHub to fetch issues, comments, and file trees.
Includes a short-lived in-process cache to avoid redundant API calls
within the same session (e.g., two calls for the same repo per request).
"""

import logging
import os
import re
import time

from github import Auth, Github, GithubException

logger = logging.getLogger(__name__)

# In-process TTL cache for PyGitHub repo objects.
# Note: this is per-process, so it does not persist across gunicorn workers.
_repo_cache: dict[str, tuple] = {}  # full_name → (repo_obj, fetched_at)
_REPO_CACHE_TTL = 300  # seconds

# GitHub API timeout (seconds)
_GITHUB_TIMEOUT = 30

# Limit on file paths returned — prevents O(n) scoring loops on giant repos
_FILE_TREE_LIMIT = 5_000


class GitHubClient:
    """Fetches GitHub issue data and repository file trees via PyGitHub."""

    def __init__(self) -> None:
        token = os.environ.get("GITHUB_TOKEN")
        self._gh = (
            Github(auth=Auth.Token(token), timeout=_GITHUB_TIMEOUT)
            if token
            else Github(timeout=_GITHUB_TIMEOUT)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_issue(self, issue_url: str, include_comments: bool = True) -> dict:
        """
        Parse a GitHub issue URL and return its data.

        Args:
            issue_url:        Full URL like https://github.com/owner/repo/issues/42
            include_comments: When False, skips fetching issue comments.

        Returns:
            dict with keys: title, body, labels, comments, owner, repo, number

        Raises:
            ValueError:       If the URL format is invalid.
            GithubException:  On API errors (rate limit, not found, etc.).
        """
        owner, repo_name, issue_number = self._parse_issue_url(issue_url)
        repo = self._get_repo(f"{owner}/{repo_name}")
        issue = repo.get_issue(number=issue_number)

        comments: list[dict] = []
        if include_comments:
            for comment in issue.get_comments():
                comments.append(
                    {
                        "author": comment.user.login if comment.user else "unknown",
                        "body": comment.body or "",
                    }
                )

        return {
            "title": issue.title,
            "body": issue.body or "",
            "labels": [label.name for label in issue.labels],
            "comments": comments,
            "owner": owner,
            "repo": repo_name,
            "number": issue_number,
        }

    def fetch_file_tree(self, owner: str, repo_name: str) -> list[str]:
        """
        Fetch the file tree of a repository (default branch).

        Returns up to _FILE_TREE_LIMIT paths. Warns if the tree was
        truncated by GitHub (> 100,000 items) or by the local cap.

        Returns:
            List of file path strings.
        """
        repo = self._get_repo(f"{owner}/{repo_name}")
        paths: list[str] = []

        try:
            tree = repo.get_git_tree(sha="HEAD", recursive=True)

            if tree.truncated:
                logger.warning(
                    "GitHub tree for %s/%s is truncated (>100,000 files). "
                    "File relevance ranking will use partial data.",
                    owner,
                    repo_name,
                )

            paths = [
                item.path for item in tree.tree if item.type == "blob"
            ][:_FILE_TREE_LIMIT]

        except GithubException:
            # Fallback: BFS traversal using get_contents()
            logger.info("Recursive tree failed for %s/%s; falling back to BFS", owner, repo_name)
            paths = self._fetch_tree_bfs(repo)

        logger.info("Fetched %d file paths for %s/%s", len(paths), owner, repo_name)
        return paths

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_repo(self, full_name: str):
        """Return a cached PyGitHub repo object, refreshing after TTL."""
        cached = _repo_cache.get(full_name)
        if cached is not None:
            repo_obj, fetched_at = cached
            if time.time() - fetched_at < _REPO_CACHE_TTL:
                return repo_obj

        repo_obj = self._gh.get_repo(full_name)
        _repo_cache[full_name] = (repo_obj, time.time())
        return repo_obj

    def _fetch_tree_bfs(self, repo, limit: int = _FILE_TREE_LIMIT) -> list[str]:
        """BFS fallback when recursive tree API is unavailable."""
        paths: list[str] = []
        queue = list(repo.get_contents(""))

        while queue and len(paths) < limit:
            item = queue.pop(0)
            if item.type == "file":
                paths.append(item.path)
            elif item.type == "dir":
                try:
                    queue.extend(repo.get_contents(item.path))
                except GithubException:
                    pass  # Skip inaccessible directories

        return paths

    @staticmethod
    def _parse_issue_url(url: str) -> tuple[str, str, int]:
        """
        Extract owner, repo, and issue number from a GitHub issue URL.

        Raises:
            ValueError: If the URL doesn't match the expected format.
        """
        pattern = r"github\.com/([^/]+)/([^/]+)/issues/(\d+)"
        match = re.search(pattern, url)
        if not match:
            raise ValueError(
                f"Invalid GitHub issue URL: {url!r}\n"
                "Expected format: https://github.com/owner/repo/issues/N"
            )
        return match.group(1), match.group(2), int(match.group(3))
