"""
DevFlow Agent — Agent Header Component
Displays agent title, description, and status indicator.
"""

import streamlit as st
from frontend.styles.mocha import AGENT_LABELS, AGENT_DESCRIPTIONS, AGENT_COLORS, COLORS

_STATUS_COLORS = {
    "idle": COLORS["overlay0"],
    "running": COLORS["green"],
    "done": COLORS["blue"],
    "error": COLORS["red"],
}
_STATUS_LABELS = {
    "idle": "Ready",
    "running": "Running…",
    "done": "Complete",
    "error": "Error",
}


def agent_header_html(agent_key: str, status: str = "idle") -> str:
    """Return the HTML string for the agent header card (for use with st.empty())."""
    label = AGENT_LABELS.get(agent_key, "Agent")
    description = AGENT_DESCRIPTIONS.get(agent_key, "")
    accent = AGENT_COLORS.get(agent_key, COLORS["mauve"])
    dot_color = _STATUS_COLORS.get(status, COLORS["overlay0"])
    status_text = _STATUS_LABELS.get(status, "Ready")
    dot_anim = "animation: pulse 2s ease-in-out infinite;" if status == "running" else ""

    return f"""<div class="agent-header" style="border-top: 3px solid {accent};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h2 style="color:{COLORS['text']}; margin:0 0 0.3rem 0;">{label}</h2>
                <p style="color:{COLORS['subtext0']}; margin:0; font-size:0.9rem;">{description}</p>
            </div>
            <div role="status" aria-live="polite"
                 style="display:flex; align-items:center; gap:6px;
                        background:{COLORS['surface0']}; padding:0.35rem 0.75rem;
                        border-radius:20px; font-size:0.75rem;">
                <span aria-hidden="true"
                      style="display:inline-block; width:8px; height:8px;
                             border-radius:50%; background:{dot_color}; {dot_anim}"></span>
                <span style="color:{COLORS['subtext0']};">{status_text}</span>
            </div>
        </div>
    </div>"""


def render_agent_header(agent_key: str, status: str = "idle"):
    """Render the agent header card with status indicator."""
    st.markdown(agent_header_html(agent_key, status), unsafe_allow_html=True)
