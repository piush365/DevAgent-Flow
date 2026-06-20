# Roadmap

Items marked **Near-term** are actively planned. Everything else is exploratory.

## Near-term

### Migrate from `google-generativeai` to `google-genai`
The `google-generativeai` package is deprecated. The replacement is `google-genai`
(package ID `google-genai`, import `from google import genai`). The API surface
differs — migration requires updating `LLMClient._stream_gemini()`.

### Streaming error propagation
Currently, LLM errors surfaced mid-stream appear as `⚠️` text inline with
generated content. A better UX would mark the response as failed and surface
a retry button in the Streamlit UI.

### `include_comments` toggle in Context Agent UI
The backend already accepts `include_comments` and `show_file_tree` params;
the Streamlit form now exposes `include_comments`. `show_file_tree` is still
backend-only.

## Exploratory

### Additional agents
- **Review Agent** — summarise a PR's diff and suggest improvements
- **Test Agent** — generate pytest scaffolding for a given module
- **Commit Message Agent** — write conventional commit messages from staged diffs

### Persistent run history
Session state is cleared on browser refresh. A lightweight SQLite store or
browser `localStorage` bridge via Streamlit components could persist runs
across sessions.

### Streaming to multiple providers simultaneously
Run Groq and Gemini in parallel, display whichever responds first, and cancel
the slower one.

### GitHub App integration
Replace personal-token auth with a GitHub App installation token so the tool
can be deployed as a shared service without users supplying their own keys.

### `gitpython` integration
`gitpython` was removed because it was listed as a dependency but never used.
A future **Local Diff Agent** could use it to extract `git diff` output
programmatically instead of requiring users to paste it.
