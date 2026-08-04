# Gate result: network_sim residual/classifier model, first validation

Date: 2026-08-04. This is a fresh technical bet, not a continuation of the Koopman/Mori-Zwanzig
approach, which failed its real-data gates (Gate 4, Gate 5). Kept intentionally lean: the author
asked to prioritize product building over publication this session, so this is a working-notes
result record, not manuscript prose.

## What this tests

Whether a small residual/classifier model, trained on self-generated Brownian-dynamics simulation
data, can beat the obstruction-scaling physics baseline (which always predicts normal diffusion,
exponent 1.0, since it only models a reduced diffusivity) at the two failure modes the literature
review identified: adhesion-driven and shape-driven deviation from that baseline.

## Method

`src/ergofluids/network_sim/`: a 2D overdamped Langevin/Brownian-dynamics simulator (`dynamics.py`)
of a probe particle among a random, static fiber network (`network.py`), with steric repulsion, an
optional short-range adhesive term, and a scoped aspect-ratio simplification (reduced effective
collision radius, not full rigid-body dynamics; see `dynamics.py`'s docstring for why). Fiber-force
lookups use a k-d tree (fiber midpoints, periodic `boxsize`) instead of a full
particles-by-fibers distance matrix, the difference between the sweep finishing in minutes and not
finishing at all. Simulation duration per condition is scaled to keep the free-diffusion RMS
displacement well under the box size, and each run includes a burn-in period before the MSD clock
starts; both were added after an initial run showed a spurious late-time superdiffusion artifact,
traced to periodic-tiling contamination and initial-condition relaxation respectively (see
`dynamics.py` docstrings).

Exponents are fit from simulated MSD curves with `ssa_denoise_exponent`
(`ergofluids.koopman.exponent`), the same estimator already validated (Gate 0/0b/0c/6) to be
unbiased on power-law-in-time curves. This is the only piece reused from the earlier,
now-superseded-for-this-purpose Koopman/MZ approach.

**Sweep** (`scripts/run_network_sweep.py`, `data/network_sim_sweep.csv`): 36 conditions (2 mesh
densities x 3 particle radii x 3 adhesion depths x 2 aspect ratios), each pooled over 3 independent
fiber-network realizations, 300 particles per realization.

**Model** (`residual_model.py`): a small random-forest regressor predicting the residual
(simulated exponent minus the baseline's flat 1.0 prediction) from adhesion depth, aspect ratio, and
confinement (particle radius / mean pore radius); a parallel random-forest classifier predicting a
coarse regime (normal / hindered / caged, from exponent thresholds 0.9 and 0.7). Validated by
leave-one-out (appropriate given the sweep's modest size, 36 conditions), not a single train/test
split.

## Result

The sweep itself shows a physically sensible, learnable structure before any model is fit: adhesion
depth systematically lowers the exponent (e.g. radius 0.5, dense mesh, sphere: 0.979 at adhesion 0
down to 0.796 at adhesion 4), and aspect ratio 3 (rod) consistently shows a *higher* (less
subdiffusive) exponent than aspect ratio 1 (sphere) at matched radius/adhesion, the same qualitative
direction Rokhforouz et al. 2025 report for real rod-like nanoparticles.

| metric | value |
|---|---|
| baseline MAE (always predict 1.0) | 0.0799 |
| residual-model MAE (leave-one-out) | 0.0300 |
| MAE reduction | 62% |
| classifier accuracy (leave-one-out) | 80.6% |
| majority-class baseline accuracy | 63.9% |

**The residual model beats the physics baseline by a wide margin out of sample, and the classifier
beats a naive majority-class guess.** This is the first real validation of this approach, on
self-generated simulation data, not yet on any real experimental dataset.

## What this does not show

- Nothing here has been tested against real experimental data. The sweep is internally consistent
  self-generated simulation data; whether the same residual/classifier approach transfers to real
  hydrogel/ECM systems is untested. This is the natural next gate, contingent on finding a suitable
  public dataset (see the earlier literature review's tractability notes).
- The regime distribution is imbalanced (23 normal / 12 hindered / 1 caged out of 36); the
  classifier's accuracy on the caged class specifically has essentially no statistical power from a
  single example and should not be trusted yet.
- The aspect-ratio effect is a scoped simplification (reduced effective collision radius), not a
  true rigid-body simulation; that it reproduces the right qualitative direction is encouraging, not
  a validation of quantitative accuracy.
- 2D, static fibers, one particle at a time (no particle-particle interaction). All stated
  plainly in `dynamics.py`'s module docstring, not just here.

## Update, 2026-08-05: rigid-body rods and an expanded sweep

`dynamics.py`'s aspect-ratio simplification (reduced effective collision radius) was replaced with
genuine rigid-body rod dynamics (`rod_dynamics.py`: position + orientation, anisotropic drag,
rotational diffusion, multi-point steric/adhesive interaction along the rod's length; see that
module's docstring for what's still simplified). The sweep grid was also expanded from 36 to 81
conditions (3 mesh densities x 3 radii x 3 adhesion depths x 3 aspect ratios, adding an
aspect_ratio=2.0 point), rerun with the new rod dynamics for all aspect_ratio > 1 conditions
(aspect_ratio = 1 still uses the original point-sphere dynamics; see `sweep.py`'s docstring for why
the two are not unified onto one code path).

| metric | 36-condition sweep (2026-08-04) | 81-condition sweep, rigid rods (2026-08-05) |
|---|---|---|
| baseline MAE | 0.0799 | 0.0993 |
| residual-model MAE (leave-one-out) | 0.0300 | 0.0348 |
| MAE reduction | 62% | **65%** |
| classifier accuracy (leave-one-out) | 80.6% | **82.7%** |
| majority-class baseline accuracy | 63.9% | 51.9% |
| regime distribution | 23 normal / 12 hindered / 1 caged | 42 normal / 37 hindered / 2 caged |

The result strengthened, not just grew: the wider grid produced a far more balanced regime
distribution, which is why the classifier's margin over the naive baseline nearly doubled (a 17-point
gap to a 31-point gap), not merely an artifact of a smaller majority class being easier to beat by
chance (baseline accuracy dropping from 63.9% to 51.9% reflects a harder, more balanced
classification task, and accuracy still rose regardless). The caged class remains thin (2 of 81) and
still should not be trusted on its own.

## Product interface

`scripts/predict_transport.py`: given particle radius, mesh pore radius, adhesion depth, and aspect
ratio, prints the baseline exponent, the corrected exponent, the predicted regime, and per-regime
probabilities. Refits both models from `data/network_sim_sweep.csv` on each call (cheap, given the
sweep's size); no separate model-serialization step yet.

## Bearing on the project

This is the working alternative to the failed Koopman/MZ transport-modeling thesis, built and
validated this session per the author's explicit direction to prioritize product building over
further publication work. IP/venture material still has not been drafted; per this project's
standing gating discipline (`venture/PLACEHOLDER.md`, memory `ergofluids-ip-gating-discipline`), that
should wait for real-data validation, not simulation-only validation, however promising.
