# Design-partner outreach: drafts, none sent

Status: **all four drafts below are unsent**. Review before anything goes out. Contact emails were
verified against each person's own institutional page (not guessed), sources noted per contact.

## Candidates, and why each one specifically

Diversified across four people with four different, genuine connection points, not four copies of
the same generic pitch (memory `feedback-pitch-outreach-framing`: lead with the strongest verified
result specific to that recipient):

| Candidate | Institution | Verified email | Connection | Ask type |
|---|---|---|---|---|
| Brian Amsden | Queen's University | amsden@queensu.ca | Author of the obstruction-scaling model itself; his own former student's thesis data was just used to find a real 2.4x parameter drift | Design partner (pilot data) |
| Wei Wang | University of Bergen | wei.wang@uib.no | Author of the real PGSE NMR dataset already used for the adhesion-axis premise check (rho = +0.50) | Design partner (pilot data) |
| Elizabeth Nance | University of Washington | eanance@uw.edu | Lab does real multiple-particle-tracking + ML on nanoparticle-ECM transport (McKenna et al. 2021, ACS Nano), the closest real precedent for what this tool's real-data version would need | Design partner / pilot data or collaboration |
| Andrea Giuntoli | University of Groningen | a.giuntoli@rug.nl | Built a closely related tool (CG-MD + Gaussian process predicting confined-mobility descriptors for drug-carrier design, Soft Matter 2025) | Peer/research collaborator, not a data ask |

Note on Amsden: he is now Associate Vice-Principal Research at Queen's (a 5-year term started
November 2023, alongside his professorship), which may mean a slower response or that a lab member
(the lab's general-inquiries contact, fei.chen@queensu.ca) is a better first point of contact than
his own address. Both are included as options below.

---

## 1. Brian Amsden

**To:** amsden@queensu.ca
**Subject:** A real-data test of the obstruction-scaling model's probe-invariance, using your student's thesis data

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

## 2. Wei Wang

**To:** wei.wang@uib.no
**Subject:** Your PGSE NMR hydrogel data and a real test of obstruction-scaling theory

Dear Dr. Wang,

I'm a computational researcher building a tool that predicts macromolecule transport through
hydrogel/ECM-like networks, meant to help formulation scientists screen candidates before committing
to wet-lab diffusion assays.

Your recent paper on drug transport in the C18ADPA liquid-crystalline hydrogel gave me a genuinely
useful, independent check on a hypothesis I was building a tool around: that steric-only
obstruction-scaling theory breaks down once chemical affinity matters. Using your Table 1 and Table 2
values directly, I checked the Spearman correlation between hydrodynamic radius and relative
diffusivity (D_gel/D_free) across your five drugs: rho = +0.50, the wrong sign for a size-only
account, which requires a strongly negative relationship. Amphotericin B, the largest solute you
tested, had by far the highest relative diffusivity of the five, consistent with what you describe in
the paper as host-guest affinity dominating over size.

I built a small model that predicts this kind of deviation from descriptors size-only theory doesn't
use (an adhesion/affinity term, among others), validated so far on self-generated simulation data and
this kind of real-data check, not yet on a real lab's own measurements gathered specifically to test
it.

Would you be open to a conversation about whether a small set of pilot measurements, existing or new,
on drug-hydrogel combinations your lab is already interested in, could be a useful real test for the
tool? I'd be glad to share the full analysis either way.

Best regards,
Eniola Olutogun

---

## 3. Elizabeth Nance

**To:** eanance@uw.edu
**Subject:** A tool for predicting/screening nanoparticle-ECM transport, built on your lab's MPT+ML approach

Dear Prof. Nance,

I'm a computational researcher building a tool that predicts how a candidate macromolecule or
nanoparticle will move through a hydrogel or ECM-like network, aimed at helping formulation
scientists narrow candidates before committing to wet-lab diffusion assays.

Your 2021 paper combining multiple-particle-tracking with a boosted decision tree to predict
neurodevelopmental age from brain ECM diffusive behavior is, as far as I've found in the literature,
the clearest real-data precedent for the approach I'm taking: extracting structural/transport features
from real particle-tracking data and learning a model on top of them, rather than relying on a
closed-form physical model alone. My own tool so far combines a physics baseline (obstruction-scaling
theory, itself real-data validated in prior work but with two documented failure modes I've confirmed
independently: chemical affinity and probe-size-dependent chain flexibility) with a residual model and
an active-learning recommender for labs with limited pilot data. Everything is validated on
self-generated simulation data and real-data consistency checks so far, not yet on real transport
measurements gathered specifically to test the predictor itself.

I'd value your perspective, as someone doing this kind of measurement and modeling for real, on
whether the approach is aimed at a real gap, and whether a small set of your lab's existing or new
pilot data might be a useful test case. I'd be glad to share the full analysis and code regardless of
what you conclude.

Best regards,
Eniola Olutogun

---

## 4. Andrea Giuntoli

**To:** a.giuntoli@rug.nl
**Subject:** A physics-baseline-first take on predicting confined nanoparticle mobility

Dear Dr. Giuntoli,

I'm a computational researcher who recently built a tool for predicting macromolecule transport
through hydrogel/ECM-like networks, and your 2025 paper on machine learning of anomalous diffusion in
crosslinked networks (coarse-grained MD plus Gaussian process regression predicting the Debye-Waller
factor) is the closest related work I've found, both in goal and in using a Gaussian process for the
same kind of problem.

My own approach starts from the opposite end: rather than learning transport behavior directly from
simulation, I start from obstruction-scaling theory (real-data validated for simple cases) and learn a
residual on top of it targeting two specific, real-data-confirmed failure modes (chemical affinity,
probe-size-dependent chain flexibility), plus a Gaussian-process-based active-learning recommender for
labs with only a little real pilot data. Everything is validated on self-generated simulation data and
real-data consistency checks so far, not against real transport measurements collected to test the
predictor directly.

I'd be glad to compare notes, share code, or discuss whether the two approaches (yours, direct
CG-MD-to-GP; mine, physics-baseline-plus-residual) could usefully validate or extend each other, if
that's of interest.

Best regards,
Eniola Olutogun

---

## Open items before sending any of these

- All four emails are verified against each person's own institutional/lab page, not guessed, but
  double-check each is still current immediately before sending (faculty pages go stale).
- Decide send order/timing: sending all four at once versus staggering to react to early replies.
- Final read against memory `cv-claims-to-avoid` before sending: none of the four claims funding, an
  incubator acceptance, a patent, or a built platform; each states a specific finding and a specific,
  honest ask. Worth one more pass by the author before anything goes out.
