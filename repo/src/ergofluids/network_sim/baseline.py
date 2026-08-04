"""Obstruction-scaling model: a real-data-validated physical baseline for
solute diffusion in a fibrous/polymer network, predicting the relative
diffusivity D/D0 from the fiber (obstacle) radius, the solute radius, and the
polymer volume fraction. Hadjiev & Amsden (J Control Release, 2015,
doi:10.1016/j.jconrel.2014.12.010) tested this exact functional form against
FRAP-measured diffusion coefficients in alginate hydrogels and found
predictions within +/-15% of measured values for near-spherical,
non-adhesive solutes; see ../../../docs/gate-result-* for how that finding
was used to scope this project's product direction.

D/D0 = exp( -pi * (fiber_radius + solute_radius)^2 * fiber_density )

Standard Ogston-style obstruction form, `fiber_density` a line-length-per-area
term (the same convention `network_sim.network.FiberNetwork.mean_pore_radius`
uses, so a simulated network's own "mesh size" and this baseline's expected
input are defined consistently, not by two different, incompatible
conventions).
"""

from __future__ import annotations

import numpy as np

from ergofluids.network_sim.network import FiberNetwork


def obstruction_scaling_relative_diffusivity(
    solute_radius: float,
    fiber_radius: float,
    fiber_line_density: float,
) -> float:
    """D/D0 predicted by the obstruction-scaling model. `fiber_line_density`
    is total fiber length per unit area (the same quantity
    `FiberNetwork.mean_pore_radius` is derived from)."""
    return float(np.exp(-np.pi * (fiber_radius + solute_radius) ** 2 * fiber_line_density))


def obstruction_scaling_from_network(solute_radius: float, network: FiberNetwork, fiber_radius: float) -> float:
    lengths = np.linalg.norm(network.ends - network.starts, axis=1)
    fiber_line_density = float(lengths.sum() / network.box_size**2)
    return obstruction_scaling_relative_diffusivity(solute_radius, fiber_radius, fiber_line_density)


def baseline_predicted_exponent(steric_only: bool) -> float:
    """The obstruction-scaling model predicts a relative *diffusivity*, not a
    time-dependent exponent; it describes long-time, unhindered (normal)
    diffusion at a reduced rate, not subdiffusion. Its own implicit
    prediction for the MSD's power-law exponent is therefore 1.0 (normal
    diffusion, just slower) whenever obstruction is purely steric. This
    function exists so callers have an explicit, named baseline exponent to
    compute a residual against, rather than hardcoding `1.0` at each call
    site. `steric_only` is accepted for interface clarity even though the
    model has no adhesive-case prediction to branch on: adhesion, and the
    departure from exponent 1.0 it can cause, is exactly what the model does
    not capture, which is the point of learning a residual on top of it."""
    return 1.0
