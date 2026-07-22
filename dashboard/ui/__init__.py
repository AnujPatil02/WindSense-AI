"""
WindSense-AI UI Package
Centralized exports for dashboard UI modules.
"""

"""WindSense-AI UI Package"""

# dashboard/ui/__init__.py

from dashboard.ui.theme import (
    inject_theme,
    COLORS,
    PRIORITY_COLORS,
    PLOTLY_THEME,
    windsense_brand_header,
)

from dashboard.ui.components import (
    kpi_card,
    section_header,
    status_badge,
    priority_badge,
    turbine_card,
    alert_banner,
    styled_table,
    metric_row,
    financial_card,
    pulse_indicator,
    live_indicator,
    nav_button,
)

from dashboard.ui.animations import (
    animated_counter,
    spinning_turbine,
    fleet_map,
    glowing_status_dot,
    loading_wave,
)

from dashboard.ui.topbar import render_topbar
from dashboard.ui.sidebar import render_sidebar


__all__ = [

    # Theme
    "inject_theme",
    "COLORS",
    "PRIORITY_COLORS",
    "PLOTLY_THEME",
    "windsense_brand_header",

    # Components
    "kpi_card",
    "section_header",
    "status_badge",
    "priority_badge",
    "turbine_card",
    "alert_banner",
    "styled_table",
    "metric_row",
    "financial_card",
    "pulse_indicator",
    "live_indicator",
    "nav_button",

    # Animations
    "animated_counter",
    "spinning_turbine",
    "fleet_map",
    "glowing_status_dot",
    "loading_wave",

    # Layout
    "render_topbar",
    "render_sidebar",
]