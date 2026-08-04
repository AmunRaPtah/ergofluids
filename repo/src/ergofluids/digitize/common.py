"""Shared pixel-extraction primitives for digitizing figures from rendered
PDF pages: render a page, crop to a panel, calibrate pixel<->data axes, and
bin a color mask into (x, y, reported_error, digitization_error) points.

Originally written for arXiv:1909.05091 (Burla et al., "Particle diffusion
in extracellular hydrogels") as scripts/digitize_fig4a.py and
scripts/digitize_s14a.py; moved here unchanged so the extraction logic is a
reusable library rather than copy-pasted per figure. See `spec.py` in this
package for the config-driven tool built on top of it.

Method, in one place so it is auditable: render the target PDF page at high
DPI, crop to a fixed sub-region around the target panel, locate the panel's
frame and tick marks by thresholding near-black pixels (axis lines/ticks are
much darker than any other content), fit a pixel-to-data affine map per axis
using at least two tick positions (more where available, see each script's
`_locate_ticks`-style diagnostics run once during development), then mask
each curve's distinctive color, bin the masked pixels by x-column, and
convert the per-bin pixel centroid and pixel spread to data units.

Two error columns are produced per point, deliberately not merged:

- `reported_error`: half the vertical pixel spread of matched-color pixels
  within a column bin, converted to data units via the same axis calibration
  used for the point itself. In these figures the visible error bars are much
  larger than the marker/line width, so this spread is dominated by the
  paper's own plotted error bars, not by our extraction noise. This is our
  best proxy for "the error the paper reported", not a re-derivation of their
  statistics.
- `digitization_error`: a fixed, conservative estimate of our own pixel-level
  uncertainty, independent of what a given point's error bar happens to look
  like: a small fixed marker/line half-width in pixels (`MARKER_HALFWIDTH_PX`)
  plus half the column bin width (`BIN_WIDTH_PX / 2`), propagated through the
  local axis calibration. This does not grow or shrink with the reported
  error bar; it is meant to capture calibration + rendering uncertainty only.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

MARKER_HALFWIDTH_PX = 3.0
BIN_WIDTH_PX = 4.0


def render_page(pdf_path: Path, page: int, out_dir: Path, dpi: int = 400) -> Path:
    """Render a single PDF page to PNG via pdftoppm, return the PNG path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / f"page{page}"
    subprocess.run(
        [
            "pdftoppm",
            "-r",
            str(dpi),
            "-f",
            str(page),
            "-l",
            str(page),
            "-png",
            str(pdf_path),
            str(prefix),
        ],
        check=True,
    )
    candidates = sorted(out_dir.glob(f"page{page}-*.png"))
    if not candidates:
        # single-page renders sometimes omit the page-number suffix
        candidates = sorted(out_dir.glob(f"page{page}.png"))
    if not candidates:
        raise FileNotFoundError(f"pdftoppm did not produce output for page {page} in {out_dir}")
    return candidates[-1]


def crop_fractional(png_path: Path, box_frac: tuple[float, float, float, float]) -> np.ndarray:
    """Crop an image using fractional (x0, y0, x1, y1) coordinates of page size."""
    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    x0, y0, x1, y1 = box_frac
    crop = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    return np.array(crop).astype(int)


@dataclass
class LinearAxis:
    """value = intercept + slope * pixel"""

    pixel0: float
    value0: float
    pixel1: float
    value1: float

    def value_at(self, pixel: np.ndarray | float) -> np.ndarray | float:
        slope = (self.value1 - self.value0) / (self.pixel1 - self.pixel0)
        return self.value0 + slope * (np.asarray(pixel) - self.pixel0)

    def delta(self, pixel_span: float, pixel: float | None = None) -> float:
        """Convert a pixel span to a data-unit span (linear axis: constant)."""
        slope = abs((self.value1 - self.value0) / (self.pixel1 - self.pixel0))
        return slope * pixel_span


@dataclass
class LogAxis:
    """log10(value) = intercept + slope * pixel"""

    pixel0: float
    log10_value0: float
    pixel1: float
    log10_value1: float

    def value_at(self, pixel: np.ndarray | float) -> np.ndarray | float:
        slope = (self.log10_value1 - self.log10_value0) / (self.pixel1 - self.pixel0)
        log10_v = self.log10_value0 + slope * (np.asarray(pixel) - self.pixel0)
        return 10.0**log10_v

    def delta(self, pixel_span: float, pixel: float) -> float:
        """Convert a pixel span to a data-unit span at a given pixel location
        (log axis: span in data units depends on where you are, via d(v) = v
        * ln(10) * d(log10 v))."""
        slope = abs((self.log10_value1 - self.log10_value0) / (self.pixel1 - self.pixel0))
        v = self.value_at(pixel)
        return float(v * np.log(10) * slope * pixel_span)


def extract_curve(
    mask: np.ndarray,
    x_axis,
    y_axis,
    x_pixel_range: tuple[int, int],
    bin_width: float = BIN_WIDTH_PX,
    marker_halfwidth_px: float = MARKER_HALFWIDTH_PX,
    max_row_span_px: float = 200.0,
) -> list[tuple[float, float, float, float, float]]:
    """Bin a boolean color mask by x-pixel column into `bin_width`-wide bins,
    and convert each bin's pixel centroid + spread to (x, y, reported_error,
    digitization_error, x_digitization_error) in data units. Returns points
    sorted by x.

    Bins whose matched-pixel row span exceeds `max_row_span_px` are dropped:
    a real marker plus its error bar spans a modest fraction of the plot
    height, so a span this large is a sign the bin accidentally caught part
    of an axis frame line or a legend border rather than actual curve data
    (the frame/legend colors can fall inside the same threshold as a dark or
    saturated curve color). This is a defense-in-depth check on top of the
    explicit interior/legend pixel masks each caller already applies.
    """
    x_lo, x_hi = x_pixel_range
    points = []
    n_bins = int(np.ceil((x_hi - x_lo) / bin_width))
    for i in range(n_bins):
        col_lo = x_lo + i * bin_width
        col_hi = min(col_lo + bin_width, x_hi)
        col_lo_i, col_hi_i = int(round(col_lo)), int(round(col_hi))
        if col_hi_i <= col_lo_i:
            continue
        sub = mask[:, col_lo_i:col_hi_i]
        rows, cols = np.nonzero(sub)
        if len(rows) == 0:
            continue
        row_span_half = float((rows.max() - rows.min()) / 2.0)
        if row_span_half * 2 > max_row_span_px:
            continue
        row_center = float(np.median(rows))
        col_center = col_lo_i + float(np.median(cols))

        x_val = float(x_axis.value_at(col_center))
        y_center_val = float(y_axis.value_at(row_center))
        y_hi_val = float(y_axis.value_at(row_center - row_span_half))
        y_lo_val = float(y_axis.value_at(row_center + row_span_half))
        reported_error = abs(y_hi_val - y_lo_val) / 2.0

        dig_err_y = y_axis.delta(marker_halfwidth_px, row_center)
        dig_err_x = x_axis.delta(bin_width / 2.0 + 1.0, col_center)
        points.append((x_val, y_center_val, reported_error, dig_err_y, dig_err_x))

    points.sort(key=lambda p: p[0])
    return points


def write_csv(path: Path, points: list[tuple[float, float, float, float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("x,y,reported_error,digitization_error\n")
        for x, y, rep_err, dig_err_y, _dig_err_x in points:
            f.write(f"{x:.6g},{y:.6g},{rep_err:.6g},{dig_err_y:.6g}\n")
