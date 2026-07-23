"""Mori-Zwanzig Mode Decomposition (MZMD), ported to Python from the Julia
reference `lanl/MoriZwanzigModalDecomposition.jl` (arXiv:2311.09524), read
directly this session (`src/main_mz_algorithm.jl`). Not a re-implementation
from a paper description alone.

Core recursion: given a (possibly rank-reduced) observable time series
X of shape (m, T), compute time-lagged correlation matrices

    C(delta) = X[:, delta : delta + t_win] @ X[:, 0 : t_win].T   for delta = 0..n_ks

then solve, via the same Yule-Walker-style recursion as the Julia reference,
for memory-kernel operators Omega(1)..Omega(n_ks):

    Omega(1) = C(1) @ pinv(C(0))
    Omega(k) = (C(k) - sum_{l=1}^{k-1} Omega(l) @ C(k-l)) @ pinv(C(0))   for k = 2..n_ks

used to predict g(t+1) = sum_{l=1}^{n_ks} Omega(l) @ g(t+1-l). At n_ks=1 this
is a single-step Markovian (DMD-like) transition operator; n_ks > 1 is a
vector-autoregressive memory kernel of order n_ks. Indices below are 0-based
(Python), unlike the 1-based Julia source; each function's docstring notes
the correspondence.
"""

import numpy as np


def obtain_correlations(x: np.ndarray, t_win: int, n_ks: int) -> np.ndarray:
    """C(delta) for delta = 0..n_ks. x: shape (m, T) with T >= t_win + n_ks.
    Returns shape (n_ks + 1, m, m); C[0] = C(0), the equal-time correlation."""
    m = x.shape[0]
    c = np.zeros((n_ks + 1, m, m))
    for delta in range(n_ks + 1):
        c[delta] = x[:, delta : delta + t_win] @ x[:, 0:t_win].T
    return c


def obtain_kernel(c: np.ndarray, n_ks: int) -> np.ndarray:
    """Memory-kernel operators. Returns Omega, shape (n_ks, m, m); Omega[l]
    is Omega(l+1) in the 1-indexed recursion above (Omega[0] = Omega(1))."""
    m = c.shape[1]
    omega = np.zeros((n_ks, m, m))
    c0_inv = np.linalg.pinv(c[0])
    omega[0] = c[1] @ c0_inv
    for k in range(2, n_ks + 1):
        s = np.zeros((m, m))
        for l in range(1, k):
            s += omega[l - 1] @ c[k - l]
        omega[k - 1] = (c[k] - s) @ c0_inv
    return omega


def fit_mzmd(x: np.ndarray, t_win: int, n_ks: int) -> np.ndarray:
    """Fit the memory kernel directly from an observable time series x, shape (m, T)."""
    c = obtain_correlations(x, t_win, n_ks)
    return obtain_kernel(c, n_ks)


def forecast(seed: np.ndarray, omega: np.ndarray, n_steps: int) -> np.ndarray:
    """Forecast n_steps forward given a seed history and fitted memory kernel.

    seed: shape (m, n_ks), the last n_ks known observations (most recent last).
    omega: shape (n_ks, m, m), from fit_mzmd.
    Returns shape (m, n_steps), the forecast g(1)..g(n_steps) continuing after
    the seed (does not include the seed itself).
    """
    n_ks = omega.shape[0]
    m = seed.shape[0]
    history = np.concatenate([seed, np.zeros((m, n_steps))], axis=1)
    for t in range(n_ks - 1, n_ks - 1 + n_steps):
        pred = np.zeros(m)
        for l in range(1, n_ks + 1):
            pred += omega[l - 1] @ history[:, t + 1 - l]
        history[:, t + 1] = pred
    return history[:, n_ks:]
