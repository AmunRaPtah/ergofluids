"""Regression checks on the Phase 3 literature digitization (Figure 4a and
Supplementary Figure S14a of arXiv:1909.05091), produced by
scripts/digitize_fig4a.py and scripts/digitize_s14a.py.

These are checks on the digitization pipeline itself (do the expected files
exist, are they non-empty, does the composite curve show its expected
plateau shape), not on Gate 4's statistical pass/fail outcome
(docs/gate-result-phase3-realdata.md). Gate 4 is run once, separately, and
is not re-derived here.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

DIGI_DIR = Path(__file__).resolve().parents[1] / "data" / "digitized"

EXPECTED_FIG4A_FILES = [
    "fig4a_composite.csv",
    "fig4a_hyaluronan.csv",
    "fig4a_collagen.csv",
]
EXPECTED_S14A_FILES = [
    "s14a_composite.csv",
    "s14a_hyaluronan.csv",
    "s14a_collagen_1mg.csv",
    "s14a_collagen_2mg.csv",
]
EXPECTED_FILES = EXPECTED_FIG4A_FILES + EXPECTED_S14A_FILES

REQUIRED_COLUMNS = {"x", "y", "reported_error", "digitization_error"}


@pytest.mark.parametrize("fname", EXPECTED_FILES)
def test_digitized_csv_exists_and_nonempty(fname):
    path = DIGI_DIR / fname
    assert path.exists(), f"missing digitized CSV: {path}"
    df = pd.read_csv(path)
    assert len(df) > 20, f"{fname} has suspiciously few points: {len(df)}"
    assert REQUIRED_COLUMNS.issubset(df.columns)
    assert df["x"].notna().all()
    assert df["y"].notna().all()
    # error columns should be present and non-negative (zero is fine; some
    # bins can have a tiny reported-error if the source curve shows an
    # essentially invisible error bar there).
    assert (df["reported_error"] >= 0).all()
    assert (df["digitization_error"] >= 0).all()


def _local_slope(df: pd.DataFrame, frac: float, tail: str) -> float:
    df = df.sort_values("x")
    x = df["x"].to_numpy()
    y = df["y"].to_numpy()
    logx = np.log10(x)
    n = len(x)
    cut = int(n * frac)
    if tail == "early":
        sel = slice(0, cut)
    else:
        sel = slice(n - cut, n)
    slope, _ = np.polyfit(logx[sel], y[sel], 1)
    return float(slope)


def test_fig4a_composite_shows_plateau_flattening():
    """The composite ISF curve should decay steeply at low tq^2 and flatten
    out (much smaller local slope magnitude) at high tq^2: the caged-dynamics
    signature the digitization is meant to capture. This is a check on the
    digitized composite curve alone, not a comparison against the pure
    hyaluronan/collagen curves (that comparison is Gate 4's job)."""
    df = pd.read_csv(DIGI_DIR / "fig4a_composite.csv")
    slope_early = _local_slope(df, frac=0.3, tail="early")
    slope_late = _local_slope(df, frac=0.3, tail="late")

    assert slope_early < 0, "expected the early-time ISF decay to be a clear negative slope"
    assert abs(slope_late) < abs(slope_early), (
        f"expected the late-window slope magnitude ({abs(slope_late):.4f}) to be measurably "
        f"lower than the early-window slope magnitude ({abs(slope_early):.4f}): "
        "the composite curve should show a flattening (plateau) signature"
    )
    # Not just "somewhat lower": require a large, unambiguous drop so this
    # test would actually fail if the digitization regressed.
    assert abs(slope_late) < 0.5 * abs(slope_early)


def test_s14a_composite_has_lower_global_exponent_than_pure_components():
    """Cross-check against the paper's own summary numbers (~0.5 for
    composite, ~1 for the pure networks): the digitized composite MSD curve's
    overall log-log slope should sit below both pure-component curves used in
    Figure 4a (1 mg/mL collagen, 2 mg/mL hyaluronan)."""
    composite = pd.read_csv(DIGI_DIR / "s14a_composite.csv").sort_values("x")
    hyaluronan = pd.read_csv(DIGI_DIR / "s14a_hyaluronan.csv").sort_values("x")
    collagen = pd.read_csv(DIGI_DIR / "s14a_collagen_1mg.csv").sort_values("x")

    def global_slope(df: pd.DataFrame) -> float:
        slope, _ = np.polyfit(np.log10(df["x"]), np.log10(df["y"]), 1)
        return float(slope)

    slope_composite = global_slope(composite)
    slope_hyaluronan = global_slope(hyaluronan)
    slope_collagen = global_slope(collagen)

    assert slope_composite < slope_hyaluronan
    assert slope_composite < slope_collagen
