"""
DevFlow Agent — LLM Client with Fallback Chain
Groq (primary) → Gemini Flash (fallback 1) → OpenRouter (fallback 2)

All three providers are on free tiers. The Groq client is instantiated
once per LLMClient instance to reuse its underlying connection pool.
"""

import json
import logging
import os
from typing import Generator

logger = logging.getLogger(__name__)

_GROQ_MODEL = "llama-3.1-8b-instant"
_GEMINI_MODEL = "gemini-1.5-flash"
_OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
_MAX_TOKENS = 2_048
_TEMPERATURE = 0.3


class LLMClient:
    """
    Streams LLM responses with automatic provider fallback on rate limits.

    Provider order: Groq → Gemini Flash → OpenRouter
    On any error from a provider the client yields a notice and tries
    the next one. If all providers fail an error message is streamed.
    """

    def __init__(self) -> None:
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")

        # Instantiate the Groq client once to reuse its connection pool.
        self._groq_client = None
        if self.groq_key:
            from groq import Groq
            self._groq_client = Groq(api_key=self.groq_key)
            logger.debug("Groq client initialised")

        # Gemini model is created per-call because system_instruction is
        # per-request; creating GenerativeModel is lightweight.
        if self.gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            logger.debug("Gemini configured")

    def stream(
        self, prompt: str, system: str = "You are a helpful developer assistant."
    ) -> Generator[str, None, None]:
        """
        Yield text chunks, trying providers in order until one succeeds.

        Args:
            prompt: User-facing prompt string.
            system: System role instruction for the LLM.

        Yields:
            String chunks of the LLM response.
        """
        # ── Primary: Groq ──────────────────────────────────────────────
        if self._groq_client:
            try:
                logger.debug("Trying Groq (%s)", _GROQ_MODEL)
                yield from self._stream_groq(prompt, system)
                return
            except Exception as exc:
                yield from self._handle_provider_error("Groq", exc, "Gemini")

        # ── Fallback 1: Gemini Flash ───────────────────────────────────
        if self.gemini_key:
            try:
                logger.debug("Trying Gemini (%s)", _GEMINI_MODEL)
                yield from self._stream_gemini(prompt, system)
                return
            except Exception as exc:
                yield from self._handle_provider_error("Gemini", exc, "OpenRouter")

        # ── Fallback 2: OpenRouter ─────────────────────────────────────
        if self.openrouter_key:
            try:
                logger.debug("Trying OpenRouter (%s)", _OPENROUTER_MODEL)
                yield from self._stream_openrouter(prompt, system)
                return
            except Exception as exc:
                logger.error("OpenRouter error: %s", exc)
                yield f"⚠️ OpenRouter error: {exc}\n\n"

        yield "❌ All LLM providers are unavailable. Check your API keys in .env\n"
        yield "Required: GROQ_API_KEY\n"
        yield "Optional fallbacks: GEMINI_API_KEY, OPENROUTER_API_KEY\n"

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    def _stream_groq(self, prompt: str, system: str) -> Generator[str, None, None]:
        """Stream from Groq (llama-3.1-8b-instant) using cached client."""
        completion = self._groq_client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            stream=True,
            max_tokens=_MAX_TOKENS,
            temperature=_TEMPERATURE,
        )
        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _stream_gemini(self, prompt: str, system: str) -> Generator[str, None, None]:
        """Stream from Google Gemini Flash."""
        import google.generativeai as genai

        model = genai.GenerativeModel(
            model_name=_GEMINI_MODEL,
            system_instruction=system,
        )
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def _stream_openrouter(
        self, prompt: str, system: str
    ) -> Generator[str, None, None]:
        """Stream from OpenRouter AI using Server-Sent Events."""
        import httpx

        with httpx.stream(
            "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://devflow-agent.local",
                "X-Title": "DevFlow Agent",
            },
            json={
                "model": _OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": _MAX_TOKENS,
                "temperature": _TEMPERATURE,
                "stream": True,
            },
            timeout=60.0,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]  # strip "data: " prefix
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    # ------------------------------------------------------------------
    # Shared error handling
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_provider_error(
        provider: str, exc: Exception, next_provider: str
    ) -> Generator[str, None, None]:
        """Yield a user-visible notice then let execution fall through."""
        err = str(exc).lower()
        is_rate_limit = "429" in str(exc) or "rate" in err or "limit" in err or "quota" in err

        if is_rate_limit:
            logger.warning("%s rate limit hit; falling back to %s", provider, next_provider)
            yield f"⚡ {provider} rate limit — switching to {next_provider}…\n\n"
        else:
            logger.error("%s error: %s", provider, exc)
            yield f"⚠️ {provider} error: {exc}\n\n"
