"""Product-facing CLI: predict a subdiffusion exponent and regime
(normal/hindered/caged) for a candidate macromolecule-network combination,
using the obstruction-scaling baseline plus the residual/classifier models
fit on the network_sim parameter sweep.

This is a prototype trained on self-generated simulation data
(data/network_sim_sweep.csv, from scripts/run_network_sweep.py), not yet
validated against real experimental data; see
docs/gate-result-network-sim-* for what has and has not been shown.

Usage:
  .venv/bin/python scripts/predict_transport.py \
    --particle-radius 0.4 --mesh-pore-radius 1.5 \
    --adhesion 2.0 --aspect-ratio 1.0
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ergofluids.network_sim.baseline import baseline_predicted_exponent
from ergofluids.network_sim.residual_model import add_derived_columns, fit_full_models, leave_one_out_validate

REPO_ROOT = Path(__file__).resolve().parents[1]
SWEEP_CSV = REPO_ROOT / "data" / "network_sim_sweep.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--particle-radius", type=float, required=True)
    parser.add_argument("--mesh-pore-radius", type=float, required=True, help="mean pore radius of the network")
    parser.add_argument("--adhesion", type=float, default=0.0, help="0 = purely steric")
    parser.add_argument("--aspect-ratio", type=float, default=1.0, help="1 = sphere, >1 = elongated")
    parser.add_argument("--show-validation", action="store_true", help="print leave-one-out validation first")
    args = parser.parse_args()

    if not SWEEP_CSV.exists():
        raise SystemExit(f"{SWEEP_CSV} not found; run scripts/run_network_sweep.py first")
    df = pd.read_csv(SWEEP_CSV)

    if args.show_validation:
        val = leave_one_out_validate(df)
        print("Leave-one-out validation on the training sweep:")
        print(json.dumps(val.__dict__, indent=2))
        print()

    reg, clf = fit_full_models(df)

    baseline_exp = baseline_predicted_exponent(steric_only=(args.adhesion == 0))
    confinement = args.particle_radius / args.mesh_pore_radius
    x = [[args.adhesion, args.aspect_ratio, confinement]]
    residual = float(reg.predict(x)[0])
    regime = clf.predict(x)[0]
    regime_proba = dict(zip(clf.classes_, clf.predict_proba(x)[0].tolist()))

    result = {
        "baseline_exponent": baseline_exp,
        "predicted_exponent": baseline_exp + residual,
        "predicted_residual": residual,
        "predicted_regime": str(regime),
        "regime_probabilities": {str(k): round(v, 3) for k, v in regime_proba.items()},
        "inputs": {
            "particle_radius": args.particle_radius,
            "mesh_pore_radius": args.mesh_pore_radius,
            "confinement": confinement,
            "adhesion_depth": args.adhesion,
            "aspect_ratio": args.aspect_ratio,
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
