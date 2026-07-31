# IP / product angle

Date: 2026-07-23, updated 2026-07-31 after Gate 5. Written after Gate 4
(`docs/gate-result-phase3-realdata.md`) returned its result: fail on the pre-registered primary
criterion, pass on a secondary descriptive check. Gate 5
(`docs/gate-result-phase3-gate5-cagedfit.md`), a model-based follow-up run 2026-07-31, also failed.

## Bottom line

Per `docs/BUILD_PLAN.md`'s own sequencing rule, Phase 4 (IP and venture material) starts "only
after a phase-3-or-later gate has passed against real (not synthetic) data." Gate 4 did not pass on
its primary criterion. This document does not open Phase 4. It records what would need to be true
first, so that work does not have to be redone from scratch later, and states plainly that nothing
here is a green light to draft IP or funding material yet.

## What is not supported right now

- No claim that this pipeline can model real macromolecular drug-vehicle transport through
  tumor-like stroma with enough accuracy to be a product.
- No patent-eligibility argument, no tiered royalty model, no market-size figure. None of the
  excluded language from the original BMF source document (the Alice/Mayo argument, the tiered
  royalty model, the "$10 billion" market figure, the "10-fold" accumulation claim) is reused here,
  matching `venture/PLACEHOLDER.md`'s existing standard. Nothing is added under `venture/` by this
  memo.
- Cross-checked against memory `cv-claims-to-avoid`: this document makes no claim of a patent filed
  or pending, no accelerator or incubator acceptance, no disavowed calibration figures, and no named
  platform or product as already built. It describes a research prototype at a specific,
  documented validation stage, nothing more.

## What would need to be true first

- A real-data gate passing on its own pre-registered primary criterion, not only a secondary
  descriptive check. `gate-result-phase3-realdata.md` named two concrete paths to that: raw
  trajectory data from the arXiv:1909.05091 authors, or a model-based test (an explicit
  caged-diffusion functional form) that might detect the plateau earlier in the digitized figure's
  accessible range. The second has since been run as Gate 5
  (`docs/gate-result-phase3-gate5-cagedfit.md`) and also failed, more decisively than Gate 4; a
  well-constrained confined-diffusion fit still lost to a plain power law by 70-149 AICc points for
  the composite curve. Author outreach (`docs/author-outreach-draft.md`) was sent and remains
  unanswered as of 2026-07-31. Raw trajectory data is now the only remaining concrete path to a
  passing real-data gate; nothing further can be extracted from the existing digitized summary
  curves by changing the statistical test applied to them.
- Separately, and still entirely untested: the Mori-Zwanzig memory kernel has never been evaluated
  against any real data. Digitized ensemble curves cannot supply the per-trajectory time series
  `fit_mzmd` requires (`repo/src/ergofluids/mz/mzmd.py`); only raw trajectory data would make that
  test possible. A future product story built on the memory-kernel differentiator specifically
  depends on this, separate from the exponent-estimator gate above.

## If those conditions are eventually met: a speculative, contingent sketch

Everything below is explicitly a hypothesis about what could become a defensible angle, not a
present claim. None of it should be treated as validated, quoted, or used in any external material
until the conditions above are met.

- **Product framing**: a computational screening aid that estimates transport exponents for
  candidate macromolecule/vehicle combinations through characterized hydrogel or ECM-mimetic
  networks, from either tracked-particle data or literature figures, intended to help formulation
  scientists narrow candidates before committing to wet-lab diffusion assays.
- **Differentiator, if validated**: the Mori-Zwanzig memory-kernel extension. Gates 2 and 3 show
  (synthetic data only, so far) that a memory-augmented forecast beats a memoryless one on systems
  built to have genuine non-Markovian structure. Whether that translates into a measurable advantage
  on real transport data is exactly what has not yet been shown, and is the single most important
  open question before any product claim is made.
- **IP posture, if that point is reached**: start from an actual claim chart against real prior art
  in Koopman/DMD-based estimation and existing Mori-Zwanzig applications in soft matter physics,
  built once there is a validated real-data result to claim over. Not before.

## Explicit non-actions taken here

- Nothing added under `venture/` beyond the existing `PLACEHOLDER.md`.
- No patent claims drafted, no claim chart started.
- No revenue, market-size, or funding figures stated, sourced or unsourced.
