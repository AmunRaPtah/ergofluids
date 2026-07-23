"""Paired-bootstrap harness for Gate 2 (docs/BUILD_PLAN.md): does the ported
MZMD memory kernel forecast the observed variable of a partially-hidden linear
system better than a memoryless (n_ks=1) fit?
"""

import numpy as np

from ergofluids.mz.mzmd import fit_mzmd, forecast


def per_trajectory_rmse(
    x: np.ndarray, t_win: int, n_ks: int, horizon: int
) -> float:
    """x: shape (1, T) observed scalar series. Fits on [0, t_win + n_ks), forecasts
    `horizon` steps starting right after, compares to the true continuation."""
    omega = fit_mzmd(x[:, : t_win + n_ks], t_win=t_win, n_ks=n_ks)
    seed = x[:, t_win - n_ks : t_win]
    fc = forecast(seed, omega, n_steps=horizon)
    true_future = x[:, t_win : t_win + horizon]
    return float(np.sqrt(np.mean((fc - true_future) ** 2)))


def paired_bootstrap_ci(
    diffs: np.ndarray, n_boot: int = 2000, ci: float = 0.95, rng: np.random.Generator | None = None
) -> tuple[float, float, float]:
    """Percentile bootstrap CI on the mean paired difference."""
    if rng is None:
        rng = np.random.default_rng()
    n = len(diffs)
    point = float(diffs.mean())
    boot_means = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_means[b] = diffs[idx].mean()
    alpha = 1 - ci
    lo, hi = np.percentile(boot_means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return point, float(lo), float(hi)
