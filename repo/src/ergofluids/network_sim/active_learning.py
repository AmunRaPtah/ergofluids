"""Active-learning "next-best-experiment" recommender: given a small set of
a formulation lab's own observed (candidate descriptors -> measured
exponent) data points, plus a pool of untested candidates, recommend which
candidate to test next.

This is a different product bet from `residual_model.py`'s zero-shot
predictor: instead of trying to predict transport behavior from nothing
(the problem that failed twice under the Koopman/Mori-Zwanzig approach, and
that `residual_model.py` has only simulation-only, not real-data, support
for), this tool assumes a lab already has a handful of real pilot
measurements and asks a narrower, more tractable question: which untested
candidate would most reduce uncertainty (or best hit a target), given what
is already known. It does not need the zero-shot problem to be solved to be
useful.

Uses a Gaussian Process, not the random forests in `residual_model.py`,
because GP regression gives a principled predictive mean and standard
deviation per candidate, the standard tool for uncertainty-driven
acquisition (and the same model class Gurel, Leenstra & Giuntoli 2025,
Soft Matter, doi:10.1039/d5sm00851d, used for the closely related problem of
predicting confined-mobility metrics from particle/network descriptors).

Real (lab-provided) observations and simulated (network_sim sweep)
observations can be combined, with per-point noise (`alpha` in
`GaussianProcessRegressor`) set lower for real points and higher for
simulated ones, so the model trusts real data more without discarding the
broader simulated coverage entirely. Given the real-data check in
`../../../docs/gate-result-network-sim-real-data-check.md` (simulated data's
transfer to real systems is only premise-level supported, not validated),
the default simulated-point noise is set high enough that a handful of real
points can dominate the fit in their local region of feature space.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

FEATURE_COLUMNS = ["adhesion_depth", "aspect_ratio", "confinement"]

REAL_POINT_NOISE = 0.005  # low: trust real measurements strongly
SIMULATED_POINT_NOISE = 0.08  # high: simulated points are a weak prior only


@dataclass
class ObservedPoint:
    adhesion_depth: float
    aspect_ratio: float
    confinement: float
    exponent: float
    source: str = "real"  # "real" | "simulated"


def _to_arrays(points: list[ObservedPoint]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    X = np.array([[p.adhesion_depth, p.aspect_ratio, p.confinement] for p in points])
    y = np.array([p.exponent for p in points])
    noise = np.array([REAL_POINT_NOISE if p.source == "real" else SIMULATED_POINT_NOISE for p in points])
    return X, y, noise


def fit_gp(points: list[ObservedPoint]) -> GaussianProcessRegressor:
    """Length-scale bounds are set to a range sensible for this feature
    space (adhesion_depth ~0-4, aspect_ratio ~1-3, confinement ~0-1), not
    left unconstrained: with very few observed points (the common case for
    this tool, by design), an unconstrained optimizer can land on a
    degenerate boundary solution, e.g. a length scale so short that
    everything looks equally "far," making uncertainty-sampling scores
    uninformative. This was caught by a failing unit test
    (test_recommend_next_uncertainty_favors_unexplored_region) before being
    fixed here, not assumed safe."""
    if len(points) < 2:
        raise ValueError("need at least 2 observed points to fit a Gaussian process")
    X, y, noise = _to_arrays(points)
    kernel = ConstantKernel(1.0, constant_value_bounds=(1e-2, 1e2)) * RBF(
        length_scale=[1.0, 1.0, 0.3], length_scale_bounds=(0.2, 20.0)
    ) + WhiteKernel(noise_level=1e-3, noise_level_bounds=(1e-5, 1e-1))
    gp = GaussianProcessRegressor(kernel=kernel, alpha=noise**2, normalize_y=True, n_restarts_optimizer=5)
    gp.fit(X, y)
    return gp


def sweep_csv_to_simulated_points(sweep_df: pd.DataFrame) -> list[ObservedPoint]:
    df = sweep_df.copy()
    df["confinement"] = df["particle_radius"] / df["mean_pore_radius"]
    return [
        ObservedPoint(
            adhesion_depth=row.adhesion_depth,
            aspect_ratio=row.aspect_ratio,
            confinement=row.confinement,
            exponent=row.simulated_exponent,
            source="simulated",
        )
        for row in df.itertuples()
    ]


def recommend_next(
    gp: GaussianProcessRegressor,
    candidate_pool: pd.DataFrame,
    strategy: str = "uncertainty",
    target: float | None = None,
    beta: float = 1.0,
) -> pd.DataFrame:
    """Rank `candidate_pool` (must have FEATURE_COLUMNS) by acquisition
    score, highest (most worth testing next) first.

    `strategy`:
    - "uncertainty": pure exploration, score = predictive std. Best default
      when the goal is characterizing the design space with the fewest
      experiments, not presuming what a "good" outcome looks like (a faster
      transport rate is not universally desirable, e.g. for sustained-release
      formulations).
    - "target": score = -(|predicted_mean - target| ) + beta * std, an
      expected-improvement-style trade-off between candidates predicted
      close to a desired exponent and candidates still uncertain enough to
      be worth checking. Requires `target`.
    """
    X = candidate_pool[FEATURE_COLUMNS].to_numpy()
    mean, std = gp.predict(X, return_std=True)

    out = candidate_pool.copy()
    out["predicted_exponent"] = mean
    out["predicted_std"] = std

    if strategy == "uncertainty":
        out["acquisition_score"] = std
    elif strategy == "target":
        if target is None:
            raise ValueError('strategy="target" requires a target exponent value')
        out["acquisition_score"] = -np.abs(mean - target) + beta * std
    else:
        raise ValueError(f"unknown strategy: {strategy!r}")

    return out.sort_values("acquisition_score", ascending=False).reset_index(drop=True)
