# ergofluids.digitize

A small, tested tool for extracting calibrated data points and power-law exponents from log-log
figures in published PDFs, when the underlying raw data was never released. It replaces manual
point-and-click digitizing with a config-driven pipeline: describe a figure panel once (crop box,
axis calibration, curve color) as a `FigureSpec`, and get back `(x, y, reported_error,
digitization_error)` points, plus, on request, a bootstrap-uncertainty power-law exponent fit.

This package also contains `ergofluids.koopman` and `ergofluids.mz`, Koopman/DMD subdiffusion
estimators and a Mori-Zwanzig memory-kernel extension, built for a separate research question (see
`../docs/` and `../HANDOFF.md` in the parent project). Those modules are not part of this software
submission; `ergofluids.digitize` reuses `ergofluids.koopman.exponent.ssa_denoise_exponent` as its
default exponent estimator because it is the one already validated (against synthetic ground truth,
across three independently implemented DMD-family methods) to be unbiased on power-law-in-time
curves, which is exactly what a digitized log-log curve is.

## Statement of need

Extracting quantitative data from a published figure, when the paper provides no data availability
statement or supplementary dataset, is common in meta-analysis and reanalysis work. General
point-and-click digitizers (e.g. WebPlotDigitizer) recover `(x, y)` pairs well but do not fit or
propagate uncertainty on a derived quantity like a power-law exponent, and re-running the same manual
click sequence on every new figure does not scale or leave an auditable record of how the axis
calibration was determined. `ergofluids.digitize` is aimed at researchers who need a specific derived
number (an anomalous-diffusion or other power-law exponent) from a log-log figure, with:

- a reusable, versionable configuration (`FigureSpec`, a plain JSON file) instead of a one-off script
  or manual click sequence per figure;
- two independently tracked error sources per point (the paper's own plotted error bars, recovered
  from marker/whisker pixel spread, versus the tool's own calibration/rendering uncertainty), rather
  than one conflated number;
- a bootstrap-propagated confidence interval on the fitted exponent, using an estimator independently
  validated to be unbiased on power-law curves; and
- an accuracy validation against synthetic ground truth with a known, exact axis calibration
  (`tests/test_digitize_tool.py`), plus two independent tests against real, external, previously
  unseen published figures, recovering their own stated exponents to within 0.002 and 0.062
  respectively (see `../docs/gate-result-gate8-external-real-figure-validation.md` and
  `../docs/gate-result-gate9-second-real-figure-validation.md`).

## Installation

```
python -m venv .venv
.venv/bin/pip install -e .
```

Requires the `pdftoppm` binary (part of `poppler-utils`) on `PATH` to render PDF pages to PNG:

```
apt-get install poppler-utils   # Debian/Ubuntu
brew install poppler            # macOS
```

## Usage

### 1. Describe the figure as a `FigureSpec`

Render the target PDF page once, at the DPI you intend to use, and read off (by eye, or with the
tick-detection approach in `docs/gate-result-gate8-external-real-figure-validation.md`) the crop box,
axis tick pixel positions, and the curve's fill color. Save as JSON:

```json
{
  "name": "my_figure_curve_a",
  "pdf_path": "paper.pdf",
  "page": 3,
  "crop_box_frac": [0.0, 0.0, 1.0, 1.0],
  "x_axis_kind": "log",
  "x_axis_params": {"pixel0": 736.5, "log10_value0": -1.0, "pixel1": 1168.5, "log10_value1": 0.0},
  "y_axis_kind": "log",
  "y_axis_params": {"pixel0": 1321.5, "log10_value0": 0.0, "pixel1": 1679.0, "log10_value1": -1.0},
  "x_pixel_range": [563, 1213],
  "y_pixel_margin": [1235, 1908],
  "color_mask": {"mode": "near_color", "target_rgb": [192, 192, 192], "tolerance": 25},
  "exclude_boxes": [[559, 1231, 850, 1500]],
  "dpi": 400
}
```

`color_mask.mode` is `"near_color"` (match a target RGB within a tolerance, for colored or grey/black
markers) or `"grey_band"` (match a brightness band with low R/G/B spread). `exclude_boxes` excludes
rectangles from extraction: legend swatches, or same-colored annotation text overlapping the curve
(see Gate 9 in `../docs/gate-result-gate9-second-real-figure-validation.md` for why this is a list,
not a single box).

### 2. Run it

Command line:

```
.venv/bin/python scripts/digitize_cli.py my_figure_spec.json --out points.csv --estimate --estimator ssa
```

Or as a library:

```python
from pathlib import Path
from ergofluids.digitize.spec import FigureSpec, digitize
from ergofluids.digitize.exponent_fit import estimate_exponent

spec = FigureSpec.from_json("my_figure_spec.json")
points = digitize(spec, render_dir=Path("_render"))
result = estimate_exponent(points, estimator="ssa", n_boot=2000)
print(result)  # {"point_estimate": ..., "ci95_low": ..., "ci95_high": ..., ...}
```

## Known limitations

- Axis calibration (tick pixel positions) is not automated; it must be read off the rendered page,
  by eye or with a scripted tick-detection pass like the one used in Gate 8/9. This is a deliberate
  scope boundary, not an oversight: Gate 7 validates the extraction math given a *correct*
  calibration, and does not claim to validate the calibration-reading step itself.
- `reported_error` (the per-point "paper's own plotted uncertainty" column) assumes the figure has
  visible per-point error bars. For bare-marker figures without them, this column can be contaminated
  by unrelated same-colored page content (an annotation line, in one documented case) and should not
  be treated as a calibrated uncertainty; see the Gate 8 write-up. The `y` values themselves are
  unaffected.

## Running the tests

```
.venv/bin/python -m pytest tests/ -q
```

## License

MIT; see `LICENSE`.
