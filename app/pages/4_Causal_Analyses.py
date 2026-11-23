"""Page 4: 2018 Brazilian Truckers' Strike DiD Event Study & Robustness."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go
import streamlit as st
from db import query

st.title("Causal Analyses: 2018 Truckers' Strike Difference-in-Differences")
ev = query("SELECT * FROM did_event_study")
fig_ev = go.Figure(go.Scatter(
    x=ev["rel_week"], y=ev["coef"], mode="lines+markers",
    error_y=dict(type="data", symmetric=False, array=ev["ci_hi"] - ev["coef"], arrayminus=ev["coef"] - ev["ci_lo"])
))
fig_ev.add_hline(y=0, line_dash="dash")
fig_ev.add_vline(x=-0.5, line_dash="dot", line_color="red")
fig_ev.update_layout(title="Event Study: Interstate vs. Intrastate Delivery Days (Ref = Week -2)",
                     xaxis_title="Weeks Relative to Strike", yaxis_title="Extra Delivery Days (95% CI)")
st.plotly_chart(fig_ev, use_container_width=True)
st.subheader("Robustness & Placebo Checks")
st.dataframe(query("SELECT * FROM did_robustness"), use_container_width=True)
