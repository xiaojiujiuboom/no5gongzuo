# Paper Scope and Hard Gates, 2026-07-06

This file is the current decision record for what the fast paper may claim.

## Current Scope

The paper is narrowed to:

```text
CD2 converter D(d,n) neutron branch
-> OpenMC Li6/Li7 tritium production
-> compare ideal vs PIC-derived neutron sources
-> report per-source-neutron TPR fidelity
```

Primary quantities:

```text
TPR_Li6_per_source_neutron
TPR_Li7_per_source_neutron
TPR_Li_total_per_source_neutron
Case B / Case A ratios
```

This keeps the core physics question intact: how the PIC-derived D-D neutron
spectrum and angular distortion change Li-target tritium production, especially
the `Li7` threshold contribution.

## Claims Allowed Now

- The completed 2D matrix gives trend evidence for source distortion effects.
- OpenMC per-source-neutron TPR/n is the robust downstream neutronics quantity.
- Natural lithium is more sensitive to the high-energy tail through the `Li7`
  threshold channel; high Li6 enrichment increases total TPR but suppresses the
  relative diagnostic role of `Li7`.
- `a0=20,t=3um` is the current preferred 3D validation candidate.

## Claims Not Allowed Yet

- Do not claim final absolute `T/shot` or absolute neutron yield.
- Do not claim TiD2 converter results.
- Do not claim direct converter tritium from `D(d,p)T`.
- Do not present SRIM-level stopping closure until an actual SRIM D-in-CD2
  output table is supplied and compared.

## Hard Gates Before Absolute-Yield Claims

### GATE-sigma

Status for current paper branch:

```text
D(d,n)3He: passed against independent Bosch-Hale implementation.
Artifact: hpc/results/physics_gates_20260706/ddn_cross_section_check.csv
```

Before any future direct-tritium yield is publishable:

```text
Add D(d,p)T absolute cross-section checks against ENDF/NRL or an equivalent
documented source in the used E_cm range.
```

This gate controls the thick-target yield normalization and reaction-energy
sampling.

### GATE-stopping

Status:

```text
The old D-in-CD2 placeholder has been replaced by a documented NIST PSTAR
same-velocity table:
data/stopping_D_in_CD2.csv
```

The stopping table directly controls the thick-target integral:

```text
Y(E0) = integral n_D sigma(E_cm) / S(E) dE
```

Thus it controls the neutron spectrum and absolute source normalization.

Current limitation:

```text
This is not yet a SRIM D-in-CD2 export. Exact SRIM closure remains pending.
Old-vs-new impact is quantified in:
hpc/results/physics_gates_20260706/stopping_spectrum_comparison.csv
```

## Material Decision

Current paper baseline:

```text
CD2 converter
```

Future extension:

```text
TiD2 converter
```

TiD2 requires its own D-in-TiD2 stopping table and stoichiometric deuteron
density. It must not be represented by relabeling the CD2 calculation.

## Direct Tritium Decision

Current paper:

```text
not included
```

Reason:

The main claim is the Li-target response per source neutron. Direct converter
tritium belongs to a total tritium accounting paper, and it can be added later
without blocking the per-source-neutron fidelity result.
