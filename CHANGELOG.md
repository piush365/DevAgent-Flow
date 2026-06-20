# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- `BaseAgent` abstract class — all agents now inherit a common `run()` contract and `_stream_llm()` helper
- `app/utils/url_validator.py` — SSRF prevention layer blocks private/reserved IP ranges before any HTTP fetch
- `app/utils/stream_utils.py` — eliminates duplicated `error_stream()` closures across all route files
- `app/utils/logging_config.py` — structured logging with per-module level control
- TTL caching in `DocFetcher` (10 min) and `GitHubClient` repo objects (5 min)
- Rate limiting via `flask-limiter`: 300 req/hr default, 30 req/hr on `/api/context` (GitHub API aware)
- CORS support via `flask-cors` with configurable `ALLOWED_ORIGINS`
- `MAX_CONTENT_LENGTH` (5 MB) request size cap
- `Config.validate()` — raises a clear `EnvironmentError` on startup if `GROQ_API_KEY` is missing
- `include_comments` and `show_file_tree` parameters on the Context Agent
- Comprehensive test suite: 130 tests, ≥85% coverage
- GitHub Actions CI pipeline (Python 3.11 + 3.12, ruff, pytest coverage gate)
- `Dockerfile`, `docker-compose.yml`, `gunicorn.conf.py` for production deployment
- `Makefile` with `dev`, `test`, `lint`, `format`, `docker-*` targets
- `CONTRIBUTING.md`, `LICENSE` (MIT), `CHANGELOG.md`, `ROADMAP.md`
- GitHub issue and PR templates

### Fixed
- `debug=True` default replaced with `Config.FLASK_DEBUG` (defaults `False`) — eliminated RCE risk in dev
- PyGitHub deprecation: switched to `Github(auth=Auth.Token(...))` pattern
- Markdown rendering in Streamlit: native `st.markdown()` replaces broken HTML-escaped div approach
- Duplicate agent header on form submit — single `st.empty()` placeholder updated in-place
- Recent Runs now shows newest first
- Dead code in `DiffParser` removed (unreachable branch after `--- `/`+++ ` filter)
- Groq client no longer rebuilt per request — instantiated once in `LLMClient.__init__`
- Hardcoded `FLASK_URL` in frontend replaced with `os.environ.get("FLASK_URL", "http://localhost:5000")`

### Security
- SSRF: `validate_fetch_url()` blocks RFC 1918, loopback, link-local, and other reserved ranges
- Debug mode now defaults to `False` in all environments
- `.env` removed from version control; `.env.example` committed as template
- `GITHUB_TOKEN` now optional and clearly documented as rate-limit booster only

### Removed
- `gitpython` dependency (was listed in requirements but never imported)
- Inconsistent `Together AI` references replaced with correct `OpenRouter` throughout
