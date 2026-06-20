# DevFlow Agent

AI-powered developer productivity tool that cuts context-switching and boilerplate work. Paste a GitHub issue URL, a git diff, or a plain-English description — get a structured output in under 10 seconds.

Built with Flask + Streamlit. All LLM providers are free tier.

---

## Agents

| Agent | Input | Output |
|---|---|---|
| **Context** | GitHub issue URL | Ready-to-code brief: issue summary, relevant files, suggested starting point, open questions |
| **Boilerplate** | Plain English description + optional style reference URL | Python boilerplate matching your repo's conventions |
| **Docs** | Library name + question | Direct answer + code snippet, grounded strictly in the official docs |
| **PR Draft** | `git diff` output + optional issue number | Structured PR description: title, summary, change list, testing checklist |

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure environment**

Create a `.env` file in the project root:
```bash
# Required
GROQ_API_KEY=your_groq_api_key        # https://console.groq.com → API Keys

# Optional — raises GitHub rate limit from 60 to 5,000 req/hr
GITHUB_TOKEN=your_github_token         # github.com/settings/tokens → public_repo scope

# Optional — LLM fallbacks if Groq hits rate limits
GEMINI_API_KEY=your_gemini_key         # aistudio.google.com → Get API Key
OPENROUTER_API_KEY=your_openrouter_key # openrouter.ai/keys
```

**3. Run both processes** (separate terminals)
```bash
# Terminal 1 — Flask backend (port 5000)
python run.py

# Terminal 2 — Streamlit frontend (port 8501)
streamlit run frontend/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## How it works

The Streamlit frontend sends requests to the Flask backend, which streams responses back token-by-token. The LLM layer automatically falls back across providers on rate limits: **Groq → Gemini Flash → OpenRouter**.

```
Streamlit UI  →  POST /api/<agent>  →  Agent class  →  LLMClient.stream()
                                             ↓
                                    GitHub API / httpx / DiffParser
```

All agent responses are streamed as plain text — you see output appearing as it's generated.

---

## API endpoints

All endpoints accept JSON and return a streamed `text/plain` response.

```
GET  /api/health
POST /api/context      { "issue_url": "https://github.com/owner/repo/issues/42" }
POST /api/boilerplate  { "description": "...", "style_ref": "https://..." }
POST /api/docs         { "library": "flask", "question": "...", "custom_url": "..." }
POST /api/pr-draft     { "diff": "<git diff output>", "issue_number": 42 }
```

---

## Tech stack

- **Backend:** Flask 3, streamed via `stream_with_context`
- **Frontend:** Streamlit (Catppuccin Mocha theme)
- **LLM:** Groq (`llama-3.1-8b-instant`) with Gemini Flash and OpenRouter as fallbacks
- **GitHub:** PyGitHub
- **Doc fetching:** httpx + BeautifulSoup
