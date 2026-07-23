# ErgoFluids

A research prototype testing whether Koopman operator / Dynamic Mode Decomposition
methods, extended with a Mori-Zwanzig memory kernel, can usefully model macromolecular
drug-vehicle transport through dense, non-Newtonian tumor tissue. Started from an idea
in `/root/research/BMF Unified Framework.docx` (Module 2), whose specific numeric claims
are treated as unverified until tested here; see `docs/concept-note.md`.

**Status (2026-07-23)**: Phase 1 through Phase 3 complete. Gate 1 (literature-anchored regime
separation, synthetic data) passed for all three estimators tested. Gate 0 (interval
calibration, synthetic data) failed for the original DMD/HODMD estimator with a diagnosed,
mechanistic bias; a replacement (Hankel-SVD denoising instead of HODMD's dynamic
reconstruction, called `ssa`) closed most of the gap, then a pre-registered higher-power
follow-up confirmed the one remaining shortfall was sampling noise, not real miscalibration.
Gate 0 now passes for `ssa`; `dmd` is retired from this pipeline. Gate 2 and Gate 3 test the
ported Mori-Zwanzig memory kernel (`repo/src/ergofluids/mz`), first on a generic linear
hidden-variable system, then on a caged-particle system built to mechanistically resemble the
literature target's reported plateau behavior; both pass, with memory-augmented forecasts
genuinely more accurate than memoryless ones (95% CIs on the improvement exclude zero in both
cases). Gate 4 (Phase 3) is the first test against real (literature-digitized, not synthetic)
data: Figure 4a and Supplementary Figure S14a of arXiv:1909.05091 were digitized from the
published PDF (`repo/scripts/digitize_fig4a.py`, `repo/scripts/digitize_s14a.py`, data in
`repo/data/digitized/`), and the `loglog`/`ssa` exponent estimators were tested against a
pre-registered criterion for the composite network's caging signature. **Gate 4 failed its
primary criterion**: the digitized MSD curve did not show a statistically significant local
slope decrease for the composite network within propagated digitization error, though a
secondary, non-pass/fail check on the ISF panel does show the qualitative plateau signature the
paper reports. Per `docs/BUILD_PLAN.md`'s phase sequencing, Phase 4 (IP/venture material) does
not proceed on this result. The Mori-Zwanzig memory kernel remains untested against any real
data (no public per-trajectory dataset exists for this system). No IP or venture material
exists. Details in `docs/gate-result-phase1-synthetic.md`, `docs/gate-result-phase2-mzmd.md`,
`docs/gate-result-phase2-gate3-caging.md`, `docs/gate-result-phase3-realdata.md`, and
`docs/BUILD_PLAN.md`.

## Layout

- `docs/`: concept note, literature map, build plan, gate results.
- `repo/`: the Python package (`src/ergofluids`), tests, and its own `.venv`.
- `venture/`: placeholder only, see `venture/PLACEHOLDER.md`.

## Running the code

```
cd repo
.venv/bin/python scripts/run_gate0.py
.venv/bin/python scripts/run_gate1.py
.venv/bin/python scripts/run_gate2.py
.venv/bin/python scripts/run_gate3.py
.venv/bin/python scripts/digitize_fig4a.py
.venv/bin/python scripts/digitize_s14a.py
.venv/bin/python scripts/run_gate4.py
.venv/bin/python -m pytest tests/ -q
```
