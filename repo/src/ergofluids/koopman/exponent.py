"""Subdiffusion-exponent estimation from an ensemble MSD(t) curve.

Three estimators, compared honestly rather than only reporting the best one:

- `loglog_fit_exponent`: the standard, direct method (OLS on log MSD vs log t).
- `dmd_denoise_exponent`: use PyDMD's HODMD to reconstruct a delay-embedded,
  denoised version of log(MSD(t)) first, then apply the same OLS slope fit to
  the reconstructed curve. Diagnosed in docs/BUILD_PLAN.md (Gate 0) as carrying
  a systematic negative bias that grows with t: HODMD reconstructs by forward-
  simulating its fitted eigenvalue decomposition, which compounds error for a
  signal that is not itself a finite sum of exponentials in real time. Kept
  here for the record and for comparison, not as the recommended estimator.
- `ssa_denoise_exponent`: uses the same delay-embedding (Hankel matrix)
  construction as HODMD, but reconstructs via a plain low-rank SVD projection
  of the Hankel matrix followed by anti-diagonal (Hankelization) averaging,
  classical Singular Spectrum Analysis, instead of HODMD's eigenvalue-based
  forward simulation. This is not a Koopman-eigenvalue reconstruction and
  should not be described as one; it is a denoising step built on the same
  delay-embedding machinery. Diagnosed to have uniformly small reconstruction
  error with no growth over the time window (see Gate 0b in BUILD_PLAN.md).
"""

import numpy as np
from pydmd import HODMD


def loglog_fit_exponent(t: np.ndarray, msd: np.ndarray) -> float:
    mask = t > 0
    slope, _ = np.polyfit(np.log(t[mask]), np.log(msd[mask]), 1)
    return float(slope)


def dmd_denoise_exponent(t: np.ndarray, msd: np.ndarray, d: int = 10, svd_rank: int = 6) -> float:
    """Reconstruct log(MSD(t)) via HODMD, then fit the exponent on the reconstruction."""
    mask = t > 0
    log_t = np.log(t[mask])
    log_msd = np.log(msd[mask])

    snapshots = log_msd.reshape(1, -1)
    hodmd = HODMD(svd_rank=svd_rank, d=d, opt=True)
    hodmd.fit(snapshots)
    reconstructed = np.real(hodmd.reconstructed_data[0])

    n = min(len(reconstructed), len(log_t))
    slope, _ = np.polyfit(log_t[:n], reconstructed[:n], 1)
    return float(slope)


def _hankel_svd_denoise(y: np.ndarray, window: int, rank: int) -> np.ndarray:
    """Low-rank SVD projection of the Hankel matrix of y, reassembled by
    anti-diagonal averaging (classical Singular Spectrum Analysis)."""
    n = len(y)
    k = n - window + 1
    hankel = np.array([y[i : i + window] for i in range(k)]).T  # (window, k)
    u, s, vt = np.linalg.svd(hankel, full_matrices=False)
    hankel_hat = (u[:, :rank] * s[:rank]) @ vt[:rank, :]

    recon = np.zeros(n)
    counts = np.zeros(n)
    for i in range(window):
        for j in range(k):
            recon[i + j] += hankel_hat[i, j]
            counts[i + j] += 1
    return recon / counts


def ssa_denoise_exponent(t: np.ndarray, msd: np.ndarray, window: int = 20, rank: int = 4) -> float:
    """Hankel-SVD-denoise log(MSD(t)), then fit the exponent on the denoised curve."""
    mask = t > 0
    log_t = np.log(t[mask])
    log_msd = np.log(msd[mask])

    reconstructed = _hankel_svd_denoise(log_msd, window=window, rank=rank)
    slope, _ = np.polyfit(log_t, reconstructed, 1)
    return float(slope)
