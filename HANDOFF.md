# ErgoFluids: handoff

Last updated: 2026-07-31.

## State

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
