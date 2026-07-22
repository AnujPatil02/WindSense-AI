# dashboard/ui/theme.py
"""WindSense-AI — Elite NeoGrid Design System"""

import streamlit as st

# ═══════════════════════════════════════════════
# COLOR TOKENS
# ═══════════════════════════════════════════════
COLORS = {
    "bg_primary":      "#050816",
    "bg_secondary":    "#0B1120",
    "bg_card":         "#0D1424",
    "text_primary":    "#F8FAFC",
    "text_secondary":  "#CBD5E1",
    "text_muted":      "#64748B",
    "cyan":            "#00D4FF",
    "purple":          "#8B5CF6",
    "healthy":         "#10B981",
    "warning":         "#F59E0B",
    "critical":        "#EF4444",
    "orange":          "#F97316",
    "border":          "#1E2D45",
    "glass":           "rgba(255,255,255,0.03)",
}

PRIORITY_COLORS = {
    "CRITICAL": COLORS["critical"],
    "HIGH":     COLORS["orange"],
    "MEDIUM":   COLORS["warning"],
    "LOW":      COLORS["healthy"],
}

PLOTLY_THEME = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor":  "rgba(0,0,0,0)",
        "font":   {"family": "Inter", "color": COLORS["text_secondary"]},
        "xaxis":  {
            "gridcolor": "rgba(255,255,255,0.04)",
            "zerolinecolor": "rgba(255,255,255,0.06)",
            "linecolor": "rgba(255,255,255,0.06)",
            "tickcolor": "rgba(255,255,255,0.06)",
        },
        "yaxis":  {
            "gridcolor": "rgba(255,255,255,0.04)",
            "zerolinecolor": "rgba(255,255,255,0.06)",
            "linecolor": "rgba(255,255,255,0.06)",
            "tickcolor": "rgba(255,255,255,0.06)",
        },
        "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"color": COLORS["text_secondary"]}},
        "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
    }
}

def windsense_brand_header() -> str:
    return (
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<div style="font-size:22px;filter:drop-shadow(0 0 10px rgba(0,212,255,0.6));">🌬️</div>'
        '<div>'
        '<div style="font-size:15px;font-weight:800;font-family:\'Space Grotesk\',sans-serif;'
        'background:linear-gradient(135deg,#00D4FF,#8B5CF6);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">WindSense-AI</div>'
        '<div style="font-size:9px;letter-spacing:2.5px;color:' + COLORS['text_muted'] + ';font-weight:600;">'
        'NEOGRID COMMAND</div>'
        '</div></div>'
    )

# ═══════════════════════════════════════════════
# GLOBAL CSS
# ═══════════════════════════════════════════════
GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@500;700;800&display=swap');

/* ROOT */
html, body, [class*="css"] {{ font-family:'Inter',sans-serif; }}
body {{ background:{COLORS['bg_primary']}; color:{COLORS['text_primary']}; }}

/* APP BACKGROUND */
.stApp {{
    background:
        radial-gradient(ellipse 80% 50% at 10% 0%,  rgba(0,212,255,0.055) 0%, transparent 50%),
        radial-gradient(ellipse 60% 40% at 90% 5%,  rgba(139,92,246,0.065) 0%, transparent 50%),
        radial-gradient(ellipse 40% 30% at 50% 100%,rgba(16,185,129,0.035) 0%, transparent 60%),
        {COLORS['bg_primary']};
    min-height:100vh;
}}
/* Fix page header badge alignment across all pages */
.ws-page-header-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
}}
.ws-page-header-row h1 {{
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
}}
/* Universal page header alignment fix */
div[class*="stMarkdown"] h1 {{
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    line-height: 1 !important;
    display: inline !important;
}}
.block-container {{
    padding-top:0.75rem;
    padding-bottom:2.5rem;
    max-width:1600px;
}}

/* HIDE STREAMLIT CHROME */
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu, footer {{ display:none !important; visibility:hidden; }}

/* PAGE ENTRANCE */
@keyframes wsPageIn {{
    from {{ opacity:0; transform:translateY(16px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
.block-container > div {{
    animation: wsPageIn 0.45s cubic-bezier(0.22,1,0.36,1) both;
}}

/* ══════════════════════════════════════
   SIDEBAR
══════════════════════════════════════ */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #04060F 0%, #080E1C 50%, #0B1120 100%);
    border-right: 1px solid {COLORS['border']};
    box-shadow: 4px 0 32px rgba(0,0,0,0.5);
}}
section[data-testid="stSidebar"] * {{ color:{COLORS['text_primary']}; }}

/* SIDEBAR NAV — zero shift on click/focus */
section[data-testid="stSidebar"] .element-container {{
    margin: 0 !important;
    padding: 0 !important;
}}
section[data-testid="stSidebar"] .stButton {{
    margin: 0 0 2px 0 !important;
    padding: 0 !important;
}}
section[data-testid="stSidebar"] .stButton > button {{
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    color: {COLORS['text_secondary']} !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    padding: 9px 14px !important;
    text-align: left !important;
    width: 100% !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 20px !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
    outline: none !important;
    box-shadow: none !important;
    transform: none !important;
    position: static !important;
    transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(0,212,255,0.07) !important;
    border-color: rgba(0,212,255,0.22) !important;
    color: {COLORS['cyan']} !important;
    transform: none !important;
    box-shadow: none !important;
}}
section[data-testid="stSidebar"] .stButton > button:focus,
section[data-testid="stSidebar"] .stButton > button:active,
section[data-testid="stSidebar"] .stButton > button:focus-visible,
section[data-testid="stSidebar"] .stButton > button:focus:not(:active) {{
    background: rgba(0,212,255,0.09) !important;
    border: 1px solid rgba(0,212,255,0.28) !important;
    border-left: 3px solid {COLORS['cyan']} !important;
    color: {COLORS['cyan']} !important;
    outline: none !important;
    box-shadow: none !important;
    transform: none !important;
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    padding: 9px 14px !important;
    padding-left: 12px !important;
    box-sizing: border-box !important;
}}
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {{
    margin: 0 !important;
    padding: 0 !important;
}}

/* SIDEBAR LINK BUTTONS */
section[data-testid="stSidebar"] .stLinkButton > a {{
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 8px !important;
    color: {COLORS['text_secondary']} !important;
    font-size: 11px !important;
    transition: all 0.18s ease !important;
}}
section[data-testid="stSidebar"] .stLinkButton > a:hover {{
    background: rgba(0,212,255,0.08) !important;
    border-color: rgba(0,212,255,0.22) !important;
    color: {COLORS['cyan']} !important;
}}

/* ══════════════════════════════════════
   KPI CARDS — uniform fixed size
══════════════════════════════════════ */
.ws-kpi-card {{
    position: relative;
    overflow: hidden;
    padding: 18px 20px !important;
    border-radius: 16px;
    background: linear-gradient(145deg, rgba(13,20,36,0.96), rgba(5,8,22,0.92));
    border: 1px solid rgba(255,255,255,0.06);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    transition: all 0.28s cubic-bezier(0.22,1,0.36,1);
    height: 160px !important;
    min-height: 160px !important;
    max-height: 160px !important;
    width: 100%;
    box-sizing: border-box !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    gap: 10px !important;
}}
.ws-kpi-card::before {{
    content:"";
    position:absolute;
    top:0; left:0; right:0;
    height:2px;
    background: var(--accent, {COLORS['cyan']});
    box-shadow: 0 0 16px var(--accent, {COLORS['cyan']});
    opacity: 0.9;
}}
.ws-kpi-card::after {{
    content:"";
    position:absolute;
    top:-10px; right:-10px;
    width:90px; height:90px;
    background: radial-gradient(circle, var(--accent-glow, rgba(0,212,255,0.09)) 0%, transparent 70%);
    border-radius:50%;
    pointer-events:none;
}}
.ws-kpi-card:hover {{
    transform: translateY(-5px);
    border-color: rgba(255,255,255,0.12);
    box-shadow: 0 16px 48px rgba(0,0,0,0.45), 0 0 30px var(--accent-glow, rgba(0,212,255,0.1));
}}
.ws-kpi-icon {{
    font-size: 20px !important;
    line-height: 1 !important;
    margin: 0 !important;
    display: block;
    flex-shrink: 0;
}}
.ws-kpi-label {{
    color: {COLORS['text_muted']};
    font-size: 14.5px !important;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    font-weight: 700;
    margin: 0 !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex-shrink: 0;
}}
.ws-kpi-value {{
    font-size: 28px !important;
    font-weight: 800;
    color: {COLORS['text_primary']};
    font-family: 'Space Grotesk', sans-serif;
    line-height: 1 !important;
    letter-spacing: -1px;
    margin: 0 !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex-shrink: 0;
}}
.ws-kpi-delta {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 4px 9px;
    border-radius: 999px;
    font-size: 12.5px !important;
    font-weight: 700;
    margin: 0 !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
    flex-shrink: 0;
    width: fit-content;
}}
.ws-delta-up      {{ background:rgba(16,185,129,0.12);  color:{COLORS['healthy']}; }}
.ws-delta-down    {{ background:rgba(239,68,68,0.12);   color:{COLORS['critical']}; }}
.ws-delta-warn    {{ background:rgba(245,158,11,0.12);  color:{COLORS['warning']}; }}
.ws-delta-neutral {{ background:rgba(255,255,255,0.06); color:{COLORS['text_secondary']}; }}

/* GLASS PANEL */
.ws-panel {{
    background: linear-gradient(145deg, rgba(13,20,36,0.92), rgba(5,8,22,0.88));
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    padding: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.04);
}}

/* SECTION HEADER */
.ws-section-header {{
    font-size: 18px;
    font-weight: 800;
    color: {COLORS['text_primary']};
    font-family: 'Space Grotesk', sans-serif;
    margin-bottom: 16px;
    letter-spacing: -0.5px;
}}

/* TABLE */
.ws-table {{ width:100%; border-collapse:collapse; }}
.ws-table thead {{ background:rgba(255,255,255,0.025); }}
.ws-table th {{
    padding: 13px 16px;
    text-align: left;
    color: {COLORS['text_muted']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.3px;
    text-transform: uppercase;
    border-bottom: 1px solid {COLORS['border']};
}}
.ws-table td {{
    padding: 13px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    color: {COLORS['text_primary']};
    font-size: 13px;
}}
.ws-table tr {{ transition:background 0.15s ease; }}
.ws-table tr:hover {{ background:rgba(0,212,255,0.025); }}

/* BADGES */
.ws-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
.ws-badge-critical {{ background:rgba(239,68,68,0.12);   color:{COLORS['critical']}; border:1px solid rgba(239,68,68,0.2); }}
.ws-badge-high     {{ background:rgba(249,115,22,0.12);  color:{COLORS['orange']};   border:1px solid rgba(249,115,22,0.2); }}
.ws-badge-medium   {{ background:rgba(245,158,11,0.12);  color:{COLORS['warning']};  border:1px solid rgba(245,158,11,0.2); }}
.ws-badge-low      {{ background:rgba(16,185,129,0.12);  color:{COLORS['healthy']};  border:1px solid rgba(16,185,129,0.2); }}
.ws-badge-cyan     {{ background:rgba(0,212,255,0.10);   color:{COLORS['cyan']};     border:1px solid rgba(0,212,255,0.2); }}
.ws-badge-purple   {{ background:rgba(139,92,246,0.10);  color:{COLORS['purple']};   border:1px solid rgba(139,92,246,0.2); }}
.ws-badge-gray     {{ background:rgba(255,255,255,0.05); color:{COLORS['text_secondary']}; border:1px solid rgba(255,255,255,0.08); }}

/* ALERTS */
.ws-alert-critical, .ws-alert-warning, .ws-alert-info {{
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 14px 16px;
    border-radius: 12px;
    margin-bottom: 10px;
    transition: all 0.2s ease;
}}
.ws-alert-critical {{ background:rgba(239,68,68,0.07);  border:1px solid rgba(239,68,68,0.18); }}
.ws-alert-warning  {{ background:rgba(245,158,11,0.07); border:1px solid rgba(245,158,11,0.18); }}
.ws-alert-info     {{ background:rgba(0,212,255,0.06);  border:1px solid rgba(0,212,255,0.18); }}

/* PULSE */
@keyframes wsPulseRing {{
    0%   {{ transform:scale(1);   opacity:0.6; }}
    100% {{ transform:scale(2.8); opacity:0; }}
}}
.ws-pulse-wrapper {{ position:relative; display:inline-flex; align-items:center; justify-content:center; }}
.ws-pulse-ring    {{ position:absolute; border-radius:50%; animation:wsPulseRing 2s infinite; }}
.ws-pulse         {{ position:relative; border-radius:50%; }}

/* STAGGER ENTRANCE */
@keyframes wsFadeUp {{
    from {{ opacity:0; transform:translateY(12px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
.ws-stagger-1 {{ animation:wsFadeUp 0.4s 0.05s cubic-bezier(0.22,1,0.36,1) both; }}
.ws-stagger-2 {{ animation:wsFadeUp 0.4s 0.13s cubic-bezier(0.22,1,0.36,1) both; }}
.ws-stagger-3 {{ animation:wsFadeUp 0.4s 0.22s cubic-bezier(0.22,1,0.36,1) both; }}
.ws-stagger-4 {{ animation:wsFadeUp 0.4s 0.31s cubic-bezier(0.22,1,0.36,1) both; }}
.ws-stagger-5 {{ animation:wsFadeUp 0.4s 0.40s cubic-bezier(0.22,1,0.36,1) both; }}

/* ══════════════════════════════════════
   WIDGET OVERRIDES
══════════════════════════════════════ */
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    background: rgba(13,20,36,0.9) !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 8px !important;
    color: {COLORS['text_primary']} !important;
}}
.stTextInput > div > div > input,
.stTextArea textarea {{
    background: rgba(13,20,36,0.9) !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 8px !important;
    color: {COLORS['text_primary']} !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {{
    border-color: {COLORS['cyan']} !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.12) !important;
}}
div[data-testid="stMetric"] {{
    background: rgba(13,20,36,0.8);
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 14px;
}}
.stTabs [data-baseweb="tab-list"] {{
    background: rgba(13,20,36,0.7);
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: 1px solid {COLORS['border']};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px;
    color: {COLORS['text_muted']} !important;
    font-size: 12px;
    font-weight: 600;
    padding: 7px 18px;
    transition: all 0.18s ease;
    letter-spacing: 0.3px;
}}
.stTabs [aria-selected="true"] {{
    background: rgba(0,212,255,0.12) !important;
    color: {COLORS['cyan']} !important;
    box-shadow: 0 0 12px rgba(0,212,255,0.10) !important;
}}

/* GLOBAL BUTTONS (non-sidebar) */
.stButton > button {{
    background: rgba(0,212,255,0.09);
    border: 1px solid rgba(0,212,255,0.22);
    border-radius: 8px;
    color: {COLORS['cyan']};
    font-weight: 600;
    font-size: 12.5px;
    letter-spacing: 0.3px;
    transition: all 0.2s cubic-bezier(0.22,1,0.36,1);
}}
.stButton > button:hover {{
    background: rgba(0,212,255,0.18);
    border-color: rgba(0,212,255,0.4);
    box-shadow: 0 0 20px rgba(0,212,255,0.15);
    transform: translateY(-2px);
}}
.stButton > button:active {{ transform: translateY(0); }}

.stDataFrame {{ border-radius:12px; overflow:hidden; border:1px solid {COLORS['border']}; }}
div[data-testid="stExpander"] {{
    background: rgba(13,20,36,0.7);
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}

/* SCROLLBAR */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:{COLORS['border']}; border-radius:999px; }}
::-webkit-scrollbar-thumb:hover {{ background:{COLORS['text_muted']}; }}

/* FOOTER */
.ws-footer {{
    margin-top: 32px;
    padding-top: 18px;
    border-top: 1px solid rgba(255,255,255,0.04);
    text-align: center;
    color: {COLORS['text_muted']};
    font-size: 11px;
    letter-spacing: 1.5px;
}}

/* NUCLEAR sidebar shift fix — target internal Streamlit wrappers */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div {{
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}}
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockSeparator"] {{
    display: none !important;
}}
section[data-testid="stSidebar"] .stButton > button:focus-visible {{
    outline: none !important;
    box-shadow: none !important;
}}
/* Remove the gap Streamlit adds between focused button and next element */
section[data-testid="stSidebar"] .stButton + div {{
    margin-top: 0 !important;
}}

/* MONO */
.ws-mono {{ font-family:'JetBrains Mono',monospace; }}
</style>
"""

def inject_theme():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)