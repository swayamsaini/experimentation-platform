"""Page 3: Decision-First Experiment Results (SRM-Gated)."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go
import streamlit as st
from db import query

st.title("Experiment Results: Fast-Ship Programme v1 (Semi-Synthetic)")
res = query("SELECT * FROM experiment_summary WHERE experiment = 'fastship_v1'")
srm_ok = bool(res["srm_p"].iloc[0] >= 1e-3)
c1, c2, c3 = st.columns(3)
c1.metric("SRM Gate", "PASS" if srm_ok else "FAIL", f"p = {res['srm_p'].iloc[0]:.4f}")
c2.metric("Achieved MDE", f"{res['mde_rel'].iloc[0]:.1%}", f"n = {int(res['n_per_arm'].iloc[0])}/arm")
c3.metric("Decision Rule", res["decision"].iloc[0])
if not srm_ok:
    st.error("Sample Ratio Mismatch detected (p < 0.001). Results hidden until assignment is fixed.")
    st.stop()

fig = go.Figure()
for _, r in res.iterrows():
    fig.add_trace(go.Scatter(
        x=[r["estimate"]], y=[r["variant"]], mode="markers", name=r["variant"],
        error_x=dict(type="data", symmetric=False, array=[r["ci_hi"] - r["estimate"]],
                     arrayminus=[r["estimate"] - r["ci_lo"]])
    ))
fig.add_vline(x=0, line_dash="dash")
fig.update_layout(title="6-Week GMV Lift per Seller (R$, 95% CI)")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Guardrails (One-Sided 95% Non-Inferiority)")
st.dataframe(query("SELECT * FROM guardrails"), use_container_width=True)
st.subheader("Exploratory Segments (BH FDR 10%)")
st.dataframe(query("SELECT * FROM segments"), use_container_width=True)

memo_file = Path("data/exports/memo_figures.json")
if memo_file.exists():
    st.download_button("Export Memo Figures (JSON)", memo_file.read_text(), "memo_figures.json")
