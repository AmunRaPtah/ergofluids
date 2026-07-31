"""Generate the two figures referenced in docs/manuscript-draft.md.

Pure visualization of already-reported, already-locked results (Gate 0, 0b,
5, 6); this script computes no new statistics and changes no pass/fail
result. The composite curve's point-estimate fit parameters (as opposed to
Gate 5's bootstrap CIs) are computed here for the first time, by re-using
Gate 5's own fitting functions on the unperturbed data, since Gate 5 itself
only ever reported bootstrap distributions, not the single best fit.

Palette: dataviz skill's validated default categorical palette (light mode),
run through scripts/validate_palette.js before use (both the 6-color and the
3-color subsets pass every hard gate; some slots carry a contrast WARN that
requires visible direct labels, already present in both figures below).

Run: .venv/bin/python scripts/make_manuscript_figures.py
Writes: ../docs/figures/fig2_coverage_comparison.png
        ../docs/figures/fig1_composite_msd_fits.png
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from run_gate5 import DIGI_DIR, _fit_confined, _fit_powerlaw, confined, powerlaw

REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT.parent / "docs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# dataviz skill categorical palette, light mode, fixed order (validated).
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
GREEN = "#008300"

INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "text.color": INK,
        "axes.edgecolor": BASELINE,
        "axes.labelcolor": INK,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
    }
)


def fig2_coverage_comparison():
    alphas = [0.5, 0.7, 1.0]
    # loglog/dmd/ssa: Gate 0b re-run (docs/BUILD_PLAN.md Table 1b / gate-result-phase1-synthetic.md).
    # hodmd_fb/bopdmd/subspace: Gate 6 (docs/gate-result-gate6-dmd-generality.md).
    series = {
        "loglog": ([18, 19, 19], BLUE),
        "dmd (HODMD)": ([17, 18, 13], ORANGE),
        "ssa": ([17, 19, 18], AQUA),
        "hodmd_fb": ([15, 12, 15], YELLOW),
        "bopdmd": ([18, 20, 20], MAGENTA),
        "subspace": ([20, 20, 19], GREEN),
    }
    required = 18
    n_repeats = 20

    fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
    n_series = len(series)
    bar_w = 0.8 / n_series
    x = np.arange(len(alphas))

    for i, (name, (coverage, color)) in enumerate(series.items()):
        offset = (i - (n_series - 1) / 2) * bar_w
        bars = ax.bar(
            x + offset,
            coverage,
            width=bar_w * 0.9,
            color=color,
            label=name,
            zorder=3,
        )
        for b, v in zip(bars, coverage):
            ax.text(
                b.get_x() + b.get_width() / 2,
                v + 0.4,
                str(v),
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=INK_SECONDARY,
            )

    ax.axhline(required, color=INK_MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
    ax.text(
        0.005,
        0.975,
        f"{required}/{n_repeats} required",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color=INK_MUTED,
    )

    ax.set_xticks(x)
    ax.set_xticklabels([f"alpha_true = {a}" for a in alphas])
    ax.set_ylabel(f"bootstrap-CI coverage (out of {n_repeats})")
    ax.set_ylim(0, n_repeats + 3.5)
    ax.set_title(
        "Coverage across six exponent estimators\n"
        "(loglog/dmd/ssa: Gate 0b; hodmd_fb/bopdmd/subspace: Gate 6)",
        fontsize=10.5,
        color=INK,
        loc="left",
    )
    ax.grid(axis="y", color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.28),
        ncol=6,
        frameon=False,
        fontsize=8,
        labelcolor=INK_SECONDARY,
    )

    fig.tight_layout()
    out = FIG_DIR / "fig2_coverage_comparison.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def fig1_composite_msd_fits():
    df = pd.read_csv(DIGI_DIR / "s14a_composite.csv").sort_values("x").reset_index(drop=True)
    t = df.x.values
    y = df.y.values
    sigma = np.sqrt(df.reported_error.values ** 2 + df.digitization_error.values ** 2)

    A, alpha = _fit_powerlaw(t, y, sigma)
    P, tau = _fit_confined(t, y, sigma)

    t_smooth = np.logspace(np.log10(t.min()), np.log10(t.max()), 300)

    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=200)
    ax.errorbar(
        t,
        y,
        yerr=sigma,
        fmt="o",
        color=BLUE,
        ecolor=BLUE,
        elinewidth=0.7,
        capsize=0,
        markersize=3.5,
        alpha=0.65,
        label="digitized composite MSD (S14a)",
        zorder=3,
    )
    ax.plot(
        t_smooth,
        powerlaw(t_smooth, A, alpha),
        color=ORANGE,
        linewidth=2,
        label=f"power law fit (alpha = {alpha:.2f})",
        zorder=4,
    )
    ax.plot(
        t_smooth,
        confined(t_smooth, P, tau),
        color=AQUA,
        linewidth=2,
        linestyle=(0, (5, 2)),
        label=f"confined-diffusion fit (tau = {tau:.2f} s)",
        zorder=4,
    )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Delta t (s)")
    ax.set_ylabel("MSD (um^2)")
    ax.set_title(
        "Composite network: digitized MSD vs. two pre-registered fits (Gate 5)",
        fontsize=10.5,
        color=INK,
        loc="left",
    )
    ax.grid(True, which="both", color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK_SECONDARY)

    fig.tight_layout()
    out = FIG_DIR / "fig1_composite_msd_fits.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
    print(f"point-estimate fit params: power law A={A:.5f} alpha={alpha:.4f}; confined P={P:.5f} tau={tau:.4f}")


if __name__ == "__main__":
    fig2_coverage_comparison()
    fig1_composite_msd_fits()
