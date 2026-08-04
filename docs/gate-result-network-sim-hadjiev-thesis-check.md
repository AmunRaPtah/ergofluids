# Gate result: obstruction-scaling baseline checked against Hadjiev's thesis data

Date: 2026-08-04. Kept lean per the author's direction to prioritize product building.

## What this improves on

`docs/gate-result-network-sim-real-data-check.md` tested the *premise* behind the residual model
(steric-only obstruction-scaling fails once chemical affinity matters) using Wang 2026, a real but
structurally different gel system with no reported mesh geometry compatible with `network_sim`'s
parameterization. This check goes further: it tests the obstruction-scaling formula itself
(`network_sim.baseline`) against real diffusion data in a system built specifically to test that
exact model, using real, matched physical parameters.

## Data

Hadjiev, N. (2014). *FRAP Measurements of Solute Diffusion Through Hydrogels*. MASc thesis, Queen's
University, supervised by Brian Amsden (the obstruction-scaling model's own author). Open access via
Queen's institutional repository (handle 1974/12603). This is the underlying work behind Hadjiev &
Amsden 2015 (J Control Release, doi:10.1016/j.jconrel.2014.12.010), with more detail than the journal
paper: four FITC-dextran probes (4, 10, 20, 40 kDa; hydrodynamic radii 1.4, 2.3, 3.3, 4.5 nm, the
thesis's own Table 2) diffusing via FRAP in alginate-methacrylate hydrogels across polymer volume
fractions 0-3%, plus a directly reported fiber (polymer chain) radius of 0.83 nm (Section 4.6, SAXS).

The thesis's own Figures 15 and 16 (real FRAP measurements plus the thesis's own obstruction-model
reference curve) were digitized with this project's own tool
(`scripts/_hadjiev_fig1{5,6}_*.spec.json`, gitignored configs; output in
`data/digitized/hadjiev2014_fdx*.csv`), then clustered into one representative point per marker
(`scripts/check_hadjiev_thesis_real_data.py`).

## Method

`network_sim.baseline` uses a straight-fiber line-density parameterization, not the thesis's own
correlation-length/blob-scaling derivation (which needs the native alginate's molecular weight, not
extracted here). Rather than reproducing their full polymer-physics chain, one free parameter, a
proportionality constant `k` linking polymer volume fraction to `network_sim`'s fiber-line-density
(`L = k * Phi`), was fit two ways: once globally (single `k` across all four probes' real data by
least squares) and once per solute (separate `k` fit to each probe's own six real data points), using
their real hydrodynamic radii and fiber radius throughout, not assumed values.

## Result

**Global fit** (one `k` for all four probes, `k = 0.0066`): mean absolute error 0.073 for the two
small probes (FDX-4, FDX-10) and 0.062 for the two large probes (FDX-20, FDX-40), essentially flat, not the
clean "small probes fit well, large probes fit badly" pattern the thesis describes qualitatively for
its own (differently-parameterized) model. This is reported as it came out, not adjusted to match the
narrative.

**Per-solute fit** (`k` allowed to vary by probe) surfaced the real, more precise finding: the
best-fit `k` decreases monotonically with probe size, from 0.0107 (FDX-4) to 0.0095 (FDX-10) to 0.0069
(FDX-20) to 0.0045 (FDX-40), a 2.4x drop from smallest to largest probe. Since `k` represents a
property of the network (effective fiber density per unit polymer), not of the probe, a
correctly-specified steric-only model fit to a single real network should need the *same* `k`
regardless of which probe is diffusing through it. It does not: larger probes need a systematically
sparser effective network to fit their own data, meaning they access more free volume than a
probe-invariant steric picture allows. This is the same direction, now as a number instead of a
described pattern, as the thesis's own reptation-based explanation (large, flexible dextran coils
weave through the network more like a snake than a rigid sphere, reducing the tortuosity a purely
steric model assumes).

## What this does and does not show

- Real, quantitative confirmation that a probe-invariant, purely steric parameterization of
  obstruction-scaling breaks down as a function of probe size in a real system, in the mechanistic
  direction the literature (reptation, this thesis; and separately, adhesion, Wang 2026) predicts.
  This is now two independent real datasets, testing two different mechanisms (adhesion, reptation),
  both showing the same qualitative failure mode: a single steric parameter is not enough.
- Does not validate `network_sim`'s simulated adhesion-depth or aspect-ratio axes specifically:
  reptation (a flexible-chain effect) is mechanistically distinct from either adhesion or the rigid
  aspect-ratio simplification `dynamics.py` uses, so this is corroborating evidence for the general
  premise, not a direct test of those specific model axes.
- Does not validate the full Brownian-dynamics simulator (`network_sim.dynamics`) against real data,
  only the closed-form baseline formula (`network_sim.baseline`); parameterizing the simulator itself
  to reproduce a real system's exact fiber geometry remains undone.

## Bearing on the project

A second, independent, real, matched-parameter data point supporting the same conclusion as the
Wang 2026 check: real systems need more than a probe-invariant steric account. Strengthens the case
for the residual-model direction generally. IP/venture material still does not open on this, per the
project's standing gating discipline; this is a stronger real-data check than the Wang 2026 one, but
still short of validating network_sim's own trained predictions.
