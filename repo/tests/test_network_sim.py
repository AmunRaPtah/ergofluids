"""Tests for the network_sim Brownian-dynamics simulator: the free-diffusion
limit (no fibers) should recover the analytically known diffusivity, and the
obstruction-scaling baseline should behave sensibly at its own limits."""

from __future__ import annotations

import numpy as np
import pytest

from ergofluids.network_sim.baseline import (
    baseline_predicted_exponent,
    obstruction_scaling_relative_diffusivity,
)
from ergofluids.network_sim.dynamics import SimParams, simulate_ensemble
from ergofluids.network_sim.network import generate_network, point_segment_distance


def test_free_diffusion_recovers_known_diffusivity_and_exponent():
    """No fibers: the simulator should reduce to a plain 2D random walk with
    MSD = 4 * D0 * t (2 spatial dimensions), a check independent of any
    fiber-interaction code."""
    rng = np.random.default_rng(0)
    net = generate_network(box_size=40.0, n_fibers=0, fiber_length=1.0, rng=rng)
    params = SimParams(box_size=40.0, particle_radius=1.0, dt=0.01)
    t, msd = simulate_ensemble(net, params, n_particles=300, n_steps=1500, rng=rng, burn_in_steps=0)

    mask = t > 0
    slope, intercept = np.polyfit(np.log(t[mask]), np.log(msd[mask]), 1)
    assert abs(slope - 1.0) < 0.1, f"free diffusion should be normal (slope~1), got {slope:.3f}"

    implied_D = np.exp(intercept) / 4.0
    assert abs(implied_D - params.free_diffusivity) / params.free_diffusivity < 0.15


def test_dense_obstruction_slows_diffusion_relative_to_free():
    """A dense fiber network should reduce the final MSD relative to the
    free-diffusion case with identical particle and duration, the basic
    physical sanity check the whole simulator rests on."""
    rng = np.random.default_rng(1)
    box = 30.0
    params = SimParams(box_size=box, particle_radius=0.6, dt=0.005)

    net_empty = generate_network(box_size=box, n_fibers=0, fiber_length=1.0, rng=np.random.default_rng(1))
    net_dense = generate_network(box_size=box, n_fibers=350, fiber_length=1.2, rng=np.random.default_rng(2))

    n_steps = 400
    _, msd_free = simulate_ensemble(net_empty, params, n_particles=200, n_steps=n_steps, rng=np.random.default_rng(10))
    _, msd_obstructed = simulate_ensemble(
        net_dense, params, n_particles=200, n_steps=n_steps, rng=np.random.default_rng(11)
    )
    assert msd_obstructed[-1] < msd_free[-1]


def test_point_segment_distance_matches_known_geometry():
    """A point directly above the midpoint of a horizontal segment should be
    at distance equal to its perpendicular offset; a point beyond the
    segment's end should be at distance to the nearest endpoint."""
    starts = np.array([[0.0, 0.0]])
    ends = np.array([[2.0, 0.0]])

    above_midpoint = np.array([[1.0, 3.0]])
    dist = point_segment_distance(above_midpoint, starts, ends)
    assert dist[0, 0] == pytest.approx(3.0)

    beyond_end = np.array([[5.0, 0.0]])
    dist2 = point_segment_distance(beyond_end, starts, ends)
    assert dist2[0, 0] == pytest.approx(3.0)  # distance to (2, 0)


def test_obstruction_scaling_limits():
    """Zero fiber density means no obstruction (D/D0 = 1); higher density or
    larger radii reduce D/D0 monotonically, the direction the physical model
    requires regardless of its absolute accuracy."""
    assert obstruction_scaling_relative_diffusivity(solute_radius=0.5, fiber_radius=0.1, fiber_line_density=0.0) == 1.0

    low = obstruction_scaling_relative_diffusivity(solute_radius=0.5, fiber_radius=0.1, fiber_line_density=0.1)
    high = obstruction_scaling_relative_diffusivity(solute_radius=0.5, fiber_radius=0.1, fiber_line_density=0.5)
    assert high < low < 1.0


def test_baseline_predicted_exponent_is_normal_diffusion():
    """The obstruction-scaling model predicts a reduced-rate but still
    normal (Fickian) diffusion; its implicit exponent prediction is always
    1.0, which is exactly the gap a residual/classifier model is meant to
    close for adhesive or anisotropic cases."""
    assert baseline_predicted_exponent(steric_only=True) == 1.0
    assert baseline_predicted_exponent(steric_only=False) == 1.0
