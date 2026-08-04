# ErgoFluids / network_sim: Everything Explained Simply

> Last updated: 4 August 2026
> Draft pitch-prep material. Not sent anywhere yet. Every number here is either real-data-checked or
> explicitly labeled simulation-only; see "Where the product stands" before using this externally.

---

## 1. WHAT IT DOES (In One Sentence)

Predicts how well a candidate drug or macromolecule will move through a hydrogel or ECM-like network,
and tells a formulation scientist which untested candidate to measure next, so fewer wet-lab
diffusion assays are needed to find a workable formulation.

---

## 2. THE PROBLEM

Formulation scientists screening drug-delivery vehicles need to know how a candidate will diffuse
through a hydrogel before committing to a wet-lab assay (FRAP, PGSE-NMR, single-particle tracking,
all slow and equipment-heavy). The standard computational shortcut, obstruction-scaling theory, is
real and does work for simple cases: Hadjiev & Amsden (2015, J Control Release) validated it to
within 15% for spherical, non-adhesive solutes. But it has two documented, real failure modes:

- **Chemical affinity**: Wang (2026, Pharmaceutics) measured five real drugs in a hydrogel by PGSE
  NMR and found relative diffusivity had no relationship, or the wrong-signed one, to solute size
  (Spearman rho = +0.50, where steric theory requires strongly negative). The largest solute tested
  diffused *fastest* relative to its own free-solution rate.
- **Chain flexibility / shape**: Hadjiev's own 2014 thesis data (four real FITC-dextran probes in
  real alginate hydrogels) shows the model's own steric parameter isn't probe-invariant: fit
  separately per probe, it drops 2.4x from the smallest to the largest solute, the signature of
  large, flexible probes accessing more free volume than a rigid-sphere picture allows.

Nobody currently ships a tool that predicts *when* the simple model will fail and *why*, or that
tells a lab which candidate to test next once they have a little of their own data.

---

## 3. THE SOLUTION

Two pieces, reflecting two different bets on how much a lab already knows:

**A residual/classifier model** (`network_sim`), built on a self-generated 2D Brownian-dynamics
simulator of a probe particle in a random fiber network (steric repulsion, adhesion, a shape
simplification), fit against the obstruction-scaling baseline's own blind spot. On the simulator's
own 36-condition sweep: cuts prediction error 62% versus the baseline alone (MAE 0.030 vs 0.080,
leave-one-out), and a regime classifier (normal/hindered/caged) beats a naive majority-class guess
(80.6% vs 63.9%).

**An active-learning recommender**, for labs that already have a handful of real pilot measurements
and don't need a zero-shot predictor to get value: a Gaussian Process suggests which untested
candidate to measure next (uncertainty sampling, or a target-seeking mode for release profiles where
"more Fickian" isn't the goal). Validated synthetically (the simulator's own sweep as a queryable
oracle): 28% lower held-out error than random candidate selection, averaged over 8 seeds.

---

## 4. HOW WELL DOES IT WORK? (The Numbers, Honestly Separated by Evidence Type)

### 4.1 Simulation-only validation (the model's own internal consistency)

| Metric | Value |
|---|---|
| Residual model MAE reduction vs baseline (leave-one-out) | 62% (0.030 vs 0.080) |
| Regime classifier accuracy vs majority-class baseline | 80.6% vs 63.9% |
| Active-learning MAE reduction vs random sampling | 28% (0.0253 vs 0.0352) |

All three numbers come from the simulator's own self-generated data, not real experiments. Real,
useful signal that the modeling approach and the acquisition strategy both work as designed. Not
evidence the numbers transfer to a real system.

### 4.2 Real-data checks (two independent real datasets, neither used to build the model)

| Check | Dataset | Finding |
|---|---|---|
| Premise check | Wang 2026, real PGSE NMR, 5 drugs | Steric-only theory gets the sign wrong: rho = +0.50, requires << 0 |
| Baseline formula check | Hadjiev 2014 thesis, real FRAP, 4 real dextran probes | Steric-only parameter drifts 2.4x with probe size, not probe-invariant as required |

Both real, both independent, both show the same qualitative failure by different mechanisms
(adhesion; chain flexibility). Neither validates `network_sim`'s own trained predictions on a real
system, only the premise that a residual/classifier layer on top of the baseline is the right kind of
fix.

### 4.3 What has not been done

The model has never been tested end to end on a real system: real solute, real network, real measured
outcome, compared to the model's own prediction. That is the next gate, and it is the one an
incubator or a design partner should expect to hear about honestly, not glossed over.

---

## 5. THE HISTORY (Why This Isn't the Original ErgoFluids Thesis)

ErgoFluids began (2026-07-22) testing whether Koopman-operator/Dynamic-Mode-Decomposition methods,
extended with a Mori-Zwanzig memory kernel, could model this same transport problem from literature-
digitized MSD curves. That thesis passed every synthetic gate, then failed its real-data test twice
(Gate 4, Gate 5): the digitized curve didn't show a statistically significant caging signature within
its own pre-registered criterion, and a follow-up model-based refit failed more decisively. No IP or
product material was drafted on that result. Full detail: `HANDOFF.md` (Koopman/MZ history section),
`docs/gate-result-phase3-realdata.md`, `docs/gate-result-phase3-gate5-cagedfit.md`.

**The pivot (2026-08-04)**: rather than force a product claim onto a failed thesis, or repackage the
same failed claim under a new name, the underlying problem was re-approached with a different
technical bet, reusing only what had actually validated (the exponent-estimation and digitization
tooling), on the same rigor discipline (pre-registered criteria, honest reporting of what fails).
This is the same discipline that killed the original TDA thesis behind Topologix before it became a
venture; see memory `cct-and-topologix-research` for the parallel.

---

## 6. THE COMPETITION

| Who | What | Limitation | Difference here |
|---|---|---|---|
| Obstruction-scaling (Amsden) | Real-data-validated closed-form baseline | Probe-invariant steric assumption breaks for adhesive or flexible/large solutes (shown above, on real data) | Residual layer targets exactly this gap |
| Gurel, Leenstra & Giuntoli 2025 (Soft Matter) | CG-MD + Gaussian process for confined-mobility metric | Simulation-only validation, no real-data check published | Same model class (GP), plus two independent real-data checks on the underlying premise |
| WebPlotDigitizer-style tools | General figure digitization | No domain-specific exponent fitting or uncertainty propagation | This project's own digitizer tool (separate JOSS track) adds calibrated exponent extraction |

---

## 7. THE FOUNDER

Eniola Olutogun. Licensed pharmacist, computational pharmacologist, MSc Digital Health candidate
(HPI/Potsdam). Same technical toolkit already applied to Topologix (protein language model embeddings
for drug-resistance prediction) and the CCT model (Bayesian ODE fitting): the pattern across all three
is the same, test the obvious thesis honestly, kill it if it fails, and only build product material on
what survives.

### 7.1 The focus question, addressed directly

Topologix is the founder's active incubator pitch. Pitching this alongside it risks the exact "can't
focus" signal already flagged as the single biggest investor risk for Topologix itself (see memory
`topologix-comprehensive-overview`, section on the founder's prior 25-venture scatter). This material
exists so the option is ready, not so it is used reflexively; the decision to pitch it now, later, or
not as a separate venture at all, is a live one, not resolved by this document existing.

---

## 8. WHERE THE PRODUCT STANDS

| Dimension | Status |
|---|---|
| Working pipeline | Yes: simulator, baseline, residual model, classifier, active-learning recommender, all with passing tests (33) |
| Real-data validation of the model itself | No: two independent real-data *checks* on the underlying premise, zero end-to-end real predictions checked |
| Design partner | No: outreach drafted (`docs/design-partner-outreach-draft.md`), not sent |
| Productised interface | Partial: CLI tools (`predict_transport.py`, `recommend_next_experiment.py`), no web app or API |
| Incorporation | No |
| IP / patents | None filed, none drafted; project's own gating discipline (`venture/PLACEHOLDER.md`) explicitly blocks this until a real-data gate passes |
| Team | Solo founder |
| Revenue | $0, pre-revenue, pre-pilot |
| Source code | Public repo, `github.com/AmunRaPtah/ergofluids` |

---

## 9. THE HONEST ONE-PARAGRAPH PITCH

"Obstruction-scaling theory is the real-data-validated standard for predicting drug transport through
hydrogels, but it has two documented failure modes, chemical affinity and chain flexibility, that we
confirmed independently on two real datasets neither used to build our model. We built a residual
layer and an active-learning recommender on top of it, validated so far on self-generated simulation
data with strong internal results (62% error reduction, 28% fewer experiments needed). We're
pre-revenue, pre-partner, and the next real step is exactly what it should be: find one lab willing to
test it against real data."

---

*This document is pitch-prep material, not a pitch that has been sent. Update the "Where the product
stands" table before using any part of this externally, and re-check every number against the
gate-result docs it cites, they are the source of truth, not this summary.*
