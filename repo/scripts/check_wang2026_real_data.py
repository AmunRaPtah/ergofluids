"""Real-data check on the steric-only obstruction-scaling premise: does
relative diffusivity decrease with solute size across five real drugs in a
real hydrogel (Wang 2026, Pharmaceutics, doi:10.3390/pharmaceutics18050592),
as steric-only obstruction-scaling requires? Numbers taken directly from
that paper's Tables 1 and 2, not estimated. Full discussion:
docs/gate-result-network-sim-real-data-check.md.

Run: .venv/bin/python scripts/check_wang2026_real_data.py
"""

import numpy as np
from scipy import stats

DRUGS = ["5-fluorouracil", "acetylcholine", "paracetamol", "prednisolone", "amphotericin_B"]
R_H_NM = np.array([0.23, 0.25, 0.31, 0.41, 0.60])
D_FREE = np.array([7.714e-10, 7.025e-10, 5.811e-10, 4.297e-10, 2.950e-10])
D_GEL_SLOW_MODE = np.array([8.434e-11, 2.084e-11, 1.186e-10, 3.719e-11, 1.528e-10])
HAS_FAST_MODE = np.array([1, 1, 1, 0, 0])  # 1 = also shows a faster, more free-like population


def main() -> None:
    ratio = D_GEL_SLOW_MODE / D_FREE
    for drug, r_h, r in zip(DRUGS, R_H_NM, ratio):
        print(f"{drug}: R_H={r_h} nm, D_gel/D_free={r:.4f}")

    rho, p = stats.spearmanr(R_H_NM, ratio)
    print()
    print(f"Spearman rho(R_H, D_gel/D_free) = {rho:.3f}, p = {p:.3f}, n = {len(DRUGS)}")
    print("Steric-only obstruction-scaling requires rho << 0; observed sign is wrong.")

    print()
    print("mean ratio, has a fast/free-like population:", ratio[HAS_FAST_MODE == 1].mean())
    print("mean ratio, fully in the slow population:", ratio[HAS_FAST_MODE == 0].mean())


if __name__ == "__main__":
    main()
