# Venture material: not started

No business plan, pitch deck, market sizing, or IP filing language exists for
ErgoFluids yet, and none should be added here until a gate has passed against
real (not synthetic) data, per `docs/BUILD_PLAN.md`.

As of 2026-07-22, Phase 1's synthetic Gate 1 passed, but Gate 0 (interval
calibration) failed and Phase 1 used synthetic data only (see
`docs/gate-result-phase1-synthetic.md`). That is not a result to build IP or
funding material on.

Specifically not carried over from `/root/research/BMF Unified Framework.docx`:
the Alice/Mayo patent-eligibility argument, the tiered royalty model, and the
unsourced "$10 billion" synthetic royalty market figure. See `cv-claims-to-avoid`
in project memory for why unsourced patent and revenue claims are treated as a
real risk here, not boilerplate.

Update, 2026-08-04: a new module (`repo/src/ergofluids/network_sim/`, see
`docs/gate-result-network-sim-residual-model.md`) shows a promising first
validation (a residual model beating a physics baseline by 62% MAE, a regime
classifier beating a majority-class guess) against self-generated simulation
data. The same rule applies: this is simulation-only, not real-data,
validation, so it does not open this file either, no matter how good the
simulated result looks.
