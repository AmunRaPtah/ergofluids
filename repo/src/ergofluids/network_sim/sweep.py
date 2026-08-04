"""Run the Brownian-dynamics simulator across a parameter grid (mesh size,
particle radius, adhesion depth, aspect ratio), fit an exponent to each
resulting MSD curve with the already-validated `ssa` estimator, and record
the obstruction-scaling baseline and residual for each condition.

Simulation duration is scaled per condition so the free-diffusion RMS
displacement stays well under the box size (`TARGET_FREE_RMS`), avoiding a
periodic-tiling artifact (spurious late-time superdiffusion) seen when a
fixed step count let small, fast-diffusing particles' RMS displacement
approach the box size; see `dynamics.py`'s `burn_in_steps` docstring for the
related initial-condition relaxation fix.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from ergofluids.koopman.exponent import ssa_denoise_exponent
from ergofluids.network_sim.baseline import baseline_predicted_exponent, obstruction_scaling_from_network
from ergofluids.network_sim.dynamics import SimParams, simulate_ensemble
from ergofluids.network_sim.network import generate_network

BOX_SIZE = 40.0
FIBER_LENGTH = 1.5
TARGET_FREE_RMS = 6.0  # << box size, avoids periodic-tiling contamination
MIN_STEPS = 250
DT = 0.005
N_PARTICLES = 300
BURN_IN_STEPS = 300
N_NETWORK_REALIZATIONS = 3  # independent fiber patches per condition, pooled


@dataclass
class SweepCondition:
    n_fibers: int  # controls mesh size
    particle_radius: float
    adhesion_depth: float
    aspect_ratio: float


@dataclass
class SweepResult:
    n_fibers: int
    particle_radius: float
    adhesion_depth: float
    aspect_ratio: float
    mean_pore_radius: float
    simulated_exponent: float
    baseline_exponent: float
    residual: float
    n_steps: int
    seed: int


def run_condition(cond: SweepCondition, seed: int) -> SweepResult:
    rng = np.random.default_rng(seed)
    params = SimParams(
        box_size=BOX_SIZE,
        particle_radius=cond.particle_radius,
        aspect_ratio=cond.aspect_ratio,
        adhesion_depth=cond.adhesion_depth,
        dt=DT,
    )
    D0 = params.free_diffusivity
    n_steps = max(int((TARGET_FREE_RMS**2 / (4 * D0)) / DT), MIN_STEPS)

    pooled_msd = None
    pore_radii = []
    baseline_exps = []
    for realization in range(N_NETWORK_REALIZATIONS):
        net = generate_network(
            box_size=BOX_SIZE, n_fibers=cond.n_fibers, fiber_length=FIBER_LENGTH, rng=rng
        )
        pore_radii.append(net.mean_pore_radius())
        rel_D = obstruction_scaling_from_network(cond.particle_radius, net, fiber_radius=params.fiber_radius)
        baseline_exps.append(rel_D)  # not used as exponent directly; recorded for diagnostics only

        t, msd = simulate_ensemble(
            net, params, n_particles=N_PARTICLES, n_steps=n_steps, rng=rng, burn_in_steps=BURN_IN_STEPS
        )
        pooled_msd = msd.copy() if pooled_msd is None else pooled_msd + msd

    pooled_msd /= N_NETWORK_REALIZATIONS
    exponent = ssa_denoise_exponent(t, pooled_msd)
    baseline_exp = baseline_predicted_exponent(steric_only=(cond.adhesion_depth == 0))

    return SweepResult(
        n_fibers=cond.n_fibers,
        particle_radius=cond.particle_radius,
        adhesion_depth=cond.adhesion_depth,
        aspect_ratio=cond.aspect_ratio,
        mean_pore_radius=float(np.mean(pore_radii)),
        simulated_exponent=float(exponent),
        baseline_exponent=baseline_exp,
        residual=float(exponent - baseline_exp),
        n_steps=n_steps,
        seed=seed,
    )


def build_grid() -> list[SweepCondition]:
    conditions = []
    for n_fibers in (250, 450):  # sparser / denser mesh
        for radius in (0.25, 0.5, 0.9):
            for adhesion in (0.0, 1.5, 4.0):
                for aspect in (1.0, 3.0):
                    conditions.append(
                        SweepCondition(
                            n_fibers=n_fibers,
                            particle_radius=radius,
                            adhesion_depth=adhesion,
                            aspect_ratio=aspect,
                        )
                    )
    return conditions


def run_sweep(seed_base: int = 0) -> list[SweepResult]:
    results = []
    for i, cond in enumerate(build_grid()):
        results.append(run_condition(cond, seed=seed_base + i))
    return results


def results_to_records(results: list[SweepResult]) -> list[dict]:
    return [asdict(r) for r in results]
