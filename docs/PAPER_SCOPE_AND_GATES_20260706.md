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
- Do not present the current CD2 stopping table or D-D cross sections as fully
  validated final physics input.

## Hard Gates Before Absolute-Yield Claims

### GATE-sigma

Before absolute neutron yield or direct-tritium yield is publishable:

```text
Check D(d,n)3He and D(d,p)T absolute cross sections
against ENDF/NRL or an equivalent documented source
at least two energies in the used E_cm range.
```

This gate controls the thick-target yield normalization and reaction-energy
sampling.

### GATE-stopping

Before absolute yield is publishable:

```text
Replace the current D-in-CD2 stopping placeholder
with a documented SRIM/PSTAR/equivalent stopping table.
```

The stopping table directly controls the thick-target integral:

```text
Y(E0) = integral n_D sigma(E_cm) / S(E) dE
```

Thus it controls the neutron spectrum and absolute source normalization.

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
