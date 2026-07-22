# dashboard/ui/page_layouts.py
"""WindSense-AI — Reusable Page Layout Components"""

import streamlit as st
from dashboard.ui.theme import COLORS
from dashboard.ui.components import section_header


def page_header(title: str, subtitle: str = "", badge: str = "",
                badge_color: str = None) -> None:
    bc = badge_color or COLORS["cyan"]
    try:
        r,g,b = int(bc[1:3],16), int(bc[3:5],16), int(bc[5:7],16)
        bg = f"rgba({r},{g},{b},0.08)"; border = f"rgba({r},{g},{b},0.22)"
    except Exception:
        bg = "rgba(0,212,255,0.08)"; border = "rgba(0,212,255,0.22)"

    badge_html = (
        '<span style="font-size:10px;font-weight:700;color:' + bc + ';'
        'letter-spacing:2px;background:' + bg + ';'
        'border:1px solid ' + border + ';'
        'border-radius:20px;padding:4px 12px;">' + badge + '</span>'
    ) if badge else ""

    sub_html = (
        '<p style="color:' + COLORS["text_muted"] + ';font-size:13px;'
        'margin:0;letter-spacing:0.3px;">' + subtitle + '</p>'
    ) if subtitle else ""

    st.markdown(
        '<div class="ws-stagger-1" style="margin-bottom:24px;">'
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">'
        '<h1 style="font-size:28px;font-weight:800;margin:0;'
        "font-family:'Space Grotesk',sans-serif;"
        'color:' + COLORS["text_primary"] + ';letter-spacing:-1px;">'
        + title + '</h1>'
        + badge_html +
        '</div>'
        + sub_html +
        '</div>',
        unsafe_allow_html=True
    )


def two_column_layout(left_weight: int = 3, right_weight: int = 2,
                      gap: str = "medium"):
    """Returns (left_col, right_col)."""
    return st.columns([left_weight, right_weight], gap=gap)


def three_column_layout(weights: list = None, gap: str = "medium"):
    weights = weights or [1, 1, 1]
    return st.columns(weights, gap=gap)


def kpi_row(items: list) -> None:
    """
    items: list of (label, value, delta, delta_type, color, icon)
    Renders uniform KPI cards in a row.
    """
    from dashboard.ui.components import kpi_card
    cols = st.columns(len(items))
    for col, (label, val, delta, dtype, color, icon) in zip(cols, items):
        with col:
            st.markdown(kpi_card(label, val, delta, dtype, icon, color),
                        unsafe_allow_html=True)


def divider(label: str = "") -> None:
    if label:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:12px;margin:20px 0;">'
            '<div style="flex:1;height:1px;background:linear-gradient(to right,'
            + COLORS["border"] + ',transparent);"></div>'
            '<span style="font-size:10px;font-weight:700;color:' + COLORS["text_muted"] + ';'
            'letter-spacing:2px;text-transform:uppercase;">' + label + '</span>'
            '<div style="flex:1;height:1px;background:linear-gradient(to left,'
            + COLORS["border"] + ',transparent);"></div>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="height:1px;background:linear-gradient(to right,transparent,'
            + COLORS["border"] + ',transparent);margin:16px 0;"></div>',
            unsafe_allow_html=True
        )


def spacer(px: int = 16) -> None:
    st.markdown(f"<div style='height:{px}px;'></div>", unsafe_allow_html=True)


def info_panel(title: str, content: str, color: str = None,
               icon: str = "ℹ️") -> None:
    c = color or COLORS["cyan"]
    try:
        r,g,b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        bg = f"rgba({r},{g},{b},0.06)"; border = f"rgba({r},{g},{b},0.18)"
    except Exception:
        bg = "rgba(0,212,255,0.06)"; border = "rgba(0,212,255,0.18)"

    st.markdown(
        '<div style="background:' + bg + ';border:1px solid ' + border + ';'
        'border-left:3px solid ' + c + ';border-radius:12px;padding:16px 20px;margin:8px 0;">'
        '<div style="display:flex;align-items:flex-start;gap:12px;">'
        '<span style="font-size:18px;line-height:1.4;">' + icon + '</span>'
        '<div>'
        '<div style="font-size:13px;font-weight:700;color:' + c + ';margin-bottom:6px;">'
        + title + '</div>'
        '<div style="font-size:13px;color:' + COLORS["text_secondary"] + ';line-height:1.7;">'
        + content + '</div>'
        '</div></div></div>',
        unsafe_allow_html=True
    )


def code_block(code: str, language: str = "bash") -> None:
    st.markdown(
        '<div style="background:rgba(5,8,22,0.9);border:1px solid ' + COLORS["border"] + ';'
        'border-radius:10px;padding:14px 16px;margin:8px 0;">'
        '<code style="font-size:12px;color:' + COLORS["cyan"] + ';'
        "font-family:'JetBrains Mono',monospace;\">" + code + '</code>'
        '</div>',
        unsafe_allow_html=True
    )


def status_row(services: list) -> None:
    """
    services: list of (name, status, label)
    status: 'healthy'|'warning'|'critical'|'offline'
    """
    status_colors = {
        "healthy":  COLORS["healthy"],
        "warning":  COLORS["warning"],
        "critical": COLORS["critical"],
        "offline":  COLORS["text_muted"],
        "active":   COLORS["cyan"],
        "running":  COLORS["purple"],
    }
    items = ""
    for name, status, label in services:
        color = status_colors.get(status.lower(), COLORS["cyan"])
        items += (
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'padding:8px 12px;background:rgba(5,8,22,0.6);border-radius:8px;margin-bottom:5px;">'
            '<span style="font-size:12px;color:' + COLORS["text_secondary"] + ';font-weight:500;">'
            + name + '</span>'
            '<span style="display:flex;align-items:center;gap:6px;">'
            '<span style="width:6px;height:6px;border-radius:50%;background:' + color + ';'
            'box-shadow:0 0 6px ' + color + ';display:inline-block;"></span>'
            '<span style="font-size:10px;color:' + color + ';font-weight:700;letter-spacing:0.5px;">'
            + label.upper() + '</span>'
            '</span></div>'
        )
    st.markdown(
        '<div style="background:rgba(13,20,36,0.8);border:1px solid ' + COLORS["border"] + ';'
        'border-radius:12px;padding:14px;">' + items + '</div>',
        unsafe_allow_html=True
    )


def tabbed_section(tabs_config: dict) -> dict:
    """
    tabs_config: {"Tab Label": "tab_key", ...}
    Returns dict of {tab_key: tab_object}
    """
    labels = list(tabs_config.keys())
    keys   = list(tabs_config.values())
    tab_objects = st.tabs(labels)
    return dict(zip(keys, tab_objects))


def empty_state(icon: str = "📭", title: str = "No data available",
                subtitle: str = "", command: str = "") -> None:
    cmd_html = (
        '<div style="font-size:12px;color:' + COLORS["text_muted"] + ';'
        "font-family:'JetBrains Mono',monospace;margin-top:8px;\">"
        + command + '</div>'
    ) if command else ""
    st.markdown(
        '<div style="background:rgba(13,20,36,0.85);border:1px solid ' + COLORS["border"] + ';'
        'border-radius:14px;padding:40px;text-align:center;">'
        '<div style="font-size:42px;margin-bottom:12px;">' + icon + '</div>'
        '<div style="font-size:16px;font-weight:700;color:' + COLORS["text_secondary"] + ';'
        "font-family:'Space Grotesk',sans-serif;\">" + title + '</div>'
        + (f'<div style="font-size:13px;color:{COLORS["text_muted"]};margin-top:6px;">{subtitle}</div>' if subtitle else '')
        + cmd_html +
        '</div>',
        unsafe_allow_html=True
    )