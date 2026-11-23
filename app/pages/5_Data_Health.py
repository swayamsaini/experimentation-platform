"""Page 5: Warehouse Row Counts & Pre-Period Covariate Balance."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st
from db import query

st.title("Data Health & Pre-Experiment Diagnostics")
manifest = Path("data/warehouse/ingest_manifest.json")
if manifest.exists():
    m = json.loads(manifest.read_text())
    st.caption(f"Last raw ingest: {m['loaded_at']} | Source: {m['source_dir']}")
    st.dataframe(pd.DataFrame.from_dict(m["tables"], orient="index").reset_index(names="raw_table"), use_container_width=True)

st.subheader("Pre-Period Covariate Balance (Love Plot — Target |SMD| < 0.10)")
bal = query("SELECT * FROM balance")
fig_bal = px.scatter(bal, x="smd", y="covariate", color="balanced", title="Standardised Mean Differences")
fig_bal.add_vline(x=-0.10, line_dash="dash", line_color="orange")
fig_bal.add_vline(x=0.10, line_dash="dash", line_color="orange")
fig_bal.add_vline(x=0.0, line_color="gray")
st.plotly_chart(fig_bal, use_container_width=True)
st.dataframe(bal, use_container_width=True)
