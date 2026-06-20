"""
DevFlow Agent — Catppuccin Mocha Theme
Custom CSS injection for Streamlit to apply the Catppuccin Mocha dark color scheme.
"""

# ── Catppuccin Mocha Palette ───────────────────────────────────
COLORS = {
    "base": "#1e1e2e",
    "mantle": "#181825",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "overlay0": "#6c7086",
    "overlay1": "#7f849c",
    "text": "#cdd6f4",
    "subtext0": "#a6adc8",
    "subtext1": "#bac2de",
    "lavender": "#b4befe",
    "blue": "#89b4fa",
    "sapphire": "#74c7ec",
    "teal": "#94e2d5",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "peach": "#fab387",
    "maroon": "#eba0ac",
    "red": "#f38ba8",
    "mauve": "#cba6f7",
    "pink": "#f5c2e7",
    "flamingo": "#f2cdcd",
    "rosewater": "#f5e0dc",
}

# ── Agent Accent Colors ───────────────────────────────────────
AGENT_COLORS = {
    "context": COLORS["blue"],       # #89b4fa
    "boilerplate": COLORS["peach"],  # #fab387
    "docs": COLORS["teal"],          # #94e2d5
    "pr_draft": COLORS["green"],     # #a6e3a1
}

AGENT_LABELS = {
    "context": "🔍 Context Agent",
    "boilerplate": "⚡ Boilerplate Agent",
    "docs": "📖 Docs Agent",
    "pr_draft": "📝 PR Drafter",
}

AGENT_DESCRIPTIONS = {
    "context": "Analyze a GitHub issue → get a ready-to-code developer brief",
    "boilerplate": "Describe what you need → get production-ready Python boilerplate",
    "docs": "Ask a library question → get answers from official documentation",
    "pr_draft": "Paste a git diff → get a structured PR description",
}


def inject_mocha_css():
    """Return the full Catppuccin Mocha CSS string for Streamlit injection."""
    return f"""
<style>
    /* ── Import Google Font ─────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Global Overrides ──────────────────────────────────── */
    .stApp {{
        background-color: {COLORS['base']};
        color: {COLORS['text']};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* ── Sidebar ───────────────────────────────────────────── */
    section[data-testid="stSidebar"] {{
        background-color: {COLORS['mantle']};
        border-right: 1px solid {COLORS['surface0']};
        width: 260px !important;
    }}

    section[data-testid="stSidebar"] .stMarkdown h1 {{
        color: {COLORS['mauve']};
        font-weight: 700;
        font-size: 1.4rem;
        letter-spacing: -0.02em;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid {COLORS['surface0']};
        margin-bottom: 1rem;
    }}

    section[data-testid="stSidebar"] .stRadio label {{
        color: {COLORS['text']} !important;
        font-size: 0.95rem;
        font-weight: 500;
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        transition: all 0.2s ease;
        cursor: pointer;
    }}

    section[data-testid="stSidebar"] .stRadio label:hover {{
        background-color: {COLORS['surface0']};
    }}

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] {{
        background-color: {COLORS['surface0']};
    }}

    /* ── Buttons ───────────────────────────────────────────── */
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['mauve']}, {COLORS['blue']});
        color: {COLORS['base']};
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(203, 166, 247, 0.3);
        cursor: pointer;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(203, 166, 247, 0.45);
        filter: brightness(1.1);
    }}

    .stButton > button:active {{
        transform: translateY(0);
    }}

    /* ── Text Inputs & Text Areas ──────────────────────────── */
    .stTextInput input, .stTextArea textarea {{
        background-color: {COLORS['surface0']} !important;
        color: {COLORS['text']} !important;
        border: 1px solid {COLORS['surface1']} !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }}

    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: {COLORS['mauve']} !important;
        box-shadow: 0 0 0 2px rgba(203, 166, 247, 0.2) !important;
    }}

    .stTextInput label, .stTextArea label, .stSelectbox label {{
        color: {COLORS['subtext1']} !important;
        font-weight: 500;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* ── Select Box ────────────────────────────────────────── */
    .stSelectbox > div > div {{
        background-color: {COLORS['surface0']} !important;
        border: 1px solid {COLORS['surface1']} !important;
        border-radius: 10px !important;
        color: {COLORS['text']} !important;
    }}

    /* ── Code Blocks ───────────────────────────────────────── */
    .stCodeBlock, code, pre {{
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        background-color: {COLORS['mantle']} !important;
        border: 1px solid {COLORS['surface0']} !important;
        border-radius: 10px !important;
    }}

    /* ── Markdown ──────────────────────────────────────────── */
    .stMarkdown {{
        color: {COLORS['text']};
    }}

    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: {COLORS['text']};
        font-weight: 600;
    }}

    .stMarkdown a {{
        color: {COLORS['blue']};
        text-decoration: none;
        transition: color 0.2s ease;
    }}

    .stMarkdown a:hover {{
        color: {COLORS['sapphire']};
    }}

    /* ── Dividers ──────────────────────────────────────────── */
    hr {{
        border-color: {COLORS['surface0']} !important;
        margin: 1.5rem 0;
    }}

    /* ── Expander ──────────────────────────────────────────── */
    .streamlit-expanderHeader {{
        background-color: {COLORS['surface0']} !important;
        color: {COLORS['text']} !important;
        border-radius: 10px !important;
        font-weight: 500;
    }}

    /* ── Status / Spinner ──────────────────────────────────── */
    .stSpinner > div {{
        border-top-color: {COLORS['mauve']} !important;
    }}

    /* ── Output Panel ──────────────────────────────────────── */
    .output-panel {{
        background-color: {COLORS['mantle']};
        border: 1px solid {COLORS['surface0']};
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        line-height: 1.6;
        color: {COLORS['text']};
        min-height: 200px;
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-y: auto;
        max-height: 600px;
        animation: fadeIn 0.3s ease;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* ── Blinking Cursor ───────────────────────────────────── */
    @keyframes blink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0; }}
    }}

    .cursor {{
        animation: blink 1s step-end infinite;
        color: {COLORS['mauve']};
        font-weight: bold;
    }}

    /* ── Agent Header Card ─────────────────────────────────── */
    .agent-header {{
        background: linear-gradient(135deg, {COLORS['surface0']}, {COLORS['mantle']});
        border: 1px solid {COLORS['surface1']};
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }}

    .agent-header::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }}

    .agent-header h2 {{
        margin: 0 0 0.5rem 0;
        font-size: 1.3rem;
        font-weight: 700;
        color: {COLORS['text']};
    }}

    .agent-header p {{
        margin: 0;
        color: {COLORS['subtext0']};
        font-size: 0.9rem;
    }}

    /* ── Status Indicator ──────────────────────────────────── */
    .status-dot {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s ease-in-out infinite;
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.6; transform: scale(1.2); }}
    }}

    .status-idle {{
        background-color: {COLORS['overlay0']};
        animation: none;
    }}

    .status-running {{
        background-color: {COLORS['green']};
    }}

    .status-error {{
        background-color: {COLORS['red']};
        animation: none;
    }}

    /* ── Recent Runs ───────────────────────────────────────── */
    .recent-run {{
        background-color: {COLORS['surface0']};
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
        color: {COLORS['subtext0']};
        border-left: 3px solid {COLORS['overlay0']};
        transition: all 0.2s ease;
    }}

    .recent-run:hover {{
        background-color: {COLORS['surface1']};
        border-left-color: {COLORS['mauve']};
    }}

    /* ── Scrollbar ─────────────────────────────────────────── */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}

    ::-webkit-scrollbar-track {{
        background: {COLORS['mantle']};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {COLORS['surface1']};
        border-radius: 3px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['surface2']};
    }}

    /* ── Copy Button ───────────────────────────────────────── */
    .copy-btn {{
        background-color: {COLORS['surface0']};
        color: {COLORS['subtext0']};
        border: 1px solid {COLORS['surface1']};
        border-radius: 8px;
        padding: 0.4rem 1rem;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }}

    .copy-btn:hover {{
        background-color: {COLORS['surface1']};
        color: {COLORS['text']};
    }}

    /* ── Hide Streamlit Defaults ────────────────────────────── */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}

    /* ── Toast / Notification ──────────────────────────────── */
    .stToast {{
        background-color: {COLORS['surface0']} !important;
        color: {COLORS['text']} !important;
        border: 1px solid {COLORS['surface1']} !important;
    }}
</style>
"""


def get_agent_gradient(agent_key: str) -> str:
    """Get a CSS gradient string for an agent's accent color."""
    color = AGENT_COLORS.get(agent_key, COLORS["mauve"])
    return f"linear-gradient(135deg, {color}, {COLORS['mauve']})"


def get_agent_header_css(agent_key: str) -> str:
    """Get the CSS for an agent header's top accent bar."""
    color = AGENT_COLORS.get(agent_key, COLORS["mauve"])
    return f"background: linear-gradient(90deg, {color}, transparent);"
