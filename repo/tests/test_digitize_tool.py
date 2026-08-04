"""Regression check on the config-driven digitization tool
(src/ergofluids/digitize/spec.py, exponent_fit.py): reproduces Gate 7's
synthetic-ground-truth check (docs/gate-result-gate7-digitization-accuracy.md)
through the generalized FigureSpec/digitize/estimate_exponent path instead of
run_gate7.py's hand-written script, to confirm the tool recovers a known
power-law exponent from a rendered PDF panel end to end.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ergofluids.digitize.exponent_fit import estimate_exponent
from ergofluids.digitize.spec import ColorMask, FigureSpec, digitize

SEED = 20260804
N_POINTS = 30
A_TRUE = 2.0
ALPHA_TRUE = 0.65
JITTER_SIGMA = 0.04
X_LO, X_HI = 1e-2, 10.0
Y_LO, Y_HI = 1e-2, 10.0
RENDER_DPI = 400
FIG_W_IN, FIG_H_IN = 6.0, 5.0
AXES_RECT = (0.15, 0.15, 0.75, 0.75)
DATA_COLOR = "#e67300"


def _build_synthetic_pdf(tmp_path: Path) -> Path:
    rng = np.random.default_rng(SEED)
    x = np.logspace(np.log10(X_LO), np.log10(X_HI), N_POINTS)
    y = A_TRUE * x**ALPHA_TRUE * rng.lognormal(mean=0.0, sigma=JITTER_SIGMA, size=N_POINTS)

    fig = plt.figure(figsize=(FIG_W_IN, FIG_H_IN), dpi=72)
    ax = fig.add_axes(AXES_RECT)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(X_LO, X_HI)
    ax.set_ylim(Y_LO, Y_HI)
    ax.plot(x, y, color=DATA_COLOR, linewidth=1.8, marker="")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.canvas.draw()

    pdf_path = tmp_path / "synthetic.pdf"
    fig.savefig(pdf_path, format="pdf")
    plt.close(fig)
    return pdf_path


def _axis_pixel_calibration():
    """Mirror run_gate7.py's analytic pixel calibration (known exactly here
    because we built the figure), rather than hand-reading tick positions as
    a human would for a real, unknown PDF."""
    fig = plt.figure(figsize=(FIG_W_IN, FIG_H_IN), dpi=72)
    ax = fig.add_axes(AXES_RECT)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(X_LO, X_HI)
    ax.set_ylim(Y_LO, Y_HI)
    fig.canvas.draw()
    scale = RENDER_DPI / 72.0
    img_h_px = round(FIG_H_IN * RENDER_DPI)

    def data_to_pixel(x, y):
        px, py = ax.transData.transform((x, y))
        return px * scale, img_h_px - py * scale

    x0_col, _ = data_to_pixel(X_LO, 1.0)
    x1_col, _ = data_to_pixel(X_HI, 1.0)
    _, y0_row = data_to_pixel(1.0, Y_LO)
    _, y1_row = data_to_pixel(1.0, Y_HI)
    plt.close(fig)
    return x0_col, x1_col, y0_row, y1_row, img_h_px


def test_digitize_and_estimate_recovers_known_exponent(tmp_path):
    pdf_path = _build_synthetic_pdf(tmp_path)
    x0_col, x1_col, y0_row, y1_row, img_h_px = _axis_pixel_calibration()

    spec = FigureSpec(
        name="synthetic_regression",
        pdf_path=str(pdf_path),
        page=1,
        crop_box_frac=(0.0, 0.0, 1.0, 1.0),
        x_axis_kind="log",
        x_axis_params=dict(pixel0=x0_col, log10_value0=np.log10(X_LO), pixel1=x1_col, log10_value1=np.log10(X_HI)),
        y_axis_kind="log",
        y_axis_params=dict(pixel0=y0_row, log10_value0=np.log10(Y_LO), pixel1=y1_row, log10_value1=np.log10(Y_HI)),
        x_pixel_range=(int(round(x0_col)) + 2, int(round(x1_col)) - 2),
        y_pixel_margin=(0, img_h_px),
        color_mask=ColorMask(mode="near_color", target_rgb=(230, 115, 0), tolerance=40),
        dpi=RENDER_DPI,
    )

    points = digitize(spec, render_dir=tmp_path / "_render")
    assert len(points) > 20, f"expected most of the {N_POINTS} points to survive binning, got {len(points)}"

    result = estimate_exponent(points, estimator="ssa", n_boot=200, seed=1)
    assert abs(result["point_estimate"] - ALPHA_TRUE) < 0.05, (
        f"recovered exponent {result['point_estimate']:.4f} too far from the known "
        f"true exponent {ALPHA_TRUE}"
    )
    # Not asserting true-value CI coverage on a single seed: this figure has no
    # plotted error bars, so reported_error is near-zero and the CI collapses
    # tightly around the point estimate. ssa is not perfectly unbiased (Gate 0c
    # measured ~89-90% coverage, not 100%), so a single tight draw missing the
    # true value by a hair is expected behavior, not a regression.


def test_figurespec_json_roundtrip(tmp_path):
    import json

    raw = {
        "name": "roundtrip",
        "pdf_path": "does_not_need_to_exist.pdf",
        "page": 1,
        "crop_box_frac": [0.0, 0.0, 1.0, 1.0],
        "x_axis_kind": "log",
        "x_axis_params": {"pixel0": 0.0, "log10_value0": -1.0, "pixel1": 100.0, "log10_value1": 0.0},
        "y_axis_kind": "linear",
        "y_axis_params": {"pixel0": 0.0, "value0": 1.0, "pixel1": 100.0, "value1": 0.0},
        "x_pixel_range": [0, 100],
        "y_pixel_margin": [0, 100],
        "color_mask": {"mode": "grey_band"},
        "legend_box": [0, 0, 10, 10],
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(raw))

    spec = FigureSpec.from_json(path)
    assert spec.name == "roundtrip"
    assert spec.color_mask.mode == "grey_band"
    # Legacy single "legend_box" key still loads, folded into exclude_boxes.
    assert spec.exclude_boxes == [(0, 0, 10, 10)]


def test_figurespec_json_multiple_exclude_boxes(tmp_path):
    import json

    raw = {
        "name": "multi-exclude",
        "pdf_path": "does_not_need_to_exist.pdf",
        "page": 1,
        "crop_box_frac": [0.0, 0.0, 1.0, 1.0],
        "x_axis_kind": "linear",
        "x_axis_params": {"pixel0": 0.0, "value0": 0.0, "pixel1": 100.0, "value1": 1.0},
        "y_axis_kind": "linear",
        "y_axis_params": {"pixel0": 0.0, "value0": 1.0, "pixel1": 100.0, "value1": 0.0},
        "x_pixel_range": [0, 100],
        "y_pixel_margin": [0, 100],
        "color_mask": {"mode": "near_color", "target_rgb": [1, 116, 184]},
        "exclude_boxes": [[0, 0, 10, 10], [50, 50, 60, 60]],
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(raw))

    spec = FigureSpec.from_json(path)
    assert spec.exclude_boxes == [(0, 0, 10, 10), (50, 50, 60, 60)]
