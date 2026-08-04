"""Real-data check on the obstruction-scaling baseline itself (not just its
premise): digitized FRAP data from Hadjiev's 2014 MaSc thesis (Queen's
University, supervised by Amsden; open-access via QSpace/Scholaris,
handle 1974/12603), the underlying work behind Hadjiev & Amsden 2015 (J
Control Release, doi:10.1016/j.jconrel.2014.12.010).

Four FITC-dextran probes (FDX-4, FDX-10, FDX-20, FDX-40 kDa) diffusing in
alginate-methacrylate hydrogels across polymer volume fractions 0-3%,
digitized from the thesis's own Figures 15 and 16
(scripts/_hadjiev_fig1{5,6}_*.spec.json, gitignored scratch configs; output
in data/digitized/hadjiev2014_fdx*.csv). Hydrodynamic radii from the
thesis's own Table 2; fiber (polymer chain) radius 0.83 nm from the
thesis's Section 4.6 (measured by SAXS, Wang et al., adjusted for
hydration).

The thesis derives its own "Model" curve from a correlation-length/blob
scaling formalism (Rubinstein-Colby), not the simple straight-fiber line
density `network_sim.baseline` uses. Rather than re-deriving their full
polymer-physics chain (which needs the native alginate's molecular weight,
not extracted here), this script fits ONE free parameter, a proportionality
constant k linking polymer volume fraction Phi to network_sim's own
fiber-line-density parameter (assumed L = k * Phi, the simplest physically
reasonable form: more polymer, proportionally more fiber length per area),
by least squares against all four real solutes simultaneously. This tests
whether `network_sim.baseline`'s functional FORM, not the thesis's specific
derivation, can fit real data, and quantifies the same small-probe-good /
large-probe-bad pattern the thesis reports in words, as actual numbers.

Run: .venv/bin/python scripts/check_hadjiev_thesis_real_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from ergofluids.network_sim.baseline import obstruction_scaling_relative_diffusivity

REPO_ROOT = Path(__file__).resolve().parents[1]
DIGI_DIR = REPO_ROOT / "data" / "digitized"

FIBER_RADIUS_NM = 0.83  # thesis Section 4.6

# Hydrodynamic radii from the thesis's own Table 2 ("HDrs", experimental radius)
SOLUTES = {
    "fdx4": {"rh_nm": 1.4, "csv": "hadjiev2014_fdx4.csv"},
    "fdx10": {"rh_nm": 2.3, "csv": "hadjiev2014_fdx10.csv"},
    "fdx20": {"rh_nm": 3.3, "csv": "hadjiev2014_fdx20.csv"},
    "fdx40": {"rh_nm": 4.5, "csv": "hadjiev2014_fdx40.csv"},
}


def cluster_by_gap(points: pd.DataFrame, x_gap: float = 0.1) -> pd.DataFrame:
    """Digitized points come in tight clusters (one per marker, from
    extract_curve's column binning across a marker's pixel width). Group by
    gaps in x larger than `x_gap` (data units), then take each cluster's
    mean (x, y) as that marker's representative value."""
    points = points.sort_values("x").reset_index(drop=True)
    gap = points["x"].diff().fillna(0)
    group = (gap > x_gap).cumsum()
    return points.groupby(group)[["x", "y"]].mean().reset_index(drop=True)


def load_markers() -> dict:
    markers = {}
    for name, info in SOLUTES.items():
        df = pd.read_csv(DIGI_DIR / info["csv"])
        markers[name] = cluster_by_gap(df)
    return markers


def fit_k(markers: dict) -> float:
    all_phi, all_ratio, all_rh = [], [], []
    for name, info in SOLUTES.items():
        m = markers[name]
        all_phi.extend(m["x"].tolist())
        all_ratio.extend(m["y"].tolist())
        all_rh.extend([info["rh_nm"]] * len(m))
    all_phi, all_ratio, all_rh = np.array(all_phi), np.array(all_ratio), np.array(all_rh)

    def model(X, k):
        phi, rh = X
        return np.array(
            [
                obstruction_scaling_relative_diffusivity(rh_i, FIBER_RADIUS_NM, k * phi_i)
                for phi_i, rh_i in zip(phi, rh)
            ]
        )

    (k_fit,), _ = curve_fit(model, (all_phi, all_rh), all_ratio, p0=[0.05], bounds=(1e-4, 1.0))
    return float(k_fit)


def main() -> None:
    markers = load_markers()
    k = fit_k(markers)
    print(f"fitted proportionality constant k (fiber_line_density = k * Phi): {k:.4f}\n")

    print(f"{'solute':<8} {'rh (nm)':>8} {'n_markers':>10} {'MAE':>8}")
    maes = {}
    for name, info in SOLUTES.items():
        m = markers[name]
        pred = np.array(
            [
                obstruction_scaling_relative_diffusivity(info["rh_nm"], FIBER_RADIUS_NM, k * phi)
                for phi in m["x"]
            ]
        )
        mae = float(np.mean(np.abs(pred - m["y"])))
        maes[name] = mae
        print(f"{name:<8} {info['rh_nm']:>8.1f} {len(m):>10} {mae:>8.4f}")

    small = np.mean([maes["fdx4"], maes["fdx10"]])
    large = np.mean([maes["fdx20"], maes["fdx40"]])
    print(f"\nmean MAE, small probes (FDX-4, FDX-10): {small:.4f}")
    print(f"mean MAE, large probes (FDX-20, FDX-40): {large:.4f}")
    print(f"ratio (large/small): {large / small:.2f}x")


if __name__ == "__main__":
    main()
