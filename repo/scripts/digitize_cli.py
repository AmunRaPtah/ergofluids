"""General-purpose CLI: digitize a figure from a FigureSpec JSON config and,
optionally, fit a power-law exponent with a bootstrap-propagated 95% CI.

This is the config-driven successor to the per-figure digitize_fig4a.py /
digitize_s14a.py scripts: those two remain as-is (they still produce the
exact CSVs Gate 4/5/the manuscript depend on), but any *new* figure should
go through this tool instead of a new bespoke script. See
`src/ergofluids/digitize/spec.py` for what a FigureSpec needs.

Usage:
  .venv/bin/python scripts/digitize_cli.py <spec.json> [--out points.csv] [--estimate] [--estimator ssa|loglog]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ergofluids.digitize.common import write_csv
from ergofluids.digitize.exponent_fit import estimate_exponent
from ergofluids.digitize.spec import FigureSpec, digitize

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="path to a FigureSpec JSON file")
    parser.add_argument("--out", type=Path, default=None, help="write digitized points here (CSV)")
    parser.add_argument("--render-dir", type=Path, default=REPO_ROOT / "scripts" / "_render_cli")
    parser.add_argument("--estimate", action="store_true", help="also fit a power-law exponent")
    parser.add_argument("--estimator", choices=["ssa", "loglog"], default="ssa")
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()

    spec = FigureSpec.from_json(args.spec)
    points = digitize(spec, render_dir=args.render_dir)
    print(f"{spec.name}: extracted {len(points)} points")

    if args.out:
        write_csv(args.out, points)
        print(f"wrote {args.out}")

    if args.estimate:
        result = estimate_exponent(points, estimator=args.estimator, n_boot=args.n_boot)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
