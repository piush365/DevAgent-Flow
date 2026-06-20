# Architecture Document — DevFlow Agent

**Version:** 1.0  
**Date:** June 2026  
**Companion to:** `prd.md`, `design.md`

---

## 1. Architecture Philosophy

Three constraints shaped every decision here:

- **8-week buildable** — no over-engineering; every layer must justify its existence
- **Team of 3** — clear ownership boundaries so work never blocks each other
- **Moderate structure** — separate agent classes with a shared LLM client; not too flat, not too abstract

The architecture is a **synchronous Flask monolith** with a Streamlit frontend. No queues, no microservices, no async complexity. Each agent is a self-contained Python class that receives input, calls external services, and returns a streamed response.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│                   Streamlit (Python)                            │
│  sidebar nav → agent input form → streaming output panel        │
└───────────────────────────┬─────────────────────────────────────┘
                            │  HTTP (requests / SSE stream)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FLASK BACKEND                             │
│                                                                 │
│   ┌─────────────┐    ┌──────────────────────────────────────┐  │
│   │   Routes    │───▶│           Agent Layer                │  │
│   │  /api/      │    │                                      │  │
│   │  context    │    │  ContextAgent   BoilerplateAgent     │  │
│   │  boilerplate│    │  DocsAgent      PRDraftAgent         │  │
│   │  docs       │    │                                      │  │
│   │  pr-draft   │    └──────────────┬───────────────────────┘  │
│   │  health     │                   │                           │
│   └─────────────┘    ┌─────────────▼───────────────────────┐  │
│                       │          Utils Layer                 │  │
│                       │                                      │  │
│                       │  LLMClient   GitHubClient            │  │
│                       │  DocFetcher  DiffParser              │  │
│                       └──────────────────────────────────────┘  │
└───────────────────────────┬──────────────────┬──────────────────┘
                            │                  │
                ┌───────────▼──────┐  ┌────────▼────────┐
                │   Groq API       │  │   GitHub API     │
                │  (LLM inference) │  │  (issues, repos) │
                └──────────────────┘  └─────────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   httpx (doc fetch)  │
                                    │   gitpython (diffs)  │
                                    └──────────────────────┘
```

---

## 3. Layer Responsibilities

### 3.1 Routes Layer (`app/routes/`)

Thin HTTP layer only. Each route file does exactly three things:

1. Parse and validate the incoming JSON request
2. Instantiate the relevant agent and call `.run()`
3. Return the streamed `Response` to the frontend

No business logic lives here. If a route file exceeds ~40 lines, something is wrong.

```python
# Example: app/routes/context.py
from flask import Blueprint, request, Response, stream_with_context
from app.agents.context_agent import ContextAgent

context_bp = Blueprint("context", __name__)

@context_bp.route("/api/context", methods=["POST"])
def context_route():
    data = request.get_json()
    issue_url = data.get("issue_url", "").strip()
    if not issue_url:
        return {"error": "issue_url is required"}, 400

    agent = ContextAgent()
    return Response(
        stream_with_context(agent.run(issue_url)),
        mimetype="text/plain"
    )
```

---

### 3.2 Agent Layer (`app/agents/`)

Each agent is a class with a single public method: `.run()`. It returns a **generator** that yields text chunks — this is what gets streamed to the frontend.

Every agent follows this pattern:

```python
class BaseAgent:
    def __init__(self):
        self.llm = LLMClient()          # shared Groq wrapper
    
    def run(self, *args, **kwargs):
        raise NotImplementedError
    
    def _build_prompt(self, *args, **kwargs):
        raise NotImplementedError
```

Each agent inherits from `BaseAgent` and implements `run()` and `_build_prompt()`.

**Why classes, not functions?**  
Shared `LLMClient` instance per request, clean separation of prompt logic from HTTP concerns, and easy to test in isolation.

---

### 3.3 Utils Layer (`app/utils/`)

Shared, stateless helpers used by agents. No agent calls an external service directly — it always goes through a util.

| Util | Responsibility |
|---|---|
| `llm_client.py` | Wraps Groq SDK; handles streaming, retries, prompt formatting |
| `github_client.py` | Wraps PyGitHub; fetches issues, comments, file trees |
| `doc_fetcher.py` | Uses httpx to fetch and clean documentation pages |
| `diff_parser.py` | Parses raw git diff text into structured change summary |

---

## 4. Agent Internals

### 4.1 ContextAgent

```
run(issue_url)
    │
    ├── GitHubClient.fetch_issue(issue_url)
    │       → title, body, labels, comments
    │
    ├── GitHubClient.fetch_file_tree(repo)
    │       → list of file paths
    │
    ├── _rank_relevant_files(issue_body, file_tree)
    │       → top 5 files by keyword overlap
    │
    ├── _build_prompt(issue, comments, relevant_files)
    │
    └── LLMClient.stream(prompt)
            → yields chunks → streamed to frontend
```

`_rank_relevant_files` is pure Python — extract keywords from issue body, score each file path by keyword matches. No LLM needed for this step; keeps it fast and deterministic.

---

### 4.2 BoilerplateAgent

```
run(description, style_ref=None)
    │
    ├── [if style_ref] DocFetcher.fetch(style_ref)
    │       → raw code/text for style inference
    │
    ├── _build_prompt(description, style_ref_content)
    │       → instructs LLM to match style conventions
    │
    └── LLMClient.stream(prompt)
            → yields code chunks → streamed to frontend
```

If no style reference is provided, the prompt defaults to PEP8-compliant Python with Flask conventions.

---

### 4.3 DocsAgent

```
run(library, question, custom_url=None)
    │
    ├── _resolve_docs_url(library, custom_url)
    │       → maps known libraries to their docs base URL
    │
    ├── DocFetcher.fetch(docs_url, query=question)
    │       → fetches page, strips HTML, returns clean text
    │
    ├── _build_prompt(question, doc_content)
    │       → instructs LLM to answer ONLY from doc content
    │
    └── LLMClient.stream(prompt)
            → yields answer + code snippet → streamed
```

Critical constraint enforced in prompt: *"Answer only using the provided documentation text. If the answer is not present, say so explicitly."* This prevents hallucinated API signatures.

---

### 4.4 PRDraftAgent

```
run(diff_text, issue_number=None)
    │
    ├── DiffParser.parse(diff_text)
    │       → {files_changed, lines_added, lines_removed, change_summary}
    │
    ├── _build_prompt(parsed_diff, issue_number)
    │
    └── LLMClient.stream(prompt)
            → yields PR description → streamed to frontend
```

`DiffParser` uses Python's built-in string processing — no external library needed. It extracts file names from `diff --git` lines and counts `+`/`-` lines.

---

## 5. LLMClient — Streaming Pattern

```python
# app/utils/llm_client.py
from groq import Groq
import os

class LLMClient:
    def __init__(self):
        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self.model = "llama-3.1-8b-instant"

    def stream(self, prompt: str, system: str = "You are a helpful developer assistant."):
        """Yields text chunks from Groq streaming response."""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            max_tokens=1024,
            temperature=0.3   # low temp for deterministic code output
        )
        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
```

Flask's `stream_with_context` passes these chunks directly to the HTTP response. Streamlit reads them chunk-by-chunk and appends to the output panel.

---

## 6. Configuration & Secrets

All config lives in `.env`. Loaded at app startup via `python-dotenv`.

```bash
# .env.example
GROQ_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_token_here   # optional but recommended
FLASK_ENV=development
FLASK_PORT=5000
```

```python
# app/config.py
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    GROQ_API_KEY = os.environ["GROQ_API_KEY"]
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")   # optional
    FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
    STREAMLIT_FLASK_URL = os.environ.get("FLASK_URL", "http://localhost:5000")
```

`GITHUB_TOKEN` is optional. Without it, the GitHub API allows 60 unauthenticated requests/hour — sufficient for demos. With it, 5000 requests/hour.

---

## 7. Request & Response Flow (End-to-End)

Using Context Agent as the example:

```
1. User pastes GitHub issue URL into Streamlit input
2. User clicks "Run Context Agent"
3. Streamlit sends POST /api/context  {"issue_url": "https://github.com/..."}
4. Flask route validates input → instantiates ContextAgent
5. ContextAgent calls GitHubClient.fetch_issue()
      → PyGitHub fetches issue from GitHub REST API
6. ContextAgent calls GitHubClient.fetch_file_tree()
      → PyGitHub fetches repo contents
7. ContextAgent ranks relevant files (pure Python)
8. ContextAgent builds prompt string
9. ContextAgent calls LLMClient.stream(prompt)
      → Groq streams response chunks
10. Flask streams chunks via Response(stream_with_context(...))
11. Streamlit receives chunks, appends to output_placeholder
12. User sees text appearing token-by-token
13. Stream ends → Copy button appears
```

Total external API calls per Context Agent run: **2 GitHub calls + 1 Groq stream**

---

## 8. Error Handling Strategy

Keep it simple — errors surface as streamed text, not JSON error responses. This way the frontend doesn't need special error-state handling.

```python
def run(self, issue_url):
    try:
        issue = self.github.fetch_issue(issue_url)
    except Exception as e:
        yield f"⚠️ Could not fetch issue: {str(e)}\n"
        yield "Check that the URL is a valid public GitHub issue."
        return

    try:
        for chunk in self.llm.stream(self._build_prompt(issue)):
            yield chunk
    except Exception as e:
        yield f"\n⚠️ LLM error: {str(e)}"
```

Common errors handled per agent:

| Error | Message shown to user |
|---|---|
| Invalid GitHub URL | "URL doesn't look like a GitHub issue. Expected: github.com/owner/repo/issues/N" |
| GitHub rate limit | "GitHub API rate limit hit. Add a GITHUB_TOKEN to .env for higher limits." |
| Groq API error | "LLM inference failed. Check your GROQ_API_KEY in .env." |
| Docs page unreachable | "Could not fetch docs for [library]. Try providing a direct URL." |
| Empty git diff | "No changes detected in diff. Paste the output of: git diff HEAD" |

---

## 9. Running the App

```bash
# 1. Clone and install
git clone https://github.com/yourteam/devflow-agent
cd devflow-agent
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your GROQ_API_KEY and optionally GITHUB_TOKEN

# 3. Start Flask backend
python run.py

# 4. Start Streamlit frontend (separate terminal)
streamlit run frontend/streamlit_app.py
```

Flask runs on `localhost:5000`. Streamlit runs on `localhost:8501`. Both must be running for the app to work.

---

## 10. Dependency List

```
# requirements.txt
flask>=3.0
groq>=0.9
PyGithub>=2.3
httpx>=0.27
gitpython>=3.1
python-dotenv>=1.0
streamlit>=1.35
requests>=2.31       # for Streamlit → Flask HTTP calls
jinja2>=3.1          # boilerplate templating
```

---

## 11. What This Architecture Deliberately Avoids

| Avoided | Reason |
|---|---|
| Async Flask / FastAPI | Adds complexity; sync streaming is sufficient for 1 user demo |
| Database / ORM | No persistence needed in v1; session state handles recent runs |
| Redis / task queues | Overkill for synchronous single-user tool |
| Docker | Adds setup overhead; direct Python run is faster for 8-week build |
| Unit test framework setup | Keep tests as simple `assert`-based scripts for now |
| JWT auth / sessions | Single-user local tool; no auth needed |

---

*DevFlow Agent Architecture — simple enough to build, solid enough to demo.*
