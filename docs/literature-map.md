# ErgoFluids: literature and tooling map

Sourced during initial scoping (this session). Every entry below is a real, checkable reference,
not a claim from the BMF document.

## Koopman operator / DMD tooling

- **PyDMD** (mathLab/SISSA, MIT license, pip-installable, actively maintained). Implements standard
  DMD plus variants relevant here: Higher-Order DMD (HODMD, useful for delay-embedding
  non-Markovian/memory effects), multiresolution DMD, compressed DMD, DMD with control,
  forward-backward DMD, optimized/total-least-squares DMD, and an online/streaming DMD module.
  Does not natively implement Extended DMD (EDMD) with arbitrary observable dictionaries.
- **PyKoopman** (Kutz/Brunton group, scikit-learn-style API). Supports flexible observable and
  dictionary construction for EDMD (polynomials, RBFs, custom, and neural-network/autoencoder
  observables), and can call PyDMD's regression backends.

**Install finding (this session)**: PyKoopman's latest release, 1.2.1, was uploaded January 2026,
so release cadence looks active. Its declared dependencies are hard-pinned, however:
`scikit-learn==1.1.3`, `numpy<=1.26`, `torch~=2.1.0`, plus `torchvision`, `torchaudio`, and
`lightning`, none of which have been relaxed for this release. `scikit-learn==1.1.3` has no wheel
for Python 3.12, so pip falls back to a source build that fails on this box (old `pkg_resources`
code incompatible with Python 3.12's removed `pkgutil.ImpImporter`). Installing PyKoopman as
specified would require pinning this whole project to an older Python and pulling in the full torch
stack for functionality (EDMD dictionaries) that Gate 0/1 do not need.

Phase 1 uses PyDMD's HODMD directly: a scalar subdiffusion-exponent recovery from delay-embedded
time series does not require EDMD's arbitrary observable dictionaries. PyKoopman is deferred to
Phase 2, to be revisited only if dictionary-based EDMD becomes necessary, and installed in its own
isolated environment if so.

## Mori-Zwanzig

No maintained Python package exists for Mori-Zwanzig Mode Decomposition (MZMD). The academic
lineage is Panos Stinis (PNNL) and collaborators, including "The Mori-Zwanzig formulation of deep
learning" (arXiv:2209.05544) and related closure/renormalization work; code from this group is
scattered across individual paper repositories rather than one maintained package.

The most directly usable reference is `lanl/MoriZwanzigModalDecomposition.jl` (Los Alamos National
Laboratory, Julia), implementing MZMD as described in arXiv:2311.09524. `n_ks=1` reduces the method
to plain DMD; `n_ks >= 2` adds Mori-Zwanzig memory terms, at roughly 1% extra compute cost per 10
memory terms. It was validated on fluid direct numerical simulation (cylinder flow, boundary-layer
transition), not on biological or tissue transport data. A follow-on paper (arXiv:2507.16058)
applies data-driven Mori-Zwanzig methods to Lagrangian particle dynamics in turbulence; also fluid
dynamics, not tissue.

No existing tool applies MZMD to macromolecular tissue transport. Building that here means porting
the algorithm from the Julia reference to Python: a bounded linear-algebra procedure (delay
embedding, a Markovian DMD term, memory-kernel terms fit from residuals), not a library install.

## Public validation data

- **arXiv:1909.05091**, "Particle diffusion in extracellular hydrogels." Supplementary data on
  hyaluronan-collagen composite matrix microrheology, subdiffusion exponents, and viscoelastic
  moduli. The closest direct match to ErgoFluids' target system (hyaluronic acid / collagen tumor
  stroma) and the primary calibration target for Gate 1.
- **Ramanujan et al., *Biophysical Journal*** (diffusion anisotropy in collagen gels and tumors,
  from the Jain-lab era of tumor transport research). Secondary calibration option, same domain.
- **ACS Nano meta-analysis of 376 nanomedicine PBPK datasets** (whole-tumor accumulation kinetics
  across many studies). Useful for macro-scale, later-stage validation, not for the first
  micro-scale DMD/EDMD fit.

**Genuinely scarce**: no public dataset of raw intravital-microscopy single-particle tracks through
tumor stroma exists on Zenodo, Figshare, or comparable repositories as of this search. Obtaining one
would likely require either wet-lab access or manually digitizing figures from published papers
(for example with WebPlotDigitizer). This is a real limitation on how far validation can go without
new data, and it is stated here rather than worked around silently.

## Prior art to position against

- **Baxter-Jain transport equations**, the founding framework for tumor vascular permeability,
  interstitial fluid pressure, and interstitial fluid velocity in this field.
- **PBPK-with-diffusion models**, the current dominant paradigm for quantifying the enhanced
  permeability and retention (EPR) effect in nanomedicine.
- **PhysiCell**, an open-source, actively used agent-based simulator for spheroid and
  nanoparticle-penetration studies.

ErgoFluids should be positioned as a data-driven, reduced-order alternative to these established
continuum and agent-based approaches, not as a replacement for the underlying physics they encode.

## Sources

- PyDMD: https://pydmd.github.io/PyDMD/ , https://github.com/PyDMD/PyDMD
- PyKoopman: https://arxiv.org/pdf/2306.12962
- Mori-Zwanzig Mode Decomposition: https://arxiv.org/abs/2311.09524 ,
  https://github.com/lanl/MoriZwanzigModalDecomposition.jl
- Mori-Zwanzig particle dynamics in turbulence: https://arxiv.org/pdf/2507.16058
- Mori-Zwanzig formulation of deep learning: https://arxiv.org/pdf/2209.05544
- Particle diffusion in extracellular hydrogels: https://arxiv.org/pdf/1909.05091
- Diffusion anisotropy in collagen gels and tumors:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2980743/
- PBPK meta-analysis of nanoparticle tumor delivery:
  https://pubs.acs.org/doi/full/10.1021/acsnano.9b08142
- PhysiCell: https://www.biorxiv.org/content/10.1101/035733.full.pdf
