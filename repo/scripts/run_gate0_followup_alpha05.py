"""Follow-up to Gate 0b: alpha_true=0.5 got 17/20 for ssa against an 18/20 bar,
one repeat below the pre-registered threshold. Re-run with 100 repeats instead
of 20 to find out whether that reflects real miscalibration or Monte Carlo
noise around a true coverage rate near 90%. loglog included for comparison;
dmd (HODMD) omitted, already clearly worse and not a live candidate.

Pre-registered here, before running: report the raw coverage fraction and its
exact binomial 95% CI (Clopper-Pearson) for both estimators. No further
parameter changes after this result, regardless of outcome.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from scipy import stats

from ergofluids.data.synthetic import generate_2d_trajectories
from ergofluids.koopman.exponent import loglog_fit_exponent, ssa_denoise_exponent
from ergofluids.validation.gate import bootstrap_ci

N_REPEATS = 100
N_PARTICLES = 150
N_STEPS = 80
N_BOOT = 150
ALPHA_TRUE = 0.5
SEED = 20260722 + 2

ESTIMATORS = {"loglog": loglog_fit_exponent, "ssa": ssa_denoise_exponent}


def clopper_pearson(hits: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    alpha = 1 - conf
    lo = stats.beta.ppf(alpha / 2, hits, n - hits + 1) if hits > 0 else 0.0
    hi = stats.beta.ppf(1 - alpha / 2, hits + 1, n - hits) if hits < n else 1.0
    return lo, hi


def run() -> None:
    rng = np.random.default_rng(SEED)
    hurst = ALPHA_TRUE / 2
    coverage = dict.fromkeys(ESTIMATORS, 0)
    for rep in range(N_REPEATS):
        traj = generate_2d_trajectories(N_PARTICLES, N_STEPS, hurst, rng)
        for name, fn in ESTIMATORS.items():
            _, lo, hi = bootstrap_ci(traj, fn, n_boot=N_BOOT, rng=rng)
            coverage[name] += int(lo <= ALPHA_TRUE <= hi)
        if (rep + 1) % 20 == 0:
            print(f"...{rep + 1}/{N_REPEATS} done")

    for name, hits in coverage.items():
        ci_lo, ci_hi = clopper_pearson(hits, N_REPEATS)
        rate = hits / N_REPEATS
        print(f"{name}: {hits}/{N_REPEATS} = {rate:.2%}, 95% CI on true rate "
              f"[{ci_lo:.2%}, {ci_hi:.2%}], 90% target {'inside' if ci_lo <= 0.90 <= ci_hi else 'outside'} this CI")


if __name__ == "__main__":
    run()
