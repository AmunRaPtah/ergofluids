"""Gate 3: does the ported MZMD memory kernel forecast better than a
memoryless fit, on a caged-particle system (fast OU fluctuation around a
slowly-diffusing hidden trap center) chosen to mechanistically resemble the
plateau/caging behavior reported in arXiv:1909.05091? Parameters locked in
docs/BUILD_PLAN.md (Gate 3) before this script was run at full scale.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from ergofluids.data.caging import simulate_caged_particle_trajectory
from ergofluids.validation.mz_gate import paired_bootstrap_ci, per_trajectory_rmse

N_TRAJ = 60
T_WIN = 100
N_KS_MEMORY = 15
HORIZON = 10
SEED = 20260726


def run() -> None:
    rng = np.random.default_rng(SEED)
    n_steps = T_WIN + N_KS_MEMORY + HORIZON + 5
    errs_memoryless = np.empty(N_TRAJ)
    errs_memory = np.empty(N_TRAJ)
    for i in range(N_TRAJ):
        traj = simulate_caged_particle_trajectory(n_steps=n_steps, rng=rng)
        x = traj[:, 0:1].T  # observe only x; c (the cage center) is discarded
        errs_memoryless[i] = per_trajectory_rmse(x, T_WIN, n_ks=1, horizon=HORIZON)
        errs_memory[i] = per_trajectory_rmse(x, T_WIN, n_ks=N_KS_MEMORY, horizon=HORIZON)

    diffs = errs_memoryless - errs_memory
    point, lo, hi = paired_bootstrap_ci(diffs, rng=rng)

    print(f"mean RMSE memoryless (n_ks=1): {errs_memoryless.mean():.4f}")
    print(f"mean RMSE memory (n_ks={N_KS_MEMORY}): {errs_memory.mean():.4f}")
    print(f"paired diff (memoryless - memory): point={point:.4f}  95% CI=[{lo:.4f}, {hi:.4f}]")
    passed = lo > 0
    print(f"PASS={passed} (CI excludes zero on the positive side: {passed})")


if __name__ == "__main__":
    run()
