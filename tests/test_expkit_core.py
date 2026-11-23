"""Automated Unit, Property (Hypothesis), Causal, and Simulation Tests."""
import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from expkit.srm import srm_test
from expkit.cuped import cuped_adjust, welch_test
from expkit.ratio import ratio_diff
from expkit.guardrails import non_inferiority_test
from expkit.sequential import obrien_fleming_boundaries
from expkit.causal.synth import synth_effect
from expkit.causal.ipw import aipw_ate
from expkit.causal.sensitivity import e_value
from scripts.run_simulations import simulate_experiment


def test_srm_catches_broken_split():
    assert srm_test({"control": 500, "treatment": 500}, {"control": 0.5, "treatment": 0.5})["srm_detected"] is False
    assert srm_test({"control": 580, "treatment": 420}, {"control": 0.5, "treatment": 0.5})["srm_detected"] is True


@settings(max_examples=100, deadline=None)
@given(st.integers(30, 300), st.floats(0.0, 0.95))
def test_cuped_never_increases_variance(n, rho):
    rng = np.random.default_rng(n)
    x = rng.normal(size=n)
    y = rho * x + np.sqrt(1 - rho ** 2) * rng.normal(size=n)
    y_adj, _ = cuped_adjust(y, x)
    assert np.var(y_adj, ddof=1) <= np.var(y, ddof=1) + 1e-12


def test_ratio_delta_recovers_zero_diff():
    rng = np.random.default_rng(12)
    den_t = rng.integers(1, 20, 400); num_t = rng.binomial(den_t, 0.10)
    den_c = rng.integers(1, 20, 400); num_c = rng.binomial(den_c, 0.10)
    res = ratio_diff(num_t, den_t, num_c, den_c)
    assert res["ci_lo"] <= 0.0 <= res["ci_hi"]


def test_guardrails_and_obf():
    assert non_inferiority_test(0.002, 0.002, 0.010, "higher")["status"] == "PASS"
    assert non_inferiority_test(0.005, 0.004, 0.010, "higher")["status"] == "INCONCLUSIVE"
    assert non_inferiority_test(0.020, 0.003, 0.010, "higher")["status"] == "BREACH"
    bounds = obrien_fleming_boundaries(6, alpha=0.05)
    assert bounds[0]["z_boundary"] > 4.0 and 1.9 < bounds[-1]["z_boundary"] < 2.5


def test_synth_and_aipw_recover_truth():
    rng = np.random.default_rng(7)
    donors = rng.normal(100, 5, size=(30, 6))
    w_true = np.array([0.4, 0.3, 0.3, 0.0, 0.0, 0.0])
    y_t = donors @ w_true + np.r_[np.zeros(20), np.full(10, 15.0)]
    assert abs(synth_effect(y_t, donors, T0=20)["post_mean_gap"] - 15.0) < 0.5
    X = rng.normal(size=(600, 2)); p = 1 / (1 + np.exp(-0.6 * X[:, 0]))
    t = rng.binomial(1, p); y = 2.0 * t + 1.5 * X[:, 0] + rng.normal(size=600)
    assert abs(aipw_ate(X, t, y)["ate"] - 2.0) < 0.35
    assert abs(e_value(1.3) - 1.92495) < 1e-3


@pytest.mark.slow
def test_aa_false_positive_and_coverage():
    y = np.random.default_rng(5).lognormal(mean=6, sigma=1, size=400)
    aa = simulate_experiment(y, n_sims=2000, effect=0.0)
    ab = simulate_experiment(y, n_sims=2000, effect=0.06)
    assert 0.035 < aa["reject_rate"] < 0.065
    assert 0.92 < ab["coverage"] < 0.98
