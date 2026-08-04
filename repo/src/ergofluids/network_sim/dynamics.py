"""Overdamped Langevin (Brownian) dynamics of probe particles among a fixed
fiber network: thermal noise plus a soft steric repulsion from nearby fibers,
an optional short-range attractive term (adhesion), and an optional
aspect-ratio effect.

Simplifications, stated plainly rather than hidden:
- 2D, not 3D.
- The particle is either a sphere or, for `aspect_ratio > 1`, a sphere with
  a *reduced effective collision radius* (`radius / sqrt(aspect_ratio)`),
  not a true rigid rod with coupled rotational/translational dynamics. This
  is a scoped stand-in for the qualitative finding in the literature that
  elongated particles access a skewed, coarser-pore-favoring subset of a
  network's pore-size distribution (Rokhforouz et al. 2025, Soft Matter,
  doi:10.1039/d5sm00195a), not a claim of quantitative equivalence to a
  full rigid-body simulation.
- Fibers are static (no thermal fluctuation of the network itself).
- The particle position used for fiber-interaction forces is wrapped modulo
  the box size (an implicit periodic tiling of the fiber pattern); true,
  unwrapped displacement is tracked separately for MSD. Near-boundary
  interactions are not minimum-image-wrapped, a known, small edge artifact
  affecting particles within one interaction range of a box edge.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from ergofluids.network_sim.network import FiberNetwork


@dataclass
class SimParams:
    box_size: float
    particle_radius: float
    fiber_radius: float = 0.15
    aspect_ratio: float = 1.0  # >1 reduces effective collision radius (see module docstring)
    adhesion_depth: float = 0.0  # 0 = purely steric; >0 = attractive well depth (kT units)
    adhesion_range: float = 0.3  # decay length of the attractive term, in the same units as radius
    steric_stiffness: float = 40.0  # soft-repulsion force constant
    gamma_per_radius: float = 1.0  # Stokes-like drag ~ radius; sets D0 = kT / (gamma_per_radius * radius)
    kT: float = 1.0
    dt: float = 0.01

    @property
    def effective_radius(self) -> float:
        return self.particle_radius / np.sqrt(self.aspect_ratio)

    @property
    def free_diffusivity(self) -> float:
        """D0 for an isolated particle (no fibers), from the same drag law
        the interaction forces use, so the "no obstruction" limit of this
        simulator is internally consistent with its own free-diffusion
        coefficient rather than an arbitrarily chosen constant."""
        gamma = self.gamma_per_radius * self.particle_radius
        return self.kT / gamma


def _pair_force(dist: np.ndarray, p: SimParams) -> np.ndarray:
    """Radial force magnitude (positive = repulsive, pushing the particle
    away from a fiber) at each (n_particles, n_fibers) distance. Steric term
    is a soft, finite-range repulsion active within `contact = effective
    particle radius + fiber radius`; the adhesive term, if `adhesion_depth >
    0`, is an exponentially decaying attraction just outside contact."""
    contact = p.effective_radius + p.fiber_radius
    overlap = np.maximum(contact - dist, 0.0)
    steric = p.steric_stiffness * overlap**2

    if p.adhesion_depth > 0:
        shell = np.maximum(dist - contact, 0.0)
        attraction = -p.adhesion_depth * np.exp(-shell / p.adhesion_range) * (dist < contact + 3 * p.adhesion_range)
    else:
        attraction = 0.0
    return steric - attraction  # net radial force magnitude; sign convention: positive = away from fiber


def _force_on_particles(
    wrapped: np.ndarray,
    network: FiberNetwork,
    fiber_tree: cKDTree,
    query_radius: float,
    params: SimParams,
) -> np.ndarray:
    """Net force (n_particles, 2) from nearby fibers only, found via a
    k-d tree query on fiber midpoints (built once per network, queried once
    per step) instead of the full (n_particles x n_fibers) distance matrix.
    This is the difference between a sweep that finishes in minutes and one
    that does not finish at all once fiber counts grow past a few hundred:
    the full matrix is O(n_particles * n_fibers) every step regardless of
    how few fibers actually matter to a given particle, while a spatial
    query only pays for pairs within `query_radius`.
    """
    n = wrapped.shape[0]
    neighbor_lists = fiber_tree.query_ball_point(wrapped, r=query_radius)
    counts = np.fromiter((len(nb) for nb in neighbor_lists), dtype=int, count=n)
    force = np.zeros((n, 2))
    if counts.sum() == 0:
        return force

    particle_idx = np.repeat(np.arange(n), counts)
    fiber_idx = np.concatenate([np.asarray(nb, dtype=int) for nb in neighbor_lists if len(nb)])

    # Elementwise (not broadcast) point-to-segment distance for each
    # (particle_idx[k], fiber_idx[k]) pair: deliberately not routed through
    # `point_segment_distance`, which broadcasts P points against S segments
    # into a P x S matrix. With K flattened candidate pairs, that would cost
    # O(K^2) to recover K diagonal values, defeating the point of pruning to
    # K candidates via the k-d tree in the first place.
    ab = network.ends[fiber_idx] - network.starts[fiber_idx]
    ab_len2 = np.maximum((ab**2).sum(axis=-1), 1e-12)
    ap = wrapped[particle_idx] - network.starts[fiber_idx]
    t = np.clip((ap * ab).sum(axis=-1) / ab_len2, 0.0, 1.0)
    closest = network.starts[fiber_idx] + t[:, None] * ab
    diff = wrapped[particle_idx] - closest
    dist_pairs = np.linalg.norm(diff, axis=-1)
    safe_dist = np.where(dist_pairs == 0, 1e-9, dist_pairs)
    direction = diff / safe_dist[:, None]

    force_mag = _pair_force(dist_pairs, params)
    pair_force = force_mag[:, None] * direction
    np.add.at(force, particle_idx, pair_force)
    return force


def simulate_ensemble(
    network: FiberNetwork,
    params: SimParams,
    n_particles: int,
    n_steps: int,
    rng: np.random.Generator,
    interaction_cutoff: float | None = None,
    burn_in_steps: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Run `n_particles` independent trajectories in the same fixed network,
    all steps vectorized together. Returns (t, msd), both shape (n_steps+1,).

    `interaction_cutoff` restricts the force sum to fibers within this
    distance of a particle (default: 5x contact distance); fibers further
    away contribute negligibly to the soft potentials used here, and, more
    importantly for runtime, are pruned before any distance is computed via
    a k-d tree query (see `_force_on_particles`), not just masked after.

    `burn_in_steps`: particles start at uniformly random positions, some of
    which land inside or very close to a fiber's steric-repulsion zone. The
    resulting sharp initial relaxation is a real feature of that (arbitrary)
    starting condition, not of the diffusive process being measured, and it
    biases the exponent fit toward mild superdiffusion at intermediate times
    if included. Running `burn_in_steps` before starting the MSD clock (and
    resetting the origin, not the position) removes it; this is standard
    equilibration practice in molecular/Brownian dynamics, not specific to
    this project.
    """
    box = network.box_size
    contact = params.effective_radius + params.fiber_radius
    cutoff = interaction_cutoff if interaction_cutoff is not None else 5.0 * contact
    fiber_length = float(np.linalg.norm(network.ends[0] - network.starts[0])) if network.n_fibers else 0.0
    query_radius = cutoff + fiber_length / 2.0

    midpoints = (network.starts + network.ends) / 2.0
    fiber_tree = cKDTree(midpoints, boxsize=box) if network.n_fibers else None

    pos = rng.uniform(0.0, box, size=(n_particles, 2))
    D0 = params.free_diffusivity
    noise_scale = np.sqrt(2.0 * D0 * params.dt)
    gamma = params.gamma_per_radius * params.particle_radius

    for _ in range(burn_in_steps):
        wrapped = pos % box
        force = (
            _force_on_particles(wrapped, network, fiber_tree, query_radius, params)
            if fiber_tree is not None
            else np.zeros((n_particles, 2))
        )
        drift = (force / gamma) * params.dt
        noise = noise_scale * rng.standard_normal(size=(n_particles, 2))
        pos = pos + drift + noise

    unwrapped = pos.copy()
    msd = np.zeros(n_steps + 1)
    origin = unwrapped.copy()
    msd[0] = 0.0

    for step in range(n_steps):
        wrapped = pos % box
        if fiber_tree is not None:
            force = _force_on_particles(wrapped, network, fiber_tree, query_radius, params)
        else:
            force = np.zeros((n_particles, 2))

        drift = (force / gamma) * params.dt
        noise = noise_scale * rng.standard_normal(size=(n_particles, 2))
        step_disp = drift + noise

        pos = pos + step_disp
        unwrapped = unwrapped + step_disp
        msd[step + 1] = ((unwrapped - origin) ** 2).sum(axis=1).mean()

    t = np.arange(n_steps + 1) * params.dt
    return t, msd
