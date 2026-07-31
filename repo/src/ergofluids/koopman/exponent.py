"""Subdiffusion-exponent estimation from an ensemble MSD(t) curve.

Three original estimators, compared honestly rather than only reporting the best one:

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

Three further estimators, added for Gate 6 (BUILD_PLAN.md) to test whether HODMD's
diagnosed bias generalizes across other established, published DMD-family methods
(not built for this project), rather than being specific to HODMD's own
implementation:

- `hodmd_fb_denoise_exponent`: the identical HODMD configuration used by
  `dmd_denoise_exponent`, plus forward-backward operator averaging (Dawson,
  Hemati, Williams & Rowley, arXiv:1507.02264), isolating whether this
  established bias-correction technique fixes HODMD's bias while keeping
  eigenvalue-based dynamic reconstruction, unlike `ssa`.
- `bopdmd_denoise_exponent`: Bagging, Optimized DMD (Askham & Kutz, SIAM J.
  Appl. Dyn. Syst. 17, 2018; Sashidhar & Kutz, arXiv:2107.10878, 2021), fit on
  the same Hankel-embedded curve `ssa` uses, in place of `ssa`'s low-rank SVD
  reconstruction step.
- `subspace_denoise_exponent`: Subspace DMD (Takeishi, Kawahara & Yairi, Phys.
  Rev. E 96, 033310, 2017), a subspace-identification method with a different
  theoretical foundation from regression-based DMD, fit the same way.
"""

import warnings

import numpy as np
from pydmd import BOPDMD, HODMD, SubspaceDMD

# Fallback-to-loglog counts for the Gate 6 estimators, keyed by estimator name.
# Gate 6's pre-registration (BUILD_PLAN.md) commits to reporting these per
# condition rather than absorbing them silently into the coverage count;
# callers should call reset_fallback_counts() before each condition and read
# fallback_counts() after.
FALLBACK_COUNTS: dict[str, int] = {"hodmd_fb": 0, "bopdmd": 0, "subspace": 0}


def reset_fallback_counts() -> None:
    for key in FALLBACK_COUNTS:
        FALLBACK_COUNTS[key] = 0


def fallback_counts() -> dict[str, int]:
    return dict(FALLBACK_COUNTS)


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


def hodmd_fb_denoise_exponent(t: np.ndarray, msd: np.ndarray, d: int = 10, svd_rank: int = 6) -> float:
    """Same HODMD configuration as `dmd_denoise_exponent`, plus forward-backward
    operator averaging (Dawson et al., arXiv:1507.02264). Gate 6 (BUILD_PLAN.md):
    isolates whether this established bias-correction technique fixes HODMD's
    diagnosed bias (Gate 0/0b) while keeping eigenvalue-based dynamic
    reconstruction, unlike `ssa`. Falls back to `loglog_fit_exponent` on any fit
    exception, per Gate 6's pre-registered numerical note."""
    mask = t > 0
    log_t = np.log(t[mask])
    log_msd = np.log(msd[mask])
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            hodmd = HODMD(svd_rank=svd_rank, d=d, opt=True, forward_backward=True)
            hodmd.fit(log_msd.reshape(1, -1))
            reconstructed = np.real(hodmd.reconstructed_data[0])
        n = min(len(reconstructed), len(log_t))
        if not np.all(np.isfinite(reconstructed[:n])):
            raise ValueError("non-finite HODMD(forward_backward) reconstruction")
        slope, _ = np.polyfit(log_t[:n], reconstructed[:n], 1)
        return float(slope)
    except Exception:
        FALLBACK_COUNTS["hodmd_fb"] += 1
        return loglog_fit_exponent(t, msd)


def _hankel_dmd_reconstruct(y: np.ndarray, dmd_obj, window: int) -> np.ndarray:
    """Fit an already-configured PyDMD estimator on the Hankel matrix of y and
    reassemble its reconstruction to a 1D curve by anti-diagonal averaging, the
    same convention `_hankel_svd_denoise` uses. `dmd_obj` must expose `.fit` and
    `.reconstructed_data`; `BOPDMD` additionally requires an explicit time
    vector (its continuous-time eigenvalue formulation needs one), so it is
    detected and handled here rather than in each caller."""
    n = len(y)
    k = n - window + 1
    hankel = np.array([y[i : i + window] for i in range(k)]).T  # (window, k)
    if isinstance(dmd_obj, BOPDMD):
        dmd_obj.fit(hankel, np.arange(k, dtype=float))
    else:
        dmd_obj.fit(hankel)
    reconstructed = np.real(dmd_obj.reconstructed_data)

    recon = np.zeros(n)
    counts = np.zeros(n)
    for i in range(window):
        for j in range(k):
            recon[i + j] += reconstructed[i, j]
            counts[i + j] += 1
    return recon / counts


def bopdmd_denoise_exponent(t: np.ndarray, msd: np.ndarray, window: int = 20, rank: int = 4) -> float:
    """Bagging, Optimized DMD (Askham & Kutz 2018; Sashidhar & Kutz,
    arXiv:2107.10878), fit on the same Hankel-embedded curve `ssa` uses, in
    place of `ssa`'s low-rank SVD reconstruction step. Gate 6 (BUILD_PLAN.md).
    Falls back to `loglog_fit_exponent` on any fit exception or non-finite
    reconstruction, per Gate 6's pre-registered numerical note (occasional
    variable-projection convergence warnings were observed in pre-registration
    smoke testing, with no exceptions or non-finite output across 40 stress
    trials)."""
    mask = t > 0
    log_t = np.log(t[mask])
    log_msd = np.log(msd[mask])
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bop = BOPDMD(svd_rank=rank, num_trials=0)
            reconstructed = _hankel_dmd_reconstruct(log_msd, bop, window=window)
        if not np.all(np.isfinite(reconstructed)):
            raise ValueError("non-finite BOPDMD reconstruction")
        slope, _ = np.polyfit(log_t, reconstructed, 1)
        return float(slope)
    except Exception:
        FALLBACK_COUNTS["bopdmd"] += 1
        return loglog_fit_exponent(t, msd)


def subspace_denoise_exponent(t: np.ndarray, msd: np.ndarray, window: int = 20, rank: int = 4) -> float:
    """Subspace DMD (Takeishi, Kawahara & Yairi, Phys. Rev. E 96, 033310, 2017),
    fit on the same Hankel-embedded curve `ssa` uses, in place of `ssa`'s
    low-rank SVD reconstruction step. Gate 6 (BUILD_PLAN.md). Falls back to
    `loglog_fit_exponent` on any fit exception or non-finite reconstruction."""
    mask = t > 0
    log_t = np.log(t[mask])
    log_msd = np.log(msd[mask])
    try:
        sub = SubspaceDMD(svd_rank=rank)
        reconstructed = _hankel_dmd_reconstruct(log_msd, sub, window=window)
        if not np.all(np.isfinite(reconstructed)):
            raise ValueError("non-finite SubspaceDMD reconstruction")
        slope, _ = np.polyfit(log_t, reconstructed, 1)
        return float(slope)
    except Exception:
        FALLBACK_COUNTS["subspace"] += 1
        return loglog_fit_exponent(t, msd)
