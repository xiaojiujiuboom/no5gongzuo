# Physics Gates G1/G2, 2026-07-06

This note records the first hard-physics closure pass for Stage B.

## Scope

Current paper scope remains:

```text
PIC deuteron source
-> external thick CD2 converter D(d,n)3He neutron source
-> OpenMC Li6/Li7 tritium production per source neutron
```

Direct `D(d,p)T` converter tritium and TiD2 are not part of the current fast
paper scope.

## G1: D(d,n)3He Cross Section

Status: **passed for the current Stage B D(d,n) branch**.

Artifact:

```text
hpc/results/physics_gates_20260706/ddn_cross_section_check.csv
```

What was checked:

- Stage B actual function:
  `moduleB_source.cross_section.sigma_ddn_bosch_hale_mb`.
- Reference:
  an independent Bosch-Hale analytic implementation using the published
  D(d,n)3He coefficients, Bosch and Hale, Nucl. Fusion 32 (1992),
  doi: `10.1088/0029-5515/32/4/I07`.
- Formula noted in the CSV:
  `sigma_mb = S(E)/(E exp(BG/sqrt(E)))`, with `S(E)` represented by the
  Bosch-Hale polynomial in `E_cm` keV.
- Check points:
  `E_cm = 25, 100, 250, 500, 1000, 2500, 4500 keV`.
- Acceptance:
  `sigma_used / sigma_ref` inside `0.85-1.15`.

Result:

```text
min ratio = 1.000
max ratio = 1.000
```

The values are exactly identical because both implementations evaluate the same
Bosch-Hale formula independently. This closes the "did the code implement the
intended analytic cross section?" gate. If a reviewer asks for a nuclear-data
library comparison, the next optional strengthening step is to sample an ENDF
charged-particle evaluation at the same `E_cm` points and add it as an
additional column, but that is not required for the current Bosch-Hale/NRL-style
gate.

Domain guardrail:

```text
hpc/results/physics_gates_20260706/ddn_cross_section_domain_summary.csv
```

Only `pic2d_a0_20_t_3um` has deuterons above the Bosch-Hale nonzero domain
(`E_cm > 4900 keV`, equivalent `E_D > 9.8 MeV`). The weight fraction is
`4.85e-4`, so the upper-domain cutoff is not a present blocker for the 7-point
2D matrix.

## G2: D-in-CD2 Stopping

Status: **placeholder removed; exact SRIM export still pending**.

Default Stage B table replaced:

```text
data/stopping_D_in_CD2.csv
```

Backup of the previous placeholder:

```text
data/stopping_D_in_CD2_placeholder_20260706.csv
```

New source:

- NIST PSTAR proton stopping in polyethylene, material 221.
- PSTAR documentation URL:
  `https://physics.nist.gov/PhysRefData/Star/Text/PSTAR.html`.
- Same-velocity deuteron proxy in the nonrelativistic MeV range:
  `E_p = E_D / 2`.
- Linear stopping scaled by `rho_CD2 = 1.06 g/cm3`.

Important limitation:

This is an entity table from a documented source, but it is **not** a SRIM
D-in-CD2 export. It is acceptable as a transparent replacement for the old
ad-hoc placeholder and as a reproducible gate artifact. A strict SRIM gate
requires running SRIM for D in CD2 and replacing or comparing against the table.

Stopping change:

```text
hpc/results/physics_gates_20260706/stopping_placeholder_vs_pstar.csv
```

The new table differs strongly from the old placeholder. Over the anchor
energies, `S_pstar / S_placeholder` ranges from `0.20` at the very lowest
energies to about `6.73` near several MeV. In the energies that dominate the
current Stage B sources, the old placeholder was too low, so it overestimated
the thick-target neutron yield.

Stage B spectrum/yield impact:

```text
hpc/results/physics_gates_20260706/stopping_spectrum_comparison.csv
hpc/results/physics_gates_20260706/stopping_spectrum_histograms.csv
hpc/results/physics_gates_20260706/stopping_spectrum_anchor_overlay.png
```

For the completed 7-point 2D source matrix:

```text
Y_pstar / Y_placeholder = 0.195 - 0.237
mean neutron energy shift = -0.103 to -0.019 MeV
Li7-threshold neutron fraction shift = -0.0478 to -0.0208 absolute
normalized spectrum total variation = 0.026 - 0.091
```

Interpretation:

- Absolute thick-target neutron yields from the old full-chain table are too
  high by about `4.2x-5.1x`.
- Normalized neutron spectral shape moves only modestly for most scan points,
  but the Li7-threshold fraction decreases by a few absolute percentage points.
- Any final `T/shot` table must be regenerated with the new stopping table.
- Per-source-neutron OpenMC response ratios remain the more robust current
  paper quantity, but source-spectrum changes still need to be propagated before
  final figures.

## Reproducibility

Run:

```bash
python3 scripts/run_physics_gates.py
```

The script regenerates the G1 CSV, replaces the default stopping table from the
documented NIST query, backs up the old placeholder if needed, and produces the
old-vs-new Stage B spectrum comparison.
