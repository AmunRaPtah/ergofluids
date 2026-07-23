import numpy as np

from ergofluids.data.synthetic import ensemble_msd, generate_2d_trajectories
from ergofluids.koopman.exponent import (
    dmd_denoise_exponent,
    loglog_fit_exponent,
    ssa_denoise_exponent,
)


def test_fbm_recovers_known_exponent_within_loose_tolerance():
    rng = np.random.default_rng(0)
    for alpha_true in (0.5, 1.0):
        traj = generate_2d_trajectories(n_particles=150, n_steps=80, hurst=alpha_true / 2, rng=rng)
        t, msd = ensemble_msd(traj)
        estimate = loglog_fit_exponent(t, msd)
        assert abs(estimate - alpha_true) < 0.2


def test_dmd_estimator_runs_and_returns_finite_value():
    rng = np.random.default_rng(1)
    traj = generate_2d_trajectories(n_particles=100, n_steps=60, hurst=0.4, rng=rng)
    t, msd = ensemble_msd(traj)
    estimate = dmd_denoise_exponent(t, msd)
    assert np.isfinite(estimate)


def test_ssa_estimator_is_less_biased_than_dmd_at_alpha_one():
    rng = np.random.default_rng(3)
    traj = generate_2d_trajectories(n_particles=150, n_steps=80, hurst=0.5, rng=rng)
    t, msd = ensemble_msd(traj)
    dmd_estimate = dmd_denoise_exponent(t, msd)
    ssa_estimate = ssa_denoise_exponent(t, msd)
    assert abs(ssa_estimate - 1.0) < abs(dmd_estimate - 1.0)


def test_ensemble_msd_starts_at_zero():
    rng = np.random.default_rng(2)
    traj = generate_2d_trajectories(n_particles=20, n_steps=30, hurst=0.5, rng=rng)
    t, msd = ensemble_msd(traj)
    assert t[0] == 0.0
    assert msd[0] == 0.0
