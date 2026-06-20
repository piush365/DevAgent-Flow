"""
DevFlow Agent — Output Panel Component
Handles streaming output display from Flask agent endpoints.
"""

import html
import logging
import os

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# Read from environment so Docker deployments with a different backend URL work.
FLASK_URL = os.environ.get("FLASK_URL", "http://localhost:5000")


def stream_agent_response(endpoint: str, payload: dict, output_placeholder) -> str:
    """
    POST to a Flask agent endpoint with streaming and display output live.

    Uses Streamlit's native markdown renderer so that LLM output (which
    contains markdown headings, bold text, code blocks, etc.) is displayed
    correctly rather than as escaped literal characters.

    Args:
        endpoint:            API path, e.g. "/api/context"
        payload:             JSON body to send
        output_placeholder:  A ``st.empty()`` container to render into

    Returns:
        Full accumulated response text.
    """
    full_text = ""

    output_placeholder.markdown("*Connecting to agent…*")
    try:
        with requests.post(
            f"{FLASK_URL}{endpoint}",
            json=payload,
            stream=True,
            timeout=120,
        ) as response:
            response.raise_for_status()
            output_placeholder.markdown("*Generating…*")
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    full_text += chunk
                    # Render markdown with a blinking cursor during streaming
                    output_placeholder.markdown(full_text + " ▌")

    except requests.ConnectionError:
        full_text += (
            "\n\n⚠️ **Cannot connect to Flask backend.**\n\n"
            "Make sure the backend is running:\n"
            "```bash\npython run.py\n```"
        )
    except requests.Timeout:
        full_text += "\n\n⚠️ **Request timed out after 120 seconds.**"
    except requests.HTTPError as exc:
        full_text += f"\n\n⚠️ **HTTP error {exc.response.status_code}.**"
    except Exception as exc:
        logger.exception("Unexpected error streaming from %s", endpoint)
        full_text += f"\n\n⚠️ **Unexpected error:** {html.escape(str(exc))}"

    # Final render — no cursor
    output_placeholder.markdown(full_text)
    return full_text


def render_empty_state(agent_label: str) -> None:
    """Render a placeholder when no output has been generated yet."""
    st.markdown(
        "<div style='text-align:center; padding: 3rem 0; opacity: 0.4;'>"
        f"<p style='font-size:2rem;'>🤖</p>"
        f"<p>Run the <strong>{agent_label}</strong> to see output here.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
