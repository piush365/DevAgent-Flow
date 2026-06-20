<div align="center">

```
██████╗ ███████╗██╗   ██╗███████╗██╗      ██████╗ ██╗    ██╗
██╔══██╗██╔════╝██║   ██║██╔════╝██║     ██╔═══██╗██║    ██║
██║  ██║█████╗  ██║   ██║█████╗  ██║     ██║   ██║██║ █╗ ██║
██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║     ██║   ██║██║███╗██║
██████╔╝███████╗ ╚████╔╝ ██║     ███████╗╚██████╔╝╚███╔███╔╝
╚═════╝ ╚══════╝  ╚═══╝  ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝

                      A G E N T
```

### *From GitHub issue to ready-to-code brief in under 10 seconds.*

<br/>

[![CI](https://github.com/piush365/DevAgent-Flow/actions/workflows/ci.yml/badge.svg)](https://github.com/piush365/DevAgent-Flow/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11_%7C_3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![Linter: ruff](https://img.shields.io/badge/linter-ruff-D7FF64?logo=ruff&logoColor=black)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-130%20passing-22c55e)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%25-22c55e)](tests/)
[![LLM](https://img.shields.io/badge/LLM-Groq_%7C_Gemini_%7C_OpenRouter-7c3aed)](https://console.groq.com)

<br/>

[**Quick Start**](#-quick-start) · [**Agents**](#-agents) · [**Architecture**](#-architecture) · [**API**](#-api-reference) · [**Contributing**](#-contributing)

</div>

---

## What is DevFlow Agent?

DevFlow Agent is a **local AI-powered productivity tool** for developers — a suite of four specialized agents that eliminate the two biggest time-sinks in a developer's day: context-switching and boilerplate.

Paste a GitHub issue URL → get a **ready-to-code brief** with relevant files and a suggested starting point. Describe what you need → get **Python boilerplate** that matches your repo's conventions. Ask about a library → get a **direct answer grounded in the official docs**, not a hallucinated response. Paste your `git diff` → get a **structured PR description** ready to post.

Everything streams token-by-token. All LLM providers are **free tier**. Zero cloud dependencies — runs entirely on your machine.

---

## ✨ Highlights

<table>
<tr>
<td width="50%">

**🔒 Security-first**
SSRF protection on every URL fetch. Debug mode off by default. Rate limiting and CORS configured. Request size capped at 5 MB.

</td>
<td width="50%">

**⚡ Streaming output**
Responses appear token-by-token — no waiting for the full LLM response before you see anything.

</td>
</tr>
<tr>
<td width="50%">

**🔄 Automatic LLM fallback**
Groq → Gemini Flash → OpenRouter. If one provider rate-limits you, the next one picks up seamlessly.

</td>
<td width="50%">

**🐳 Production-ready**
Dockerfile, docker-compose, Gunicorn config, and a Makefile included. `docker compose up` and you're running.

</td>
</tr>
<tr>
<td width="50%">

**🧪 Tested**
130 tests across unit and integration layers. All external services are mocked. 85% coverage enforced in CI.

</td>
<td width="50%">

**🎨 Dark theme**
Catppuccin Mocha palette throughout. Looks good at 2 AM when you're shipping a hotfix.

</td>
</tr>
</table>

---

## 🤖 Agents

### 🔍 Context Agent
> *Eliminate the cold-start problem when picking up a new issue.*

Paste any public GitHub issue URL. DevFlow fetches the issue body, comments, and repository file tree, then uses keyword ranking to surface the most relevant files — and asks an LLM to write you a structured brief before you've even opened your editor.

```
Input  → https://github.com/org/repo/issues/42
Output → ## Issue Summary
          Adds rate limiting to the /api/upload endpoint to prevent abuse.

          ## Relevant Files
          1. app/routes/upload.py   — the endpoint being modified
          2. app/middleware/auth.py — existing middleware pattern to follow
          3. tests/test_upload.py   — test file to extend

          ## Suggested Starting Point
          Add flask-limiter decorator to the upload route, following
          the pattern in app/routes/context.py (already rate-limited).

          ## Open Questions
          - Should the limit be per-user or per-IP?
```

**Options:** `include_comments` (default: true) · `show_file_tree` (default: true)

---

### ⚡ Boilerplate Agent
> *Never write structural scaffolding from scratch again.*

Describe what you need in plain English. Optionally paste a URL to a file in your repo as a style reference — DevFlow will match its import organisation, docstring format, naming conventions, and error handling patterns.

```
Input  → "Flask route for user registration with email and password validation"
         style_ref: https://raw.githubusercontent.com/org/repo/main/app/routes/login.py

Output → """User registration endpoint."""
          from flask import Blueprint, request, jsonify
          from app.utils.validators import validate_email, validate_password
          from app.models import User, db
          ...
```

---

### 📖 Docs Agent
> *Ask the docs directly — get a grounded answer with a code snippet.*

Select from 17 built-in libraries or paste any docs URL. DevFlow fetches the actual documentation page and answers your question strictly from its content — no hallucinated API signatures.

**Built-in libraries:** Flask · FastAPI · SQLAlchemy · Pydantic · Streamlit · httpx · Requests · Django · Pytest · NumPy · Pandas · Celery · Python stdlib · Groq · PyGitHub · BeautifulSoup · dotenv

---

### 📝 PR Draft Agent
> *Turn a git diff into a PR description in one paste.*

Paste the output of `git diff HEAD` (or any diff). The agent parses the changed files, line counts, and structure — then writes a professional PR description with title, summary, change list, and a testing checklist. Optionally link an issue number.

```bash
git diff HEAD | pbcopy   # copy diff to clipboard
# paste into DevFlow → get a PR description ready to post
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or 3.12
- A free [Groq API key](https://console.groq.com) (takes 30 seconds)

### Option A — Local (two terminals)

```bash
# 1. Clone and install
git clone https://github.com/piush365/DevAgent-Flow.git
cd DevAgent-Flow
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Open .env and add your GROQ_API_KEY

# Terminal 1 — Flask backend
python run.py

# Terminal 2 — Streamlit frontend
streamlit run frontend/streamlit_app.py
```

Open **http://localhost:8501** in your browser.

### Option B — Docker (one command)

```bash
git clone https://github.com/piush365/DevAgent-Flow.git
cd DevAgent-Flow
cp .env.example .env   # add your GROQ_API_KEY
docker compose up --build
```

Backend: `http://localhost:5000` · Frontend: `http://localhost:8501`

---

## 🔑 API Keys

| Key | Required | Free limit | Where to get it |
|-----|:--------:|-----------|-----------------|
| `GROQ_API_KEY` | **Yes** | 14,400 req/day | [console.groq.com](https://console.groq.com) → API Keys |
| `GITHUB_TOKEN` | No | Raises limit 60 → 5,000 req/hr | github.com/settings/tokens |
| `GEMINI_API_KEY` | No | 1,500 req/day | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| `OPENROUTER_API_KEY` | No | Free model, no hard limit | [openrouter.ai/keys](https://openrouter.ai/keys) |

> Gemini and OpenRouter activate **automatically** as fallbacks if Groq hits its rate limit — you never see an error, just a notice in the stream.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│         (Catppuccin Mocha · port 8501)               │
│                                                      │
│  Sidebar nav → Agent form → st.empty() stream panel  │
└──────────────────────┬──────────────────────────────┘
                       │  POST /api/<agent>
                       │  stream=True · text/plain
                       ▼
┌─────────────────────────────────────────────────────┐
│                   Flask Backend                      │
│              (Gunicorn · port 5000)                  │
│                                                      │
│  Routes (thin)  →  Agents (logic)  →  Utils          │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │              BaseAgent (ABC)                   │  │
│  │  run() · _build_prompt() · _stream_llm()       │  │
│  └──────┬──────────┬────────────┬────────────────┘  │
│         │          │            │                    │
│  ContextAgent  BoilerplateAgent DocsAgent PRDraft    │
│                                                      │
│  ┌─────────────┐ ┌──────────┐ ┌───────────────────┐ │
│  │ LLMClient   │ │GitHubClient│ │DocFetcher · Parser│ │
│  │ Groq        │ │PyGitHub  │ │httpx + BS4        │ │
│  │ → Gemini    │ │TTL cache │ │TTL cache · SSRF ✓ │ │
│  │ → OpenRouter│ └──────────┘ └───────────────────┘ │
│  └─────────────┘                                     │
└─────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Synchronous** — no async complexity; each gunicorn sync worker handles one streaming request
- **Generators everywhere** — `agent.run()` is always a generator; Flask streams it via `stream_with_context()`
- **TTL caching** — GitHub repo objects (5 min) and doc page content (10 min) cached in-process
- **SSRF protection** — every URL resolved via `socket.getaddrinfo()` before any HTTP request; RFC 1918 ranges blocked

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full technical reference.

---

## 📡 API Reference

All endpoints accept `application/json` and return streamed `text/plain`.

```
GET  /api/health
     → {"status": "ok", "providers": {"groq": true, "gemini": true, ...}}

POST /api/context
     {"issue_url": "https://github.com/owner/repo/issues/42",
      "include_comments": true,   // optional, default true
      "show_file_tree": true}     // optional, default true

POST /api/boilerplate
     {"description": "Flask route for user registration",
      "style_ref": "https://raw.githubusercontent.com/..."}  // optional

POST /api/docs
     {"library": "flask",         // or omit and use custom_url
      "question": "How do I use Blueprints?",
      "custom_url": "https://..."}  // optional override

POST /api/pr-draft
     {"diff": "<git diff output>",
      "issue_number": 42}         // optional
```

**Rate limits:** 300 req/hr global · 30 req/hr on `/api/context`

---

## ⚙️ Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` to get started.

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | **Required.** Primary LLM provider |
| `GEMINI_API_KEY` | — | Optional fallback LLM |
| `OPENROUTER_API_KEY` | — | Optional second fallback LLM |
| `GITHUB_TOKEN` | — | Optional; raises GitHub rate limit to 5,000/hr |
| `FLASK_DEBUG` | `false` | Never set to `true` in production |
| `FLASK_PORT` | `5000` | Flask backend port |
| `FLASK_URL` | `http://localhost:5000` | URL the frontend uses to reach the backend |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS origins |
| `LOG_LEVEL` | `INFO` | Python logging level |

---

## 🛠 Development

```bash
# Install everything
pip install -r requirements.txt -r requirements-dev.txt

make test      # pytest with coverage report (≥80% enforced)
make lint      # ruff check
make format    # black auto-format
make dev       # start Flask backend
make frontend  # start Streamlit frontend
```

### Project structure

```
DevAgent-Flow/
├── app/
│   ├── agents/          # BaseAgent + 4 agent implementations
│   ├── routes/          # Thin Flask blueprints (one per agent)
│   └── utils/           # LLMClient, GitHubClient, DocFetcher, DiffParser,
│                        # url_validator, stream_utils, logging_config
├── frontend/
│   ├── streamlit_app.py # Single-page app
│   ├── components/      # output_panel, sidebar, agent_header
│   └── styles/          # Catppuccin Mocha theme
├── tests/
│   ├── unit/            # Pure unit tests — no external calls
│   └── integration/     # Flask test client + mocked agents
├── .github/workflows/   # CI: ruff + pytest + black check
├── Dockerfile
├── docker-compose.yml
├── gunicorn.conf.py
└── Makefile
```

### Adding a new agent

1. `app/agents/<name>_agent.py` — inherit `BaseAgent`, implement `run()`, `_build_prompt()`, `_system_prompt()`
2. `app/routes/<name>.py` — blueprint using `agent_stream_response()`
3. Register in `app/__init__.py`
4. Add UI section in `frontend/streamlit_app.py`
5. Write tests in `tests/unit/` and `tests/integration/`

Full guide in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first — it covers setup, the commit style (Conventional Commits), and the PR checklist.

**Quick checklist before opening a PR:**
- [ ] `make test` passes with ≥80% coverage
- [ ] `make lint` is clean
- [ ] New code has type hints and docstrings
- [ ] PR description explains *why*, not just *what*

Bug reports and feature requests → [GitHub Issues](https://github.com/piush365/DevAgent-Flow/issues) (templates provided).

---

## 📋 Roadmap

See [ROADMAP.md](ROADMAP.md) for what's planned. Near-term highlights:
- Migrate from deprecated `google-generativeai` to `google-genai`
- Review Agent — summarise a PR diff and suggest improvements
- Test Agent — generate pytest scaffolding for a module
- Persistent run history across browser sessions

---

<div align="center">

**Built with** Flask · Streamlit · Groq · PyGitHub · httpx

**Theme** [Catppuccin Mocha](https://github.com/catppuccin/catppuccin)

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE)

*If this saved you time, a ⭐ on GitHub is appreciated.*

</div>
