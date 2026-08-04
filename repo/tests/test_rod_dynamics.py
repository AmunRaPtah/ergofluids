"""Tests for rigid-body rod dynamics: the free-rod limit should match the
drag-coefficient predictions used to build it, and obstruction should
decrease (less subdiffusive) with increasing aspect ratio, the same
qualitative result the earlier reduced-collision-radius stand-in produced,
now from genuine multi-point rigid-body physics instead of a shortcut."""

from __future__ import annotations

import numpy as np

from ergofluids.koopman.exponent import ssa_denoise_exponent
from ergofluids.network_sim.network import generate_network
from ergofluids.network_sim.rod_dynamics import RodParams, simulate_rod_ensemble


def test_free_rod_recovers_average_of_parallel_and_perpendicular_diffusivity():
    """No fibers, long enough duration to cross the rotational relaxation
    time (so parallel/perpendicular anisotropy has averaged out): the
    isotropic long-time diffusivity should approach (D_par + D_perp) / 2."""
    rng = np.random.default_rng(0)
    net = generate_network(box_size=40.0, n_fibers=0, fiber_length=1.0, rng=rng)
    params = RodParams(box_size=40.0, particle_radius=1.0, aspect_ratio=4.0, dt=0.01)

    gamma_par, gamma_perp, gamma_rot = params.drag
    D_par, D_perp = params.kT / gamma_par, params.kT / gamma_perp
    rot_relaxation_time = gamma_rot / params.kT
    n_steps = int(7 * rot_relaxation_time / params.dt)  # several rotational relaxation times

    t, msd = simulate_rod_ensemble(net, params, n_particles=400, n_steps=n_steps, rng=rng, burn_in_steps=0)
    mask = t > 0
    slope, intercept = np.polyfit(np.log(t[mask]), np.log(msd[mask]), 1)
    assert abs(slope - 1.0) < 0.1, f"free rod should show normal diffusion at long times, got slope {slope:.3f}"

    implied_D = np.exp(intercept) / 4.0
    expected_D = (D_par + D_perp) / 2.0
    assert abs(implied_D - expected_D) / expected_D < 0.2


def test_elongated_rods_are_less_obstructed_than_short_ones():
    """Same network, same nominal particle_radius, increasing aspect_ratio:
    the recovered exponent should increase (less subdiffusive), matching
    the qualitative literature finding (Rokhforouz et al. 2025) this
    project's aspect-ratio axis is built to capture."""
    rng = np.random.default_rng(2)
    box = 30.0
    net = generate_network(box_size=box, n_fibers=350, fiber_length=1.2, rng=rng)

    exponents = []
    for i, aspect in enumerate([1.5, 4.0]):
        params = RodParams(box_size=box, particle_radius=0.5, aspect_ratio=aspect, dt=0.01)
        t, msd = simulate_rod_ensemble(
            net, params, n_particles=300, n_steps=800, rng=np.random.default_rng(50 + i), burn_in_steps=300
        )
        exponents.append(ssa_denoise_exponent(t, msd))

    assert exponents[1] > exponents[0], (
        f"expected higher aspect ratio to show a higher (less subdiffusive) exponent, got {exponents}"
    )


def test_rod_geometry_reduces_correctly_at_aspect_ratio_one():
    params = RodParams(box_size=10.0, particle_radius=0.7, aspect_ratio=1.0)
    assert params.cross_radius == params.half_length == 0.7
