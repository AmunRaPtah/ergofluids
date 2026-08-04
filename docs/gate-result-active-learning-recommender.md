# Gate result: active-learning next-best-experiment recommender

Date: 2026-08-04. Kept lean per the author's direction to prioritize product building.

## What this is

A different product bet from `residual_model.py`'s zero-shot predictor (`docs/gate-result-network-sim-residual-model.md`):
instead of predicting transport behavior from nothing, `active_learning.py` assumes a lab already
has a handful of real pilot measurements and recommends which untested candidate to measure next,
via Gaussian Process uncertainty sampling (default) or a target-seeking acquisition score. This
sidesteps the exact problem that has not yet been validated against real data (see
`docs/gate-result-network-sim-real-data-check.md`): it does not need a trustworthy zero-shot
predictor to be useful, only a model that gets *more* useful as real measurements accumulate.

## Method

`src/ergofluids/network_sim/active_learning.py`: a `GaussianProcessRegressor` (RBF kernel,
length-scale bounds tuned to this feature space after an unconstrained fit degenerated on too few
points, see the module docstring) fit on observed `(adhesion_depth, aspect_ratio, confinement) ->
exponent` points. Real and simulated points can be mixed, with per-point noise set low for real
data and high for simulated data (the network_sim sweep), so a handful of real measurements can
dominate the fit locally without discarding simulated coverage entirely, an explicit design choice
given the real-data check found only premise-level, not quantitative, support for the simulated
data transferring to real systems.

## Validation

No real lab data exists yet to test this against directly. What was tested instead: does the
acquisition strategy itself do what active learning is supposed to do, using the network_sim sweep
as a synthetic, queryable ground-truth oracle (`tests/test_active_learning.py`). Starting from 6
randomly observed points out of the 36-condition sweep, running 8 sequential queries, and measuring
held-out prediction error on the remaining candidates, averaged over 8 random seeds:

| strategy | held-out MAE (mean) | held-out MAE (std) |
|---|---|---|
| uncertainty-sampling (this tool) | 0.0253 | 0.0052 |
| random sampling | 0.0352 | 0.0109 |

**Uncertainty sampling reduces held-out error by 28% versus random sampling on average, and is also
more consistent (lower run-to-run variance).** A deterministic unit test additionally confirms the
qualitative behavior directly: given three observed points clustered at low adhesion, a candidate at
high adhesion (far from anything observed) is ranked above a candidate immediately adjacent to an
existing observation.

## What this does not show

- Not tested against real data: the "ground truth" here is the self-generated simulation sweep, not
  a real lab's measurements. This validates the *acquisition strategy* (does querying
  high-uncertainty points reduce error faster than random querying), not the underlying model's
  accuracy on real systems, which remains the open question from the real-data check.
- The real/simulated noise weighting (`REAL_POINT_NOISE`, `SIMULATED_POINT_NOISE` in
  `active_learning.py`) is a reasonable-by-construction choice, not itself calibrated against any
  data showing what the right relative trust level actually is.

## Product interface

`scripts/recommend_next_experiment.py`: given a CSV of your own observed data points and a CSV of
untested candidates, prints the top-N candidates to test next, ranked by acquisition score, with
predicted exponent and uncertainty shown for each. `--strategy target --target <value>` switches
from pure exploration to seeking a specific desired exponent (e.g. for a sustained-release
formulation targeting a specific subdiffusive profile, rather than assuming "more Fickian is
better").

## Bearing on the project

Completes the three-part direction from the author (validate network_sim against real data where
possible, then build the active-learning tool). IP/venture material still does not open on any of
this, per the project's standing gating discipline; both the residual-model predictor and this
recommender remain simulation-validated and premise-checked against real data, not real-data
validated in the sense that discipline requires.
