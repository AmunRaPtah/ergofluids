"""Config-driven digitization: describe a figure panel (crop box, axis
calibration, curve color) once as a JSON `FigureSpec`, and run the same
pixel-extraction pipeline `scripts/digitize_fig4a.py` and
`scripts/digitize_s14a.py` originally hand-wrote per figure. This is the
piece that turns "a pair of one-off scripts for one paper" into a reusable
tool for any new figure, at the cost of still needing a human (or an agent
looking at the rendered panel) to read off the crop box and tick-mark pixel
positions per figure; that calibration step is not yet automated. See the
module docstring in `common.py` for why (Gate 7 validated the extraction
math against synthetic ground truth with an analytically-known calibration,
not the tick-reading step itself on a real, messy PDF).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ergofluids.digitize.common import LinearAxis, LogAxis, crop_fractional, extract_curve, render_page


@dataclass
class ColorMask:
    """Selects which pixels belong to a curve. Two modes cover what the
    existing figures needed: a saturated/colored curve (`near_color`,
    matched against a target RGB within a tolerance) or a black/grey curve
    (`grey_band`, matched by low R-G-B spread within a brightness range)."""

    mode: str  # "near_color" | "grey_band"
    target_rgb: tuple[int, int, int] | None = None
    tolerance: int = 60
    grey_lo: int = 20
    grey_hi: int = 190
    grey_tolerance: int = 12

    def apply(self, arr: np.ndarray) -> np.ndarray:
        R, G, B = arr[..., 0], arr[..., 1], arr[..., 2]
        if self.mode == "near_color":
            if self.target_rgb is None:
                raise ValueError("near_color mode requires target_rgb")
            tr, tg, tb = self.target_rgb
            return (np.abs(R - tr) < self.tolerance) & (np.abs(G - tg) < self.tolerance) & (
                np.abs(B - tb) < self.tolerance
            )
        if self.mode == "grey_band":
            return (
                (np.abs(R - G) < self.grey_tolerance)
                & (np.abs(G - B) < self.grey_tolerance)
                & (R > self.grey_lo)
                & (R < self.grey_hi)
            )
        raise ValueError(f"unknown color mask mode: {self.mode!r}")


@dataclass
class FigureSpec:
    """Everything needed to digitize one curve from one PDF panel.

    Pixel coordinates (`x_pixel_range`, `y_pixel_margin`, axis pixel
    calibration, `legend_box`) are in crop-local pixels, i.e. pixel (0, 0) is
    the top-left corner of the region `crop_box_frac` selects out of the
    full rendered page, not the full page itself. Get these by rendering the
    page once at the target DPI and reading pixel positions off the image
    (visual inspection), the same way the original two figures were
    calibrated.
    """

    name: str
    pdf_path: str
    page: int
    crop_box_frac: tuple[float, float, float, float]
    x_axis_kind: str  # "log" | "linear"
    x_axis_params: dict
    y_axis_kind: str
    y_axis_params: dict
    x_pixel_range: tuple[int, int]
    y_pixel_margin: tuple[int, int]  # (top, bottom), crop-local pixel rows
    color_mask: ColorMask
    # Rectangles to exclude from extraction, e.g. a legend swatch or a
    # same-colored text label/annotation that overlaps the curve's color and
    # region (col_lo, row_lo, col_hi, row_hi) each. Originally a single
    # `legend_box`; generalized to a list after Gate 9 found a same-colored
    # slope-label ("proportional to t^0.98") needed excluding in addition to
    # the legend, in the same figure.
    exclude_boxes: list[tuple[int, int, int, int]] = field(default_factory=list)
    dpi: int = 400

    @classmethod
    def from_json(cls, path: str | Path) -> "FigureSpec":
        raw = json.loads(Path(path).read_text())
        raw = dict(raw)
        raw["color_mask"] = ColorMask(**raw["color_mask"])
        raw["crop_box_frac"] = tuple(raw["crop_box_frac"])
        raw["x_pixel_range"] = tuple(raw["x_pixel_range"])
        raw["y_pixel_margin"] = tuple(raw["y_pixel_margin"])
        legend_box = raw.pop("legend_box", None)
        exclude_boxes = raw.get("exclude_boxes") or ([legend_box] if legend_box else [])
        raw["exclude_boxes"] = [tuple(box) for box in exclude_boxes]
        return cls(**raw)


def _build_axis(kind: str, params: dict):
    if kind == "log":
        return LogAxis(**params)
    if kind == "linear":
        return LinearAxis(**params)
    raise ValueError(f"unknown axis kind: {kind!r}")


def digitize(spec: FigureSpec, render_dir: Path) -> list[tuple[float, float, float, float, float]]:
    """Render `spec.pdf_path` page `spec.page`, crop to the panel, mask the
    curve's color, and extract calibrated (x, y, reported_error,
    digitization_error, x_digitization_error) points."""
    png_path = render_page(Path(spec.pdf_path), page=spec.page, out_dir=render_dir, dpi=spec.dpi)
    arr = crop_fractional(png_path, spec.crop_box_frac)

    mask = spec.color_mask.apply(arr)
    interior = np.zeros(arr.shape[:2], dtype=bool)
    top, bottom = spec.y_pixel_margin
    interior[top:bottom, spec.x_pixel_range[0] : spec.x_pixel_range[1]] = True
    mask &= interior

    for lc0, lr0, lc1, lr1 in spec.exclude_boxes:
        excluded = np.zeros(arr.shape[:2], dtype=bool)
        excluded[lr0:lr1, lc0:lc1] = True
        mask &= ~excluded

    x_axis = _build_axis(spec.x_axis_kind, spec.x_axis_params)
    y_axis = _build_axis(spec.y_axis_kind, spec.y_axis_params)
    return extract_curve(mask, x_axis, y_axis, spec.x_pixel_range)
