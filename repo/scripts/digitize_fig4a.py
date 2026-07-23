"""Digitize Figure 4a from arXiv:1909.05091 (Burla et al., "Particle diffusion
in extracellular hydrogels"): intermediate scattering function (ISF) vs tq^2
for 0.6 um tracer particles in three networks (composite collagen-hyaluronan,
orange; pure hyaluronan, blue; pure collagen, black/grey).

PDF page 12 (400 DPI render), cropped to the panel. Axis calibration derived
once from tick-mark pixel positions (see the tick-detection output recorded
in the digitization session that produced this script) and hardcoded below;
x is log10(tq^2) in s/um^2, y is linear ISF in [0, 1].

Run: .venv/bin/python scripts/digitize_fig4a.py
Writes: data/digitized/fig4a_{composite,hyaluronan,collagen}.csv
"""

from pathlib import Path

import numpy as np

from digitize_common import LinearAxis, LogAxis, crop_fractional, extract_curve, render_page, write_csv

REPO_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = Path(
    "/root/.claude/projects/-root/79aad091-2005-4085-9203-76889a1908fe/"
    "tool-results/webfetch-1784756646963-fkzsvo.pdf"
)
RENDER_DIR = REPO_ROOT / "scripts" / "_render"
OUT_DIR = REPO_ROOT / "data" / "digitized"

# Fractional crop box (x0, y0, x1, y1) of the full rendered page, chosen by
# inspection to isolate panel (a) with its full axes and tick labels.
CROP_BOX = (0.04, 0.155, 0.53, 0.475)

# Axis calibration in crop-local pixel coordinates, derived from tick marks
# (major ticks at decades / 0.2-ISF gridlines, cross-checked against 6-8 log
# minor ticks per axis, sub-pixel-consistent; see script docstring above).
# x: log10(tq^2) = -1 at pixel 417.0, +1 decade per 160.0 px
X_AXIS = LogAxis(pixel0=417.0, log10_value0=-1.0, pixel1=417.0 + 160.0, log10_value1=0.0)
# y: ISF = 1.0 at pixel 562.5 (top frame), 0.0 at pixel 1189.5 (bottom frame)
Y_AXIS = LinearAxis(pixel0=562.5, value0=1.0, pixel1=1189.5, value1=0.0)

# Plot interior in crop-local pixels, margin pulled in from the frame edges
# (417/1265 horiz, 561/1193 vert) to avoid the frame line and tick marks
# themselves being picked up as data.
X_PIXEL_RANGE = (428, 1258)
Y_PIXEL_MARGIN_TOP = 570
Y_PIXEL_MARGIN_BOTTOM = 1170

# Legend box occupies the upper-right of the panel; exclude it so legend
# swatches/text are never mistaken for curve data.
LEGEND_BOX = (985, 565, 1263, 705)  # (col_lo, row_lo, col_hi, row_hi)


def _color_masks(arr: np.ndarray) -> dict[str, np.ndarray]:
    R, G, B = arr[..., 0], arr[..., 1], arr[..., 2]
    orange = (R - B > 60) & (R > 180) & (G > 80) & (G < 230) & (B < 190)
    blue = (B - R > 60) & (B > 150)
    grey = (np.abs(R - G) < 12) & (np.abs(G - B) < 12) & (R > 20) & (R < 190)

    interior = np.zeros(R.shape, dtype=bool)
    interior[Y_PIXEL_MARGIN_TOP:Y_PIXEL_MARGIN_BOTTOM, X_PIXEL_RANGE[0] : X_PIXEL_RANGE[1]] = True
    legend = np.zeros(R.shape, dtype=bool)
    lc0, lr0, lc1, lr1 = LEGEND_BOX
    legend[lr0:lr1, lc0:lc1] = True

    not_legend = ~legend
    return {
        "composite": orange & interior & not_legend,
        "hyaluronan": blue & interior & not_legend,
        "collagen": grey & interior & not_legend,
    }


def main() -> None:
    png_path = render_page(PDF_PATH, page=12, out_dir=RENDER_DIR)
    arr = crop_fractional(png_path, CROP_BOX)
    masks = _color_masks(arr)

    for name, mask in masks.items():
        pts = extract_curve(mask, X_AXIS, Y_AXIS, X_PIXEL_RANGE)
        out_path = OUT_DIR / f"fig4a_{name}.csv"
        write_csv(out_path, pts)
        print(f"{name}: {len(pts)} points -> {out_path}")


if __name__ == "__main__":
    main()
