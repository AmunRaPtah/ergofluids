# Design-partner outreach: draft, not sent

Status: **draft only**, not yet sent. Shown to the author for review before anything goes out.

## Why Amsden's lab specifically

Brian Amsden (Queen's University, Chemical Engineering) is the author of the obstruction-scaling
model `network_sim.baseline` uses, and the supervisor of the thesis
(`docs/gate-result-network-sim-hadjiev-thesis-check.md`) whose real FRAP data was just used to show
that model's steric-only parameter is not probe-invariant in a real system. This is a genuine,
specific connection, not a cold, generic pitch: the outreach can open with a concrete finding about
his own model, on his own former student's own data, rather than an unsolicited tool description.
This directly follows the project's standing framing rule (memory `feedback-pitch-outreach-framing`):
lead with the strongest verified result, not a request.

The ask is narrower than "share your raw data": a small number of real pilot measurements (existing
or new) on solutes/networks his lab already has reason to test, in exchange for early access to the
active-learning recommender and the residual-model predictor.

## Draft email

**To:** (Amsden's current Queen's University email, not yet verified)
**Subject:** A real-data test of the obstruction-scaling model's probe-invariance, using your student's thesis data

---

Dear Prof. Amsden,

I'm a computational researcher building a tool that predicts macromolecule transport through
hydrogel/ECM-like networks, aimed at helping formulation scientists screen candidates before
committing to wet-lab diffusion assays.

Your obstruction-scaling model is the real-data-validated core of the tool's baseline. While testing
it, I used Nicholas Hadjiev's 2014 thesis data (FITC-dextran diffusion in alginate-methacrylate
hydrogels, Figures 15 and 16) as a real-world check, since it reports hydrodynamic radii and fiber
geometry in a form I could parameterize directly. Fitting the model's proportionality constant
separately for each of the four probes, rather than assuming one value across all of them, showed it
decreases monotonically by about 2.4x from the smallest (FDX-4) to the largest (FDX-40) probe. Since
that constant represents a property of the network, not the probe, a probe-invariant steric model
should need the same value for all four. It doesn't, in the same direction (and, I'd guess, for the
same reptation-related reason) the thesis itself describes qualitatively for the largest probes.

I built a small model on top of the obstruction-scaling baseline that predicts this kind of deviation
from descriptors the baseline itself doesn't use (an adhesion/affinity term, particle shape), and an
active-learning tool that recommends which untested candidate to measure next given a handful of real
pilot points, so a lab doesn't need a large dataset to get value from it. Both are validated so far
only on self-generated simulation data and this kind of real-data consistency check, not on a real
lab's own measurements yet.

Would you or a member of your group be open to trying the tool against a small set of pilot data,
existing or new, in exchange for early access and whatever comes out of the comparison? I'd be glad
to share the underlying analysis (code and full writeup) regardless of how it goes.

Best regards,
Eniola Olutogun

---

## Open items before sending

- Verify Amsden's current email (not looked up yet; his Queen's faculty page or the thesis's own
  front matter should have it).
- Decide whether to also draft a parallel outreach to Wang (University of Bergen, the PGSE NMR
  drug-diffusion paper), a second, independently relevant contact for the adhesion axis specifically.
- This references real, already-published numbers (the 2.4x finding); worth a final read against
  memory `cv-claims-to-avoid` before sending, though nothing here should trip it: no claim of
  acceptance, funding, or a platform, just a specific finding and a specific ask.
