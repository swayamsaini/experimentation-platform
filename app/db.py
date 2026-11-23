"""Shared read-only DuckDB connection helper for all 6 Streamlit pages."""
import duckdb
import pandas as pd
import streamlit as st


@st.cache_resource
def get_con():
    return duckdb.connect("data/exports/results.duckdb", read_only=True)


@st.cache_data(ttl=3600)
def query(sql: str) -> pd.DataFrame:
    return get_con().execute(sql).df()
