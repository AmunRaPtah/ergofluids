# Publication angle

Date: 2026-07-23, updated 2026-07-31 after Gate 5 and Gate 7. Written after Gate 4
(`docs/gate-result-phase3-realdata.md`) returned its result: fail on the pre-registered primary
criterion, pass on a secondary descriptive check. Everything below is framed against that actual
outcome, not against a hoped-for one. Gate 5 (`docs/gate-result-phase3-gate5-cagedfit.md`), a
model-based follow-up test run 2026-07-31, also failed; see "Next steps" below for what that
changes.

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

2. **The full pre-registered gate sequence (0 through 5) as a case study.** A Koopman/SSA exponent
   estimator plus a Mori-Zwanzig memory-kernel extension, validated stepwise on synthetic data
   (Gates 0-3, all passed), then tested against literature-digitized real data two independent ways
   (Gate 4, a fixed-window local-slope comparison, failed on its primary criterion but passed a
   secondary descriptive check; Gate 5, a whole-curve nonlinear model comparison, failed more
   decisively). Worth writing up precisely because it is not a clean win: it shows what synthetic
   validation does and does not guarantee once real (if indirect) data enters, and documents a
   specific, reproduced-two-ways failure mode, a short digitized Delta t range that captures the
   front part of a subdiffusive stretch but not the local flattening into a plateau, rather than
   treating "gate failed" as a dead end to bury.

3. **The digitization methodology itself.** Programmatic, color-segmented, tick-calibrated
   extraction with two separately tracked error sources (reported/paper error bars vs.
   digitization/pixel error), including three documented extraction bugs (frame-line, legend-swatch,
   and tick-mark contamination) and how each was caught and fixed. This is a reusable, checkable
   procedure for anyone digitizing figures for quantitative reuse, distinct from manual
   point-and-click tools, and is worth describing on its own regardless of what Gate 4 concluded. Now
   backed by a quantified accuracy number rather than only the qualitative shape checks in
   `test_digitization.py`: Gate 7 (`docs/gate-result-gate7-digitization-accuracy.md`) tested the
   shared extraction machinery against a synthetic panel with known ground truth, rendered through
   the same PDF-to-PNG path the real scripts use, and passed both pre-registered checks well inside
   threshold (curve-following median relative error 0.35% against a <2% bar; error-bar recovery
   median relative error 1.15% with Pearson r=0.991 against a <15%/>0.8 bar). Scope, stated in the
   gate itself: this validates the extraction code given correct axis calibration, not whether the
   two real scripts' hand-read tick-mark pixel positions were themselves correct, since no
   independent ground truth exists for that step on the real PDF pages.

   Since generalized into a config-driven tool (`src/ergofluids/digitize/`, 2026-08-04) and tested a
   second, independent way: Gate 8 (`docs/gate-result-gate8-external-real-figure-validation.md`) ran
   the generalized pipeline, including programmatic tick-mark calibration, on a real figure never
   used anywhere else in this project (Zhao et al., *Nature Communications* 2026,
   doi:10.1038/s41467-026-74008-w), recovering an exponent of 0.852 against the paper's own labeled
   value of 0.85. This is the first test of the tool on a figure neither it nor its authors had seen
   before, and it also surfaced a genuine limitation worth reporting alongside the pass: for figures
   with no plotted error bars, `reported_error` can be contaminated by other page content (here, a
   slope-reference annotation line), producing an uncalibrated confidence interval even when the
   point estimate is accurate. Both the pass and the limitation belong in the write-up.

   A third, independent pass followed: Gate 9 (`docs/gate-result-gate9-second-real-figure-validation.md`)
   tested a different curve, color, and target value in the same paper (0.918 recovered against a
   labeled 0.98), after diagnosing and fixing a related contamination mode, a same-colored slope
   label overlapping the curve, by generalizing the tool's exclusion-box API from one box to a list.

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

- Author outreach for raw trajectory data was sent (`docs/author-outreach-draft.md`) and has not
  received a response as of 2026-07-31. Raw data remains the only way to probe further into the
  Delta t range where a plateau might actually appear, or to test the memory kernel against
  anything real; this path is not closed, just not yet productive.
- The model-based alternative named in the paragraph above has since been run: Gate 5
  (`docs/gate-result-phase3-gate5-cagedfit.md`), pre-registered in `docs/BUILD_PLAN.md` before
  running, fit an explicit confined-diffusion functional form against a global power law on the
  same digitized curves. It also failed, more decisively than Gate 4, a well-constrained
  confined-diffusion fit still lost to the power-law null by 70-149 AICc points for the composite
  curve. This closes the "a different functional form might catch it" question; two independent
  statistical approaches on the existing digitized data now agree there is no detectable
  within-range MSD flattening.
- With both named follow-ups now attempted, raw trajectory data from the original authors is the
  only remaining path to a sharper test. Until (or unless) that arrives, "the estimator pipeline
  and the digitization methodology both work as designed; two independent real-data tests attempted
  here did not confirm the target signature within their primary criteria" is the warranted claim,
  not a stronger one.
- The digitization methodology's own accuracy is no longer only qualitatively supported: Gate 7
  (`docs/gate-result-gate7-digitization-accuracy.md`) tested the shared extraction machinery against
  synthetic ground truth and passed both pre-registered checks well inside threshold. This closes the
  "contribution 3" gap named above; the digitization-methodology write-up now has a quantified
  accuracy number to cite alongside the documented extraction-bug history.
