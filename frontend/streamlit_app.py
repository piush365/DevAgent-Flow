"""
DevFlow Agent — Streamlit Frontend
Run with: streamlit run frontend/streamlit_app.py
"""

import sys
import os

# Add project root to path so we can import frontend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from frontend.styles.mocha import inject_mocha_css, COLORS, AGENT_COLORS
from frontend.components.sidebar import render_sidebar, add_recent_run
from frontend.components.agent_header import render_agent_header
from frontend.components.output_panel import stream_agent_response

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


# ═══════════════════════════════════════════════════════════════
# CONTEXT AGENT
# ═══════════════════════════════════════════════════════════════
if selected_agent == "context":
    render_agent_header("context", st.session_state.agent_status)

    with st.form("context_form", clear_on_submit=False):
        issue_url = st.text_input(
            "GitHub Issue URL",
            placeholder="https://github.com/owner/repo/issues/42",
            help="Paste a public GitHub issue URL",
        )
        submitted = st.form_submit_button(
            "🔍 Analyze Issue",
            use_container_width=True,
        )

    if submitted and issue_url:
        st.session_state.agent_status = "running"
        render_agent_header("context", "running")
        output_placeholder = st.empty()
        result = stream_agent_response(
            "/api/context",
            {"issue_url": issue_url},
            output_placeholder,
        )
        st.session_state.agent_status = "done"
        st.session_state.last_output = result
        add_recent_run("context", issue_url)
    elif submitted:
        st.warning("Please enter a GitHub issue URL.")


# ═══════════════════════════════════════════════════════════════
# BOILERPLATE AGENT
# ═══════════════════════════════════════════════════════════════
elif selected_agent == "boilerplate":
    render_agent_header("boilerplate", st.session_state.agent_status)

    with st.form("boilerplate_form", clear_on_submit=False):
        description = st.text_area(
            "Description",
            placeholder="e.g., Flask route for user registration with email and password validation",
            height=120,
            help="Describe what boilerplate code you need",
        )
        style_ref = st.text_input(
            "Style Reference URL (optional)",
            placeholder="https://github.com/owner/repo/blob/main/app/routes/auth.py",
            help="URL of a code file to match its conventions",
        )
        submitted = st.form_submit_button(
            "⚡ Generate Boilerplate",
            use_container_width=True,
        )

    if submitted and description:
        st.session_state.agent_status = "running"
        render_agent_header("boilerplate", "running")
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
        st.session_state.last_output = result
        add_recent_run("boilerplate", description)
    elif submitted:
        st.warning("Please enter a description.")


# ═══════════════════════════════════════════════════════════════
# DOCS AGENT
# ═══════════════════════════════════════════════════════════════
elif selected_agent == "docs":
    render_agent_header("docs", st.session_state.agent_status)

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
        render_agent_header("docs", "running")
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
        st.session_state.last_output = result
        add_recent_run("docs", f"{library}: {question}")
    elif submitted:
        st.warning("Please enter a question.")


# ═══════════════════════════════════════════════════════════════
# PR DRAFT AGENT
# ═══════════════════════════════════════════════════════════════
elif selected_agent == "pr_draft":
    render_agent_header("pr_draft", st.session_state.agent_status)

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
        render_agent_header("pr_draft", "running")
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
        st.session_state.last_output = result
        add_recent_run("pr_draft", f"PR draft ({len(diff_text)} chars)")
    elif submitted:
        st.warning("Please paste a git diff.")


# ── Copy Output Button ───────────────────────────────────────
if st.session_state.get("last_output"):
    st.markdown("---")
    with st.expander("📋 Copy Raw Output", expanded=False):
        st.code(st.session_state.last_output, language="markdown")
