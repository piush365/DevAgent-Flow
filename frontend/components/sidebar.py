"""
DevFlow Agent — Sidebar Component
Navigation sidebar with app branding, agent selection, and recent runs.
"""

import streamlit as st
from frontend.styles.mocha import AGENT_LABELS, AGENT_COLORS, COLORS


def render_sidebar() -> str:
    """
    Render the sidebar navigation.

    Returns:
        Selected agent key (context, boilerplate, docs, pr_draft)
    """
    with st.sidebar:
        # ── App Branding ───────────────────────────────────────
        st.markdown("# 🚀 DevFlow Agent")
        st.markdown(
            f"<p style='color: {COLORS['subtext0']}; font-size: 0.8rem; "
            f"margin-top: -0.5rem; margin-bottom: 1.5rem;'>"
            f"AI-powered developer productivity</p>",
            unsafe_allow_html=True,
        )

        # ── Agent Navigation ──────────────────────────────────
        st.markdown(
            f"<p style='color: {COLORS['overlay1']}; font-size: 0.7rem; "
            f"text-transform: uppercase; letter-spacing: 0.1em; "
            f"font-weight: 600; margin-bottom: 0.5rem;'>Agents</p>",
            unsafe_allow_html=True,
        )

        # Build radio options with colored dots
        agent_keys = list(AGENT_LABELS.keys())
        agent_options = []
        for key in agent_keys:
            color = AGENT_COLORS[key]
            label = AGENT_LABELS[key]
            agent_options.append(label)

        selected_label = st.radio(
            "Select Agent",
            agent_options,
            label_visibility="collapsed",
        )

        # Map label back to key
        label_to_key = {v: k for k, v in AGENT_LABELS.items()}
        selected_key = label_to_key.get(selected_label, "context")

        # ── Color indicator dots (aria-labelled for screen readers) ──
        dots_html = ""
        for key in agent_keys:
            color = AGENT_COLORS[key]
            label_text = AGENT_LABELS[key]
            is_active = key == selected_key
            opacity = "1" if is_active else "0.4"
            size = "10px" if is_active else "6px"
            aria_label = f"{label_text} — {'active' if is_active else 'inactive'}"
            dots_html += (
                f"<span role='listitem' aria-label='{aria_label}' "
                f"style='display:inline-block; width:{size}; height:{size}; "
                f"border-radius:50%; background-color:{color}; margin:0 4px; "
                f"opacity:{opacity}; transition: all 0.3s ease;'></span>"
            )

        st.markdown(
            f"<div role='list' aria-label='Agent indicators' "
            f"style='text-align:center; margin: 0.5rem 0 1.5rem 0;'>{dots_html}</div>",
            unsafe_allow_html=True,
        )

        # ── Divider ───────────────────────────────────────────
        st.markdown("---")

        # ── Recent Runs ───────────────────────────────────────
        st.markdown(
            f"<p style='color: {COLORS['overlay1']}; font-size: 0.7rem; "
            f"text-transform: uppercase; letter-spacing: 0.1em; "
            f"font-weight: 600; margin-bottom: 0.5rem;'>Recent Runs</p>",
            unsafe_allow_html=True,
        )

        if "recent_runs" not in st.session_state:
            st.session_state.recent_runs = []

        runs = st.session_state.recent_runs
        if runs:
            for run in reversed(runs[-3:]):  # Show last 3, most-recent first
                color = AGENT_COLORS.get(run["agent"], COLORS["overlay0"])
                st.markdown(
                    f"<div class='recent-run' style='border-left-color: {color};'>"
                    f"<strong>{AGENT_LABELS.get(run['agent'], run['agent'])}</strong><br>"
                    f"<span style='font-size: 0.75rem;'>{run['preview']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f"<p style='color: {COLORS['overlay0']}; font-size: 0.8rem; "
                f"font-style: italic;'>No runs yet</p>",
                unsafe_allow_html=True,
            )

        # ── Footer ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            f"<p style='color: {COLORS['overlay0']}; font-size: 0.7rem; text-align: center;'>"
            f"Built with Flask + Streamlit<br>"
            f"LLM: Groq → Gemini → OpenRouter</p>",
            unsafe_allow_html=True,
        )

    return selected_key


def add_recent_run(agent_key: str, preview: str):
    """Add a run to the recent runs list in session state."""
    if "recent_runs" not in st.session_state:
        st.session_state.recent_runs = []

    st.session_state.recent_runs.append({
        "agent": agent_key,
        "preview": preview[:60] + "..." if len(preview) > 60 else preview,
    })

    # Keep only last 10
    if len(st.session_state.recent_runs) > 10:
        st.session_state.recent_runs = st.session_state.recent_runs[-10:]
