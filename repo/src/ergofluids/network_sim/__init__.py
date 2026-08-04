"""Self-generated Brownian-dynamics simulation of a probe particle in a random
fiber network, an obstruction-scaling physics baseline, and a small
residual/classifier model on top of both. A fresh technical bet on the
original ErgoFluids problem (predicting transport of a candidate
macromolecule through a characterized hydrogel/ECM-mimetic network), distinct
from the Koopman/Mori-Zwanzig approach in `ergofluids.koopman`/`ergofluids.mz`,
which failed its real-data gates (see ../../../docs/gate-result-phase3-realdata.md
and gate-result-phase3-gate5-cagedfit.md). Nothing here reuses or depends on
that approach except the already-validated `ssa_denoise_exponent` estimator
from `ergofluids.koopman.exponent`, used to fit exponents to simulated MSD
curves the same way it was validated to fit them to real ones."""
