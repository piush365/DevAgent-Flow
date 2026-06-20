# Contributing to DevFlow Agent

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Getting started

1. **Fork** the repository and clone your fork
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
3. **Copy the env template** and fill in your keys
   ```bash
   cp .env.example .env
   ```
4. **Run the test suite** to confirm everything works before making changes
   ```bash
   make test
   ```

## Development workflow

### Running locally

```bash
# Terminal 1 — Flask backend
make dev

# Terminal 2 — Streamlit frontend
make frontend
```

### Running tests

```bash
make test          # pytest with coverage
make lint          # ruff linter
make format        # black auto-formatter
```

Coverage must stay at or above **80%**. New features require tests.

## Adding a new agent

1. Create `app/agents/<name>_agent.py` — class inheriting `BaseAgent` with `run()`, `_build_prompt()`, `_system_prompt()`
2. Create `app/routes/<name>.py` — thin blueprint wrapping the agent with `agent_stream_response()`
3. Register the blueprint in `app/__init__.py`
4. Add the UI section in `frontend/streamlit_app.py`
5. Add unit tests in `tests/unit/` and integration tests in `tests/integration/`

See `CLAUDE.md` for the full architecture reference.

## Commit style

This project follows **Conventional Commits**:

```
type: short description (≤72 chars)

Optional longer body explaining the why.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `deploy`, `security`, `ux`, `perf`.

## Pull request checklist

- [ ] Tests pass (`make test`)
- [ ] Linter clean (`make lint`)
- [ ] New code has type hints
- [ ] New public functions have docstrings
- [ ] PR description explains *why*, not just *what*

## Reporting bugs

Use the **Bug Report** issue template. Include:
- Steps to reproduce
- Expected vs actual behaviour
- Python version and OS

## Security

Do **not** open a public issue for security vulnerabilities. Email the maintainer directly instead.
