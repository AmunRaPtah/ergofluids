"""Gate 2: does the ported MZMD memory kernel forecast better than a
memoryless fit, on a linear system where a hidden variable is known to
induce real memory in the observed variable? Parameters locked in
docs/BUILD_PLAN.md (Gate 2) before this script was run at full scale.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from ergofluids.data.hidden_variable import simulate_hidden_variable_trajectory
from ergofluids.validation.mz_gate import paired_bootstrap_ci, per_trajectory_rmse

N_TRAJ = 60
N_STEPS = 80
T_WIN = 50
N_KS_MEMORY = 6
HORIZON = 3
SEED = 20260725


def run() -> None:
    rng = np.random.default_rng(SEED)
    errs_memoryless = np.empty(N_TRAJ)
    errs_memory = np.empty(N_TRAJ)
    for i in range(N_TRAJ):
        traj = simulate_hidden_variable_trajectory(n_steps=N_STEPS, rng=rng)
        x = traj[:, 0:1].T  # observe only x; y is discarded here
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
