"""Gate 4: real-data test (literature-digitized, not synthetic).

Pre-registered protocol and pass/fail criterion, written before this script
was run at full scale (see docs/gate-result-phase3-realdata.md for the
identical text, plus the result). Do not change the criterion or parameters
below after seeing the printed output; if a re-run is ever needed, do it as
a new, separately labeled gate.

Data: digitized points from Figure 4a (ISF vs tq^2) and Supplementary
Figure S14a (MSD vs Delta t) of arXiv:1909.05091, produced by
scripts/digitize_fig4a.py and scripts/digitize_s14a.py. Three curves shared
by both panels are used: composite (1 mg/mL collagen + 2 mg/mL hyaluronan),
2 mg/mL hyaluronan alone, and 1 mg/mL collagen alone. The S14a-only
"2 mg/mL collagen" curve is deliberately excluded: it is not part of the
main-text three-way contrast Figure 4a makes, and the paper's own
supplementary scatter (S14c/d) reports an intermediate exponent for it
that would confuse a test built around "composite vs the two pure networks
Figure 4a highlights."

Primary test, on the S14a MSD curves (the shape `loglog_fit_exponent` and
`ssa_denoise_exponent` are built for): for each curve, fit a local
log-log slope in an EARLY window (bottom 40% of that curve's own
log10(Delta t) range) and a LATE window (top 40% of the same range), using
both surviving estimators (`loglog`, `ssa`; `dmd` is excluded, retired per
Gate 0/0b/0c, not rehabilitated here). Propagate the digitized error bars
(reported_error and digitization_error, combined in quadrature per point
for this propagation step only; the CSVs keep them as separate columns)
via a 2000-draw Gaussian-perturbation bootstrap: perturb each point's y by
N(0, sigma), refit, repeat, and take the 95% percentile CI of quantities of
interest.

Pass criterion:
  (A) Composite: the 95% CI of (slope_early - slope_late) is entirely
      positive (excludes zero) for BOTH loglog and ssa. This operationalizes
      "the local slope measurably flattens toward the plateau region."
  (B) Hyaluronan AND 1 mg/mL collagen: the 95% CI lower bound of slope_late
      exceeds 0.5, for BOTH loglog and ssa. This operationalizes "stays
      close to 1" as "does not drop into clearly subdiffusive territory",
      a looser bar than CI subset of [0.9, 1.1] chosen because digitized
      data over a short Delta t window (at most ~1 decade for these two
      curves) is noisier than the synthetic curves Gate 0/1 used.
Fail if (A) fails for composite under either estimator, or (B) fails for
either pure-component curve under either estimator.

Secondary, descriptive check (not part of the pass/fail arithmetic: the
exponent estimators are built for power-law MSD curves, and ISF is a
bounded, non-power-law quantity, so it is not run through them): on the
Fig 4a ISF curves, does composite's late-window (top 40% of log10(tq^2))
mean ISF sit measurably above hyaluronan's and collagen's, within the same
error-propagated bootstrap? This directly probes the paper's own framing of
the composite plateau as a non-decaying caged fraction, distinct from the
MSD slope test above.

Explicitly not tested here: the Mori-Zwanzig memory kernel (`src/ergofluids/mz`)
is not evaluated against this or any real data in this gate. No public
per-trajectory time series exists for arXiv:1909.05091 (only these two
derived, digitized summary curves), and MZMD requires that shape of data.
The MZMD memory-kernel result remains the synthetic-only finding from Gate 2
and Gate 3; nothing here extends or re-tests it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from ergofluids.koopman.exponent import loglog_fit_exponent, ssa_denoise_exponent

REPO_ROOT = Path(__file__).resolve().parents[1]
DIGI_DIR = REPO_ROOT / "data" / "digitized"

N_BOOT = 2000
SEED = 20260723
EARLY_FRAC = 0.40
LATE_FRAC = 0.40
LOWER_BOUND_PURE = 0.5

ESTIMATORS = {"loglog": loglog_fit_exponent, "ssa": ssa_denoise_exponent}

MSD_CURVES = {
    "composite": "s14a_composite.csv",
    "hyaluronan": "s14a_hyaluronan.csv",
    "collagen_1mg": "s14a_collagen_1mg.csv",
}
ISF_CURVES = {
    "composite": "fig4a_composite.csv",
    "hyaluronan": "fig4a_hyaluronan.csv",
    "collagen_1mg": "fig4a_collagen.csv",
}


def _load(name_to_file: dict) -> dict[str, pd.DataFrame]:
    out = {}
    for name, fname in name_to_file.items():
        df = pd.read_csv(DIGI_DIR / fname).sort_values("x").reset_index(drop=True)
        out[name] = df
    return out


def _windows(logx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = logx.min(), logx.max()
    span = hi - lo
    early = logx <= lo + EARLY_FRAC * span
    late = logx >= hi - LATE_FRAC * span
    return early, late


def _local_slope(t: np.ndarray, y: np.ndarray, mask: np.ndarray, estimator) -> float:
    """Fit the estimator on the restricted (t, y) window. Both estimators do
    their own log(t)/log(y) handling internally, so just slice and pass on;
    ssa's Hankel window/rank defaults (20/4) are left at their Gate-0 values
    (no retuning here), and any window with too few points to build that
    Hankel matrix falls back to loglog's plain OLS slope on the same subset.
    """
    t_w, y_w = t[mask], y[mask]
    if estimator is ssa_denoise_exponent and len(t_w) <= 25:
        return loglog_fit_exponent(t_w, y_w)
    return estimator(t_w, y_w)


def _bootstrap_msd_curve(df: pd.DataFrame, estimator, rng: np.random.Generator) -> np.ndarray:
    """Returns array of shape (N_BOOT, 2): columns are (slope_early, slope_late)."""
    t = df.x.values
    y0 = df.y.values
    sigma = np.sqrt(df.reported_error.values ** 2 + df.digitization_error.values ** 2)
    logx = np.log10(t)
    early_mask, late_mask = _windows(logx)

    out = np.empty((N_BOOT, 2))
    for b in range(N_BOOT):
        y_pert = y0 + rng.normal(0.0, sigma)
        y_pert = np.clip(y_pert, 1e-6, None)  # keep strictly positive for log
        out[b, 0] = _local_slope(t, y_pert, early_mask, estimator)
        out[b, 1] = _local_slope(t, y_pert, late_mask, estimator)
    return out


def _bootstrap_isf_late_mean(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    t = df.x.values
    y0 = df.y.values
    sigma = np.sqrt(df.reported_error.values ** 2 + df.digitization_error.values ** 2)
    logx = np.log10(t)
    _, late_mask = _windows(logx)

    out = np.empty(N_BOOT)
    for b in range(N_BOOT):
        y_pert = y0 + rng.normal(0.0, sigma)
        out[b] = y_pert[late_mask].mean()
    return out


def _ci(x: np.ndarray) -> tuple[float, float, float]:
    return float(np.mean(x)), float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))


def run() -> None:
    rng = np.random.default_rng(SEED)

    msd = _load(MSD_CURVES)
    isf = _load(ISF_CURVES)

    print("=" * 70)
    print("PRIMARY TEST: local MSD log-log slope, early vs late window")
    print("=" * 70)

    primary_pass = True
    per_curve_results = {}
    for curve_name, df in msd.items():
        per_curve_results[curve_name] = {}
        for est_name, est_fn in ESTIMATORS.items():
            boot = _bootstrap_msd_curve(df, est_fn, rng)
            early, lo_e, hi_e = _ci(boot[:, 0])
            late, lo_l, hi_l = _ci(boot[:, 1])
            diff = boot[:, 0] - boot[:, 1]
            d_mean, d_lo, d_hi = _ci(diff)
            per_curve_results[curve_name][est_name] = {
                "early": (early, lo_e, hi_e),
                "late": (late, lo_l, hi_l),
                "diff": (d_mean, d_lo, d_hi),
            }
            print(
                f"{curve_name:14s} {est_name:7s} "
                f"slope_early={early:.3f} [{lo_e:.3f},{hi_e:.3f}]  "
                f"slope_late={late:.3f} [{lo_l:.3f},{hi_l:.3f}]  "
                f"(early-late)={d_mean:.3f} [{d_lo:.3f},{d_hi:.3f}]"
            )
            if curve_name == "composite":
                ok = d_lo > 0.0
                print(f"    -> criterion (A) [(early-late) CI > 0]: {'PASS' if ok else 'FAIL'}")
                primary_pass &= ok
            else:
                ok = lo_l > LOWER_BOUND_PURE
                print(f"    -> criterion (B) [slope_late CI lower bound > {LOWER_BOUND_PURE}]: {'PASS' if ok else 'FAIL'}")
                primary_pass &= ok

    print()
    print("=" * 70)
    print("SECONDARY, DESCRIPTIVE TEST: ISF late-window plateau height")
    print("=" * 70)
    plateau = {}
    for curve_name, df in isf.items():
        boot = _bootstrap_isf_late_mean(df, rng)
        plateau[curve_name] = boot
        mean, lo, hi = _ci(boot)
        print(f"{curve_name:14s} late-window mean ISF = {mean:.3f} [{lo:.3f}, {hi:.3f}]")

    for other in ("hyaluronan", "collagen_1mg"):
        diff = plateau["composite"] - plateau[other]
        d_mean, d_lo, d_hi = _ci(diff)
        overlap = not (d_lo > 0)
        print(
            f"composite - {other}: {d_mean:.3f} [{d_lo:.3f}, {d_hi:.3f}] "
            f"-> composite plateau higher, CI excludes zero: {'YES' if not overlap else 'NO'}"
        )

    print()
    print("=" * 70)
    print(f"GATE 4 PRIMARY-TEST VERDICT: {'PASS' if primary_pass else 'FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    run()
