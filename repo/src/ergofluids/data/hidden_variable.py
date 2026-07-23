"""A stable, stochastic, fully Markovian 2D linear system (x, y), used to test
whether the Mori-Zwanzig memory kernel (src/ergofluids/mz) captures a real,
theory-guaranteed memory effect: the marginal dynamics of x alone become
non-Markovian once the hidden variable y is integrated out. See Gate 2 in
docs/BUILD_PLAN.md.
"""

import numpy as np

DEFAULT_A = np.array([[0.4, 0.3], [0.2, 0.7]])  # eigenvalues 0.263, 0.837; stable


def simulate_hidden_variable_trajectory(
    n_steps: int,
    rng: np.random.Generator,
    a_matrix: np.ndarray = DEFAULT_A,
    noise_std: float = 0.3,
) -> np.ndarray:
    """One trajectory of z(t+1) = A z(t) + noise, z = (x, y). Shape (n_steps + 1, 2)."""
    z = np.zeros((n_steps + 1, 2))
    for t in range(n_steps):
        z[t + 1] = a_matrix @ z[t] + noise_std * rng.standard_normal(2)
    return z


def simulate_many(
    n_traj: int, n_steps: int, rng: np.random.Generator, **kwargs
) -> np.ndarray:
    """n_traj independent trajectories, shape (n_traj, n_steps + 1, 2)."""
    return np.stack(
        [simulate_hidden_variable_trajectory(n_steps, rng, **kwargs) for _ in range(n_traj)]
    )
