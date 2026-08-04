"""Fit a power-law exponent to digitized (x, y, reported_error,
digitization_error) points, with a bootstrap-propagated confidence interval.

Uses the same error-propagation convention Gate 4/5 used by hand
(docs/gate-result-phase3-realdata.md, scripts/run_gate4.py): combine
reported_error and digitization_error in quadrature per point, perturb y by
a Gaussian draw with that combined sigma, refit, repeat, and take the 95%
percentile CI. Generalized here so it applies to any digitized curve, not
just the two Burla et al. panels Gate 4/5 were built around.
"""

from __future__ import annotations

import numpy as np

from ergofluids.koopman.exponent import loglog_fit_exponent, ssa_denoise_exponent

_ESTIMATORS = {"ssa": ssa_denoise_exponent, "loglog": loglog_fit_exponent}


def estimate_exponent(
    points: list[tuple[float, float, float, float, float]],
    estimator: str = "ssa",
    n_boot: int = 2000,
    seed: int = 0,
) -> dict:
    """`points` is the (x, y, reported_error, digitization_error,
    x_digitization_error) 5-tuple list `digitize.common.extract_curve`
    returns. `estimator` selects the fit function: `ssa` is the recommended
    one (unbiased per Gate 0c/Gate 6); `loglog` is the plain OLS baseline.
    """
    if estimator not in _ESTIMATORS:
        raise ValueError(f"unknown estimator {estimator!r}, choose from {sorted(_ESTIMATORS)}")
    if len(points) < 4:
        raise ValueError(f"need at least 4 points to fit an exponent, got {len(points)}")

    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    reported_err = np.array([p[2] for p in points])
    dig_err = np.array([p[3] for p in points])
    sigma = np.sqrt(reported_err**2 + dig_err**2)
    fallback_sigma = np.median(sigma[sigma > 0]) if np.any(sigma > 0) else 0.01 * np.median(np.abs(y))
    sigma = np.where(sigma > 0, sigma, fallback_sigma)

    fit_fn = _ESTIMATORS[estimator]
    point_estimate = fit_fn(x, y)

    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        y_perturbed = y + rng.normal(0.0, sigma)
        y_perturbed = np.clip(y_perturbed, 1e-12, None)  # guard log(y) against non-positive draws
        boot[i] = fit_fn(x, y_perturbed)

    ci_lo, ci_hi = (float(v) for v in np.percentile(boot, [2.5, 97.5]))
    return {
        "estimator": estimator,
        "point_estimate": float(point_estimate),
        "ci95_low": ci_lo,
        "ci95_high": ci_hi,
        "n_points": len(points),
        "n_boot": n_boot,
    }
