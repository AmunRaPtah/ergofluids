---
title: 'ergofluids.digitize: config-driven extraction of calibrated data and power-law exponents from published log-log figures'
tags:
  - Python
  - data digitization
  - figure extraction
  - anomalous diffusion
  - reproducibility
authors:
  - name: Eniola Olutogun
    orcid: 0009-0001-9272-6735
    affiliation: 1
affiliations:
  - name: Hasso Plattner Institute, University of Potsdam, Potsdam, Germany
    index: 1
date: 04 August 2026
bibliography: paper.bib
---

# Summary

`ergofluids.digitize` extracts calibrated data points from log-log figures in published PDFs, and
fits a power-law exponent to them with a bootstrap-propagated confidence interval. A figure panel is
described once, as a plain-JSON `FigureSpec`: a crop box, an axis calibration (two tick pixel
positions per axis), a curve color, and any rectangles to exclude (a legend swatch, or same-colored
annotation text overlapping the curve). The tool then renders the source PDF page, masks the curve's
color, bins matched pixels by column, and converts each bin's pixel centroid and vertical spread into
a data point with two independently tracked error terms: `reported_error` (a proxy for the figure's
own plotted error bars, from the vertical pixel spread within a bin) and `digitization_error` (a
fixed pixel-uncertainty budget from marker width and column-bin width, propagated through the axis
calibration). A power-law exponent is then fit to the extracted curve using a Hankel-SVD-denoised
delay-embedding estimator (`ssa`, from the sibling `ergofluids.koopman` module). A plain Dynamic Mode
Decomposition reconstruction [@schmid2010], by contrast, forward-simulates from a fitted eigenvalue
decomposition and was found, in the parent project's own synthetic benchmark, to carry a systematic
bias on power-law-in-time curves that are not themselves a finite sum of exponentials in real time.
`ssa` replaces that forward-simulation step with denoising only, and was confirmed unbiased on the
same benchmark, alongside two further established DMD-family estimators tested for the same property,
Bagging Optimized DMD [@askham2018] and Subspace DMD [@takeishi2017].

# Statement of need

Extracting a quantitative value from a published figure, when a paper provides no data availability
statement or supplementary dataset, is routine in meta-analysis and reanalysis work. General-purpose
point-and-click digitizers such as WebPlotDigitizer [@rohatgi] recover `(x, y)` pairs accurately but
leave fitting and uncertainty propagation on a *derived* quantity, such as a power-law or
anomalous-diffusion exponent, to the user, and each new figure requires a fresh manual click sequence
with no reusable, versionable record of how the axis calibration was determined.
`ergofluids.digitize` targets the narrower case of researchers who need a specific exponent from a
log-log curve: the axis calibration and curve color live in a small JSON file that can be checked
into version control and rerun, two error sources are tracked separately rather than conflated into
one, and the final exponent carries a bootstrap confidence interval computed with an estimator
already shown to be unbiased on this curve shape.

The extraction machinery was validated against a synthetic panel with an exactly known axis
calibration, recovering ground-truth values to a median relative error of 0.35% and error-bar values
to 1.15%, well inside pre-registered thresholds. It was then tested twice against real, external,
previously unseen figures from a *Nature Communications* paper on nanoparticle diffusion at
water/oil interfaces [@zhao2026], recovering the paper's own two independently stated exponents
(0.85 and 0.98, for two different curves in two different colors) to within 0.002 and 0.062
respectively. The second of these tests failed on its first attempt, because a same-colored
slope-reference annotation in the source figure was binned as curve data; diagnosing this from the
extracted output led directly to generalizing the tool's single legend-exclusion rectangle into a
list of exclusion rectangles, now covered by a regression test. Both real-figure tests, including the
diagnosed failure and fix, are documented in full alongside the synthetic validation in the parent
project's gate-result records, in keeping with that project's practice of reporting negative and
partial results rather than only clean passes.

A known, stated limitation: axis tick-pixel calibration is not automated and must currently be read
off the rendered page, either by eye or with a short scripted tick-detection pass (used for both
real-figure validations above); this is a deliberate scope boundary rather than an oversight, since
the synthetic validation specifically isolates and tests the extraction and fitting machinery given a
*correct* calibration, not the calibration-reading step itself.

# Acknowledgements

This tool grew out of a broader project testing Koopman/Dynamic-Mode-Decomposition and Mori-Zwanzig
methods for modeling macromolecular transport, where the digitization pipeline for two literature
figures was originally written as two non-reusable, per-figure scripts before being generalized here.

# References
