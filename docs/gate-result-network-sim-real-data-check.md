# Gate result: real-data check on the steric-only obstruction-scaling premise

Date: 2026-08-04. Kept lean per the author's direction to prioritize product building. This is a
narrower, more honest claim than "the network_sim model is validated against real data" would
suggest; read the scope section before the result.

## What this does and does not test

The `network_sim` residual/classifier model (`docs/gate-result-network-sim-residual-model.md`) has
**not** been calibrated or tested against real experimental numbers. Doing that properly would need a
real dataset reporting solute size, network mesh/fiber geometry in units comparable to the
simulator's, and diffusion measurements spanning both non-adhesive and adhesive solutes in the same
system, ideally as a single, unambiguous diffusion rate per solute rather than a multi-population fit
that needs interpretation.

No such dataset was found. What this check does instead: test the *premise* the residual-model
approach is built on, that pure steric (size-only) obstruction-scaling is insufficient once
chemical affinity is present, against real, independent data never used to build the simulator or
baseline.

## Data

Wang 2026 (*Pharmaceutics* 18(5):592, doi:10.3390/pharmaceutics18050592): PGSE NMR diffusion
coefficients of five model drugs in free solution and in a C18ADPA liquid-crystalline supramolecular
hydrogel, at pH 5.37. Table 1 (hydrodynamic radius, free-solution diffusivity) and Table 2 (in-gel
diffusivity, fit as one or two diffusive populations depending on the drug) were read directly from
the paper's own published tables, not estimated.

| drug | R_H (nm) | D_free (m^2/s) | D_gel, slow population (m^2/s) | D_gel/D_free |
|---|---|---|---|---|
| 5-fluorouracil | 0.23 | 7.714e-10 | 8.434e-11 | 0.109 |
| acetylcholine | 0.25 | 7.025e-10 | 2.084e-11 | 0.030 |
| paracetamol | 0.31 | 5.811e-10 | 1.186e-10 | 0.204 |
| prednisolone | 0.41 | 4.297e-10 | 3.719e-11 | 0.087 |
| amphotericin B | 0.60 | 2.950e-10 | 1.528e-10 | 0.518 |

`D_gel` here is each drug's slower ("Mode 2") diffusive population, the only one reported for
prednisolone and amphotericin B (fully hindered, no fast population at all) and the minority,
more-hindered population for the other three (which also show a faster, more free-like population).
Using this consistently across all five is an approximation stated plainly, not hidden: the physical
meaning of "the slow population's rate" is not perfectly identical between a drug that is entirely in
that population and one where it is a minority fraction. A cleaner test would use a single,
unambiguous rate per drug; this dataset does not offer one.

## Test

Steric-only obstruction-scaling (the baseline `network_sim` uses) requires relative diffusivity
(D_gel/D_free) to decrease as solute size increases, nothing else should matter. Spearman correlation
between R_H and D_gel/D_free across the five drugs:

**rho = +0.50 (p = 0.39, n = 5).**

Steric-only theory predicts a strongly *negative* rho. The observed correlation is not just weak, it
has the wrong sign: amphotericin B, the largest solute (R_H = 0.60 nm), has by far the *highest*
relative diffusivity (0.518) of the five, not the lowest a size-only account would require. With
n = 5 this is not a statistically powered test (p = 0.39), so the honest reading is "consistent with
failure of the steric-only account, not a small effect masked by noise," not a rejection at any
conventional significance threshold.

This matches the source paper's own stated conclusion in words ("transport is governed by host-guest
chemical affinity rather than molecular size"), now checked as a number rather than taken on trust.

A secondary categorical comparison (mean D_gel/D_free for the three drugs with a detectable
free-like fast population vs. the two with none) did not produce a clean, interpretable pattern
(0.114 vs. 0.302, the wrong direction from a naive "no fast population = more bound = lower ratio"
expectation), most likely because of the population-fraction ambiguity noted above. This is reported
rather than dropped, since it is the honest result, not a supporting one.

## Reading the result

Real, independent evidence that steric-only obstruction-scaling can fail badly, in the specific
qualitative way (chemical affinity dominating over size) that motivated building a residual/adhesion
axis on top of it in the first place. This is premise-level support, not a validation of
`network_sim`'s specific trained model, its simulated adhesion-depth parameterization, or its
quantitative accuracy on any real system. Those remain untested. The clearest next step, if pursued,
is finding or generating a dataset that reports mesh/fiber geometry in comparable units alongside
multiple solutes spanning both non-adhesive and adhesive cases with a single, unambiguous diffusion
rate each, which this dataset does not provide.

## Bearing on the project

Supports continuing to build on the network_sim direction rather than reverting to a steric-only
model, without claiming more than that. IP/venture material still does not open on this, per the
project's standing gating discipline; a premise-level real-data check is a weaker bar than the
real-data gate that discipline requires.
