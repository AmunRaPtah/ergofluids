"""Gate 7: digitization pipeline accuracy against synthetic ground truth.

Pre-registered in docs/BUILD_PLAN.md ("Gate 7") before this script was run.
Builds a synthetic log-log panel with known (x, y, error) ground truth,
renders it through the project's own PDF -> PNG path
(digitize_common.render_page, i.e. actual pdftoppm), computes axis
calibration analytically (not hand-read), and runs the same
digitize_common.extract_curve function the two real digitization scripts
use, unmodified, to recover points. Compares recovered values against the
known ground truth.

Run: .venv/bin/python scripts/run_gate7.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from digitize_common import LogAxis, extract_curve, render_page

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = REPO_ROOT / "scripts" / "_render_gate7"
SEED = 20260731  # distinguished from other gates by the "rev7" label in BUILD_PLAN.md prose

N_POINTS = 30
A_TRUE = 2.0
ALPHA_TRUE = 0.65
JITTER_SIGMA = 0.04
ERROR_FRAC = 0.10
X_LO, X_HI = 1e-2, 10.0
Y_LO, Y_HI = 1e-2, 10.0
RENDER_DPI = 400
FIG_W_IN, FIG_H_IN = 6.0, 5.0
AXES_RECT = (0.15, 0.15, 0.75, 0.75)  # figure-fraction [left, bottom, width, height]

DATA_COLOR = "#e67300"  # inside digitize_s14a's orange_c mask: R>200, 80<G<180, B<80


def _color_mask(arr: np.ndarray) -> np.ndarray:
    R, G, B = arr[..., 0], arr[..., 1], arr[..., 2]
    return (R > 200) & (G > 80) & (G < 180) & (B < 80)


def build_ground_truth():
    rng = np.random.default_rng(SEED)
    x = np.logspace(np.log10(X_LO), np.log10(X_HI), N_POINTS)
    y_clean = A_TRUE * x**ALPHA_TRUE
    jitter = rng.lognormal(mean=0.0, sigma=JITTER_SIGMA, size=N_POINTS)
    y = y_clean * jitter
    err = ERROR_FRAC * y
    return x, y, err


def interpolate_loglog(x_query, x_vertices, y_vertices):
    """Log-log linear interpolation between known vertices, matching how
    matplotlib draws straight segments between consecutive plotted points."""
    logx_v = np.log10(x_vertices)
    logy_v = np.log10(y_vertices)
    logx_q = np.log10(x_query)
    logy_q = np.interp(logx_q, logx_v, logy_v)
    return 10.0**logy_q


def main():
    x_true, y_true, err_true = build_ground_truth()

    fig = plt.figure(figsize=(FIG_W_IN, FIG_H_IN), dpi=72)
    ax = fig.add_axes(AXES_RECT)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(X_LO, X_HI)
    ax.set_ylim(Y_LO, Y_HI)
    ax.errorbar(
        x_true,
        y_true,
        yerr=err_true,
        color=DATA_COLOR,
        ecolor=DATA_COLOR,
        linewidth=1.8,
        elinewidth=1.2,
        capsize=0,
        marker="",
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.canvas.draw()

    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = RENDER_DIR / "gate7_synthetic.pdf"
    fig.savefig(pdf_path, format="pdf")
    plt.close(fig)

    png_path = render_page(pdf_path, page=1, out_dir=RENDER_DIR, dpi=RENDER_DPI)
    from PIL import Image

    arr = np.array(Image.open(png_path).convert("RGB")).astype(int)
    img_h_px, img_w_px = arr.shape[0], arr.shape[1]
    assert img_h_px == round(FIG_H_IN * RENDER_DPI)
    assert img_w_px == round(FIG_W_IN * RENDER_DPI)

    scale = RENDER_DPI / 72.0  # verified against detected frame edges in pre-registration smoke test

    def data_to_pixel(x, y):
        px, py = ax.transData.transform((x, y))
        col = px * scale
        row = img_h_px - py * scale
        return col, row

    x0_col, _ = data_to_pixel(X_LO, 1.0)
    x1_col, _ = data_to_pixel(X_HI, 1.0)
    _, y0_row = data_to_pixel(1.0, Y_LO)
    _, y1_row = data_to_pixel(1.0, Y_HI)

    X_AXIS = LogAxis(pixel0=x0_col, log10_value0=np.log10(X_LO), pixel1=x1_col, log10_value1=np.log10(X_HI))
    Y_AXIS = LogAxis(pixel0=y0_row, log10_value0=np.log10(Y_LO), pixel1=y1_row, log10_value1=np.log10(Y_HI))

    mask = _color_mask(arr)
    x_pixel_range = (int(round(x0_col)) + 2, int(round(x1_col)) - 2)
    points = extract_curve(mask, X_AXIS, Y_AXIS, x_pixel_range)
    print(f"extracted {len(points)} points from {x_pixel_range[1] - x_pixel_range[0]}px interior")

    rec_x = np.array([p[0] for p in points])
    rec_y = np.array([p[1] for p in points])
    rec_reported_err = np.array([p[2] for p in points])

    # Check 1: curve-following accuracy across all extracted bins.
    y_expected = interpolate_loglog(rec_x, x_true, y_true)
    rel_err = np.abs(rec_y - y_expected) / y_expected
    median_rel_err = float(np.median(rel_err))
    p95_rel_err = float(np.percentile(rel_err, 95))
    print(f"check 1 (curve-following, n={len(rec_x)}): median rel err = {median_rel_err:.5f}, "
          f"95th pct = {p95_rel_err:.5f}")
    check1_pass = median_rel_err < 0.02 and p95_rel_err < 0.08
    print(f"check 1 pass (median<2%, p95<8%): {check1_pass}")

    # Check 2: error-bar recovery at the 30 known vertices.
    vertex_rec_err = []
    for xv, ev in zip(x_true, err_true):
        idx = int(np.argmin(np.abs(rec_x - xv)))
        vertex_rec_err.append(rec_reported_err[idx])
    vertex_rec_err = np.array(vertex_rec_err)
    rel_err_bars = np.abs(vertex_rec_err - err_true) / err_true
    median_rel_err_bars = float(np.median(rel_err_bars))
    corr = float(np.corrcoef(vertex_rec_err, err_true)[0, 1])
    print(f"check 2 (error-bar recovery, n={len(x_true)}): median rel err = {median_rel_err_bars:.5f}, "
          f"pearson r = {corr:.4f}")
    check2_pass = median_rel_err_bars < 0.15 and corr > 0.8
    print(f"check 2 pass (median<15%, r>0.8): {check2_pass}")

    print(f"\nOVERALL: {'PASS' if (check1_pass and check2_pass) else 'FAIL'}")


if __name__ == "__main__":
    main()
