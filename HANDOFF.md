# ErgoFluids: handoff

Last updated: 2026-08-04.

## New direction (2026-08-04): network_sim, a fresh technical bet

Per the author's direction to prioritize product building over further publication work, and after
researching alternatives to the Koopman/Mori-Zwanzig approach (which failed its real-data gates, see
below), a new module `src/ergofluids/network_sim/` was built and validated this session: a
self-generated Brownian-dynamics simulator of a probe particle in a random fiber network, an
obstruction-scaling physics baseline, and a residual/classifier model targeting the two documented
failure modes of that baseline (adhesion, particle shape). First validation: the residual model cuts
prediction error 62% versus the baseline alone (leave-one-out MAE 0.030 vs 0.080), and a regime
classifier (normal/hindered/caged) beats a majority-class guess (80.6% vs 63.9%). Full detail:
`docs/gate-result-network-sim-residual-model.md`. Product CLI: `scripts/predict_transport.py`.
**Not yet validated against real experimental data**, only self-generated simulation; IP/venture
material still should not open on this alone, per the same gating discipline that applied to the
Koopman/MZ work (see "New direction" above and memory `ergofluids-ip-gating-discipline`).

The rest of this file is the (still-accurate, unmodified) history of the earlier Koopman/Mori-Zwanzig
transport-modeling thesis, which this new direction sits alongside, not on top of.

## State (Koopman/Mori-Zwanzig thesis, superseded as the active direction)

Phase 1 (synthetic validation) is done and fully resolved. Gate 1 passed for
all three estimators (loglog, dmd, ssa). Gate 0 failed for the original dmd
(HODMD) estimator; root cause was diagnosed (systematic forward-simulation
bias), a fix was pre-registered and tested (`ssa`, Hankel-SVD denoising with
no dynamic reconstruction), and it closed most of the gap but still missed
the bar by one at alpha_true=0.5 (17/20 vs 18/20 required, Gate 0b). A
pre-registered 100-repeat follow-up at that condition (Gate 0c) found true
coverage at 89 to 90%, confirming the 17/20 was Monte Carlo noise, not real
miscalibration. **Gate 0 now passes for `ssa`.** `dmd` (HODMD) is retired
from this pipeline; use `ssa` going forward. See
`docs/gate-result-phase1-synthetic.md` for the full result, and
`docs/BUILD_PLAN.md` for what Phase 2 to 4 look like.

Environment: `repo/.venv` (Python 3.12), created this session. `pip install`
for scikit-learn-dependent packages needs `--only-binary=:all:` on this box,
because a source build hits a `pkgutil.ImpImporter` incompatibility with
Python 3.12's stdlib. PyKoopman is not installed (see `literature-map.md` for
why); only PyDMD is used in Phase 1.

## Immediate next step

Phase 3 is done, and its one open follow-up (the model-based caged-diffusion
refit, Gate 5) has now also been run and failed; see "Gate 5" below. Phase 4
does not open on this result; see the paragraph after the Gate 4 result for
what would need to be true first, and `docs/publication-angle.md` /
`docs/ip-product-angle.md` for the two contingent write-ups produced instead
of IP/venture material.

Phase 2 is done. Gate 2 (`docs/gate-result-phase2-mzmd.md`): the ported MZMD
memory kernel (`repo/src/ergofluids/mz/mzmd.py`) beats a memoryless fit on a
generic linear hidden-variable system, 95% CI on the RMSE improvement
[0.0132, 0.0458]. Gate 3 (`docs/gate-result-phase2-gate3-caging.md`), built
because Gate 2's system was linear and possibly an easy case: a caged-particle
system (`repo/src/ergofluids/data/caging.py`) with a verified MSD
plateau-then-escape crossover, mechanistically resembling the literature
target's reported caging behavior. MZMD beats memoryless there too, 95% CI
[0.0112, 0.0587]. Both gates pass; the approach is no longer resting on a
single easy synthetic case.

Neither gate used the paper's actual data or its specific reported numbers
(mesh sizes, moduli, the ~0.5 exponent); Gate 3's caging system was designed
to reproduce the qualitative crossover, not fit to those figures.

Phase 3 (real-data test) is done, chose the literature-digitization path
(no author response mechanism was pursued this pass; raw trajectory data is
still not available). Figure 4a (ISF vs tq^2) and Supplementary Figure S14a
(MSD vs Delta t) were digitized from the paper's own PDF
(`repo/scripts/digitize_fig4a.py`, `repo/scripts/digitize_s14a.py`, output in
`repo/data/digitized/`), with two separately-tracked error columns
(`reported_error` from the paper's own plotted error bars,
`digitization_error` from our pixel/calibration uncertainty). Gate 4
(`docs/gate-result-phase3-realdata.md`) tested whether the koopman exponent
estimators (`loglog`, `ssa`; `dmd` still retired) detect the composite
network's caging signature in this digitized data.

**Gate 4 result: FAIL on its pre-registered primary criterion.** The digitized
S14a MSD curve does not show a statistically significant local slope decrease
from an early to a late Delta t window for the composite network, within
propagated digitization error (95% CI of the early-late slope difference
includes zero, both `loglog` and `ssa`). The two pure-component curves do pass
their own criterion (late-window slope stays above 0.5). A secondary,
descriptive check on the Fig 4a ISF panel does show the qualitative caging
signature clearly (composite's ISF plateaus at approx 0.4, versus approx 0.09
to 0.14 for the pure networks, CI excludes zero both comparisons), but that
check was not part of the locked pass/fail rule. See
`docs/gate-result-phase3-realdata.md` for the full result and the honest
discussion of why the two checks disagree (the paper's own S14a panel likely
does not extend to long enough Delta t to show MSD-level flattening; the
caging signature shows up as a sustained lower exponent and an incomplete ISF
decay, not as detectable within-window curvature over the range this specific
supplementary figure covers).

Per `BUILD_PLAN.md`'s phase sequencing rule ("Phase 4+: IP and venture
material, only after a phase-3-or-later gate has passed against real data"),
**Phase 4 should not proceed** on the strength of this gate; Gate 4 failed its
primary criterion. Both follow-up options named at the time (request raw
trajectory data from the paper's authors, or refit with an explicit
caged-diffusion functional form instead of fixed-window OLS slopes) have now
been pursued; see "Gate 5" below and the author-outreach note in "Gotchas."

## Gate 5 (2026-07-31): model-based caged-diffusion refit

`docs/gate-result-phase3-gate5-cagedfit.md`: fit an explicit confined-diffusion
MSD model (`P * [1 - exp(-t/tau)]`, the standard Kusumi et al. 1993
single-particle-tracking form) against a global power law on the same S14a
digitized curves Gate 4 used, compared by AICc under the same style of
error-propagated bootstrap, pre-registered in `docs/BUILD_PLAN.md` ("Gate 5")
before running. **Result: FAIL**, and more decisively than Gate 4. For the
composite curve, `tau` came out well-constrained inside the observed range
(95% CI [1.199, 1.658], curve extends to Delta t = 10.727), so this was a
fair fit, not a degenerate one, and the power-law model still beat the
confined model by roughly 70 to 149 AICc points across the full bootstrap
distribution, decisively past the conventional `|delta AICc| > 10` "strong
support" bar. Both pure-component curves show the same pattern, as expected.
Two independent statistical approaches (Gate 4's local two-window slope
comparison, Gate 5's whole-curve nonlinear model comparison) now agree: no
MSD-level flattening is detectable within this digitized Delta t range. This
does not overturn Gate 4's own result or the separate, non-locked ISF-plateau
check (which does show a real effect); it specifically closes the "maybe a
different functional form would catch it" question that Gate 4 left open.
Removes the model-based refit as an open follow-up in
`docs/publication-angle.md` and `docs/ip-product-angle.md` (both updated
alongside this gate). Phase 4 still does not open.

`docs/publication-angle.md` and `docs/ip-product-angle.md` record what this
result does and does not support: a modest methods story (the Gate 0 HODMD
bias diagnosis, the digitization methodology, the full gate sequence as an
honest mixed-result case study) is publishable now; no IP or product claim is
yet, per the sequencing rule above. See memory `ergofluids-ip-gating-discipline`
for why this gating was upheld even under a request to complete the project,
IP and product angle included, overnight with no check-in.

The Mori-Zwanzig memory kernel (`repo/src/ergofluids/mz`) was not touched or
retested in Phase 3; no per-trajectory real data exists to test it against,
only the two derived summary curves used above. It remains a synthetic-only
result (Gate 2, Gate 3).

## Gate 6 (2026-07-31): does HODMD's bias generalize across other DMD-family methods?

`docs/gate-result-gate6-dmd-generality.md`: separate from the real-data gates
above, a follow-up on Gate 0/0b's HODMD bias diagnosis. Tested three further
established, published, PyDMD-implemented estimators, chosen for mechanistic
diversity, against the same synthetic protocol Gate 0 used (fBm trajectories,
alpha_true in {0.5, 0.7, 1.0}, 18/20 coverage bar), pre-registered in
`docs/BUILD_PLAN.md` ("Gate 6") before running:
`HODMD(forward_backward=True)` (`hodmd_fb`), `BOPDMD` (`bopdmd`),
`SubspaceDMD` (`subspace`). **Result: `hodmd_fb` FAILS decisively at all three
conditions (15/20, 12/20, 15/20) with bias larger than plain HODMD's
diagnosed bias, i.e. forward-backward averaging makes the original problem
worse, not better. `bopdmd` and `subspace` both PASS cleanly at all three
conditions**, with near-zero bias. Zero `loglog`-fallback triggers across all
27,180 estimator calls for any candidate. This sharpens rather than simply
broadens the Gate 0/0b diagnosis: the bias isn't fixed by a minimal
bias-correction patch to HODMD's own estimation procedure (aimed at a
different problem, sensor-noise bias, than the one diagnosed here), but is
avoided by two mechanistically different established methods that don't
reuse HODMD's own forward-simulation route. Strengthens
`docs/publication-angle.md`'s claim that the HODMD diagnosis is the
project's most broadly useful finding. Does not touch or reopen any real-data
gate or Phase 4.

Alpha=0.7 and alpha=1.0 for `ssa` (Gate 0) were only tested at n=20 (19/20,
18/20). If either becomes load-bearing for a future claim, run the same
100-repeat check used for alpha=0.5 before trusting it.

## Gate 7 (2026-07-31): digitization pipeline accuracy against synthetic ground truth

`docs/gate-result-gate7-digitization-accuracy.md`: fills the "contribution 3" gap named in
`docs/publication-angle.md`. Built a synthetic log-log panel with known `(x, y, error)` ground truth
(30 points, `y = 2.0 * x^0.65` plus fixed-seed jitter, unrelated to any real exponent used elsewhere
in this project), rendered it through the project's own PDF-to-PNG path
(`digitize_common.render_page`, i.e. actual `pdftoppm`), computed axis calibration analytically
(verified against detected axis-frame pixel positions in a pre-registration smoke test, not hand-read
from the image), and ran the unmodified `digitize_common.extract_curve` function both real
digitization scripts use, pre-registered in `docs/BUILD_PLAN.md` ("Gate 7") before running. **Result:
PASS on both pre-registered checks, well inside every threshold**: curve-following median relative
error 0.35% (bar: <2%) across 449 extracted bins, error-bar recovery median relative error 1.15% with
Pearson r=0.991 against ground truth (bars: <15%, r>0.8) across the 30 known vertices. Scope, stated
before running: this validates the shared extraction machinery given correct axis calibration; it
does not and cannot validate whether the two real scripts' hand-read tick-mark pixel positions were
themselves correct, since no independent ground truth exists for that step on the real PDF pages.
Does not touch or reopen any real-data gate or Phase 4.

## Tool generalization and Gate 8 (2026-08-04)

Separate decision, made outside the transport-modeling thesis: since Phase 4 (IP/venture material)
never opened, a fresh product angle was scoped instead of the original tumor-stroma transport claim,
built on exactly what has already validated: the unbiased exponent estimator (Gate 0/0b/0c/6) and the
digitization pipeline (Gate 7). What's actually validated is not "we model tumor-stroma transport,"
it is "we accurately extract calibrated power-law exponents from published diffusion/rheology
figures." That narrower claim became the scope for a standalone research tool, not a rename of the
original thesis.

The two hand-written per-figure scripts (`digitize_fig4a.py`, `digitize_s14a.py`) were generalized
into a config-driven library and CLI: `src/ergofluids/digitize/{common,spec,exponent_fit}.py` (moved
and extended from the old top-level `scripts/digitize_common.py`) plus `scripts/digitize_cli.py`. A
new `FigureSpec` JSON describes a figure's crop box, axis calibration, and curve color once; the tool
then digitizes it and, on request, fits a bootstrap-uncertainty power-law exponent using the same
`ssa` estimator and error-propagation convention Gate 4/5 used by hand. The two original scripts and
`run_gate7.py` were repointed to import from the package; all three reproduce their pre-refactor
output exactly (same point counts, Gate 7 still passes with identical numbers). Two new tests added
(`tests/test_digitize_tool.py`); full suite is 21 passing.

`docs/gate-result-gate8-external-real-figure-validation.md` (protocol in `docs/BUILD_PLAN.md`, "Gate
8"): tested the generalized tool on a real figure it had never seen, Fig. 1b of Zhao et al. (*Nature
Communications* 17:7149, 2026, doi:10.1038/s41467-026-74008-w), which labels its own 7%-coverage
EA-MSD curve's fitted slope as 0.85. The tool recovered 0.852 end to end from the raw PDF: axis
calibration by programmatic tick-height detection, not by eye. **PASS.** It also surfaced a real,
now-documented limitation: this figure has no plotted error bars, and a black slope-reference
annotation line crossing the curve inflates `reported_error` in that region, producing a wide,
asymmetric bootstrap CI despite the tight point estimate. The `y` values themselves are unaffected;
the uncertainty quantification specifically needs either a contamination check or an honest
no-calibrated-uncertainty fallback for bare-marker figures, before any claim stronger than "the point
estimate matched" is made about that case.

Direction from the author (2026-08-04): pursue both (1) folding this real-data validation into the
already-drafted PLOS ONE manuscript's digitization-methodology contribution (done: new Section 3.8/
Table 6 and a Discussion paragraph, reference [22]), and (2) a standalone JOSS software paper for the
tool.

Gate 9 (`docs/gate-result-gate9-second-real-figure-validation.md`): a second real-figure test, a
different curve/color/target value in the same Zhao et al. paper (Fig. 1d's blue `<TA-MSD>` curve,
labeled 0.98). First attempt failed (0.653 recovered) because the panel's own blue slope-label text
shares the curve's color and got binned as data; fixed by generalizing `FigureSpec`'s single
`legend_box` to a list, `exclude_boxes`. After the fix: 0.918 recovered, PASS. Full suite now 22
tests.

JOSS prep remaining: LICENSE (done, MIT), README with statement of need/install/usage (todo),
`paper.md`/`paper.bib` (todo).

## Manuscript submission prep (2026-07-31)

Target venue decided: PLOS ONE, direct submission (no arXiv-first preprint step per author
preference). Confirmed against PLOS ONE's own published criteria pages (fetched, not assumed):
soundness over novelty/impact, negative and null results explicitly considered, formatting
requirements (manuscript structure/order, 300-word abstract cap, Vancouver numbered citations,
TIFF figure specs, double-spacing/continuous line numbers). `docs/manuscript-draft.md` updated
to match: title page now has a short/running title and an affiliation line (institution + location
only, no degree/program name per standing instruction, see memory
`feedback-affiliation-institution-only`), abstract trimmed 376 -> 293 words, all in-text citations
converted from author-date to numbered `[1]`-`[11]` with a matching Vancouver-style reference list,
figure captions reformatted to PLOS's "Fig 1."/"Fig 2." label style with merged legend text.

Two build scripts produce the actual submission assets from the markdown source (not hand-maintained
separately): `repo/scripts/make_manuscript_figures.py` now also writes `docs/figures/Fig1.tif` and
`Fig2.tif` (RGB, 300 dpi, LZW-compressed, no embedded titles, within PLOS's pixel-width bounds).
`repo/scripts/build_plos_docx.py` generates `docs/ergofluids_manuscript_PLOS_ONE.docx` via pandoc,
stripping the source markdown's internal-only "Status" paragraph and embedded figure images (PLOS
requires figures as separate files), then post-processes with python-docx for double line spacing,
continuous line numbering, and a page-number footer field.

Data availability statement cites the live GitHub repo pinned to a specific commit SHA, not a
Zenodo DOI snapshot; the author was told PLOS's own policy language prefers a persistent identifier
and chose the GitHub-link approach anyway. Revisit if a reviewer flags it.

## Gotchas

- No raw experimental trajectory data exists publicly for the literature
  target (arXiv:1909.05091). Phase 1 used synthetic fBm anchored to two
  reported exponent values only. Do not describe Gate 1 as "validated against
  real data" anywhere; it was not.
- The BMF source document's IP/revenue language (Alice/Mayo argument, royalty
  tiers, "$10 billion" market figure) is not sourced and is not reused
  anywhere in this project. See `venture/PLACEHOLDER.md`.
- Author outreach (`docs/author-outreach-draft.md`, sent to the corresponding
  author, Prof. Gijsje Koenderink) has not received a response as of
  2026-07-31. Raw trajectory data therefore remains unavailable; do not treat
  it as "in progress with a likely reply coming" in any future write-up
  without checking for an actual response first.
