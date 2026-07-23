"""Gate 0: pipeline correctness on synthetic data with known ground truth.

Pass criterion (pre-registered in docs/BUILD_PLAN.md, written before this script
was run): across >= 20 independent realizations at each alpha_true in
{0.5, 0.7, 1.0}, the bootstrap 95% CI of alpha_hat contains alpha_true in at
least 18 of 20 runs (90% nominal coverage).
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

N_REPEATS = 20
N_PARTICLES = 150
N_STEPS = 80
N_BOOT = 150
ALPHAS_TRUE = [0.5, 0.7, 1.0]
SEED = 20260722


def run() -> dict:
    rng = np.random.default_rng(SEED)
    results = {}
    estimators = {
        "loglog": loglog_fit_exponent,
        "dmd": dmd_denoise_exponent,
        "ssa": ssa_denoise_exponent,
    }
    for alpha_true in ALPHAS_TRUE:
        hurst = alpha_true / 2
        coverage = dict.fromkeys(estimators, 0)
        rows = []
        for rep in range(N_REPEATS):
            traj = generate_2d_trajectories(N_PARTICLES, N_STEPS, hurst, rng)
            row = {"rep": rep}
            for name, fn in estimators.items():
                pe, lo, hi = bootstrap_ci(traj, fn, n_boot=N_BOOT, rng=rng)
                hit = lo <= alpha_true <= hi
                coverage[name] += int(hit)
                row[name] = (pe, lo, hi, hit)
            rows.append(row)
        results[alpha_true] = {"coverage": coverage, "rows": rows}
        cov_str = ", ".join(f"{k} {v}/{N_REPEATS}" for k, v in coverage.items())
        print(f"alpha_true={alpha_true}: {cov_str}")
    return results


if __name__ == "__main__":
    run()
