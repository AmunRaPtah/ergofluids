# Publication angle

Date: 2026-07-23. Written after Gate 4 (`docs/gate-result-phase3-realdata.md`) returned its result:
fail on the pre-registered primary criterion, pass on a secondary descriptive check. Everything
below is framed against that actual outcome, not against a hoped-for one.

## Bottom line

There is a modest, honest methods story here. There is not yet a "the pipeline works on real
tissue-like data" story, because Gate 4 did not show that on its primary, locked criterion.

## What is publishable now

1. **The Gate 0/0b/0c diagnosis.** HODMD showed a systematic, mechanistically explained bias
   (-0.026 to -0.054, worsening toward the end of the fitting window) when reconstructing
   power-law-in-time curves, because HODMD forward-simulates from a fitted eigenvalue decomposition
   and a power law is not a finite sum of exponentials in real time. Replacing dynamic
   reconstruction with SSA-style Hankel-SVD denoising (same delay embedding, no forward simulation)
   removed most of the bias, confirmed by a pre-registered 100-repeat follow-up (Gate 0c). This is a
   concrete, falsifiable, already-tested finding about when DMD-family estimators fail on
   subdiffusive curves and what fixes it. It stands on its own as a short methods note, independent
   of what Gate 4 found.

2. **The full pre-registered gate sequence (0 through 4) as a case study.** A Koopman/SSA exponent
   estimator plus a Mori-Zwanzig memory-kernel extension, validated stepwise on synthetic data
   (Gates 0-3, all passed), then tested against literature-digitized real data (Gate 4, failed on
   its primary criterion, passed a secondary descriptive check). Worth writing up precisely because
   it is not a clean win: it shows what synthetic validation does and does not guarantee once real
   (if indirect) data enters, and documents a specific failure mode, a short digitized Delta t range
   that captures the front part of a subdiffusive stretch but not the local flattening into a
   plateau, rather than treating "gate failed" as a dead end to bury.

3. **The digitization methodology itself.** Programmatic, color-segmented, tick-calibrated
   extraction with two separately tracked error sources (reported/paper error bars vs.
   digitization/pixel error), including three documented extraction bugs (frame-line, legend-swatch,
   and tick-mark contamination) and how each was caught and fixed. This is a reusable, checkable
   procedure for anyone digitizing figures for quantitative reuse, distinct from manual
   point-and-click tools, and is worth describing on its own regardless of what Gate 4 concluded.

## What is not publishable yet

- Any claim that this pipeline "validates," "confirms," or "demonstrates" Koopman/Mori-Zwanzig
  modeling of real macromolecular transport in tumor-like stroma. Gate 4's primary criterion, a
  measurable local slope decrease for the composite network within the digitized Delta t range, did
  not hold. The secondary ISF-plateau check does show a clear, statistically supported difference, but it was
  not part of the locked pass/fail rule and is weaker evidence by design.
- Any claim about the Mori-Zwanzig memory kernel's performance on real data. It has not been tested
  against real data of any kind. Digitized ensemble curves cannot supply the per-trajectory time
  series `fit_mzmd` requires; that gap is structural, not a matter of more digitization effort.

## Next steps, if pursuing publication

- Contact the arXiv:1909.05091 authors for raw trajectory data (the long-standing Phase 3 option
  that has not been attempted). Raw data would let the local-slope test probe further into the
  Delta t range where the plateau should actually appear, and would be the only way to test the
  memory kernel against anything real.
- Alternatively, as `gate-result-phase3-realdata.md` itself notes, a model-based test (fitting an
  explicit caged-diffusion functional form rather than comparing two-window OLS slopes) might detect
  the plateau earlier in the accessible range. This was deliberately not attempted post hoc, to
  avoid building a criterion around this specific dataset's outcome; it would need its own
  pre-registration before being run.
- Either path is required before any stronger claim than "the estimator pipeline and the
  digitization methodology both work as designed; the specific real-data test attempted here did
  not confirm the target signature within its primary criterion" is warranted.
