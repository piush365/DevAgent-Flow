"""
DevFlow Agent — Documentation Fetcher
Fetches and cleans documentation pages via httpx + BeautifulSoup.
"""

import httpx
from bs4 import BeautifulSoup


class DocFetcher:
    """Fetches a URL and strips HTML to clean plain text."""

    # Maximum characters to return (keeps prompts within LLM context limits)
    MAX_CONTENT_LENGTH = 8000

    def fetch(self, url: str) -> str:
        """
        Fetch a URL and return cleaned plain text content.

        Args:
            url: Full URL to fetch (e.g., docs page, GitHub raw file)

        Returns:
            Plain text content, truncated to MAX_CONTENT_LENGTH.

        Raises:
            Exception with descriptive message on failure.
        """
        try:
            response = httpx.get(
                url,
                timeout=15.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "DevFlow-Agent/1.0 (documentation-fetcher)"
                },
            )
            response.raise_for_status()
        except httpx.TimeoutException:
            raise Exception(f"Timeout fetching {url} — the site took too long to respond.")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code} fetching {url}")
        except httpx.RequestError as e:
            raise Exception(f"Could not reach {url}: {e}")

        content_type = response.headers.get("content-type", "")

        # If it's HTML, strip tags and extract text
        if "html" in content_type:
            return self._clean_html(response.text)

        # Otherwise return raw text (e.g., .py, .md, .txt files)
        text = response.text
        if len(text) > self.MAX_CONTENT_LENGTH:
            text = text[: self.MAX_CONTENT_LENGTH] + "\n\n[... content truncated ...]"
        return text

    def _clean_html(self, html: str) -> str:
        """Strip HTML tags and extract readable text content."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script, style, nav, footer, header elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Try to find main content area
        main = soup.find("main") or soup.find("article") or soup.find(role="main")
        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        if len(text) > self.MAX_CONTENT_LENGTH:
            text = text[: self.MAX_CONTENT_LENGTH] + "\n\n[... content truncated ...]"

        return text
