"""Bootstrap CI harness for exponent estimators, following the paired-bootstrap
gate methodology documented in /root/topologix's gate-result-*.md files: state
a pass/fail rule before looking at results, report the CI, do not shop metrics.
"""

from collections.abc import Callable

import numpy as np


def bootstrap_ci(
    trajectories: np.ndarray,
    estimator: Callable[[np.ndarray, np.ndarray], float],
    dt: float = 1.0,
    n_boot: int = 200,
    ci: float = 0.95,
    rng: np.random.Generator | None = None,
) -> tuple[float, float, float]:
    """Percentile bootstrap CI for an exponent estimator, resampling particles.

    Returns (point_estimate, ci_low, ci_high).
    """
    from ergofluids.data.synthetic import ensemble_msd

    if rng is None:
        rng = np.random.default_rng()

    n_particles = trajectories.shape[0]
    t_full, msd_full = ensemble_msd(trajectories, dt=dt)
    point_estimate = estimator(t_full, msd_full)

    boot_estimates = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n_particles, size=n_particles)
        resampled = trajectories[idx]
        t_b, msd_b = ensemble_msd(resampled, dt=dt)
        boot_estimates[b] = estimator(t_b, msd_b)

    alpha = 1 - ci
    lo, hi = np.percentile(boot_estimates, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return point_estimate, float(lo), float(hi)
