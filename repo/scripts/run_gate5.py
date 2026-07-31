"""Gate 5: model-based caged-diffusion fit (same digitized data as Gate 4, different
functional form).

Pre-registered protocol and pass/fail criterion, written before this script was run
(see docs/BUILD_PLAN.md, "Gate 5" section, for the identical text plus the result).
Do not change the criterion or parameters below after seeing the printed output; if a
re-run is ever needed, do it as a new, separately labeled gate.

Data: same S14a-digitized MSD curves Gate 4 used (composite, hyaluronan, collagen_1mg),
data/digitized/s14a_*.csv, unchanged.

Two models, both 2 free parameters, fit by weighted nonlinear least squares
(weights = 1/sigma_i^2, sigma_i = combined reported_error/digitization_error in
quadrature, same as Gate 4) on the FULL curve, no early/late windowing:

  MSD_powerlaw(t) = A * t^alpha
  MSD_confined(t) = P * (1 - exp(-t / tau))    [Kusumi, Sako & Yamamoto 1993]

Compared via small-sample-corrected AIC (AICc = chi^2 + 2k + 2k(k+1)/(n-k-1), k=2 for
both models). Propagated via a 2000-draw Gaussian-perturbation bootstrap on y (seed
20260731, a fresh seed for this later gate; Gate 4's seed 20260723 is not reused),
recording delta_AICc = AICc_powerlaw - AICc_confined and, for the confined model, tau,
per draw. Draws where either fit fails to converge are dropped and the drop count is
reported, not silently absorbed into a smaller-than-stated n.

Pass criterion:
  (A) Composite: 95% CI of delta_AICc entirely positive (confined preferred in every
      draw) AND 95% CI of tau has a lower bound below the curve's own max digitized
      Delta t (plateau at least partly constrained within the observed range, not a
      pure extrapolation beyond it).
  (B) Hyaluronan AND collagen_1mg: (A)'s two parts do NOT both hold.
Fail if (A) fails for composite, or (B) fails for either pure-component curve.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

REPO_ROOT = Path(__file__).resolve().parents[1]
DIGI_DIR = REPO_ROOT / "data" / "digitized"

N_BOOT = 2000
SEED = 20260731
TAU_UPPER_BOUND_FACTOR = 1e4  # cap tau at 1e4 * max(t); only affects numerical
                              # stability, not the pass/fail decision (which depends
                              # on the CI *lower* bound of tau, not the upper bound).

MSD_CURVES = {
    "composite": "s14a_composite.csv",
    "hyaluronan": "s14a_hyaluronan.csv",
    "collagen_1mg": "s14a_collagen_1mg.csv",
}


def powerlaw(t, A, alpha):
    return A * t**alpha


def confined(t, P, tau):
    return P * (1.0 - np.exp(-t / tau))


def _chi2(y, yhat, sigma):
    return float(np.sum(((y - yhat) / sigma) ** 2))


def _aicc(chi2, k, n):
    return chi2 + 2 * k + (2 * k * (k + 1)) / (n - k - 1)


def _fit_powerlaw(t, y, sigma):
    p0 = (1.0, 0.5)
    popt, _ = curve_fit(
        powerlaw, t, y, p0=p0, sigma=sigma, absolute_sigma=True,
        bounds=([1e-8, 0.01], [1e6, 3.0]), maxfev=20000,
    )
    return popt


def _fit_confined(t, y, sigma):
    tau_max = TAU_UPPER_BOUND_FACTOR * t.max()
    p0 = (max(y.max() * 1.5, 1e-6), float(np.median(t)))
    popt, _ = curve_fit(
        confined, t, y, p0=p0, sigma=sigma, absolute_sigma=True,
        bounds=([1e-8, 1e-6], [1e6, tau_max]), maxfev=20000,
    )
    return popt


def _bootstrap_curve(df: pd.DataFrame, rng: np.random.Generator):
    t = df.x.values
    y0 = df.y.values
    sigma = np.sqrt(df.reported_error.values ** 2 + df.digitization_error.values ** 2)
    n = len(t)
    tmax = float(t.max())

    delta_aiccs, taus = [], []
    n_fail = 0
    for _ in range(N_BOOT):
        y = y0 + rng.normal(0.0, sigma)
        y = np.clip(y, 1e-6, None)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                A, alpha = _fit_powerlaw(t, y, sigma)
                P, tau = _fit_confined(t, y, sigma)
        except RuntimeError:
            n_fail += 1
            continue
        chi2_pl = _chi2(y, powerlaw(t, A, alpha), sigma)
        chi2_cf = _chi2(y, confined(t, P, tau), sigma)
        aicc_pl = _aicc(chi2_pl, 2, n)
        aicc_cf = _aicc(chi2_cf, 2, n)
        delta_aiccs.append(aicc_pl - aicc_cf)
        taus.append(tau)
    return np.array(delta_aiccs), np.array(taus), n_fail, tmax


def _ci(x: np.ndarray) -> tuple[float, float, float]:
    return float(np.mean(x)), float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))


def run() -> None:
    rng = np.random.default_rng(SEED)
    print("=" * 78)
    print("GATE 5: model-based caged-diffusion fit vs global power law")
    print("=" * 78)

    primary_pass = True
    for curve_name, fname in MSD_CURVES.items():
        df = pd.read_csv(DIGI_DIR / fname).sort_values("x").reset_index(drop=True)
        delta_aiccs, taus, n_fail, tmax = _bootstrap_curve(df, rng)
        n_ok = len(delta_aiccs)
        d_mean, d_lo, d_hi = _ci(delta_aiccs)
        tau_mean, tau_lo, tau_hi = _ci(taus)

        confined_always_preferred = d_lo > 0.0
        tau_constrained = tau_lo < tmax

        print(
            f"\n{curve_name} (n_points={len(df)}, max Delta t={tmax:.3f}, "
            f"bootstrap converged {n_ok}/{N_BOOT}, dropped {n_fail})"
        )
        print(
            f"  delta_AICc (powerlaw - confined) = {d_mean:.3f} [{d_lo:.3f}, {d_hi:.3f}]  "
            f"-> confined preferred in all draws: {'YES' if confined_always_preferred else 'NO'}"
        )
        print(
            f"  tau [95% CI] = {tau_mean:.3f} [{tau_lo:.3f}, {tau_hi:.3f}]  "
            f"-> CI lower bound below max Delta t: {'YES' if tau_constrained else 'NO'}"
        )

        if curve_name == "composite":
            ok = confined_always_preferred and tau_constrained
            print(f"  -> criterion (A): {'PASS' if ok else 'FAIL'}")
            primary_pass &= ok
        else:
            ok = not (confined_always_preferred and tau_constrained)
            print(f"  -> criterion (B): {'PASS' if ok else 'FAIL'}")
            primary_pass &= ok

    print()
    print("=" * 78)
    print(f"GATE 5 VERDICT: {'PASS' if primary_pass else 'FAIL'}")
    print("=" * 78)


if __name__ == "__main__":
    run()
