import numpy as np

from ergofluids.data.caging import ensemble_msd_from_origin, simulate_caged_particle_trajectory
from ergofluids.validation.mz_gate import per_trajectory_rmse


def test_msd_shows_caging_then_escape_crossover():
    rng = np.random.default_rng(5)
    n_traj = 150
    n_steps = 400
    xs = np.empty((n_traj, n_steps + 1))
    for i in range(n_traj):
        xs[i] = simulate_caged_particle_trajectory(n_steps, rng)[:, 0]
    t, msd = ensemble_msd_from_origin(xs)

    early_mask = (t >= 1) & (t <= 8)
    late_mask = (t >= 200) & (t <= 400)
    slope_early, _ = np.polyfit(np.log(t[early_mask]), np.log(msd[early_mask]), 1)
    slope_late, _ = np.polyfit(np.log(t[late_mask]), np.log(msd[late_mask]), 1)

    # Caging signature: growth is much slower right after the initial rise
    # than it is once the hidden cage center has had time to diffuse away.
    assert slope_late > slope_early


def test_per_trajectory_rmse_runs_on_caged_system():
    rng = np.random.default_rng(6)
    traj = simulate_caged_particle_trajectory(n_steps=130, rng=rng)
    x = traj[:, 0:1].T
    err = per_trajectory_rmse(x, t_win=100, n_ks=15, horizon=10)
    assert np.isfinite(err)
    assert err >= 0
