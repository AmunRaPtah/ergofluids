"""Gate 1: literature-anchored synthetic validation.

Pass criterion (pre-registered in docs/BUILD_PLAN.md, written before this script
was run): fit the pipeline to synthetic trajectories built to match two literature
regimes from arXiv:1909.05091 (single-component networks, alpha ~ 1; the
hyaluronan-collagen composite network, alpha ~ 0.5), without telling the pipeline
which regime it came from. Pass if the two regimes' bootstrap 95% CIs do not
overlap, and the composite-regime point estimate falls within +/- 0.15 of 0.5.

Includes the ssa estimator alongside loglog and dmd, added per Gate 0b in
docs/BUILD_PLAN.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from ergofluids.data.synthetic import generate_2d_trajectories
from ergofluids.koopman.exponent import (
    dmd_denoise_exponent,
    loglog_fit_exponent,
    ssa_denoise_exponent,
)
from ergofluids.validation.gate import bootstrap_ci

N_PARTICLES = 150
N_STEPS = 80
N_BOOT = 150
SEED = 20260722 + 1

REGIMES = {
    "single_component_alpha_1": 1.0,
    "composite_alpha_0.5": 0.5,
}

ESTIMATORS = {
    "loglog": loglog_fit_exponent,
    "dmd": dmd_denoise_exponent,
    "ssa": ssa_denoise_exponent,
}


def run() -> dict:
    rng = np.random.default_rng(SEED)
    results = {}
    for name, alpha_true in REGIMES.items():
        hurst = alpha_true / 2
        traj = generate_2d_trajectories(N_PARTICLES, N_STEPS, hurst, rng)
        results[name] = {"alpha_true": alpha_true}
        for label, fn in ESTIMATORS.items():
            pe, lo, hi = bootstrap_ci(traj, fn, n_boot=N_BOOT, rng=rng)
            results[name][label] = (pe, lo, hi)
        print(
            f"{name}: "
            + "  ".join(
                f"{label}={results[name][label][0]:.3f} "
                f"[{results[name][label][1]:.3f},{results[name][label][2]:.3f}]"
                for label in ESTIMATORS
            )
        )

    for label in ESTIMATORS:
        lo_a, hi_a = results["single_component_alpha_1"][label][1:]
        lo_b, hi_b = results["composite_alpha_0.5"][label][1:]
        separated = (lo_a > hi_b) or (lo_b > hi_a)
        composite_pe = results["composite_alpha_0.5"][label][0]
        within_tol = abs(composite_pe - 0.5) <= 0.15
        print(
            f"[{label}] CIs separated: {separated}; composite within +/-0.15 of 0.5: {within_tol}"
            f" (composite point estimate={composite_pe:.3f}); PASS={separated and within_tol}"
        )

    return results


if __name__ == "__main__":
    run()
