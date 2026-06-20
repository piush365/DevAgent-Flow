"""
DevFlow Agent — Streamlit Frontend
Run with: streamlit run frontend/streamlit_app.py
"""

import sys
import os

# Add project root to path so we can import frontend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from frontend.styles.mocha import inject_mocha_css
from frontend.components.sidebar import render_sidebar, add_recent_run
from frontend.components.agent_header import agent_header_html
from frontend.components.output_panel import stream_agent_response, render_empty_state

# ── Page Config ────────────────────────────────────────────────
st.set_page_config(
    page_title="DevFlow Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Theme CSS ──────────────────────────────────────────
st.markdown(inject_mocha_css(), unsafe_allow_html=True)

# ── Sidebar Navigation ───────────────────────────────────────
selected_agent = render_sidebar()

# ── Initialize Session State ──────────────────────────────────
if "agent_status" not in st.session_state:
    st.session_state.agent_status = "idle"
if "last_output" not in st.session_state:
    st.session_state.last_output = ""
if "active_agent" not in st.session_state:
    st.session_state.active_agent = selected_agent

# Reset status and output when the user switches to a different agent
if selected_agent != st.session_state.active_agent:
    st.session_state.agent_status = "idle"
    st.session_state.last_output = ""
    st.session_state.active_agent = selected_agent


def _update_header(placeholder, agent_key: str, status: str) -> None:
    """Replace header placeholder content with the given status."""
    placeholder.markdown(agent_header_html(agent_key, status), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# CONTEXT AGENT
# ═══════════════════════════════════════════════════════════════
if selected_agent == "context":
    header_ph = st.empty()
    _update_header(header_ph, "context", st.session_state.agent_status)

    with st.form("context_form", clear_on_submit=False):
        issue_url = st.text_input(
            "GitHub Issue URL",
            placeholder="https://github.com/owner/repo/issues/42",
            help="Paste a public GitHub issue URL",
        )
        include_comments = st.checkbox(
            "Include issue comments",
            value=True,
            help="Fetch and analyse comments from the issue thread",
        )
        submitted = st.form_submit_button(
            "🔍 Analyze Issue",
            use_container_width=True,
        )

    if submitted and issue_url:
        st.session_state.agent_status = "running"
        _update_header(header_ph, "context", "running")
        output_placeholder = st.empty()
        result = stream_agent_response(
            "/api/context",
            {"issue_url": issue_url, "include_comments": include_comments},
            output_placeholder,
        )
        st.session_state.agent_status = "done"
        _update_header(header_ph, "context", "done")
        st.session_state.last_output = result
        add_recent_run("context", issue_url)
    elif submitted:
        st.warning("Please enter a GitHub issue URL.")
    elif not st.session_state.last_output:
        render_empty_state("Context Agent")


# ═══════════════════════════════════════════════════════════════
# BOILERPLATE AGENT
# ═══════════════════════════════════════════════════════════════
elif selected_agent == "boilerplate":
    header_ph = st.empty()
    _update_header(header_ph, "boilerplate", st.session_state.agent_status)

    with st.form("boilerplate_form", clear_on_submit=False):
        description = st.text_area(
            "Description",
            placeholder="e.g., Flask route for user registration with email and password validation",
            height=120,
            help="Describe what boilerplate code you need",
        )
        style_ref = st.text_input(
            "Style Reference URL (optional)",
            placeholder="https://raw.githubusercontent.com/owner/repo/main/app/routes/auth.py",
            help="Raw URL of a code file to match its conventions",
        )
        submitted = st.form_submit_button(
            "⚡ Generate Boilerplate",
            use_container_width=True,
        )

    if submitted and description:
        st.session_state.agent_status = "running"
        _update_header(header_ph, "boilerplate", "running")
        output_placeholder = st.empty()
        payload = {"description": description}
        if style_ref:
            payload["style_ref"] = style_ref
        result = stream_agent_response(
            "/api/boilerplate",
            payload,
            output_placeholder,
        )
        st.session_state.agent_status = "done"
        _update_header(header_ph, "boilerplate", "done")
        st.session_state.last_output = result
        add_recent_run("boilerplate", description)
    elif submitted:
        st.warning("Please enter a description.")
    elif not st.session_state.last_output:
        render_empty_state("Boilerplate Agent")


# ═══════════════════════════════════════════════════════════════
# DOCS AGENT
# ═══════════════════════════════════════════════════════════════
elif selected_agent == "docs":
    header_ph = st.empty()
    _update_header(header_ph, "docs", st.session_state.agent_status)

    with st.form("docs_form", clear_on_submit=False):
        col1, col2 = st.columns([1, 1])
        with col1:
            library = st.selectbox(
                "Library",
                ["Flask", "FastAPI", "SQLAlchemy", "Pydantic", "Streamlit",
                 "httpx", "Requests", "Django", "Pytest", "NumPy", "Pandas",
                 "Celery", "Python stdlib", "Groq", "PyGithub",
                 "BeautifulSoup", "dotenv", "(custom URL)"],
                help="Select a library or choose custom URL",
            )
        with col2:
            custom_url = st.text_input(
                "Custom Docs URL (optional)",
                placeholder="https://docs.example.com/api/reference",
                help="Override the built-in docs URL",
            )

        question = st.text_area(
            "Question",
            placeholder="e.g., How do I use async sessions in SQLAlchemy?",
            height=100,
            help="What do you want to know about this library?",
        )
        submitted = st.form_submit_button(
            "📖 Search Docs",
            use_container_width=True,
        )

    if submitted and question:
        st.session_state.agent_status = "running"
        _update_header(header_ph, "docs", "running")
        output_placeholder = st.empty()
        payload = {"question": question}
        if library != "(custom URL)":
            payload["library"] = library
        if custom_url:
            payload["custom_url"] = custom_url
        result = stream_agent_response(
            "/api/docs",
            payload,
            output_placeholder,
        )
        st.session_state.agent_status = "done"
        _update_header(header_ph, "docs", "done")
        st.session_state.last_output = result
        add_recent_run("docs", f"{library}: {question}")
    elif submitted:
        st.warning("Please enter a question.")
    elif not st.session_state.last_output:
        render_empty_state("Docs Agent")


# ═══════════════════════════════════════════════════════════════
# PR DRAFT AGENT
# ═══════════════════════════════════════════════════════════════
elif selected_agent == "pr_draft":
    header_ph = st.empty()
    _update_header(header_ph, "pr_draft", st.session_state.agent_status)

    with st.form("pr_draft_form", clear_on_submit=False):
        diff_text = st.text_area(
            "Git Diff",
            placeholder="Paste the output of: git diff HEAD",
            height=200,
            help="Paste your git diff output here",
        )
        issue_number = st.text_input(
            "Related Issue Number (optional)",
            placeholder="e.g., 101",
            help="Issue number to reference in the PR description",
        )
        submitted = st.form_submit_button(
            "📝 Draft PR Description",
            use_container_width=True,
        )

    if submitted and diff_text:
        st.session_state.agent_status = "running"
        _update_header(header_ph, "pr_draft", "running")
        output_placeholder = st.empty()
        payload = {"diff": diff_text}
        if issue_number:
            try:
                payload["issue_number"] = int(issue_number)
            except ValueError:
                pass
        result = stream_agent_response(
            "/api/pr-draft",
            payload,
            output_placeholder,
        )
        st.session_state.agent_status = "done"
        _update_header(header_ph, "pr_draft", "done")
        st.session_state.last_output = result
        add_recent_run("pr_draft", f"PR draft ({len(diff_text)} chars)")
    elif submitted:
        st.warning("Please paste a git diff.")
    elif not st.session_state.last_output:
        render_empty_state("PR Draft Agent")


# ── Copy Output Button ───────────────────────────────────────
if st.session_state.get("last_output"):
    st.markdown("---")
    with st.expander("📋 Copy Raw Output", expanded=False):
        st.code(st.session_state.last_output, language="markdown")
