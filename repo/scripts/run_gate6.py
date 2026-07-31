"""Gate 6: does HODMD's diagnosed bias (Gate 0/0b) generalize across other
established DMD-family methods, or is it specific to HODMD's own
implementation?

Pre-registered protocol and pass/fail criterion, written before this script
was run (see docs/BUILD_PLAN.md, "Gate 6" section, for the identical text
plus the result). Do not change the criterion or parameters below after
seeing the printed output; if a re-run is ever needed, do it as a new,
separately labeled gate.

Identical protocol to Gate 0 (run_gate0.py) in every respect except which
estimators are tested: `generate_2d_trajectories` (150 particles, 80 steps,
2D fractional Brownian motion), alpha_true in {0.5, 0.7, 1.0}, 20 independent
realizations per condition, 150-resample percentile bootstrap CI per
realization, pass bar 18/20 coverage at nominal 90%. Three candidates, all
published, PyDMD-implemented methods, not built for this project:
`hodmd_fb_denoise_exponent` (HODMD + forward-backward averaging),
`bopdmd_denoise_exponent` (Bagging, Optimized DMD), `subspace_denoise_exponent`
(Subspace DMD). See docs/BUILD_PLAN.md "Gate 6" for citations and rationale.

Secondary, descriptive report (not part of pass/fail): mean point-estimate
bias per candidate per condition, mirroring Gate 0's own root-cause table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from ergofluids.data.synthetic import generate_2d_trajectories
from ergofluids.koopman.exponent import (
    bopdmd_denoise_exponent,
    fallback_counts,
    hodmd_fb_denoise_exponent,
    reset_fallback_counts,
    subspace_denoise_exponent,
)
from ergofluids.validation.gate import bootstrap_ci

N_REPEATS = 20
N_PARTICLES = 150
N_STEPS = 80
N_BOOT = 150
ALPHAS_TRUE = [0.5, 0.7, 1.0]
SEED = 20260731
REQUIRED_COVERAGE = 18


def run() -> dict:
    rng = np.random.default_rng(SEED)
    results = {}
    estimators = {
        "hodmd_fb": hodmd_fb_denoise_exponent,
        "bopdmd": bopdmd_denoise_exponent,
        "subspace": subspace_denoise_exponent,
    }
    for alpha_true in ALPHAS_TRUE:
        hurst = alpha_true / 2
        coverage = dict.fromkeys(estimators, 0)
        bias_sum = dict.fromkeys(estimators, 0.0)
        reset_fallback_counts()
        rows = []
        for rep in range(N_REPEATS):
            traj = generate_2d_trajectories(N_PARTICLES, N_STEPS, hurst, rng)
            row = {"rep": rep}
            for name, fn in estimators.items():
                pe, lo, hi = bootstrap_ci(traj, fn, n_boot=N_BOOT, rng=rng)
                hit = lo <= alpha_true <= hi
                coverage[name] += int(hit)
                bias_sum[name] += pe - alpha_true
                row[name] = (pe, lo, hi, hit)
            rows.append(row)
        fallbacks = fallback_counts()
        n_calls_per_estimator = N_REPEATS * (1 + N_BOOT)
        results[alpha_true] = {"coverage": coverage, "rows": rows, "fallbacks": fallbacks}
        cov_str = ", ".join(f"{k} {v}/{N_REPEATS}" for k, v in coverage.items())
        bias_str = ", ".join(f"{k} {bias_sum[k] / N_REPEATS:+.4f}" for k in estimators)
        fb_str = ", ".join(f"{k} {v}/{n_calls_per_estimator}" for k, v in fallbacks.items())
        print(f"alpha_true={alpha_true}: coverage {cov_str}")
        print(f"  mean point-estimate bias (descriptive only): {bias_str}")
        print(f"  loglog-fallback triggers out of {n_calls_per_estimator} calls per estimator: {fb_str}")

    print()
    print("=" * 70)
    print(f"GATE 6 PASS BAR: {REQUIRED_COVERAGE}/{N_REPEATS} at every alpha_true")
    for name in estimators:
        covs = {a: results[a]["coverage"][name] for a in ALPHAS_TRUE}
        passed = all(c >= REQUIRED_COVERAGE for c in covs.values())
        print(f"  {name}: {covs} -> {'PASS' if passed else 'FAIL'}")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run()
