# Gate result: Phase 2, Gate 3 (Mori-Zwanzig on a caging test)

Date: 2026-07-22. Criteria and parameters locked in `docs/BUILD_PLAN.md` (Gate 3) before this
script was run at full scale, following a 30-trial pilot used only to size the protocol. Script:
`repo/scripts/run_gate3.py`, seed 20260726.

## What was tested

A fast Ornstein-Uhlenbeck fluctuation x(t) around a slowly, unboundedly diffusing hidden trap
center c(t) (`repo/src/ergofluids/data/caging.py`, `kappa=0.5`, `sigma_x=0.3`, `sigma_c=0.03`).
Only x is observed; c is discarded before fitting. This is mechanistically motivated by, not fit
to, the caging behavior arXiv:1909.05091 reports for the composite hyaluronan-collagen network:
a particle transiently confined by a locally deforming mesh, escaping only as the mesh relaxes.

**System check, done first**: a 150 to 300-trajectory ensemble MSD of x alone showed the expected
crossover, local log-log slope 0.18 over steps 1-8 (fast equilibration), 0.26 over steps 10-100
(confined, near-plateau), 0.65 over steps 200-400 (escape, rising toward diffusive). This confirms
the system produces a genuine caging-then-escape signature before it was used as a test case,
verified by `test_msd_shows_caging_then_escape_crossover` in `repo/tests/test_caging.py`.

60 independent trajectories, fitting window 100 steps, 10-step-ahead forecast horizon spanning the
plateau-to-escape region. n_ks=1 (memoryless) and n_ks=15 (memory) memory kernels, same MZMD port
used in Gate 2 (`repo/src/ergofluids/mz/mzmd.py`), fit per trajectory; forecast RMSE against the
true held-out continuation; paired bootstrap (2000 resamples) on the per-trajectory RMSE difference.

## Result

| | mean RMSE |
|---|---|
| memoryless (n_ks=1) | 0.3987 |
| memory (n_ks=15) | 0.3637 |

Paired difference (memoryless minus memory): point estimate 0.0350, 95% CI [0.0112, 0.0587].

**Verdict: PASS.** The CI excludes zero on the positive side. RMSE improves by about 9% (0.399 to
0.364), close to Gate 2's improvement, on a system deliberately built to be harder and more
physically relevant than Gate 2's generic linear hidden-variable case.

## What this does and does not establish

Two independent synthetic tests now support the same conclusion: the ported MZMD memory kernel
captures memory effects that a memoryless fit misses, both in a generic linear hidden-variable
system (Gate 2) and in a system built to mechanistically resemble the specific caging behavior
reported for the real target material (Gate 3). This is a stronger basis for the approach than
Gate 2 alone, and is the second and last synthetic gate planned before Phase 3 (real-data
acquisition, per `docs/BUILD_PLAN.md`).

It still does not validate anything against the paper's actual measurements. The caging system
here was designed to reproduce the qualitative MSD/ISF crossover the paper reports, not fit to any
of its specific numbers (mesh sizes, moduli, the composite network's ~0.5 subdiffusive exponent),
and it uses different underlying dynamics (an OU process with a diffusing trap center) than
whatever mechanism actually produces the real material's plateau. Phase 3 is the point at which
that gap gets addressed, with real or literature-digitized data, not before.
