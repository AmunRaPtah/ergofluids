"""Run the full network_sim parameter sweep and write results to CSV.

Run: .venv/bin/python scripts/run_network_sweep.py
Writes: data/network_sim_sweep.csv
"""

from pathlib import Path

import pandas as pd

from ergofluids.network_sim.sweep import build_grid, results_to_records, run_sweep

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "data" / "network_sim_sweep.csv"


def main() -> None:
    grid = build_grid()
    print(f"running {len(grid)} conditions x 3 network realizations each")
    results = run_sweep(seed_base=20260804)
    df = pd.DataFrame(results_to_records(results))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"wrote {len(df)} rows to {OUT_PATH}")
    print(df.describe())


if __name__ == "__main__":
    main()
