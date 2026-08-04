"""Validates the active-learning recommender the honest way available before
any real lab data exists: does uncertainty-sampling acquisition reduce
held-out prediction error faster than random sampling, using the
network_sim sweep as a synthetic ground-truth oracle (queryable, but its
values withheld from the model until "tested")? This does not validate the
tool against real data (see docs/gate-result-network-sim-real-data-check.md
for why that has not been done), only that the acquisition strategy itself
does what active learning is supposed to do.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ergofluids.network_sim.active_learning import FEATURE_COLUMNS, ObservedPoint, fit_gp, recommend_next

REPO_ROOT = Path(__file__).resolve().parents[1]
SWEEP_CSV = REPO_ROOT / "data" / "network_sim_sweep.csv"


def _load_pool() -> pd.DataFrame:
    df = pd.read_csv(SWEEP_CSV)
    df["confinement"] = df["particle_radius"] / df["mean_pore_radius"]
    return df


def _held_out_mae(gp, held_out: pd.DataFrame) -> float:
    X = held_out[FEATURE_COLUMNS].to_numpy()
    y = held_out["simulated_exponent"].to_numpy()
    pred, _ = gp.predict(X, return_std=True)
    return float(np.mean(np.abs(pred - y)))


def _run_loop(df: pd.DataFrame, n_initial: int, n_queries: int, strategy: str, seed: int) -> float:
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(df))
    observed_idx = list(idx[:n_initial])
    pool_idx = list(idx[n_initial:])

    def make_points(indices):
        return [
            ObservedPoint(
                adhesion_depth=df.iloc[i]["adhesion_depth"],
                aspect_ratio=df.iloc[i]["aspect_ratio"],
                confinement=df.iloc[i]["confinement"],
                exponent=df.iloc[i]["simulated_exponent"],
                source="real",  # treat sweep rows as the "measured" oracle for this synthetic test
            )
            for i in indices
        ]

    for _ in range(n_queries):
        pool_df = df.iloc[pool_idx]

        if strategy == "random":
            chosen = rng.choice(pool_idx)
        elif strategy == "uncertainty":
            gp = fit_gp(make_points(observed_idx))
            ranked = recommend_next(gp, pool_df, strategy="uncertainty")
            # ranked is sorted by acquisition score; map the top row back to
            # its original df index by matching feature values (recommend_next
            # returns a reset-index copy, not the original index).
            top_row = ranked.iloc[0]
            match = pool_df[
                (pool_df["adhesion_depth"] == top_row["adhesion_depth"])
                & (pool_df["aspect_ratio"] == top_row["aspect_ratio"])
                & (pool_df["confinement"] == top_row["confinement"])
            ]
            chosen = match.index[0]
        else:
            raise ValueError(f"unknown strategy: {strategy!r}")

        observed_idx.append(chosen)
        pool_idx.remove(chosen)

    final_gp = fit_gp(make_points(observed_idx))
    return _held_out_mae(final_gp, df.iloc[pool_idx])


@pytest.mark.skipif(not SWEEP_CSV.exists(), reason="run scripts/run_network_sweep.py first")
def test_uncertainty_sampling_beats_random_on_average():
    df = _load_pool()
    n_initial, n_queries = 6, 8
    seeds = range(5)

    uncertainty_errors = [_run_loop(df, n_initial, n_queries, "uncertainty", s) for s in seeds]
    random_errors = [_run_loop(df, n_initial, n_queries, "random", s) for s in seeds]

    assert np.mean(uncertainty_errors) < np.mean(random_errors), (
        f"uncertainty sampling MAE {np.mean(uncertainty_errors):.4f} should beat "
        f"random sampling MAE {np.mean(random_errors):.4f} on average"
    )


def test_recommend_next_uncertainty_favors_unexplored_region():
    """A tighter, deterministic unit check: with observed points clustered
    at low adhesion, a candidate at high adhesion (far from any observation)
    should score higher under uncertainty sampling than a candidate right
    next to an existing observation."""
    points = [
        ObservedPoint(adhesion_depth=0.0, aspect_ratio=1.0, confinement=0.2, exponent=0.98, source="real"),
        ObservedPoint(adhesion_depth=0.1, aspect_ratio=1.0, confinement=0.2, exponent=0.97, source="real"),
        ObservedPoint(adhesion_depth=0.2, aspect_ratio=1.0, confinement=0.25, exponent=0.96, source="real"),
    ]
    gp = fit_gp(points)
    candidates = pd.DataFrame(
        {
            "adhesion_depth": [0.05, 4.0],
            "aspect_ratio": [1.0, 1.0],
            "confinement": [0.2, 0.2],
        }
    )
    ranked = recommend_next(gp, candidates, strategy="uncertainty")
    assert ranked.iloc[0]["adhesion_depth"] == 4.0, "the far, unexplored candidate should rank first"
