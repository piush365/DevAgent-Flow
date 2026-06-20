# Product Requirements Document — DevFlow Agent

**Version:** 1.0  
**Date:** June 2026  
**Team Size:** 3  
**Program:** Agent AI Program — Capabl  
**Duration:** 8 Weeks  

---

## 1. Overview

### 1.1 Problem Statement

Developers lose significant time every day to two invisible productivity killers:

- **Context-switching** — jumping between GitHub issues, documentation tabs, and the editor to piece together enough context to start working.
- **Repetitive boilerplate** — writing the same structural code patterns over and over, manually, for every new feature or module.

There is no single tool that eliminates both. Developers either rely on memory, scattered browser tabs, or expensive AI coding assistants that don't integrate with their actual workflow.

### 1.2 Solution

**DevFlow Agent** is a Flask-based agentic productivity tool for developers. It accepts natural language inputs and GitHub/documentation URLs, then routes tasks across four specialized agents — each targeting a specific friction point in the development workflow. The result is a single interface that takes you from "I just picked up a new issue" to "I'm ready to write the first line of code" in under 60 seconds.

### 1.3 Target Users

- Open source contributors (GSoC applicants, first-time contributors)
- Student developers working on internship/college projects
- Junior to mid-level developers onboarding into new codebases

---

## 2. Goals

| Goal | Description |
|---|---|
| Eliminate context-switching | Developer should get a full "ready to code" brief from just a GitHub issue URL |
| Eliminate boilerplate fatigue | Developer should get repo-style boilerplate from a plain English description |
| Reduce doc-hunting time | Developer should get a direct answer + code snippet from any library's docs |
| Streamline PR creation | Developer should get a draft PR description generated from their git diff |

### 2.1 Non-Goals

- This is NOT a code editor or IDE plugin
- This is NOT a CI/CD or deployment tool
- This does NOT write full feature implementations — only structural boilerplate
- This does NOT replace human code review

---

## 3. Agents — Functional Requirements

### 3.1 Context Agent

**Purpose:** Eliminate the cold-start problem when picking up a GitHub issue.

**Input:** GitHub issue URL  
**Output:** A structured "ready to code" brief

**Behavior:**
- Fetch the issue title, body, labels, and comments via GitHub API
- Identify linked PRs and cross-referenced issues
- Scan the repository file tree and identify files most likely relevant to the issue (by keyword matching issue body against file names and paths)
- Output a structured brief containing:
  - Issue summary (2–3 sentences)
  - Relevant files to look at (ranked list)
  - Suggested starting point
  - Open questions / ambiguities from issue comments

**Constraints:**
- Must work with public repositories without authentication
- Authenticated mode (GitHub token via `.env`) for private repos and higher rate limits
- Response time target: under 10 seconds

---

### 3.2 Boilerplate Agent

**Purpose:** Generate project-style boilerplate from a plain English description.

**Input:** Natural language description of what needs to be built  
**Output:** Ready-to-use boilerplate code matching the repo's conventions

**Behavior:**
- Accept a description like: *"Flask route for user registration with email and password"*
- Optionally accept a GitHub repo URL or local file snippet as style reference
- Analyze the style reference to infer: naming conventions, import style, docstring format, error handling patterns
- Generate boilerplate that matches the inferred style
- Output code with inline comments explaining each section

**Constraints:**
- Must work without a style reference (uses sensible Python defaults)
- Style reference is optional but improves output quality significantly
- Boilerplate is structural only — no business logic implementation

---

### 3.3 Docs Agent

**Purpose:** Get a direct, no-fluff answer from any library's official documentation.

**Input:** Library name + question in plain English  
**Output:** A concise answer with a working code snippet

**Behavior:**
- Accept queries like: *"How do I use async sessions in SQLAlchemy?"*
- Fetch the relevant documentation page using `httpx`
- Parse and extract the most relevant section using the LLM
- Return:
  - A 2–3 sentence plain English answer
  - A minimal working code example
  - A direct link to the source documentation section

**Supported sources (initial):**
- Python standard library docs (docs.python.org)
- Flask, FastAPI, SQLAlchemy, Pydantic, Celery official docs
- Any URL the user explicitly provides

**Constraints:**
- Must not hallucinate API signatures — only use content fetched from the actual docs page
- If docs page is inaccessible, return a clear error rather than a fabricated answer

---

### 3.4 PR Drafter Agent

**Purpose:** Auto-generate a professional PR description from a git diff.

**Input:** Git diff (pasted text or auto-fetched from local repo path)  
**Output:** A structured PR description ready to paste into GitHub

**Behavior:**
- Parse the git diff to identify: files changed, lines added/removed, nature of changes
- Generate a PR description containing:
  - **Title:** concise one-liner
  - **Summary:** what was changed and why (2–4 sentences)
  - **Changes:** bullet list of specific modifications
  - **Testing:** placeholder checklist for manual/automated tests
  - **Related Issues:** extracted from branch name or user input

**Constraints:**
- Works with `git diff HEAD` output pasted into the UI
- Optional: auto-fetch diff if user provides a local repo path
- PR description should follow conventional open source formatting

---

## 4. System Architecture

```
User (Streamlit UI)
        |
        v
  Flask REST API
        |
   ┌────┴────┐
   |  Router  |   ← determines which agent handles the request
   └────┬────┘
        |
  ┌─────┼──────┬──────┐
  v     v      v      v
Context Boiler- Docs  PR
Agent   plate  Agent  Drafter
        Agent
  |     |      |      |
  └─────┴──────┴──────┘
        |
   Groq LLM (llama-3.1-8b-instant)
        |
   GitHub API / httpx / gitpython
```

### 4.1 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| LLM Inference | Groq API (`llama-3.1-8b-instant`) |
| GitHub Integration | PyGitHub |
| HTTP / Doc Fetching | httpx |
| Git Operations | gitpython |
| Frontend | Streamlit |
| Environment Config | python-dotenv |
| Templating | Jinja2 (for boilerplate generation) |

---

## 5. API Endpoints

| Method | Endpoint | Agent | Description |
|---|---|---|---|
| POST | `/api/context` | Context Agent | Accepts GitHub issue URL, returns ready-to-code brief |
| POST | `/api/boilerplate` | Boilerplate Agent | Accepts description + optional style ref, returns code |
| POST | `/api/docs` | Docs Agent | Accepts library name + question, returns answer + snippet |
| POST | `/api/pr-draft` | PR Drafter Agent | Accepts git diff, returns PR description |
| GET | `/api/health` | — | Health check |

---

## 6. Project Structure

```
devflow-agent/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── context.py
│   │   ├── boilerplate.py
│   │   ├── docs.py
│   │   └── pr_draft.py
│   ├── agents/
│   │   ├── context_agent.py
│   │   ├── boilerplate_agent.py
│   │   ├── docs_agent.py
│   │   └── pr_draft_agent.py
│   └── utils/
│       ├── github_client.py
│       ├── llm_client.py
│       └── doc_fetcher.py
├── frontend/
│   └── streamlit_app.py
├── templates/
│   └── boilerplate/
│       ├── flask_route.jinja2
│       └── class_module.jinja2
├── tests/
│   ├── test_context_agent.py
│   ├── test_boilerplate_agent.py
│   └── test_docs_agent.py
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```

---

## 7. Team Responsibilities

| Member | Ownership |
|---|---|
| **Piush (You)** | Context Agent + GitHub API integration + project architecture + `.env` config |
| **Teammate 2** | Boilerplate Agent + Jinja2 templates + prompt engineering |
| **Teammate 3** | Docs Agent + PR Drafter + Streamlit frontend |

All members jointly responsible for: integration testing, demo preparation, final PPT.

---

## 8. 8-Week Execution Plan

| Week | Milestone | Owner |
|---|---|---|
| 1 | Project setup, repo structure, Flask skeleton, `.env` config, health endpoint | All |
| 2 | Context Agent complete — GitHub API fetch, file relevance ranking, brief generation | Piush |
| 3 | Boilerplate Agent complete — style inference from reference, Jinja2 templates | TM2 |
| 4 | Docs Agent complete — httpx fetching, doc parsing, LLM answer extraction | TM3 |
| 5 | PR Drafter Agent complete — git diff parsing, PR description generation | TM3 |
| 6 | Streamlit frontend — unified UI for all 4 agents | TM3 + TM2 |
| 7 | Integration testing, edge case handling, error messages, rate limit handling | All |
| 8 | Demo polish, final PPT preparation, dry run presentation | All |

**Weekly Sunday submissions:** document progress per agent, attach screenshots or short demo clips.

---

## 9. Evaluation Criteria (aligned to Capabl guidelines)

| Criterion | How DevFlow Agent addresses it |
|---|---|
| Real-world applicability | Solves daily pain points every developer faces |
| Agentic architecture | 4 distinct agents with clear roles and tool use |
| Technical depth | GitHub API, LLM chaining, doc fetching, git parsing |
| Demo quality | Live demo: paste issue URL → get brief in <10s |
| Presentation clarity | One clear story: "from issue to PR, without leaving the tool" |

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| GitHub API rate limits | Use authenticated requests via token in `.env`; cache responses |
| LLM response quality | Prompt engineering + output validation; fallback messages |
| Docs page structure varies | Use LLM to extract relevant content rather than fixed selectors |
| Scope creep | Freeze feature set at Week 4; Week 5–6 is polish only |
| Team coordination | Weekly sync every Monday; shared GitHub repo with clear branch naming |

---

## 11. Success Metrics

- All 4 agents functional and demo-able end-to-end
- Context Agent returns a useful brief for any public GitHub issue in < 10 seconds
- Boilerplate Agent generates syntactically valid Python for 5+ common patterns
- Docs Agent correctly answers questions for at least 5 supported libraries
- PR Drafter produces a readable, correctly structured PR description from any valid diff
- Team completes minimum 6 of 8 allowed weekly submissions

---

## 12. Out of Scope (for v1)

- Authentication / user accounts
- Saving history across sessions
- IDE plugin / VS Code extension
- Support for non-Python boilerplate
- Private repo access beyond token auth

---

*DevFlow Agent — built by developers, for developers.*
