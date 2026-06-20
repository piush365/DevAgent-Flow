"""
DevFlow Agent — GitHub Client
Wraps PyGitHub to fetch issues, comments, and file trees.
"""

import os
import re
from github import Github, GithubException


class GitHubClient:
    """Fetches GitHub issue data and repository file trees via PyGitHub."""

    def __init__(self):
        token = os.environ.get("GITHUB_TOKEN")
        self.github = Github(token) if token else Github()

    def fetch_issue(self, issue_url: str) -> dict:
        """
        Parse a GitHub issue URL and fetch its data.

        Args:
            issue_url: Full URL like https://github.com/owner/repo/issues/42

        Returns:
            dict with keys: title, body, labels, comments, owner, repo, number
        """
        owner, repo_name, issue_number = self._parse_issue_url(issue_url)

        repo = self.github.get_repo(f"{owner}/{repo_name}")
        issue = repo.get_issue(number=issue_number)

        # Fetch comments
        comments = []
        for comment in issue.get_comments():
            comments.append({
                "author": comment.user.login if comment.user else "unknown",
                "body": comment.body or "",
            })

        return {
            "title": issue.title,
            "body": issue.body or "",
            "labels": [label.name for label in issue.labels],
            "comments": comments,
            "owner": owner,
            "repo": repo_name,
            "number": issue_number,
        }

    def fetch_file_tree(self, owner: str, repo_name: str) -> list:
        """
        Fetch the full file tree of a repository (default branch).

        Returns:
            List of file path strings.
        """
        repo = self.github.get_repo(f"{owner}/{repo_name}")

        try:
            tree = repo.get_git_tree(sha="HEAD", recursive=True)
            return [item.path for item in tree.tree if item.type == "blob"]
        except GithubException:
            # Fallback: get top-level contents only
            contents = repo.get_contents("")
            paths = []
            while contents:
                item = contents.pop(0)
                if item.type == "file":
                    paths.append(item.path)
                elif item.type == "dir":
                    try:
                        contents.extend(repo.get_contents(item.path))
                    except GithubException:
                        pass
            return paths

    def _parse_issue_url(self, url: str) -> tuple:
        """
        Extract owner, repo, and issue number from a GitHub issue URL.

        Raises:
            ValueError if URL doesn't match expected format.
        """
        pattern = r"github\.com/([^/]+)/([^/]+)/issues/(\d+)"
        match = re.search(pattern, url)
        if not match:
            raise ValueError(
                f"Invalid GitHub issue URL: {url}\n"
                "Expected format: https://github.com/owner/repo/issues/N"
            )
        return match.group(1), match.group(2), int(match.group(3))
