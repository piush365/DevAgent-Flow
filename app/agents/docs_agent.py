"""
DevFlow Agent — Docs Agent
Answers library questions using only official documentation content.

Input:  Library name + question + optional custom docs URL
Output: Streamed answer grounded in fetched documentation
"""

from app.utils.llm_client import LLMClient
from app.utils.doc_fetcher import DocFetcher


# Built-in docs URL mapping for popular Python libraries
DOCS_URLS = {
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


class DocsAgent:
    """Answers library questions grounded strictly in official documentation."""

    def __init__(self):
        self.llm = LLMClient()
        self.fetcher = DocFetcher()

    def run(self, library: str, question: str, custom_url: str = None):
        """
        Fetch documentation, then answer the question using only that content.
        Yields text chunks for streaming.
        """
        # ── Step 1: Resolve docs URL ──────────────────────────
        docs_url = self._resolve_docs_url(library, custom_url)
        if not docs_url:
            yield (
                f"⚠️ Library \"{library}\" not in supported list.\n"
                "Provide a custom_url to fetch docs directly.\n\n"
                "Supported libraries: " + ", ".join(sorted(DOCS_URLS.keys())) + "\n"
            )
            return

        yield f"📖 Fetching docs from: {docs_url}\n\n"

        # ── Step 2: Fetch docs content ─────────────────────────
        try:
            doc_content = self.fetcher.fetch(docs_url)
        except Exception as e:
            yield f"⚠️ Could not fetch documentation: {e}\n"
            yield "Tip: Paste the relevant doc text directly or provide a more specific URL.\n"
            return

        if not doc_content or len(doc_content.strip()) < 50:
            yield "⚠️ Fetched page appears to have very little content.\n"
            yield "Try providing a more specific docs URL (e.g., a specific page, not the index).\n"
            return

        yield f"✅ Loaded {len(doc_content)} characters of documentation\n\n"

        # ── Step 3: Build prompt and stream LLM response ──────
        prompt = self._build_prompt(library, question, doc_content, docs_url)

        yield "---\n\n"

        try:
            for chunk in self.llm.stream(prompt, system=self._system_prompt()):
                yield chunk
        except Exception as e:
            yield f"\n⚠️ LLM error: {e}"

    def _resolve_docs_url(self, library: str, custom_url: str = None) -> str:
        """Resolve a documentation URL for the given library."""
        if custom_url:
            return custom_url.strip()

        # Look up in built-in mapping (case-insensitive)
        key = library.lower().strip()
        return DOCS_URLS.get(key)

    def _build_prompt(self, library: str, question: str, doc_content: str, source_url: str) -> str:
        """Build the LLM prompt — strictly grounded in documentation."""
        return f"""Answer the following question about {library} using ONLY the documentation text provided below.

## Question
{question}

## Documentation Content (from {source_url})
{doc_content}

## STRICT Instructions
1. Answer ONLY using information from the documentation text above
2. If the answer is not present in the documentation, say: "This information is not available in the fetched documentation. Try a more specific docs URL."
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
            "You are a documentation assistant. You answer questions STRICTLY using only "
            "the documentation text provided. Never use outside knowledge. If the answer "
            "is not in the provided text, say so explicitly. Always cite the source URL."
        )
