"""Digitize Supplementary Figure S14, panel (a) from arXiv:1909.05091 (Burla
et al., "Particle diffusion in extracellular hydrogels"): ensemble MSD vs
Delta t for 0.6 um tracer particles in four networks: 1 mg/mL collagen
(black), 2 mg/mL collagen (grey), 2 mg/mL hyaluronan (blue), composite
collagen-hyaluronan (orange).

PDF page 32 (400 DPI render), cropped to panel (a) only (the top-left
log-log MSD plot; panels b/c/d are not digitized here). Axis calibration
derived once from tick-mark pixel positions and hardcoded below; both axes
are log10 (Delta t in seconds, MSD in um^2).

Run: .venv/bin/python scripts/digitize_s14a.py
Writes: data/digitized/s14a_{collagen_1mg,collagen_2mg,hyaluronan,composite}.csv
"""

from pathlib import Path

import numpy as np

from ergofluids.digitize.common import LogAxis, crop_fractional, extract_curve, render_page, write_csv

REPO_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = Path(
    "/root/.claude/projects/-root/79aad091-2005-4085-9203-76889a1908fe/"
    "tool-results/webfetch-1784756646963-fkzsvo.pdf"
)
RENDER_DIR = REPO_ROOT / "scripts" / "_render"
OUT_DIR = REPO_ROOT / "data" / "digitized"

# Fractional crop box (x0, y0, x1, y1) of the full rendered page, chosen by
# inspection to isolate panel (a) (MSD vs Delta t) with its full axes.
CROP_BOX = (0.05, 0.06, 0.52, 0.32)

# Axis calibration in crop-local pixel coordinates.
# x: log10(Delta t) = -2 at pixel 432.1, +1 decade per 278.8 px
X_AXIS = LogAxis(pixel0=432.1, log10_value0=-2.0, pixel1=432.1 + 278.8, log10_value1=-1.0)
# y: log10(MSD) = 0 at pixel 378.0, +1 decade per -234.5 px (row decreases as value increases)
Y_AXIS = LogAxis(pixel0=378.0, log10_value0=0.0, pixel1=378.0 - 234.5, log10_value1=1.0)

# Plot interior in crop-local pixels, pulled in from the frame edges
# (405/1352 horiz, 145/846 vert) to avoid the frame line and tick marks.
X_PIXEL_RANGE = (425, 1338)
Y_PIXEL_MARGIN_TOP = 158
Y_PIXEL_MARGIN_BOTTOM = 835

# Legend box (top-left of the panel) excluded so legend swatches/text are
# never mistaken for curve data.
LEGEND_BOX = (450, 150, 900, 390)  # (col_lo, row_lo, col_hi, row_hi)


def _color_masks(arr: np.ndarray) -> dict[str, np.ndarray]:
    R, G, B = arr[..., 0], arr[..., 1], arr[..., 2]
    black_c = (R < 40) & (G < 40) & (B < 40)
    grey_c = (np.abs(R - 128) < 20) & (np.abs(G - 128) < 20) & (np.abs(B - 128) < 20)
    blue_c = (B - R > 100) & (B > 150) & (G < 100)
    orange_c = (R > 200) & (G > 80) & (G < 180) & (B < 80)

    interior = np.zeros(R.shape, dtype=bool)
    interior[Y_PIXEL_MARGIN_TOP:Y_PIXEL_MARGIN_BOTTOM, X_PIXEL_RANGE[0] : X_PIXEL_RANGE[1]] = True
    legend = np.zeros(R.shape, dtype=bool)
    lc0, lr0, lc1, lr1 = LEGEND_BOX
    legend[lr0:lr1, lc0:lc1] = True
    not_legend = ~legend

    return {
        "collagen_1mg": black_c & interior & not_legend,
        "collagen_2mg": grey_c & interior & not_legend,
        "hyaluronan": blue_c & interior & not_legend,
        "composite": orange_c & interior & not_legend,
    }


def main() -> None:
    png_path = render_page(PDF_PATH, page=32, out_dir=RENDER_DIR)
    arr = crop_fractional(png_path, CROP_BOX)
    masks = _color_masks(arr)

    for name, mask in masks.items():
        pts = extract_curve(mask, X_AXIS, Y_AXIS, X_PIXEL_RANGE)
        out_path = OUT_DIR / f"s14a_{name}.csv"
        write_csv(out_path, pts)
        print(f"{name}: {len(pts)} points -> {out_path}")


if __name__ == "__main__":
    main()
