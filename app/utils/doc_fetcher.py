"""
DevFlow Agent — Documentation Fetcher
Fetches and cleans documentation pages via httpx + BeautifulSoup.
All user-supplied URLs are validated against SSRF before fetching.
"""

import logging
import time

import httpx
from bs4 import BeautifulSoup

from app.utils.url_validator import validate_fetch_url

logger = logging.getLogger(__name__)

# Characters returned per fetch (keeps prompts within LLM context limits)
MAX_CONTENT_LENGTH = 8_000

# Simple in-process TTL cache: url → (content, fetched_at)
_cache: dict[str, tuple[str, float]] = {}
CACHE_TTL_SECONDS = 600  # 10 minutes


class DocFetcher:
    """Fetches a URL and strips HTML to return clean plain text."""

    def fetch(self, url: str) -> str:
        """
        Validate, fetch, and return cleaned plain text for a URL.

        Results are cached for 10 minutes to avoid hammering documentation
        sites with repeated identical requests.

        Args:
            url: Fully qualified URL to fetch (http/https only).

        Returns:
            Plain text content, truncated to MAX_CONTENT_LENGTH characters.

        Raises:
            ValueError: If the URL fails SSRF validation.
            Exception:  With a descriptive message on HTTP or network failure.
        """
        # SSRF guard — raises ValueError for private/reserved addresses
        validate_fetch_url(url)

        # Return from cache if still fresh
        cached = _cache.get(url)
        if cached is not None:
            content, fetched_at = cached
            if time.time() - fetched_at < CACHE_TTL_SECONDS:
                logger.debug("DocFetcher cache hit for %s", url)
                return content

        logger.info("DocFetcher fetching %s", url)
        content = self._fetch_fresh(url)

        _cache[url] = (content, time.time())
        return content

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_fresh(self, url: str) -> str:
        """Perform the actual HTTP request and return cleaned content."""
        try:
            response = httpx.get(
                url,
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": "DevFlow-Agent/1.0"},
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise Exception(
                f"Timeout fetching {url} — the site took too long to respond."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise Exception(
                f"HTTP {exc.response.status_code} when fetching {url}"
            ) from exc
        except httpx.RequestError as exc:
            raise Exception(f"Could not reach {url}: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            return self._clean_html(response.text)

        # Plain text (e.g., raw .py / .md / .txt files)
        return self._truncate(response.text)

    def _clean_html(self, html: str) -> str:
        """Strip HTML tags and extract the main readable text."""
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find(attrs={"role": "main"})
        )
        raw_text = (main or soup).get_text(separator="\n", strip=True)

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return self._truncate("\n".join(lines))

    @staticmethod
    def _truncate(text: str) -> str:
        if len(text) > MAX_CONTENT_LENGTH:
            return text[:MAX_CONTENT_LENGTH] + "\n\n[... content truncated ...]"
        return text
