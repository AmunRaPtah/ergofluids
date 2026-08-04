"""Rigid-body rod dynamics: replaces `dynamics.py`'s aspect-ratio stand-in
(a sphere with a reduced effective collision radius) with an actual rigid
rod, position (x, y) plus orientation theta, anisotropic translational drag
(harder to move sideways than along its own axis, the standard qualitative
result for slender bodies), and rotational diffusion, interacting with the
fiber network at several points along its length rather than one.

Simplifications, stated plainly:
- 2D, not 3D.
- The rod is discretized into `N_SAMPLE_POINTS` circular contact points
  along its length for steric/adhesive interaction with fibers, not a
  continuous line integral.
- Drag coefficients (`RodParams.drag`) use a simplified, clearly-approximate
  slender-body-style scaling (parallel drag ~ length/ln(length/radius),
  perpendicular ~ 2x parallel, rotational ~ parallel x length^2), chosen to
  reproduce the right qualitative behavior (harder to translate sideways
  than lengthwise, faster rotation for shorter rods), not literature-exact
  coefficients (e.g. Broersma's or Perrin's friction factors). This is
  checked against its own free-rod limit in
  `tests/test_rod_dynamics.py`, not assumed correct.
- Fibers are static, as in `dynamics.py`.
- At `aspect_ratio = 1.0`, this module does NOT reduce to a point sphere:
  it is still `N_SAMPLE_POINTS` contact circles spread across a
  `2 * particle_radius`-long segment, closer to a short, fat capsule than a
  single sphere of that radius. `dynamics.simulate_ensemble` (a true point
  sphere) remains the aspect_ratio = 1 baseline used everywhere in this
  project; `sweep.py` only routes to `simulate_rod_ensemble` for
  `aspect_ratio > 1`, specifically to avoid silently changing the
  already-reported sphere-case numbers (e.g. the 62% MAE reduction result)
  by switching their underlying geometry.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from ergofluids.network_sim.dynamics import _pair_force
from ergofluids.network_sim.network import FiberNetwork

N_SAMPLE_POINTS = 5
SAMPLE_FRACTIONS = np.linspace(-1.0, 1.0, N_SAMPLE_POINTS)


@dataclass
class RodParams:
    box_size: float
    particle_radius: float  # geometric-mean size; reduces to a sphere of this radius at aspect_ratio=1
    aspect_ratio: float = 1.0  # >=1
    fiber_radius: float = 0.15
    adhesion_depth: float = 0.0
    adhesion_range: float = 0.3
    steric_stiffness: float = 40.0
    gamma_per_radius: float = 1.0
    kT: float = 1.0
    dt: float = 0.01

    @property
    def cross_radius(self) -> float:
        return self.particle_radius / np.sqrt(self.aspect_ratio)

    @property
    def half_length(self) -> float:
        return self.particle_radius * np.sqrt(self.aspect_ratio)

    @property
    def drag(self) -> tuple[float, float, float]:
        """(gamma_parallel, gamma_perpendicular, gamma_rotational), the
        simplified slender-body-style scaling described in the module
        docstring."""
        a = self.cross_radius
        half_l = self.half_length
        full_l = 2.0 * half_l
        shape_ratio = max(full_l / a, 1.0 + 1e-6)
        gamma_par = self.gamma_per_radius * a * shape_ratio / (np.log(shape_ratio) + 0.5)
        gamma_perp = 2.0 * gamma_par
        gamma_rot = gamma_par * half_l**2 / 3.0
        return gamma_par, gamma_perp, gamma_rot

    def as_dynamics_params(self):
        """A `dynamics.SimParams`-compatible shim so `_pair_force` (steric +
        adhesive radial force law) can be reused unmodified for each sample
        point's contact radius, without duplicating that logic here."""
        from ergofluids.network_sim.dynamics import SimParams

        return SimParams(
            box_size=self.box_size,
            particle_radius=self.cross_radius,
            aspect_ratio=1.0,
            fiber_radius=self.fiber_radius,
            adhesion_depth=self.adhesion_depth,
            adhesion_range=self.adhesion_range,
            steric_stiffness=self.steric_stiffness,
            gamma_per_radius=self.gamma_per_radius,
            kT=self.kT,
            dt=self.dt,
        )


def _sample_points_world(center: np.ndarray, theta: np.ndarray, half_length: float) -> np.ndarray:
    """center: (n, 2), theta: (n,). Returns (n, N_SAMPLE_POINTS, 2) world
    positions of each rod's sample points."""
    direction = np.stack([np.cos(theta), np.sin(theta)], axis=-1)  # (n, 2)
    offsets = SAMPLE_FRACTIONS[None, :, None] * half_length * direction[:, None, :]  # (n, P, 2)
    return center[:, None, :] + offsets


def _force_and_torque(
    center: np.ndarray,
    theta: np.ndarray,
    network: FiberNetwork,
    fiber_tree: cKDTree,
    query_radius: float,
    params: RodParams,
    box: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Net force (n, 2) and torque (n,) on each rod, summed over its
    `N_SAMPLE_POINTS` contact points, each interacting with nearby fibers
    the same way a single sphere does in `dynamics.py`."""
    n = center.shape[0]
    points = _sample_points_world(center, theta, params.half_length) % box  # (n, P, 2)
    flat_points = points.reshape(-1, 2)

    neighbor_lists = fiber_tree.query_ball_point(flat_points, r=query_radius)
    counts = np.fromiter((len(nb) for nb in neighbor_lists), dtype=int, count=len(flat_points))
    point_force = np.zeros((len(flat_points), 2))

    if counts.sum() > 0:
        point_idx = np.repeat(np.arange(len(flat_points)), counts)
        fiber_idx = np.concatenate([np.asarray(nb, dtype=int) for nb in neighbor_lists if len(nb)])

        ab = network.ends[fiber_idx] - network.starts[fiber_idx]
        ab_len2 = np.maximum((ab**2).sum(axis=-1), 1e-12)
        ap = flat_points[point_idx] - network.starts[fiber_idx]
        t = np.clip((ap * ab).sum(axis=-1) / ab_len2, 0.0, 1.0)
        closest = network.starts[fiber_idx] + t[:, None] * ab
        diff = flat_points[point_idx] - closest
        dist_pairs = np.linalg.norm(diff, axis=-1)
        safe_dist = np.where(dist_pairs == 0, 1e-9, dist_pairs)
        direction = diff / safe_dist[:, None]

        force_mag = _pair_force(dist_pairs, params.as_dynamics_params())
        pair_force = force_mag[:, None] * direction
        np.add.at(point_force, point_idx, pair_force)

    point_force = point_force.reshape(n, N_SAMPLE_POINTS, 2)
    net_force = point_force.sum(axis=1)

    offsets = points - center[:, None, :]  # (n, P, 2), world-frame offsets from center
    # 2D cross product per point: torque_z = dx*Fy - dy*Fx, summed over sample points
    torque = (offsets[..., 0] * point_force[..., 1] - offsets[..., 1] * point_force[..., 0]).sum(axis=1)
    return net_force, torque


def simulate_rod_ensemble(
    network: FiberNetwork,
    params: RodParams,
    n_particles: int,
    n_steps: int,
    rng: np.random.Generator,
    interaction_cutoff: float | None = None,
    burn_in_steps: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Same interface and MSD convention as `dynamics.simulate_ensemble`,
    for a rigid rod instead of a sphere. Center-of-mass MSD only (rotational
    motion isn't included in the returned MSD, matching what an experiment
    tracking a particle's centroid would measure)."""
    box = network.box_size
    contact = params.cross_radius + params.fiber_radius
    cutoff = interaction_cutoff if interaction_cutoff is not None else 5.0 * contact
    fiber_length = float(np.linalg.norm(network.ends[0] - network.starts[0])) if network.n_fibers else 0.0
    query_radius = cutoff + fiber_length / 2.0

    midpoints = (network.starts + network.ends) / 2.0
    fiber_tree = cKDTree(midpoints, boxsize=box) if network.n_fibers else None

    pos = rng.uniform(0.0, box, size=(n_particles, 2))  # kept UNWRAPPED throughout, like dynamics.py
    theta = rng.uniform(0.0, 2 * np.pi, size=n_particles)

    gamma_par, gamma_perp, gamma_rot = params.drag
    D_par, D_perp, D_rot = params.kT / gamma_par, params.kT / gamma_perp, params.kT / gamma_rot
    noise_par = np.sqrt(2.0 * D_par * params.dt)
    noise_perp = np.sqrt(2.0 * D_perp * params.dt)
    noise_rot = np.sqrt(2.0 * D_rot * params.dt)

    def step_displacement(wrapped_center, theta):
        """Force is computed from `wrapped_center` (must be in [0, box) for
        the fiber lookup); returns (translational displacement, new theta),
        NOT a new position, so the caller can add the displacement to a
        persistent unwrapped accumulator instead of losing track of true
        displacement across wrap boundaries."""
        if fiber_tree is not None:
            force, torque = _force_and_torque(wrapped_center, theta, network, fiber_tree, query_radius, params, box)
        else:
            force, torque = np.zeros((n_particles, 2)), np.zeros(n_particles)

        u_par = np.stack([np.cos(theta), np.sin(theta)], axis=-1)
        u_perp = np.stack([-np.sin(theta), np.cos(theta)], axis=-1)
        f_par = (force * u_par).sum(axis=-1)
        f_perp = (force * u_perp).sum(axis=-1)

        drift = (
            (f_par / gamma_par)[:, None] * u_par * params.dt
            + (f_perp / gamma_perp)[:, None] * u_perp * params.dt
        )
        trans_noise = (
            noise_par * rng.standard_normal(n_particles)[:, None] * u_par
            + noise_perp * rng.standard_normal(n_particles)[:, None] * u_perp
        )
        disp = drift + trans_noise

        rot_drift = (torque / gamma_rot) * params.dt
        rot_noise = noise_rot * rng.standard_normal(n_particles)
        new_theta = theta + rot_drift + rot_noise
        return disp, new_theta

    for _ in range(burn_in_steps):
        disp, theta = step_displacement(pos % box, theta)
        pos = pos + disp

    unwrapped = pos.copy()
    origin = unwrapped.copy()
    msd = np.zeros(n_steps + 1)
    msd[0] = 0.0

    for i in range(n_steps):
        disp, theta = step_displacement(pos % box, theta)
        pos = pos + disp
        unwrapped = unwrapped + disp
        msd[i + 1] = ((unwrapped - origin) ** 2).sum(axis=1).mean()

    t = np.arange(n_steps + 1) * params.dt
    return t, msd
