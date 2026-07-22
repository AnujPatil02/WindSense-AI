"""Embeds the built 3D digital twin (digital-twin/dist/index.html) into Streamlit."""
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

DIST_PATH = Path(__file__).parent.parent / "digital-twin" / "dist" / "index.html"


def render_digital_twin(height: int = 850):
    if not DIST_PATH.exists():
        st.warning(
            f"Digital twin build not found at {DIST_PATH}. "
            f"Run 'npm install && npm run build' inside digital-twin/ first."
        )
        return
    html = DIST_PATH.read_text(encoding="utf-8")
    components.html(html, height=height, scrolling=False)