"""Page 6: Pre-Registered Design, Assumptions & Limitations."""
from pathlib import Path
import streamlit as st

st.title("Methodology, Pre-Registration & Limitations")
st.info("Integrity Policy: Warehouse, EDA, 2018 Truckers' Strike DiD & IPW use 100% real Olist data. The Fast-Ship A/B test is semi-synthetic.")
for title, path in [
    ("Business Brief (docs/01_business_brief.md)", Path("docs/01_business_brief.md")),
    ("Pre-Registered Experiment Design (docs/experiment_design.md)", Path("docs/experiment_design.md")),
]:
    with st.expander(title, expanded=True):
        st.markdown(path.read_text() if path.exists() else f"File `{path}` not found.")
