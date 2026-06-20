"""
DevFlow Agent — Boilerplate Agent
Generates Python boilerplate code from a plain English description.

Input:  Description string + optional style reference URL
Output: Streamed Python boilerplate with inline comments
"""

from app.utils.llm_client import LLMClient
from app.utils.doc_fetcher import DocFetcher


class BoilerplateAgent:
    """Generates Python boilerplate from natural language descriptions."""

    def __init__(self):
        self.llm = LLMClient()
        self.fetcher = DocFetcher()

    def run(self, description: str, style_ref: str = None):
        """
        Generate boilerplate code, optionally matching a style reference.
        Yields text chunks for streaming.
        """
        style_content = None

        # ── Step 1: Fetch style reference if provided ──────────
        if style_ref:
            yield f"📄 Fetching style reference: {style_ref}\n\n"
            try:
                style_content = self.fetcher.fetch(style_ref)
                yield "✅ Style reference loaded — will match its conventions\n\n"
            except Exception as e:
                yield f"⚠️ Could not fetch style reference: {e}\n"
                yield "Generating with default Python conventions instead.\n\n"
                style_content = None

        # ── Step 2: Build prompt and stream LLM response ──────
        prompt = self._build_prompt(description, style_content)

        yield "---\n\n"

        try:
            for chunk in self.llm.stream(prompt, system=self._system_prompt()):
                yield chunk
        except Exception as e:
            yield f"\n⚠️ LLM error: {e}"

    def _build_prompt(self, description: str, style_content: str = None) -> str:
        """Build the LLM prompt for boilerplate generation."""
        style_section = ""
        if style_content:
            # Truncate to avoid exceeding context
            truncated = style_content[:3000]
            style_section = f"""

## Style Reference
Match the coding conventions, naming patterns, docstring style, and structure from this reference code:

```
{truncated}
```

Follow the same patterns for:
- Import organization
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
2. Include comprehensive inline comments explaining each section
3. Add proper docstrings for all classes and functions
4. Include TODO markers for parts that need customization
5. Follow PEP 8 conventions
6. Include necessary imports at the top
7. Add type hints where appropriate
8. Include a brief module docstring at the top

Output ONLY the Python code with comments — no explanatory text before or after."""

    def _system_prompt(self) -> str:
        return (
            "You are an expert Python developer who writes clean, well-documented boilerplate code. "
            "Generate production-quality code with helpful inline comments. "
            "Follow PEP 8, use type hints, and write clear docstrings."
        )
