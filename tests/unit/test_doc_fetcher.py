"""
Unit tests for DocFetcher.
All httpx calls are patched via mocker — no network access required.
"""

import pytest

from app.utils.doc_fetcher import DocFetcher, MAX_CONTENT_LENGTH, _cache

# ── Helpers ───────────────────────────────────────────────────────────


class _FakeResponse:
    """Minimal stand-in for an httpx.Response object."""

    def __init__(
        self, text: str, content_type: str = "text/plain", status_code: int = 200
    ):
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        if self.status_code >= 400:
            # Mimic httpx.HTTPStatusError
            import httpx

            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=None,
                response=type("_R", (), {"status_code": self.status_code})(),
            )


@pytest.fixture(autouse=True)
def clear_doc_cache():
    """Clear the module-level TTL cache before and after each test."""
    _cache.clear()
    yield
    _cache.clear()


@pytest.fixture
def fetcher():
    return DocFetcher()


@pytest.fixture
def patched_validate(mocker):
    """Bypass SSRF validation so tests can use any URL."""
    mocker.patch("app.utils.doc_fetcher.validate_fetch_url", side_effect=lambda u: u)


TEST_URL = "https://docs.example.com/page"


# ── Successful fetches ────────────────────────────────────────────────


class TestSuccessfulFetch:
    def test_plain_text_returned(self, fetcher, mocker, patched_validate):
        mocker.patch(
            "httpx.get",
            return_value=_FakeResponse("Hello, plain world!", "text/plain"),
        )
        result = fetcher.fetch(TEST_URL)
        assert "Hello, plain world!" in result

    def test_html_tags_stripped(self, fetcher, mocker, patched_validate):
        html = "<html><body><main><p>Clean text here</p></main></body></html>"
        mocker.patch(
            "httpx.get",
            return_value=_FakeResponse(html, "text/html"),
        )
        result = fetcher.fetch(TEST_URL)
        assert "Clean text here" in result
        assert "<p>" not in result

    def test_nav_and_footer_removed(self, fetcher, mocker, patched_validate):
        html = (
            "<html><body>"
            "<nav>Skip me</nav>"
            "<main>Keep me</main>"
            "<footer>Also skip</footer>"
            "</body></html>"
        )
        mocker.patch(
            "httpx.get",
            return_value=_FakeResponse(html, "text/html"),
        )
        result = fetcher.fetch(TEST_URL)
        assert "Keep me" in result
        assert "Skip me" not in result
        assert "Also skip" not in result

    def test_plain_text_truncated_at_max_length(
        self, fetcher, mocker, patched_validate
    ):
        long_text = "x" * (MAX_CONTENT_LENGTH + 500)
        mocker.patch(
            "httpx.get",
            return_value=_FakeResponse(long_text, "text/plain"),
        )
        result = fetcher.fetch(TEST_URL)
        assert "truncated" in result
        assert len(result) < len(long_text)

    def test_html_content_truncated(self, fetcher, mocker, patched_validate):
        long_html = "<html><body><main>" + ("word " * 5000) + "</main></body></html>"
        mocker.patch(
            "httpx.get",
            return_value=_FakeResponse(long_html, "text/html"),
        )
        result = fetcher.fetch(TEST_URL)
        assert len(result) <= MAX_CONTENT_LENGTH + len(
            "\n\n[... content truncated ...]"
        )


# ── TTL Cache ─────────────────────────────────────────────────────────


class TestCaching:
    def test_second_call_uses_cache(self, fetcher, mocker, patched_validate):
        mock_get = mocker.patch(
            "httpx.get",
            return_value=_FakeResponse("Cached content", "text/plain"),
        )
        fetcher.fetch(TEST_URL)
        fetcher.fetch(TEST_URL)
        # httpx.get should only have been called once
        assert mock_get.call_count == 1

    def test_cache_cleared_between_tests(self, fetcher, mocker, patched_validate):
        """Confirms autouse fixture clears cache correctly."""
        assert TEST_URL not in _cache

    def test_different_urls_fetched_separately(self, fetcher, mocker, patched_validate):
        mock_get = mocker.patch(
            "httpx.get",
            return_value=_FakeResponse("content", "text/plain"),
        )
        url2 = "https://other.example.com/"
        fetcher.fetch(TEST_URL)
        fetcher.fetch(url2)
        assert mock_get.call_count == 2


# ── Error handling ────────────────────────────────────────────────────


class TestErrorHandling:
    def test_http_404_raises_exception(self, fetcher, mocker, patched_validate):
        mocker.patch(
            "httpx.get",
            return_value=_FakeResponse("", "text/html", status_code=404),
        )
        with pytest.raises(Exception, match="404"):
            fetcher.fetch(TEST_URL)

    def test_connection_error_raises_exception(self, fetcher, mocker, patched_validate):
        import httpx

        mocker.patch("httpx.get", side_effect=httpx.RequestError("DNS failed"))
        with pytest.raises(Exception, match="Could not reach"):
            fetcher.fetch(TEST_URL)

    def test_timeout_raises_descriptive_exception(
        self, fetcher, mocker, patched_validate
    ):
        import httpx

        mocker.patch("httpx.get", side_effect=httpx.TimeoutException("timed out"))
        with pytest.raises(Exception, match="Timeout"):
            fetcher.fetch(TEST_URL)


# ── SSRF guard is invoked ─────────────────────────────────────────────


class TestSSRFGuardCalled:
    def test_validate_called_before_any_http_request(self, fetcher, mocker):
        mock_validate = mocker.patch(
            "app.utils.doc_fetcher.validate_fetch_url",
            side_effect=ValueError("blocked by SSRF guard"),
        )
        mock_get = mocker.patch("httpx.get")

        with pytest.raises(ValueError, match="blocked"):
            fetcher.fetch(TEST_URL)

        mock_validate.assert_called_once_with(TEST_URL)
        mock_get.assert_not_called()  # HTTP must NOT be called if validation fails
