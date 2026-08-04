"""A random fiber network in a 2D periodic box: fixed line segments scattered
uniformly at random (position, orientation, length), controlled by an areal
density that sets the mean pore size. This is a deliberate simplification of
a real hydrogel/ECM network (fibers are static, not thermally fluctuating;
2D, not 3D; a single length scale, not the polydisperse mesh a real gel has).
It is built to be internally self-consistent for testing whether a
physics-baseline-plus-residual-model approach can recover known structure
from simulated data, not to be a quantitative model of any specific real
material. See the module docstring in `../__init__.py` for how this differs
from the project's earlier Koopman/Mori-Zwanzig approach.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FiberNetwork:
    box_size: float
    starts: np.ndarray  # (n_fibers, 2)
    ends: np.ndarray  # (n_fibers, 2)

    @property
    def n_fibers(self) -> int:
        return self.starts.shape[0]

    def mean_pore_radius(self) -> float:
        """Ogston-style estimate: mean pore radius ~ 1 / sqrt(fiber line
        density), line density = total fiber length / box area. This is the
        standard scaling used by obstruction-scaling theory itself (see
        `baseline.py`), so the simulation's own notion of "mesh size" is
        defined the same way the physics baseline expects it, not by a
        separately invented convention."""
        lengths = np.linalg.norm(self.ends - self.starts, axis=1)
        line_density = lengths.sum() / self.box_size**2  # length per area
        return 1.0 / np.sqrt(line_density) if line_density > 0 else np.inf


def generate_network(
    box_size: float,
    n_fibers: int,
    fiber_length: float,
    rng: np.random.Generator,
) -> FiberNetwork:
    """Uniformly random fiber centers, orientations, and a fixed length."""
    centers = rng.uniform(0.0, box_size, size=(n_fibers, 2))
    angles = rng.uniform(0.0, 2 * np.pi, size=n_fibers)
    half = fiber_length / 2.0
    delta = np.stack([np.cos(angles), np.sin(angles)], axis=1) * half
    starts = centers - delta
    ends = centers + delta
    return FiberNetwork(box_size=box_size, starts=starts, ends=ends)


def point_segment_distance(points: np.ndarray, starts: np.ndarray, ends: np.ndarray) -> np.ndarray:
    """Plain (non-periodic) distance from each of `points` (n_pts, 2) to each
    segment defined by `starts`/`ends` (n_seg, 2). Returns (n_pts, n_seg).
    The network itself is not wrapped at the box edges (a fixed, finite
    patch of fibers); `dynamics.py` keeps the probe well inside the patch
    for the run length used, rather than implementing minimum-image
    wrapping, which is a deliberate simplification (see that module).

    Vectorized: broadcasts points against segments. For n_pts x n_seg beyond
    a few hundred thousand this becomes memory-heavy; callers should chunk if
    needed (not required at this project's sweep scale).
    """
    # points: (P, 1, 2), seg vectors: (1, S, 2)
    p = points[:, None, :]
    a = starts[None, :, :]
    b = ends[None, :, :]
    ab = b - a
    ap = p - a
    ab_len2 = (ab**2).sum(axis=-1)
    ab_len2 = np.where(ab_len2 == 0, 1e-12, ab_len2)
    t = (ap * ab).sum(axis=-1) / ab_len2
    t = np.clip(t, 0.0, 1.0)
    closest = a + t[..., None] * ab
    diff = p - closest
    return np.linalg.norm(diff, axis=-1)
