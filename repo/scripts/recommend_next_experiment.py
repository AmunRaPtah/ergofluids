"""Product-facing CLI: given a small CSV of a lab's own observed
(candidate descriptors -> measured exponent) data points, and a CSV of
untested candidates, recommend which candidate to test next.

This does not require the zero-shot prediction problem to be solved (see
docs/gate-result-network-sim-real-data-check.md for why that remains
untested against real data); it only assumes a handful of real pilot
measurements already exist, and asks which untested candidate would most
reduce model uncertainty (default) or best approach a target exponent.

Observed-points CSV columns: adhesion_depth, aspect_ratio, confinement, exponent
Candidate-pool CSV columns: adhesion_depth, aspect_ratio, confinement (+ any
other columns you want carried through to the output, e.g. a candidate name)

Usage:
  .venv/bin/python scripts/recommend_next_experiment.py \
    --observed my_lab_data.csv --candidates my_candidates.csv \
    [--strategy uncertainty | --strategy target --target 0.7] \
    [--top-n 3] [--seed-with-simulated]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ergofluids.network_sim.active_learning import ObservedPoint, fit_gp, recommend_next, sweep_csv_to_simulated_points

REPO_ROOT = Path(__file__).resolve().parents[1]
SWEEP_CSV = REPO_ROOT / "data" / "network_sim_sweep.csv"


def _load_observed(path: Path) -> list[ObservedPoint]:
    df = pd.read_csv(path)
    required = {"adhesion_depth", "aspect_ratio", "confinement", "exponent"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{path} is missing required columns: {sorted(missing)}")
    return [
        ObservedPoint(
            adhesion_depth=row.adhesion_depth,
            aspect_ratio=row.aspect_ratio,
            confinement=row.confinement,
            exponent=row.exponent,
            source="real",
        )
        for row in df.itertuples()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--observed", type=Path, required=True, help="CSV of your own measured data points")
    parser.add_argument("--candidates", type=Path, required=True, help="CSV of untested candidates")
    parser.add_argument("--strategy", choices=["uncertainty", "target"], default="uncertainty")
    parser.add_argument("--target", type=float, default=None, help="required if --strategy target")
    parser.add_argument("--beta", type=float, default=1.0, help="exploration weight for --strategy target")
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument(
        "--seed-with-simulated",
        action="store_true",
        help=(
            "also include the self-generated network_sim sweep as a weak prior "
            "(high per-point noise; see active_learning.py docstring for why "
            "this is not treated as trustworthy as real data)"
        ),
    )
    args = parser.parse_args()

    if args.strategy == "target" and args.target is None:
        raise SystemExit("--strategy target requires --target")

    observed = _load_observed(args.observed)
    if args.seed_with_simulated:
        if not SWEEP_CSV.exists():
            raise SystemExit(f"{SWEEP_CSV} not found; run scripts/run_network_sweep.py first")
        observed = observed + sweep_csv_to_simulated_points(pd.read_csv(SWEEP_CSV))

    gp = fit_gp(observed)
    candidates = pd.read_csv(args.candidates)
    ranked = recommend_next(gp, candidates, strategy=args.strategy, target=args.target, beta=args.beta)

    print(f"Top {args.top_n} candidates to test next ({args.strategy} strategy):")
    print(ranked.head(args.top_n).to_string(index=False))


if __name__ == "__main__":
    main()
