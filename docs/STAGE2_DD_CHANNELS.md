# Stage 2 D-D Channels and Converter Material

This note records the adopted Stage 2 policy after reviewing the tritium
handoff plan in `/Volumes/billboom/paperwork/tritium/EXECUTION_stage1_pic.md`.

## Adopted Channels

The external converter does not only create neutrons. D-D has two relevant
branches:

```text
D + D -> n + He3     neutron branch for Stage C Li transport
D + D -> p + T       direct triton branch inside the converter
```

Therefore the paper should report two tritium contributions separately:

```text
T_direct_DD      from D(d,p)T in the converter
T_Li_neutron     from D(d,n)He3 neutrons transported into Li
T_total          optional sum, only after both components are normalized per shot
```

Do not fold the direct converter tritons into OpenMC Li tallies. OpenMC Stage C
only receives the neutron source from the `D(d,n)He3` branch.

## Converter Material

The intended baseline converter material is upgraded from CD2 to TiD2:

```text
Stage 1: laser on thin CD2 foil -> forward deuteron beam
Stage 2 baseline: external thick TiD2 converter
Stage 2 sensitivity: external thick CD2 converter
Stage 3: neutron branch into Li target
```

Rationale:

- TiD2 is a practical solid deuteride catcher and avoids carbon-reaction
  backgrounds as the baseline interpretation.
- CD2 remains useful as a sensitivity/material-scan case because the current
  software path and provisional stopping table already support it.
- TiD2 will change both the stopping power and deuteron number density, so it
  must not be emulated by simply renaming the CD2 table.

Before final TiD2 results, Stage B needs:

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
CD2 converter only. It is valid for software bring-up and for a CD2 comparison
case, but not yet the final TiD2 baseline. The next Stage B implementation pass
should add a material abstraction and the direct triton branch before final
paper numbers are produced.
