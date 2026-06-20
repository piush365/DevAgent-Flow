# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

DevFlow Agent is a developer productivity tool with four AI-powered agents:
- **Context Agent** — analyzes a GitHub issue URL and identifies relevant files
- **Boilerplate Agent** — generates Python boilerplate from a plain English description
- **Docs Agent** — answers library questions grounded in fetched official documentation
- **PR Draft Agent** — writes PR descriptions from `git diff` output

Architecture: Flask backend (streaming JSON-less API) + Streamlit frontend. Both processes run concurrently; Streamlit calls Flask at `http://localhost:5000`.

## Running the app

Two processes must run simultaneously in separate terminals:

```bash
# Terminal 1 — Flask backend
python run.py

# Terminal 2 — Streamlit frontend
streamlit run frontend/streamlit_app.py
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Copy `.env` from its committed template and fill in keys:
```bash
# Required
GROQ_API_KEY=...

# Optional — raises GitHub API rate limit from 60 to 5,000 req/hr
GITHUB_TOKEN=...

# Optional — LLM fallbacks (Groq → Gemini → OpenRouter, all free tier)
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...
```

Health check: `GET http://localhost:5000/api/health`

## Architecture

### Backend (`app/`)

**Application factory** — `app/__init__.py:create_app()` registers four blueprints.

**Agents** (`app/agents/`) are the core logic layer. Each is a class with a `run(*args)` method that is a **generator** — it `yield`s string chunks for streaming. The pattern in every agent:
1. Validate and preprocess inputs
2. Fetch external data (GitHub, docs, parse diff)
3. Build a prompt string
4. `yield from self.llm.stream(prompt, system=...)`

**Routes** (`app/routes/`) are thin Flask blueprints that instantiate an agent and wrap its generator in `stream_with_context()`, returning `Response(mimetype="text/plain")` with `X-Accel-Buffering: no`. All endpoints are `POST /api/<name>`.

**LLM fallback chain** (`app/utils/llm_client.py`) — `LLMClient.stream()` tries Groq (`llama-3.1-8b-instant`) → Gemini Flash → OpenRouter (`llama-3.1-8b-instruct:free`). On a 429/rate-limit from any provider it yields a notice and falls through to the next.

**Utilities:**
- `github_client.py` — `GitHubClient` wraps PyGitHub to fetch issues, comments, and recursive file trees
- `diff_parser.py` — `DiffParser.parse()` converts raw unified diff text to `{files_changed, total_added, total_removed, summary}`
- `doc_fetcher.py` — fetches and extracts text from documentation URLs

### Frontend (`frontend/`)

`streamlit_app.py` is a single-page app. Agent selection via `render_sidebar()` returns a key (`context`, `boilerplate`, `docs`, `pr_draft`); each section is a big `if/elif` block rendering the form for that agent.

`stream_agent_response()` in `components/output_panel.py` drives the streaming display: it POSTs to Flask with `stream=True`, accumulates chunks, and re-renders a `st.empty()` placeholder on each chunk with a blinking cursor.

The UI uses the Catppuccin Mocha color palette injected via `frontend/styles/mocha.py`.

### Adding a new agent

1. Create `app/agents/<name>_agent.py` — class with `run()` as a generator
2. Create `app/routes/<name>.py` — blueprint that wraps the agent in `stream_with_context()`
3. Register the blueprint in `app/__init__.py`
4. Add the UI section in `frontend/streamlit_app.py`

## API surface

| Method | Path | Body keys | Notes |
|--------|------|-----------|-------|
| GET | `/api/health` | — | Returns provider availability |
| POST | `/api/context` | `issue_url` | Full GitHub issue URL |
| POST | `/api/boilerplate` | `description`, `style_ref?` | `style_ref` is a raw code URL |
| POST | `/api/docs` | `library?`, `question`, `custom_url?` | Built-in libs listed in `docs_agent.py:DOCS_URLS` |
| POST | `/api/pr-draft` | `diff`, `issue_number?` | Raw `git diff` output |

All responses are `text/plain` streamed chunks.
