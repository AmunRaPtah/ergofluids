"""Synthetic subdiffusive trajectory generation.

No raw single-particle-tracking dataset is publicly available for the literature
target (arXiv:1909.05091, see docs/literature-map.md), so Gate 0 and Gate 1 validate
the modeling pipeline against synthetic fractional Brownian motion (fBm) with a
known, chosen Hurst exponent H. For fBm, the mean squared displacement scales as
MSD(t) ~ t^(2H), so a target subdiffusive exponent alpha corresponds to H = alpha / 2.
"""

import numpy as np
from scipy.linalg import toeplitz


def fgn_autocovariance(n: int, hurst: float) -> np.ndarray:
    """First row of the Toeplitz autocovariance matrix of fractional Gaussian noise."""
    k = np.arange(n)
    return 0.5 * (
        np.abs(k + 1) ** (2 * hurst)
        - 2 * np.abs(k) ** (2 * hurst)
        + np.abs(k - 1) ** (2 * hurst)
    )


def generate_fbm_path(n_steps: int, hurst: float, rng: np.random.Generator) -> np.ndarray:
    """One fractional Brownian motion path of length n_steps + 1, starting at 0.

    Built via Cholesky factorization of the fGn covariance matrix. Exact, and fast
    enough at the trajectory lengths used here (a few hundred points); not the
    O(n log n) circulant-embedding method, which is unnecessary at this scale.
    """
    gamma = fgn_autocovariance(n_steps, hurst)
    cov = toeplitz(gamma)
    chol = np.linalg.cholesky(cov)
    increments = chol @ rng.standard_normal(n_steps)
    return np.concatenate([[0.0], np.cumsum(increments)])


def generate_2d_trajectories(
    n_particles: int, n_steps: int, hurst: float, rng: np.random.Generator
) -> np.ndarray:
    """n_particles independent 2D fBm trajectories, shape (n_particles, n_steps + 1, 2)."""
    traj = np.empty((n_particles, n_steps + 1, 2))
    for i in range(n_particles):
        traj[i, :, 0] = generate_fbm_path(n_steps, hurst, rng)
        traj[i, :, 1] = generate_fbm_path(n_steps, hurst, rng)
    return traj


def ensemble_msd(trajectories: np.ndarray, dt: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Ensemble-averaged MSD(t) from the origin, across the particle axis.

    trajectories: shape (n_particles, n_steps + 1, 2). Returns (t, msd), both of
    length n_steps + 1, with t[0] = 0 dropped by the caller before any log-log fit.
    """
    n_steps_plus_1 = trajectories.shape[1]
    t = np.arange(n_steps_plus_1) * dt
    sq_disp = np.sum(trajectories**2, axis=2)  # (n_particles, n_steps + 1)
    msd = sq_disp.mean(axis=0)
    return t, msd
