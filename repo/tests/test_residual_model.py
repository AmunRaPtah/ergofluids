"""Tests for the residual/classifier model: a fast synthetic check on the
model-fitting logic itself, plus a check against the actual committed sweep
results (data/network_sim_sweep.csv, produced by scripts/run_network_sweep.py)
confirming the residual model still beats the physics baseline out of
sample. The second test does not re-run the (multi-minute) simulation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ergofluids.network_sim.residual_model import add_derived_columns, leave_one_out_validate

REPO_ROOT = Path(__file__).resolve().parents[1]
SWEEP_CSV = REPO_ROOT / "data" / "network_sim_sweep.csv"


def _fabricated_sweep_df(n: int = 30) -> pd.DataFrame:
    """A small synthetic dataset with a known, learnable adhesion-driven
    residual (exponent = 1 - 0.05 * adhesion_depth + small noise) and no
    dependence on aspect_ratio or confinement, so the residual model should
    clearly beat a baseline that always predicts 1.0, without needing the
    real (slow) simulator."""
    rng = np.random.default_rng(0)
    adhesion = rng.uniform(0, 4, size=n)
    aspect = rng.choice([1.0, 3.0], size=n)
    radius = rng.uniform(0.2, 0.9, size=n)
    pore = np.full(n, 2.0)
    exponent = 1.0 - 0.05 * adhesion + rng.normal(0, 0.01, size=n)
    return pd.DataFrame(
        {
            "n_fibers": 300,
            "particle_radius": radius,
            "adhesion_depth": adhesion,
            "aspect_ratio": aspect,
            "mean_pore_radius": pore,
            "simulated_exponent": exponent,
            "baseline_exponent": 1.0,
            "residual": exponent - 1.0,
        }
    )


def test_residual_model_beats_baseline_on_synthetic_data():
    df = _fabricated_sweep_df()
    val = leave_one_out_validate(df)
    assert val.residual_model_mae < val.baseline_mae


def test_add_derived_columns_regime_binning():
    df = _fabricated_sweep_df()
    out = add_derived_columns(df)
    assert "confinement" in out.columns
    assert "regime" in out.columns
    assert set(out["regime"].cat.categories) == {"caged", "hindered", "normal"}


def test_committed_sweep_residual_model_beats_baseline():
    if not SWEEP_CSV.exists():
        import pytest

        pytest.skip(f"{SWEEP_CSV} not present; run scripts/run_network_sweep.py to regenerate")
    df = pd.read_csv(SWEEP_CSV)
    val = leave_one_out_validate(df)
    assert val.residual_model_mae < val.baseline_mae
    assert val.classifier_accuracy >= val.classifier_baseline_accuracy
