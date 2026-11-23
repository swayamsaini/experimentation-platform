"""Page 2: Customer Retention Cohorts & Fulfillment Funnel."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import streamlit as st
from db import query

st.title("Customer Retention Cohorts & Fulfillment Funnel")
coh = query("SELECT * FROM cohorts")
piv = coh.pivot(index="cohort_month", columns="month_offset", values="active_customers")
ret = piv.div(piv[0], axis=0) * 100
st.plotly_chart(px.imshow(ret.round(2), text_auto=True, title="Monthly Repeat Retention (%)"), use_container_width=True)
st.subheader("Fulfillment Funnel by Customer State")
st.dataframe(query("SELECT * FROM funnel ORDER BY created DESC"), use_container_width=True)
