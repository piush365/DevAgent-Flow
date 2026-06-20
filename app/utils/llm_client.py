"""
DevFlow Agent — LLM Client with Fallback Chain
Groq (primary) → Gemini Flash (fallback 1) → OpenRouter AI (fallback 2)
All three providers are 100% free tier.
"""

import os


class LLMClient:
    """Streams LLM responses with automatic provider fallback on rate limits."""

    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")

    def stream(self, prompt: str, system: str = "You are a helpful developer assistant."):
        """
        Try Groq → Gemini → OpenRouter, yielding text chunks.
        On 429 / rate limit, automatically falls through to next provider.
        """

        # ── Primary: Groq ──────────────────────────────────────
        if self.groq_key:
            try:
                yield from self._stream_groq(prompt, system)
                return
            except Exception as e:
                err = str(e).lower()
                if "429" in str(e) or "rate" in err or "limit" in err:
                    yield "⚡ Groq rate limit hit — switching to Gemini...\n\n"
                else:
                    yield f"⚠️ Groq error: {e}\n\n"

        # ── Fallback 1: Gemini Flash ───────────────────────────
        if self.gemini_key:
            try:
                yield from self._stream_gemini(prompt, system)
                return
            except Exception as e:
                err = str(e).lower()
                if "429" in str(e) or "quota" in err or "rate" in err:
                    yield "⚡ Gemini rate limit hit — switching to OpenRouter...\n\n"
                else:
                    yield f"⚠️ Gemini error: {e}\n\n"

        # ── Fallback 2: OpenRouter AI ──────────────────────────
        if self.openrouter_key:
            try:
                yield from self._stream_openrouter(prompt, system)
                return
            except Exception as e:
                yield f"⚠️ OpenRouter error: {e}\n\n"

        # ── All providers failed ───────────────────────────────
        yield "❌ All LLM providers are unavailable. Check your API keys in .env\n"
        yield "Required: GROQ_API_KEY\n"
        yield "Optional fallbacks: GEMINI_API_KEY, OPENROUTER_API_KEY\n"

    def _stream_groq(self, prompt: str, system: str):
        """Stream from Groq (llama-3.1-8b-instant)."""
        from groq import Groq

        client = Groq(api_key=self.groq_key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            stream=True,
            max_tokens=2048,
            temperature=0.3,
        )
        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _stream_gemini(self, prompt: str, system: str):
        """Stream from Google Gemini Flash."""
        import google.generativeai as genai

        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system,
        )
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def _stream_openrouter(self, prompt: str, system: str):
        """Stream from OpenRouter AI (free Llama model via OpenAI-compatible API)."""
        import httpx
        import json

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
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 2048,
                "temperature": 0.3,
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
