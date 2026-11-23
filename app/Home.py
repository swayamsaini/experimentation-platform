"""Page 1: Marketplace Overview (Real Olist Data)."""
import plotly.express as px
import streamlit as st
from db import query

st.set_page_config(page_title="Experimentation & Causal Platform", layout="wide")
st.sidebar.info(
    "Honesty Note: Warehouse, EDA, 2018 Truckers' Strike DiD & IPW use 100% real Olist data. "
    "The Fast-Ship A/B test is semi-synthetic (known injected effect) to validate statistical accuracy."
)
st.title("Marketplace Overview (Real Olist Data)")
wk = query("SELECT * FROM kpi_weekly")
c1, c2, c3 = st.columns(3)
c1.metric("Total Delivered GMV", f"R$ {wk['gmv'].sum():,.0f}")
c2.metric("Total Delivered Orders", f"{int(wk['orders'].sum()):,}")
c3.metric("Mean Weekly Late Rate", f"{wk['late_rate'].mean():.1%}")
fig = px.line(wk, x="week_start", y="gmv", title="Weekly Delivered GMV (Black Friday 2017 & May 2018 Strike)")
st.plotly_chart(fig, use_container_width=True)
