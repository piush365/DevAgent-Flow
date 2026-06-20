"""
DevFlow Agent — Boilerplate Agent
Generates Python boilerplate code from a plain English description.

Input:  Description string + optional style reference URL
Output: Streamed Python boilerplate with inline comments
"""

import logging
from typing import Generator

from app.agents.base_agent import BaseAgent
from app.utils.doc_fetcher import DocFetcher

logger = logging.getLogger(__name__)

# Characters of style reference to include in the prompt
_STYLE_REF_CHAR_LIMIT = 3_000


class BoilerplateAgent(BaseAgent):
    """Generates Python boilerplate from natural language descriptions."""

    def __init__(self) -> None:
        super().__init__()
        self.fetcher = DocFetcher()

    def run(
        self, description: str, style_ref: str | None = None
    ) -> Generator[str, None, None]:
        """
        Generate boilerplate code, optionally matching a style reference.

        Args:
            description: Plain English description of what to build.
            style_ref:   Optional URL of a code file to match conventions.

        Yields:
            Text chunks for streaming to the frontend.
        """
        style_content: str | None = None

        # ── Step 1: Fetch style reference if provided ──────────────────
        if style_ref:
            logger.info("BoilerplateAgent: fetching style reference %s", style_ref)
            yield f"📄 Fetching style reference…\n\n"
            try:
                style_content = self.fetcher.fetch(style_ref)
                yield "✅ Style reference loaded — matching its conventions\n\n"
            except ValueError as exc:
                # URL failed SSRF validation
                yield f"⚠️ Invalid style reference URL: {exc}\n"
                yield "Generating with default Python conventions instead.\n\n"
            except Exception as exc:
                yield f"⚠️ Could not fetch style reference: {exc}\n"
                yield "Generating with default Python conventions instead.\n\n"

        # ── Step 2: Build prompt and stream LLM response ───────────────
        prompt = self._build_prompt(description, style_content)
        yield "---\n\n"
        yield from self._stream_llm(prompt)

    def _build_prompt(
        self, description: str, style_content: str | None = None
    ) -> str:
        """Build the LLM prompt for boilerplate generation."""
        style_section = ""
        if style_content:
            truncated = style_content[:_STYLE_REF_CHAR_LIMIT]
            style_section = f"""

## Style Reference
Match the coding conventions, naming patterns, docstring style, and structure
from this reference code:

```
{truncated}
```

Follow the same patterns for:
- Import organisation
- Class/function naming
- Docstring format
- Error handling patterns
- Code structure and layout
"""

        return f"""Generate Python boilerplate code for the following requirement:

## Requirement
{description}
{style_section}

## Instructions
1. Generate clean, production-ready Python code
2. Include inline comments explaining each section
3. Add proper docstrings for all classes and functions
4. Include TODO markers for parts that need customisation
5. Follow PEP 8 conventions
6. Include necessary imports at the top
7. Add type hints where appropriate
8. Include a brief module docstring at the top

Output ONLY the Python code with comments — no explanatory text before or after."""

    def _system_prompt(self) -> str:
        return (
            "You are an expert Python developer who writes clean, well-documented "
            "boilerplate code. Generate production-quality code with helpful inline "
            "comments. Follow PEP 8, use type hints, and write clear docstrings."
        )
