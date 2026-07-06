# Stage 2 D-D Channels and Converter Material

This note records the current Stage 2 paper scope after the 2026-07-06 scope
reset.

## Current Paper Scope

The current fast-paper scope is deliberately narrowed to:

```text
laser on thin CD2 foil -> forward deuteron beam
-> external thick CD2 converter, D(d,n)He3 neutron branch only
-> neutron branch into Li target
-> compare Li TPR per source neutron for ideal vs PIC-derived neutron sources
```

Primary observable:

```text
TPR_Li6_per_source_neutron
TPR_Li7_per_source_neutron
TPR_Li_total_per_source_neutron
```

The robust claim is source-fidelity / spectral-angular distortion, not absolute
tritium per shot. Any `T/shot` numbers currently in result tables are diagnostic
normalizations and must be marked provisional until the cross-section and
stopping-power gates below pass.

## Adopted Channels

Physically, the external converter has two D-D branches:

```text
D + D -> n + He3     neutron branch for Stage C Li transport
D + D -> p + T       direct triton branch inside the converter
```

For the current paper, only the neutron branch is implemented and used. The
direct `D(d,p)T` branch is explicitly future work. If it is implemented later,
the accounting should be:

```text
T_direct_DD      from D(d,p)T in the converter
T_Li_neutron     from D(d,n)He3 neutrons transported into Li
T_total          optional sum, only after both components are normalized per shot
```

Do not fold the direct converter tritons into OpenMC Li tallies. OpenMC Stage C
only receives the neutron source from the `D(d,n)He3` branch.

## Converter Material

Current paper baseline:

```text
Stage 2 baseline for this paper: external thick CD2 converter
Future material extension: TiD2
Stage 3: neutron branch into Li target
```

Rationale:

- This matches the current Stage B implementation and the completed 2D
  full-chain results.
- It removes a mismatch between paper claims and actual calculations.
- It keeps the core question intact: how a non-ideal D-D neutron spectrum and
  angular distribution changes Li TPR per source neutron.
- TiD2 remains scientifically interesting, but it needs its own stopping table
  and deuteron density. It must not be emulated by simply renaming the CD2
  table.

## Hard Gates Before Absolute-Yield Claims

The following gates are blocking for final absolute neutron yield or `T/shot`
claims:

```text
GATE-sigma:
  Check D(d,n)He3 and D(d,p)T absolute cross sections against ENDF/NRL
  at least two energies over the used E_cm range.

GATE-stopping:
  Replace the current D-in-CD2 stopping placeholder with a documented
  SRIM/PSTAR/equivalent table.
```

If TiD2 is revived later, Stage B also needs:

```text
D-in-TiD2 stopping table from SRIM or an equivalent documented source
TiD2 density and stoichiometric deuteron density:
  n_D = 2 * rho_TiD2 * N_A / M_TiD2
verified D(d,n)He3 and D(d,p)T cross sections over the used E_cm range
separate exported products:
  neutron_source.h5
  triton_direct_source.h5 or an equivalent direct-T yield table
```

## Current Implementation Status

The current committed Stage B code still implements the neutron branch for a
CD2 converter only. Under the current narrowed scope, this is the paper
baseline for per-source-neutron Li TPR comparisons. It is not yet sufficient for
final absolute `T/shot` claims, TiD2 claims, or direct converter tritium claims.
