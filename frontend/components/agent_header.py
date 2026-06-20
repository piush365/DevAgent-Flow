"""
DevFlow Agent — Agent Header Component
Displays agent title, description, and status indicator.
"""

import streamlit as st
from frontend.styles.mocha import AGENT_LABELS, AGENT_DESCRIPTIONS, AGENT_COLORS, COLORS


def render_agent_header(agent_key: str, status: str = "idle"):
    """Render the agent header card with status indicator."""
    label = AGENT_LABELS.get(agent_key, "Agent")
    description = AGENT_DESCRIPTIONS.get(agent_key, "")
    accent = AGENT_COLORS.get(agent_key, COLORS["mauve"])

    status_colors = {"idle": COLORS["overlay0"], "running": COLORS["green"],
                     "done": COLORS["blue"], "error": COLORS["red"]}
    status_labels = {"idle": "Ready", "running": "Running...",
                     "done": "Complete", "error": "Error"}
    dot_color = status_colors.get(status, COLORS["overlay0"])
    status_text = status_labels.get(status, "Ready")
    dot_anim = "animation: pulse 2s ease-in-out infinite;" if status == "running" else ""

    st.markdown(f"""
    <div class="agent-header" style="border-top: 3px solid {accent};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h2 style="color:{COLORS['text']}; margin:0 0 0.3rem 0;">{label}</h2>
                <p style="color:{COLORS['subtext0']}; margin:0; font-size:0.9rem;">{description}</p>
            </div>
            <div style="display:flex; align-items:center; gap:6px;
                        background:{COLORS['surface0']}; padding:0.35rem 0.75rem;
                        border-radius:20px; font-size:0.75rem;">
                <span style="display:inline-block; width:8px; height:8px;
                             border-radius:50%; background:{dot_color}; {dot_anim}"></span>
                <span style="color:{COLORS['subtext0']};">{status_text}</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
