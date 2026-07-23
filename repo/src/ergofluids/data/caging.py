"""A caged-particle system: a fast Ornstein-Uhlenbeck fluctuation x(t) around
a slowly-diffusing, hidden trap center c(t). Mechanistically, this is the
textbook picture behind the caging/ISF-plateau behavior reported for the
composite hyaluronan-collagen network in arXiv:1909.05091 (particle
transiently confined by the local mesh, escaping only as the mesh itself
rearranges), rather than an arbitrary linear coupling. Used for Gate 3
(docs/BUILD_PLAN.md): a harder, more physically motivated test of the
Mori-Zwanzig memory kernel than Gate 2's generic hidden-variable system.

    c(t+1) = c(t) + sigma_c * noise_c            (slow, unbounded, diffusive)
    x(t+1) = x(t) + kappa * (c(t) - x(t)) + sigma_x * noise_x   (fast pull to c)

Only x is observed; c is discarded before fitting. At short times x's MSD is
dominated by fast equilibration around c and saturates (the "cage"); at long
times x inherits c's unbounded diffusion (the eventual "escape").
"""

import numpy as np

DEFAULT_KAPPA = 0.5
DEFAULT_SIGMA_X = 0.3
DEFAULT_SIGMA_C = 0.03  # much smaller: c diffuses slowly relative to x's relaxation


def simulate_caged_particle_trajectory(
    n_steps: int,
    rng: np.random.Generator,
    kappa: float = DEFAULT_KAPPA,
    sigma_x: float = DEFAULT_SIGMA_X,
    sigma_c: float = DEFAULT_SIGMA_C,
) -> np.ndarray:
    """One trajectory, shape (n_steps + 1, 2): columns (x, c)."""
    z = np.zeros((n_steps + 1, 2))
    for t in range(n_steps):
        x, c = z[t]
        c_next = c + sigma_c * rng.standard_normal()
        x_next = x + kappa * (c - x) + sigma_x * rng.standard_normal()
        z[t + 1] = (x_next, c_next)
    return z


def ensemble_msd_from_origin(x_trajectories: np.ndarray, dt: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """x_trajectories: shape (n_traj, n_steps + 1). Returns (t, msd) of x alone."""
    n_steps_plus_1 = x_trajectories.shape[1]
    t = np.arange(n_steps_plus_1) * dt
    msd = (x_trajectories**2).mean(axis=0)
    return t, msd
