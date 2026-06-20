# Architecture

DevFlow Agent is a synchronous Flask monolith with a Streamlit frontend. No queues, no microservices, no async complexity. Each agent is a self-contained class that validates input, fetches external data, builds a prompt, and streams the LLM response back to the caller.

## Process model

Two processes must run concurrently:

```
Streamlit (port 8501)  ──POST /api/<agent>──►  Flask (port 5000)
                            stream=True
```

Streamlit POSTs to Flask with `stream=True` and reads chunks as they arrive, re-rendering a `st.empty()` placeholder on each one.

## Directory layout

```
app/
├── __init__.py          # create_app() — registers blueprints, CORS, rate limiter
├── config.py            # Config class — reads .env, validate() raises on missing keys
├── agents/
│   ├── base_agent.py    # BaseAgent ABC — run(), _build_prompt(), _system_prompt(), _stream_llm()
│   ├── context_agent.py
│   ├── boilerplate_agent.py
│   ├── docs_agent.py
│   └── pr_draft_agent.py
├── routes/
│   ├── context.py       # POST /api/context
│   ├── boilerplate.py   # POST /api/boilerplate
│   ├── docs.py          # POST /api/docs
│   ├── pr_draft.py      # POST /api/pr-draft
│   └── health.py        # GET /api/health
└── utils/
    ├── llm_client.py    # LLMClient — Groq → Gemini → OpenRouter fallback chain
    ├── github_client.py # GitHubClient — PyGitHub wrapper, TTL repo cache
    ├── doc_fetcher.py   # DocFetcher — httpx + BeautifulSoup, TTL content cache
    ├── diff_parser.py   # DiffParser — unified diff → structured summary dict
    ├── url_validator.py # validate_fetch_url() — SSRF protection
    ├── stream_utils.py  # agent_stream_response(), error_stream_response()
    └── logging_config.py

frontend/
├── streamlit_app.py     # single-page app — sidebar nav + 4 agent sections
├── components/
│   ├── output_panel.py  # stream_agent_response() — drives streaming display
│   ├── sidebar.py       # render_sidebar(), add_recent_run()
│   └── agent_header.py  # agent_header_html(), render_agent_header()
└── styles/
    └── mocha.py         # Catppuccin Mocha palette + inject_mocha_css()
```

## Agent pattern

Every agent inherits `BaseAgent`:

```python
class BaseAgent(ABC):
    def __init__(self) -> None:
        self.llm = LLMClient()

    @abstractmethod
    def run(self, *args, **kwargs) -> Generator[str, None, None]: ...

    @abstractmethod
    def _build_prompt(self, *args, **kwargs) -> str: ...

    @abstractmethod
    def _system_prompt(self) -> str: ...

    def _stream_llm(self, prompt: str) -> Generator[str, None, None]:
        try:
            yield from self.llm.stream(prompt, system=self._system_prompt())
        except Exception as exc:
            logger.exception("%s LLM error", self.__class__.__name__)
            yield f"\n⚠️ LLM error: {exc}"
```

The `run()` method is always a generator. It `yield`s progress messages, then delegates to `_stream_llm()` which calls `LLMClient.stream()`.

## Route pattern

Every route is a thin blueprint (~30 lines):

```python
bp = Blueprint("context", __name__)

@bp.post("/api/context")
def context_endpoint():
    body = request.get_json(silent=True) or {}
    issue_url = (body.get("issue_url") or "").strip()
    if not issue_url:
        return error_stream_response("issue_url is required")
    agent = ContextAgent()
    return agent_stream_response(agent.run(issue_url, ...))
```

`agent_stream_response()` wraps the generator in `stream_with_context()` and returns `Response(mimetype="text/plain", headers={"X-Accel-Buffering": "no"})`.

## LLM fallback chain

`LLMClient.stream()` tries providers in order, catching 429 / rate-limit errors:

```
Groq  (llama-3.1-8b-instant)     ← primary, fastest
  └─► Gemini Flash                ← on 429
       └─► OpenRouter (llama-3.1-8b-instruct:free)  ← final fallback
```

The Groq client is instantiated once in `__init__` to avoid per-request overhead.

## Security

- **SSRF**: `validate_fetch_url()` resolves hostnames via `socket.getaddrinfo()` and rejects any resolved IP in RFC 1918, loopback, link-local, or other reserved ranges. Called by `DocFetcher.fetch()` before every HTTP request.
- **Debug mode**: `Config.FLASK_DEBUG` defaults to `False`. Never set `debug=True` in production.
- **Rate limiting**: `flask-limiter` enforces 300 req/hr globally, 30 req/hr on `/api/context` (GitHub API aware).
- **Request size**: `MAX_CONTENT_LENGTH = 5 MB` blocks oversized payloads.
- **CORS**: `flask-cors` with `ALLOWED_ORIGINS` from environment (defaults to `*` in dev).

## Caching

| Module | What is cached | TTL |
|--------|----------------|-----|
| `DocFetcher` | Fetched + extracted doc text | 10 min |
| `GitHubClient` | `github.Repository` objects | 5 min |

Both caches are module-level dicts `{key: (value, timestamp)}`. No external cache dependency.

## Adding a new agent

1. `app/agents/<name>_agent.py` — inherit `BaseAgent`, implement `run()`, `_build_prompt()`, `_system_prompt()`
2. `app/routes/<name>.py` — blueprint using `agent_stream_response()` / `error_stream_response()`
3. Register the blueprint in `app/__init__.py`
4. Add the UI section in `frontend/streamlit_app.py`
5. Add tests in `tests/unit/` and `tests/integration/`
