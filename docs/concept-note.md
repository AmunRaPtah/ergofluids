# ErgoFluids: concept note

Status: pre-validation. No result in this document has been tested yet.

## Origin

ErgoFluids started as Module 2 of a 22-module conceptual framework, "Bio-Mathematical Frontiers"
(BMF), found in `/root/research/BMF Unified Framework.docx`, signed "OIQB / Olutogun Institute of
Quantitative Biosciences," June 2026. That document proposes modeling macromolecular drug-vehicle
transport through dense, non-Newtonian tumor stroma as a nonlinear chaotic dynamical system, using
Koopman operator theory and a Mori-Zwanzig projection.

The BMF document contains no citations for any of its numeric or clinical claims. A search of this
machine found no code, no data, and no prior experiment for ErgoFluids anywhere. The document's
sibling module with real code behind it, Module 1 (TopoLogic Bio, built as Topologix), was tested
against five pre-registered gates and failed all five. This concept note treats the BMF text as a
source of a mathematical idea worth testing, not as a record of results.

## The idea, restated

Model how a drug-carrying nanoparticle or macromolecule moves through dense tissue such as
desmoplastic tumor stroma, a mesh of hyaluronic acid and collagen fibers with high interstitial
pressure and non-Newtonian mechanics. Two components:

1. **Koopman operator / Dynamic Mode Decomposition (DMD).** Treat the local tissue state (position,
   shear stress, viscoelastic strain) as a point on a manifold evolving under some unknown nonlinear
   dynamics. The Koopman operator advances scalar observables of that state linearly in time, even
   though the underlying dynamics are nonlinear, which makes the system amenable to spectral
   analysis (eigenvalues, eigenfunctions, modes). DMD estimates that operator from time-series data.
2. **Mori-Zwanzig projection.** Real tissue transport has memory: the fiber mesh deforms and relaxes
   on multiple timescales, so a Markovian (memory-free) model misses real physics. The Mori-Zwanzig
   formalism derives a generalized Langevin equation with an explicit memory-kernel term, and
   "Mori-Zwanzig Mode Decomposition" (MZMD) extends DMD to fit that memory kernel from data.

## Claims from the BMF document, and their status

| Claim in BMF doc | Status |
|---|---|
| "Demonstrated 10-fold increase in deep-tumor drug accumulation in desmoplastic pancreatic stroma" | **UNVERIFIED.** No source, dataset, or experiment cited. No such experiment exists on this machine. |
| "Isolation of tissue resonance windows where tailored nanoparticle geometries... encounter minimized physical resistance" | **UNVERIFIED.** Presented as a capability, not a measured result. |
| Patent eligibility argument under Alice/Mayo (Section 5) and a tiered royalty/revenue model citing a "$10 billion" synthetic royalty market (Section 6) | **NOT ADOPTED.** No source for the market figure. This language is not reused in any IP or venture material for this project. See memory `cv-claims-to-avoid` for why: prior instances of unsourced patent and figure claims in this workspace had to be publicly retracted. |

## What is actually novel here, stated narrowly

The tumor-transport modeling space is not empty. Baxter-Jain transport equations, PBPK models with
diffusion terms, and PhysiCell (an open-source agent-based tumor simulator) are established tools
already used for this problem. The specific, defensible claim worth testing is narrow: whether a
data-driven, reduced-order model (DMD/EDMD plus a Mori-Zwanzig memory kernel) can match or
complement continuum PBPK and agent-based models on real diffusion data, at lower computational
cost or with less mechanistic assumption-baking. That is a modeling-methods question, not a claim
of a new physical theory of tumor transport. See `literature-map.md` for the prior art this sits
next to.

## What "validated" will mean here

Following the discipline documented in `/root/projects/cct-bayesian-validation/REPORT.md` and in
Topologix's `gate-result-*.md` files: state a pass/fail criterion before running the experiment,
test it against real public data, report the result honestly including any convergence problems or
discrepancies, and do not carry a claim forward into IP or venture material until it has passed a
gate. The first such gate is defined in `BUILD_PLAN.md`.
