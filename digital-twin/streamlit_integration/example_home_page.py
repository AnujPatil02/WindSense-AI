"""
Example: how to use the digital twin embed inside your existing
WindSense-AI Streamlit app (replaces home_ui.py content).

Copy digital-twin/dist/ and digital-twin/streamlit_integration/digital_twin_embed.py
into your dashboard project, e.g.:

    dashboard/
    ├── streamlit_app.py
    ├── digital_twin/
    │   ├── dist/index.html          <- built bundle
    │   └── digital_twin_embed.py
    └── ui/...

Then in your Home page module:
"""

import streamlit as st
from digital_twin.digital_twin_embed import render_digital_twin

st.set_page_config(layout="wide", page_title="WindSense-AI")

selected_turbine = render_digital_twin(height=900)

if selected_turbine:
    st.success(f"Selected turbine: {selected_turbine}")
    # Route to your existing Asset Detail page logic here, e.g.:
    # st.session_state["active_turbine"] = selected_turbine
    # switch_page("asset_detail")
