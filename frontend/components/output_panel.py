"""
DevFlow Agent — Output Panel Component
Streaming output display with copy functionality.
"""

import streamlit as st
import requests
from frontend.styles.mocha import COLORS


FLASK_URL = "http://localhost:5000"


def stream_agent_response(endpoint: str, payload: dict, output_placeholder) -> str:
    """
    Call a Flask agent endpoint with streaming and display output live.

    Args:
        endpoint: API path (e.g., "/api/context")
        payload: JSON body to send
        output_placeholder: st.empty() to render into

    Returns:
        Full response text
    """
    full_text = ""
    try:
        with requests.post(
            f"{FLASK_URL}{endpoint}",
            json=payload,
            stream=True,
            timeout=120,
        ) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    full_text += chunk
                    # Show with blinking cursor
                    output_placeholder.markdown(
                        f"<div class='output-panel'>{_escape_html(full_text)}"
                        f"<span class='cursor'>▌</span></div>",
                        unsafe_allow_html=True,
                    )
    except requests.ConnectionError:
        full_text += "\n\n⚠️ Could not connect to Flask backend.\n"
        full_text += "Make sure Flask is running: python run.py\n"
    except requests.Timeout:
        full_text += "\n\n⚠️ Request timed out after 120 seconds.\n"
    except Exception as e:
        full_text += f"\n\n⚠️ Error: {e}\n"

    # Final render without cursor
    output_placeholder.markdown(
        f"<div class='output-panel'>{_escape_html(full_text)}</div>",
        unsafe_allow_html=True,
    )
    return full_text


def render_output_panel(text: str, show_copy: bool = True):
    """Render a static output panel with optional copy button."""
    if not text:
        st.markdown(
            f"<div class='output-panel' style='color:{COLORS['overlay0']}; "
            f"font-style:italic; min-height:100px;'>"
            f"Output will appear here...</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<div class='output-panel'>{_escape_html(text)}</div>",
        unsafe_allow_html=True,
    )

    if show_copy and text:
        st.code(text, language="markdown")


def _escape_html(text: str) -> str:
    """Minimal HTML escaping that preserves newlines."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("\n", "<br>")
    return text
