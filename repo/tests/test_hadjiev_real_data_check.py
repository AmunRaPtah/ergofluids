"""Regression check on the Hadjiev thesis real-data comparison
(docs/gate-result-network-sim-hadjiev-thesis-check.md): the per-solute
best-fit obstruction-scaling proportionality constant should decrease
monotonically with probe size, the quantitative signature of the
reptation-driven model breakdown the source thesis describes."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import curve_fit

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

DIGI_DIR = REPO_ROOT / "data" / "digitized"


@pytest.mark.skipif(
    not (DIGI_DIR / "hadjiev2014_fdx4.csv").exists(), reason="digitized Hadjiev thesis data not present"
)
def test_per_solute_k_decreases_with_probe_size():
    from check_hadjiev_thesis_real_data import FIBER_RADIUS_NM, SOLUTES, load_markers
    from ergofluids.network_sim.baseline import obstruction_scaling_relative_diffusivity

    markers = load_markers()
    ks = {}
    for name, info in SOLUTES.items():
        m = markers[name]

        def model(phi, k, rh=info["rh_nm"]):
            return np.array([obstruction_scaling_relative_diffusivity(rh, FIBER_RADIUS_NM, k * p) for p in phi])

        (k_fit,), _ = curve_fit(model, m["x"], m["y"], p0=[0.05], bounds=(1e-5, 1.0))
        ks[name] = k_fit

    ordered = [ks["fdx4"], ks["fdx10"], ks["fdx20"], ks["fdx40"]]
    assert ordered == sorted(ordered, reverse=True), (
        f"expected best-fit k to decrease monotonically with probe size, got {ordered}"
    )
