"""
DevFlow Agent — Docs Agent
Answers library questions using only official documentation content.

Input:  Library name + question + optional custom docs URL
Output: Streamed answer grounded strictly in fetched documentation
"""

import logging
from typing import Generator

from app.agents.base_agent import BaseAgent
from app.utils.doc_fetcher import DocFetcher

logger = logging.getLogger(__name__)

# Built-in URL mapping for popular Python libraries.
# Maps lowercase library name → root documentation URL.
DOCS_URLS: dict[str, str] = {
    "flask": "https://flask.palletsprojects.com/en/stable/",
    "fastapi": "https://fastapi.tiangolo.com/",
    "sqlalchemy": "https://docs.sqlalchemy.org/en/20/",
    "pydantic": "https://docs.pydantic.dev/latest/",
    "celery": "https://docs.celeryq.dev/en/stable/",
    "streamlit": "https://docs.streamlit.io/",
    "requests": "https://requests.readthedocs.io/en/latest/",
    "httpx": "https://www.python-httpx.org/",
    "python": "https://docs.python.org/3/",
    "python stdlib": "https://docs.python.org/3/library/",
    "django": "https://docs.djangoproject.com/en/5.0/",
    "pytest": "https://docs.pytest.org/en/stable/",
    "numpy": "https://numpy.org/doc/stable/",
    "pandas": "https://pandas.pydata.org/docs/",
    "groq": "https://console.groq.com/docs/",
    "pygithub": "https://pygithub.readthedocs.io/en/stable/",
    "beautifulsoup": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
    "dotenv": "https://saurabh-kumar.com/python-dotenv/",
}

_MIN_CONTENT_CHARS = 50


class DocsAgent(BaseAgent):
    """Answers library questions grounded strictly in official documentation."""

    def __init__(self) -> None:
        super().__init__()
        self.fetcher = DocFetcher()

    def run(
        self,
        library: str,
        question: str,
        custom_url: str | None = None,
    ) -> Generator[str, None, None]:
        """
        Fetch documentation then answer the question using only that content.

        Args:
            library:    Library name (matched case-insensitively against DOCS_URLS).
            question:   Plain English question about the library.
            custom_url: Override URL — skips the built-in library lookup.

        Yields:
            Text chunks for streaming to the frontend.
        """
        # ── Step 1: Resolve docs URL ───────────────────────────────────
        docs_url = self._resolve_docs_url(library, custom_url)
        if not docs_url:
            supported = ", ".join(sorted(DOCS_URLS.keys()))
            yield (
                f'⚠️ Library "{library}" is not in the built-in list.\n'
                "Provide a custom_url to fetch docs directly.\n\n"
                f"Supported libraries: {supported}\n"
            )
            return

        logger.info("DocsAgent: fetching %s", docs_url)
        yield f"📖 Fetching docs from: {docs_url}\n\n"

        # ── Step 2: Fetch docs content ─────────────────────────────────
        try:
            doc_content = self.fetcher.fetch(docs_url)
        except ValueError as exc:
            yield f"⚠️ Invalid docs URL: {exc}\n"
            return
        except Exception as exc:
            yield f"⚠️ Could not fetch documentation: {exc}\n"
            yield "Tip: provide a more specific docs URL (e.g., a specific page, not the index).\n"
            return

        if not doc_content or len(doc_content.strip()) < _MIN_CONTENT_CHARS:
            yield "⚠️ Fetched page has very little readable content.\n"
            yield "Try a more specific docs URL (e.g., the API reference page).\n"
            return

        yield f"✅ Loaded {len(doc_content):,} characters of documentation\n\n"

        # ── Step 3: Build prompt and stream LLM response ───────────────
        prompt = self._build_prompt(library, question, doc_content, docs_url)
        yield "---\n\n"
        yield from self._stream_llm(prompt)

    def _resolve_docs_url(
        self, library: str, custom_url: str | None
    ) -> str | None:
        """Return the docs URL to use, preferring custom_url if provided."""
        if custom_url:
            return custom_url.strip()
        return DOCS_URLS.get(library.lower().strip())

    def _build_prompt(
        self,
        library: str,
        question: str,
        doc_content: str,
        source_url: str,
    ) -> str:
        """Build the strictly-grounded LLM prompt."""
        return f"""Answer the following question about {library} using ONLY the \
documentation text provided below.

## Question
{question}

## Documentation Content (from {source_url})
{doc_content}

## STRICT Instructions
1. Answer ONLY using information from the documentation text above
2. If the answer is not present, say: "This information is not in the fetched \
documentation. Try a more specific docs URL."
3. Do NOT use your general knowledge — only the text above
4. Include relevant code examples from the documentation
5. Keep the answer concise and practical

## Response Format

**Answer**
[Your answer here]

**Code Example**
[Code snippet if applicable]

**Source**
{source_url}"""

    def _system_prompt(self) -> str:
        return (
            "You are a documentation assistant. You answer questions STRICTLY "
            "using only the documentation text provided. Never use outside knowledge. "
            "If the answer is not in the provided text, say so explicitly. "
            "Always cite the source URL."
        )
