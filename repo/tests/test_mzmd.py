import numpy as np

from ergofluids.data.hidden_variable import DEFAULT_A, simulate_hidden_variable_trajectory
from ergofluids.mz.mzmd import fit_mzmd, forecast
from ergofluids.validation.mz_gate import per_trajectory_rmse


def test_mzmd_recovers_known_transition_matrix_exactly_when_noiseless():
    rng = np.random.default_rng(0)
    t_total = 60
    z = np.zeros((2, t_total))
    z[:, 0] = rng.standard_normal(2)
    for t in range(t_total - 1):
        z[:, t + 1] = DEFAULT_A @ z[:, t]

    t_win = 40
    omega = fit_mzmd(z[:, : t_win + 1], t_win=t_win, n_ks=1)
    assert np.allclose(omega[0], DEFAULT_A, atol=1e-8)


def test_forecast_matches_true_trajectory_when_noiseless():
    rng = np.random.default_rng(0)
    t_total = 60
    z = np.zeros((2, t_total))
    z[:, 0] = rng.standard_normal(2)
    for t in range(t_total - 1):
        z[:, t + 1] = DEFAULT_A @ z[:, t]

    t_win = 40
    omega = fit_mzmd(z[:, : t_win + 1], t_win=t_win, n_ks=1)
    seed = z[:, t_win - 1 : t_win]
    fc = forecast(seed, omega, n_steps=10)
    true_future = z[:, t_win : t_win + 10]
    assert np.allclose(fc, true_future, atol=1e-6)


def test_memory_kernel_reduces_to_markovian_at_n_ks_one():
    rng = np.random.default_rng(2)
    traj = simulate_hidden_variable_trajectory(n_steps=80, rng=rng)
    x = traj[:, 0:1].T
    omega = fit_mzmd(x[:, :51], t_win=50, n_ks=1)
    assert omega.shape == (1, 1, 1)


def test_per_trajectory_rmse_runs_and_is_finite():
    rng = np.random.default_rng(3)
    traj = simulate_hidden_variable_trajectory(n_steps=80, rng=rng)
    x = traj[:, 0:1].T
    err = per_trajectory_rmse(x, t_win=50, n_ks=6, horizon=3)
    assert np.isfinite(err)
    assert err >= 0
