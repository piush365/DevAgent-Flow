# Design Document — DevFlow Agent

**Version:** 1.0  
**Date:** June 2026  
**Companion to:** `prd.md`

---

## 1. Design Philosophy

Three principles guide every design decision in DevFlow Agent:

- **Functional first** — every element earns its place by serving the developer's task
- **Low friction** — minimal clicks between "open tool" and "get answer"
- **Quiet polish** — dark, consistent, readable; not flashy, never distracting

The UI should feel like a well-configured terminal setup — familiar, fast, and focused.

---

## 2. Color System — Catppuccin Mocha

All colors sourced from the Catppuccin Mocha palette for consistency with the dark theme.

| Role | Name | Hex |
|---|---|---|
| Background (base) | Mocha Base | `#1e1e2e` |
| Surface (cards, panels) | Mocha Mantle | `#181825` |
| Elevated surface | Mocha Crust | `#11111b` |
| Sidebar background | Mocha Mantle | `#181825` |
| Primary text | Mocha Text | `#cdd6f4` |
| Muted / secondary text | Mocha Subtext0 | `#a6adc8` |
| Accent (primary CTA) | Mocha Mauve | `#cba6f7` |
| Success / output ready | Mocha Green | `#a6e3a1` |
| Warning / loading | Mocha Yellow | `#f9e2af` |
| Error | Mocha Red | `#f38ba8` |
| Code block background | Mocha Surface0 | `#313244` |
| Borders / dividers | Mocha Surface1 | `#45475a` |
| Agent badge — Context | Mocha Blue | `#89b4fa` |
| Agent badge — Boilerplate | Mocha Peach | `#fab387` |
| Agent badge — Docs | Mocha Teal | `#94e2d5` |
| Agent badge — PR Drafter | Mocha Green | `#a6e3a1` |

---

## 3. Typography

| Use | Font | Size | Weight |
|---|---|---|---|
| App title | JetBrains Mono | 22px | Bold |
| Section headings | JetBrains Mono | 16px | Semibold |
| Body / labels | Inter (fallback: system-ui) | 14px | Regular |
| Code output | JetBrains Mono | 13px | Regular |
| Muted captions | Inter | 12px | Regular |
| Agent badge labels | Inter | 11px | Medium |

Use JetBrains Mono for anything code-adjacent. Inter for all prose and UI labels.

---

## 4. Layout

### 4.1 Overall Structure

```
┌─────────────────────────────────────────────────────────┐
│  [Sidebar 260px]    │  [Main Content Area — flexible]   │
│                     │                                   │
│  App logo + name    │  Agent Header                     │
│  ─────────────────  │  ─────────────────────────────    │
│  ● Context Agent    │  Input Panel                      │
│  ○ Boilerplate      │                                   │
│  ○ Docs Agent       │  [Run Agent Button]               │
│  ○ PR Drafter       │                                   │
│                     │  Output Panel (streaming)         │
│  ─────────────────  │                                   │
│  Recent runs (last  │                                   │
│  3 queries)         │                                   │
│                     │                                   │
│  ─────────────────  │                                   │
│  Settings icon      │                                   │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Sidebar (260px fixed)

- App name: `DevFlow Agent` in JetBrains Mono, Mauve accent color
- Small tagline below: `"your dev co-pilot"` in Subtext0
- Divider line in Surface1
- Agent list: 4 navigation items, each with:
  - Colored dot indicator (agent's badge color)
  - Agent name
  - One-line description in Subtext0
  - Active state: left border in Mauve, Surface0 background
- Divider line
- Recent Runs section: last 3 query snippets (truncated to 40 chars), clickable to reload
- Bottom: gear icon for settings (GitHub token input, theme toggle placeholder)

### 4.3 Main Content Area

Divided into three vertical zones:

**Zone 1 — Agent Header (fixed, ~80px)**
- Agent name in large text with its badge color
- Agent description in Subtext0
- Status indicator: `idle` / `running` / `done` / `error`

**Zone 2 — Input Panel**
- Varies per agent (see Section 5)
- Always ends with a primary CTA button: `Run [Agent Name]` in Mauve
- Button disabled while agent is running

**Zone 3 — Output Panel (streaming)**
- Appears below input after Run is clicked
- Streams token-by-token using `st.write_stream` or manual chunk rendering
- Output rendered in a dark code-style container (Surface0 background)
- Streaming cursor indicator while output is generating
- Copy button (top-right of output box) appears after streaming completes
- Clear button to reset output

---

## 5. Agent-Specific Input Panels

### 5.1 Context Agent (Blue — `#89b4fa`)

```
┌─────────────────────────────────────┐
│  GitHub Issue URL                   │
│  ┌───────────────────────────────┐  │
│  │ https://github.com/...        │  │
│  └───────────────────────────────┘  │
│                                     │
│  [ ] Include issue comments         │
│  [ ] Show relevant file tree        │
│                                     │
│  [  Run Context Agent  ]            │
└─────────────────────────────────────┘
```

Output format (streamed):
```
## Issue Brief — #101: Add .pyi stub support

**Summary**
...streamed here...

**Relevant Files**
- src/parser.py
- tests/test_parser.py

**Suggested Starting Point**
...

**Open Questions**
...
```

### 5.2 Boilerplate Agent (Peach — `#fab387`)

```
┌─────────────────────────────────────┐
│  What do you need?                  │
│  ┌───────────────────────────────┐  │
│  │ Flask route for user login    │  │
│  │ with JWT auth                 │  │
│  └───────────────────────────────┘  │
│                                     │
│  Style Reference (optional)         │
│  ┌───────────────────────────────┐  │
│  │ Paste a code snippet or URL   │  │
│  └───────────────────────────────┘  │
│                                     │
│  Language: [Python ▾]               │
│                                     │
│  [  Run Boilerplate Agent  ]        │
└─────────────────────────────────────┘
```

Output: syntax-highlighted Python code block, streamed line by line.

### 5.3 Docs Agent (Teal — `#94e2d5`)

```
┌─────────────────────────────────────┐
│  Library                            │
│  ┌───────────────────────────────┐  │
│  │ SQLAlchemy                    │  │
│  └───────────────────────────────┘  │
│                                     │
│  Your Question                      │
│  ┌───────────────────────────────┐  │
│  │ How do I use async sessions?  │  │
│  └───────────────────────────────┘  │
│                                     │
│  Custom Docs URL (optional)         │
│  ┌───────────────────────────────┐  │
│  │ https://docs.example.com/...  │  │
│  └───────────────────────────────┘  │
│                                     │
│  [  Run Docs Agent  ]               │
└─────────────────────────────────────┘
```

Output format (streamed):
```
**Answer**
...plain English explanation...

**Code Example**
...syntax-highlighted snippet...

**Source**
docs.sqlalchemy.org/en/20/orm/...
```

### 5.4 PR Drafter Agent (Green — `#a6e3a1`)

```
┌─────────────────────────────────────┐
│  Git Diff                           │
│  ┌───────────────────────────────┐  │
│  │ Paste output of:              │  │
│  │ git diff HEAD                 │  │
│  │                               │  │
│  │ ...                           │  │
│  └───────────────────────────────┘  │
│                                     │
│  Related Issue # (optional)         │
│  ┌───────────────────────────────┐  │
│  │ 101                           │  │
│  └───────────────────────────────┘  │
│                                     │
│  [  Run PR Drafter  ]               │
└─────────────────────────────────────┘
```

Output format (streamed):
```
**Title**
feat: add .pyi stub file support to parser

**Summary**
...

**Changes**
- ...
- ...

**Testing**
- [ ] Unit tests pass
- [ ] Manual test: ...

**Related Issues**
Closes #101
```

---

## 6. Interaction States

| State | Visual Treatment |
|---|---|
| Idle | Input fields active, button in Mauve, status dot grey |
| Running | Button disabled + spinner, status dot in Yellow, "Agent is thinking..." below input |
| Streaming | Output panel appears, text streams in, cursor blinks at end |
| Done | Status dot turns Green, Copy button appears, button re-enables |
| Error | Status dot turns Red, error message in Red below output panel |

---

## 7. Streaming Output Implementation

Use Streamlit's native streaming with a placeholder:

```python
import streamlit as st
import requests

output_placeholder = st.empty()
full_response = ""

with requests.get(FLASK_STREAM_ENDPOINT, stream=True) as r:
    for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
        full_response += chunk
        output_placeholder.markdown(
            f"```\n{full_response}▌\n```"  # blinking cursor effect
        )

# Final render without cursor
output_placeholder.markdown(f"```\n{full_response}\n```")
```

Flask backend uses `Response` with `stream_with_context` + `generate()` pattern to stream Groq chunks to the frontend.

---

## 8. Streamlit Configuration

`streamlit_app.py` top-level config:

```python
st.set_page_config(
    page_title="DevFlow Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

Custom CSS injected via `st.markdown(..., unsafe_allow_html=True)` to apply Catppuccin Mocha colors since Streamlit's native theming is limited:

```python
MOCHA_CSS = """
<style>
    .stApp { background-color: #1e1e2e; color: #cdd6f4; }
    .stSidebar { background-color: #181825; }
    .stTextInput > div > div > input {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 6px;
    }
    .stButton > button {
        background-color: #cba6f7;
        color: #1e1e2e;
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button:hover { background-color: #b4befe; }
    code, pre { background-color: #313244 !important; }
</style>
"""
st.markdown(MOCHA_CSS, unsafe_allow_html=True)
```

---

## 9. Responsive Behavior

This tool targets desktop/laptop use (1280px+ width). No mobile optimization required for v1.

Sidebar collapses on narrow viewports (Streamlit default behavior) — acceptable fallback.

---

## 10. Recent Runs (Session State)

Store last 3 queries per agent in `st.session_state`:

```python
if "recent_runs" not in st.session_state:
    st.session_state.recent_runs = []

# After each run, prepend and trim
st.session_state.recent_runs.insert(0, {
    "agent": current_agent,
    "query": user_input[:40],
    "output": full_response
})
st.session_state.recent_runs = st.session_state.recent_runs[:3]
```

Clicking a recent run reloads its input and output without re-running the agent.

---

## 11. File Structure (Frontend)

```
frontend/
├── streamlit_app.py       # Main entry point, layout, sidebar
├── pages/                 # Not used — single-page with sidebar nav
├── components/
│   ├── sidebar.py         # Sidebar nav + recent runs
│   ├── agent_header.py    # Agent title + status indicator
│   ├── output_panel.py    # Streaming output renderer
│   └── copy_button.py     # Copy-to-clipboard utility
├── styles/
│   └── mocha.py           # Catppuccin Mocha CSS string
└── config.py              # FLASK_BASE_URL, agent metadata
```

---

## 12. What's NOT in the Design (v1)

- No animations or transitions (keep it fast)
- No user accounts or login screen
- No persistent history across sessions (session state only)
- No mobile layout
- No light theme toggle (dark only for v1)
- No onboarding tour or tooltips

---

*DevFlow Agent Design Document — keep it dark, keep it fast.*
