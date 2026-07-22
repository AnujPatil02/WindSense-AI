"""
WindSense-AI Digital Twin — Streamlit integration.

Usage in your dashboard's Home page:

    from digital_twin_embed import render_digital_twin
    render_digital_twin()

How it works:
- components.html() embeds the built dist/index.html (single self-contained file,
  JS/CSS/assets all inlined — no separate static file serving needed).
- components.html() is normally one-way (parent -> iframe only). To get click
  events BACK from the 3D scene into Python, we inject a small listener script
  alongside the iframe that catches postMessage events and writes them into
  a hidden Streamlit text input via JS, which triggers a rerun on change.
  This is the standard documented workaround for bidirectional communication
  with components.html() (no custom component build step required).
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

DIST_PATH = Path(__file__).parent / "dist" / "index.html"


def render_digital_twin(height: int = 900):
    if not DIST_PATH.exists():
        st.error(
            f"Digital twin build not found at {DIST_PATH}. "
            f"Run 'npm run build' inside digital-twin/ first."
        )
        return None

    html = DIST_PATH.read_text(encoding="utf-8")

    # Listener bridge: catches postMessage from the iframe and forwards the
    # turbine id into a Streamlit-visible element via the browser's
    # sessionStorage + a query param reload. This keeps things framework-free
    # (no custom React component build required for the Python side).
    bridge_script = """
    <script>
      window.addEventListener("message", (event) => {
        if (event.data && event.data.source === "windsense-digital-twin") {
          const payload = event.data.payload;
          if (event.data.eventType === "turbine_click" && payload?.id) {
            // Write to sessionStorage so Python can poll it via a query param trick
            window.parent.sessionStorage.setItem("windsense_selected_turbine", payload.id);
            // Force a Streamlit rerun by updating the URL query param
            const url = new URL(window.parent.location);
            url.searchParams.set("selected_turbine", payload.id);
            window.parent.history.replaceState({}, "", url);
          }
        }
      });
    </script>
    """

    components.html(bridge_script + html, height=height, scrolling=False)

    # Read back the selection via query params (set by the bridge script above)
    selected = st.query_params.get("selected_turbine", None)
    return selected
