# Experimentation & Causal Impact Platform

End-to-end analytics warehouse, governed metrics layer, statistical A/B engine, quasi-experimental causal inference suite, and 6-page decision dashboard built on 100K Brazilian e-commerce orders (Olist).

**[Live 6-Page Streamlit Dashboard](<YOUR-STREAMLIT-URL>)** | **[1-Page Decision Memo](docs/Fast_Ship_Decision_Memo.pdf)**

## Integrity & Honesty Note
- **100% Real Olist Data:** dbt star-schema warehouse, EDA (cohorts, funnel, RFM), 2018 Brazilian Truckers' Strike Difference-in-Differences, and observational propensity analysis.
- **Semi-Synthetic (Known Ground Truth):** Fast-Ship Programme seller A/B test (known heterogeneous effects injected onto real seller baselines to validate false-positive rates, CI coverage, and power).

## Verified Results (Commit `ee97b21`)
- **Governed Warehouse:** `63` dbt models & `41` data tests passing (`0` errors); **R$ 13,221,498.11** delivered GMV across **97,819 orders** verified via 3-route reconciliation (`raw == fct_order_items == mart_seller_week`).
- **A/B Testing Engine (`src/expkit`):** `626` eligible sellers (`328` T / `298` C); **SRM PASS** (`p = 0.2305`); **CUPED variance reduction of 63.97%** (~2.8x effective sample); achieved MDE `24.99%` (`est = -R$ 18.27`, 95% CI `[-292.44, +255.90]`, `p = 0.896`) → **Decision: Expand Targeted Test**.
- **Causal Inference (`src/expkit/causal`):** May 2018 Truckers' Strike DiD estimated **+0.31 extra delivery days** on interstate orders (seller-state + week FE, seller-clustered SEs, event-study pre-trends & placebo checks).
- **Automated Testing:** `5/5` unit, Hypothesis property, guardrail, and causal recovery tests passing in `pytest`.

## Tech Stack
`DuckDB` · `dbt Core` · `Python 3.12` · `SciPy / statsmodels / EconML` · `Plotly` · `Streamlit` · `pytest + Hypothesis` · `GitHub Actions`

## Quickstart
```bash
pip install -e ".[dev]"
python scripts/download_data.py
cd dbt && dbt deps && dbt build --profiles-dir . && cd ..
python scripts/build_experiment.py
python scripts/export_results.py
python -m pytest -m "not slow" -q
streamlit run app/Home.py
