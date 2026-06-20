# DevFlow Agent

[![CI](https://github.com/piush365/DevAgent-Flow/actions/workflows/ci.yml/badge.svg)](https://github.com/piush365/DevAgent-Flow/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20|%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI-powered developer productivity tool that cuts context-switching and boilerplate work. Paste a GitHub issue URL, a git diff, or a plain-English description — get structured, actionable output in seconds.

Flask backend · Streamlit frontend · All LLM providers are **free tier**

---

## Agents

| Agent | Input | Output |
|-------|-------|--------|
| **Context** | GitHub issue URL | Ready-to-code brief: issue summary, relevant files, suggested approach, open questions |
| **Boilerplate** | Plain English description + optional style reference URL | Python boilerplate matching your repo's conventions |
| **Docs** | Library name + question | Direct answer + code snippet, grounded in the official docs |
| **PR Draft** | `git diff` output + optional issue number | Structured PR description: title, summary, change list, testing checklist |

---

## Quick start

### Local (two terminals)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (required)

# Terminal 1 — Flask backend (port 5000)
python run.py

# Terminal 2 — Streamlit frontend (port 8501)
streamlit run frontend/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

### Docker

```bash
cp .env.example .env   # fill in keys
docker compose up --build
```

Backend: `http://localhost:5000` · Frontend: `http://localhost:8501`

---

## API keys

| Key | Required | Where to get it |
|-----|----------|-----------------|
| `GROQ_API_KEY` | **Yes** | [console.groq.com](https://console.groq.com) → API Keys |
| `GITHUB_TOKEN` | No | github.com/settings/tokens (raises rate limit 60 → 5,000 req/hr) |
| `GEMINI_API_KEY` | No | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| `OPENROUTER_API_KEY` | No | [openrouter.ai/keys](https://openrouter.ai/keys) |

Gemini and OpenRouter are used as automatic fallbacks if Groq hits rate limits.

---

## How it works

```
Streamlit UI
    │
    └─► POST /api/<agent>  (Flask, streamed text/plain)
              │
              ├─► GitHubClient    (issue + file tree)
              ├─► DocFetcher      (httpx + BeautifulSoup, SSRF-protected)
              ├─► DiffParser      (unified diff → structured summary)
              └─► LLMClient.stream()
                      │
                      ├─► Groq  (llama-3.1-8b-instant)   ← primary
                      ├─► Gemini Flash                    ← 429 fallback
                      └─► OpenRouter (llama-3.1-8b)      ← final fallback
```

All responses stream token-by-token to the Streamlit UI.

---

## API reference

All endpoints accept `application/json` and return streamed `text/plain`.

```
GET  /api/health
POST /api/context      {"issue_url": "https://github.com/owner/repo/issues/42",
                        "include_comments": true}
POST /api/boilerplate  {"description": "...", "style_ref": "https://..."}
POST /api/docs         {"library": "flask", "question": "...", "custom_url": "..."}
POST /api/pr-draft     {"diff": "<git diff output>", "issue_number": 42}
```

---

## Development

```bash
pip install -r requirements.txt -r requirements-dev.txt

make test      # pytest --cov (≥80% required)
make lint      # ruff
make format    # black
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including how to add a new agent.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask 3, `stream_with_context`, flask-limiter, flask-cors |
| Frontend | Streamlit, Catppuccin Mocha theme |
| LLM | Groq → Gemini Flash → OpenRouter (automatic fallback) |
| GitHub | PyGitHub |
| HTTP | httpx + BeautifulSoup |
| Production | Gunicorn, Docker |
| Tests | pytest, pytest-cov, pytest-mock |
| Lint | ruff, black |
