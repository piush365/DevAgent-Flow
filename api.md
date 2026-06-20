# API Document — DevFlow Agent

**Version:** 1.0  
**Date:** June 2026  
**Companion to:** `prd.md`, `design.md`, `architecture.md`

---

## 1. API Philosophy

- **No auth** — local tool, no API key protection needed on Flask endpoints
- **100% free** — every external API used is on a free tier with documented limits
- **Graceful fallbacks** — if a free API hits its limit, a free alternative takes over automatically
- **Mixed style** — REST for simple calls (`/health`), SSE streaming for all agent endpoints

---

## 2. Free External APIs Used

### 2.1 Groq API (Primary LLM)

| Property | Detail |
|---|---|
| Cost | Free tier |
| Model used | `llama-3.1-8b-instant` |
| Free limit | 14,400 requests/day, 6,000 tokens/minute |
| Latency | ~200ms to first token (fastest free LLM option) |
| Sign up | console.groq.com |
| Env var | `GROQ_API_KEY` |

**Why Groq:** Fastest free inference available. The `llama-3.1-8b-instant` model is more than capable for code generation, summarization, and Q&A tasks.

---

### 2.2 GitHub REST API (Context Agent)

| Property | Detail |
|---|---|
| Cost | Free (public repos) |
| Unauthenticated limit | 60 requests/hour |
| Authenticated limit | 5,000 requests/hour |
| Token type | Classic Personal Access Token (free) |
| Scopes needed | `public_repo` (read-only) |
| Sign up | github.com/settings/tokens |
| Env var | `GITHUB_TOKEN` (optional but recommended) |

**Note:** Each Context Agent run makes 2 GitHub API calls (issue fetch + file tree). At 60 unauthenticated requests/hour, that's 30 runs/hour — fine for demos. Add a free token for 5,000 requests/hour.

---

### 2.3 Google Gemini API (LLM Fallback — Free)

| Property | Detail |
|---|---|
| Cost | Free tier |
| Model used | `gemini-1.5-flash` |
| Free limit | 1,500 requests/day, 1M tokens/minute |
| Latency | ~500ms to first token |
| Sign up | aistudio.google.com |
| Env var | `GEMINI_API_KEY` |

**When used:** Automatically activates if Groq returns a rate limit error (429). Since you've already used Gemini in your Marathi project, you have the key ready.

---

### 2.4 Together AI (LLM Fallback #2 — Free)

| Property | Detail |
|---|---|
| Cost | $25 free credits on signup (no card needed) |
| Model used | `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-Free` |
| Free limit | Marked as `FREE` — no token limit on free model |
| Sign up | api.together.ai |
| Env var | `TOGETHER_API_KEY` |

**When used:** If both Groq and Gemini are rate-limited. Together AI's free model is permanent — not a trial.

---

### 2.5 httpx (Doc Fetching — No API Key)

| Property | Detail |
|---|---|
| Cost | Free — direct HTTP requests |
| No rate limit | Respects `robots.txt` and standard HTTP |
| Used by | DocsAgent — fetches official docs pages |
| Fallback | If a docs page blocks scraping, user can paste doc text directly |

---

### 2.6 PyGitHub + gitpython (No API Cost)

| Property | Detail |
|---|---|
| Cost | Free — Python libraries |
| PyGitHub | Wraps GitHub REST API (same limits as above) |
| gitpython | Reads local git diffs — no network call |
| Used by | ContextAgent (PyGitHub), PRDraftAgent (gitpython) |

---

## 3. LLM Fallback Chain

The `LLMClient` automatically tries providers in order until one succeeds:

```
Request → Groq (primary)
              │ 429 rate limit?
              ▼
         Gemini Flash (fallback #1)
              │ 429 rate limit?
              ▼
         Together AI Free (fallback #2)
              │ all failed?
              ▼
         Stream error message to user
```

Implementation:

```python
# app/utils/llm_client.py

import os
from groq import Groq
import google.generativeai as genai
from together import Together

class LLMClient:
    def __init__(self):
        self.groq = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.together_key = os.environ.get("TOGETHER_API_KEY")

    def stream(self, prompt: str, system: str = "You are a helpful developer assistant."):
        """Try Groq → Gemini → Together AI, yield chunks."""

        # Primary: Groq
        try:
            yield from self._stream_groq(prompt, system)
            return
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                yield "⚡ Groq rate limit hit — switching to Gemini...\n\n"
            else:
                yield f"⚠️ Groq error: {e}\n\n"

        # Fallback 1: Gemini Flash
        if self.gemini_key:
            try:
                yield from self._stream_gemini(prompt, system)
                return
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    yield "⚡ Gemini rate limit hit — switching to Together AI...\n\n"
                else:
                    yield f"⚠️ Gemini error: {e}\n\n"

        # Fallback 2: Together AI
        if self.together_key:
            try:
                yield from self._stream_together(prompt, system)
                return
            except Exception as e:
                yield f"⚠️ Together AI error: {e}\n\n"

        yield "❌ All LLM providers are unavailable. Check your API keys in .env."

    def _stream_groq(self, prompt, system):
        completion = self.groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            max_tokens=1024,
            temperature=0.3
        )
        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _stream_gemini(self, prompt, system):
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system
        )
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def _stream_together(self, prompt, system):
        client = Together(api_key=self.together_key)
        stream = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-Free",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            max_tokens=1024,
            temperature=0.3
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
```

---

## 4. Flask API Endpoints

Base URL: `http://localhost:5000`

---

### 4.1 GET `/api/health`

**Type:** REST  
**Purpose:** Confirm Flask is running and all API keys are loaded

**Request:** No body

**Response:**
```json
{
  "status": "ok",
  "providers": {
    "groq": true,
    "gemini": true,
    "together": false,
    "github_token": true
  }
}
```

`true` = key present in env, `false` = key missing (will use unauthenticated/skip)

---

### 4.2 POST `/api/context` — SSE Stream

**Type:** SSE (Server-Sent Events)  
**Agent:** ContextAgent  
**Purpose:** Generate a ready-to-code brief from a GitHub issue URL

**Request:**
```json
{
  "issue_url": "https://github.com/owner/repo/issues/101",
  "include_comments": true,
  "show_file_tree": true
}
```

| Field | Type | Required | Default |
|---|---|---|---|
| `issue_url` | string | Yes | — |
| `include_comments` | boolean | No | `true` |
| `show_file_tree` | boolean | No | `true` |

**Response:** `text/plain` stream

```
## Issue Brief — #101: Add .pyi stub support

**Summary**
The issue requests support for Python stub files (.pyi) in the docspec parser...

**Relevant Files**
- src/docspec/parser.py
- tests/test_parser.py
- docspec/__init__.py

**Suggested Starting Point**
Begin in `src/docspec/parser.py` around the file extension check logic...

**Open Questions**
- Should .pyi files be parsed identically to .py files?
- Comment from @NiklasRosenstein: "stubs should be treated as type hints only"
```

**Error responses (streamed):**
```
⚠️ Invalid GitHub URL. Expected format: github.com/owner/repo/issues/N
⚠️ GitHub API rate limit hit. Add GITHUB_TOKEN to .env for 5,000 requests/hour (free).
⚠️ Repository not found or is private.
```

---

### 4.3 POST `/api/boilerplate` — SSE Stream

**Type:** SSE  
**Agent:** BoilerplateAgent  
**Purpose:** Generate Python boilerplate from a plain English description

**Request:**
```json
{
  "description": "Flask route for user registration with email and password",
  "style_ref": "https://github.com/owner/repo/blob/main/app/routes/auth.py",
  "language": "python"
}
```

| Field | Type | Required | Default |
|---|---|---|---|
| `description` | string | Yes | — |
| `style_ref` | string | No | `null` |
| `language` | string | No | `"python"` |

**Response:** `text/plain` stream (Python code block)

```python
# app/routes/register.py
# Generated by DevFlow Agent — Boilerplate Agent

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

register_bp = Blueprint("register", __name__)

@register_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user with email and password.
    
    Body: { "email": str, "password": str }
    Returns: 201 on success, 400 on validation error
    """
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # TODO: validate email format
    # TODO: check if email already exists in DB
    # TODO: hash password and save user

    return jsonify({"message": "User registered"}), 201
```

**Error responses (streamed):**
```
⚠️ Description is required.
⚠️ Could not fetch style reference URL. Generating with default Python conventions.
```

---

### 4.4 POST `/api/docs` — SSE Stream

**Type:** SSE  
**Agent:** DocsAgent  
**Purpose:** Answer a library question using only official documentation

**Request:**
```json
{
  "library": "SQLAlchemy",
  "question": "How do I use async sessions?",
  "custom_url": null
}
```

| Field | Type | Required | Default |
|---|---|---|---|
| `library` | string | Yes (if no custom_url) | — |
| `question` | string | Yes | — |
| `custom_url` | string | No | `null` |

**Supported libraries (built-in URL mapping):**

| Library | Docs URL |
|---|---|
| Flask | flask.palletsprojects.com/en/stable |
| FastAPI | fastapi.tiangolo.com |
| SQLAlchemy | docs.sqlalchemy.org/en/20 |
| Pydantic | docs.pydantic.dev/latest |
| Celery | docs.celeryq.dev/en/stable |
| Groq Python | console.groq.com/docs |
| Python stdlib | docs.python.org/3 |
| Streamlit | docs.streamlit.io |
| Requests | requests.readthedocs.io |
| httpx | www.python-httpx.org |

Any library not in this list requires `custom_url`.

**Response:** `text/plain` stream

```
**Answer**
SQLAlchemy async sessions use `AsyncSession` from `sqlalchemy.ext.asyncio`.
You create an async engine, bind it to a session factory, and use it with
`async with` syntax inside your async functions.

**Code Example**
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_user(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.get(User, user_id)
        return result

**Source**
docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
```

**Error responses (streamed):**
```
⚠️ Library "XYZ" not in supported list. Provide a custom_url to fetch docs directly.
⚠️ Could not fetch documentation page. The site may be blocking requests.
   Tip: Paste the relevant doc text directly into custom_url field as plain text.
⚠️ Answer not found in the fetched documentation. Try rephrasing your question.
```

---

### 4.5 POST `/api/pr-draft` — SSE Stream

**Type:** SSE  
**Agent:** PRDraftAgent  
**Purpose:** Generate a PR description from a git diff

**Request:**
```json
{
  "diff": "diff --git a/src/parser.py b/src/parser.py\n...",
  "issue_number": 101
}
```

| Field | Type | Required | Default |
|---|---|---|---|
| `diff` | string | Yes | — |
| `issue_number` | integer | No | `null` |

**Response:** `text/plain` stream

```
**Title**
feat: add .pyi stub file support to docspec parser

**Summary**
This PR adds support for parsing Python stub files (.pyi) in docspec.
The parser now detects .pyi extensions and processes them as type-hint-only
modules, consistent with PEP 484 conventions.

**Changes**
- Modified `src/docspec/parser.py` to handle .pyi file extensions
- Added `is_stub_file()` helper function
- Updated `tests/test_parser.py` with 3 new test cases for stub files
- Added `.pyi` to supported extensions list in `docspec/__init__.py`

**Testing**
- [ ] Existing tests pass: `pytest tests/`
- [ ] New stub file tests pass
- [ ] Manual test: parsed a real .pyi file from typeshed

**Related Issues**
Closes #101
```

**Error responses (streamed):**
```
⚠️ No diff provided. Paste the output of: git diff HEAD
⚠️ Diff appears to be empty — no changes detected.
```

---

## 5. SSE Streaming — How It Works

Flask streams responses using `Response` + `stream_with_context`. Streamlit reads chunks via `requests` with `stream=True`.

**Flask side:**
```python
from flask import Response, stream_with_context

@bp.route("/api/context", methods=["POST"])
def context_route():
    data = request.get_json()
    agent = ContextAgent()
    return Response(
        stream_with_context(agent.run(data["issue_url"])),
        mimetype="text/plain",
        headers={"X-Accel-Buffering": "no"}   # disable nginx buffering if deployed
    )
```

**Streamlit side:**
```python
import requests
import streamlit as st

def call_agent_stream(endpoint: str, payload: dict):
    output = st.empty()
    full_text = ""
    with requests.post(
        f"http://localhost:5000{endpoint}",
        json=payload,
        stream=True,
        timeout=60
    ) as r:
        for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                full_text += chunk
                output.markdown(f"```\n{full_text}▌\n```")
    output.markdown(f"```\n{full_text}\n```")   # final render, no cursor
    return full_text
```

---

## 6. Free Tier Limits Summary

| API | Free Limit | Resets | Fallback |
|---|---|---|---|
| Groq | 14,400 req/day, 6,000 tok/min | Daily | Gemini Flash |
| Gemini Flash | 1,500 req/day, 1M tok/min | Daily | Together AI |
| Together AI (free model) | No hard limit on free model | — | Error message |
| GitHub (unauth) | 60 req/hour | Hourly | Add free token → 5,000/hr |
| GitHub (with token) | 5,000 req/hour | Hourly | — |
| httpx (doc fetch) | No limit | — | User pastes text |

**Realistic daily capacity at free tier:**
- ~7,000 Context Agent runs (2 GitHub calls + 1 Groq call each, token limit binding)
- ~14,000 Boilerplate / Docs / PR Draft runs (Groq only)
- Demo usage will never approach these limits

---

## 7. .env.example — All Keys

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional but recommended
GITHUB_TOKEN=your_github_personal_access_token_here

# Optional — LLM fallbacks (all free)
GEMINI_API_KEY=your_gemini_api_key_here
TOGETHER_API_KEY=your_together_ai_api_key_here

# Flask config
FLASK_ENV=development
FLASK_PORT=5000
FLASK_URL=http://localhost:5000
```

**Where to get each key (all free):**

| Key | URL |
|---|---|
| `GROQ_API_KEY` | console.groq.com → API Keys |
| `GITHUB_TOKEN` | github.com/settings/tokens → Generate new (classic) → `public_repo` scope |
| `GEMINI_API_KEY` | aistudio.google.com → Get API Key |
| `TOGETHER_API_KEY` | api.together.ai → Settings → API Keys |

---

## 8. Adding a New Free API (Guide for Teammates)

If you find a new free API worth adding, follow this checklist:

1. Verify it has a **permanent free tier** (not just a trial with expiry)
2. Document its rate limits in Section 6
3. Add its key to `.env.example` as optional
4. Add it to `LLMClient` fallback chain OR create a new util in `app/utils/`
5. Update `GET /api/health` to report its key presence
6. Note it in `requirements.txt`

---

*DevFlow Agent API Document — 100% free, zero compromises.*
