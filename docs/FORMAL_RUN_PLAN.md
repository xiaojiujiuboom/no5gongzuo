# Formal Run Plan

This is the reviewer-facing decision path for the no5 DD-neutron / Li TPR
project. It intentionally separates diagnostic runs from publication runs.

## 1. Lock the Physical Geometry

Baseline geometry:

```text
laser -> thin CD2 foil -> vacuum gap -> external thick CD2 converter -> Li tally
```

The PIC source is the deuteron phase space crossing the converter entrance
plane. It is not a late-time snapshot of all deuterons still inside the PIC box.
EPOCH `begin:probe` records particles crossing a plane. With repeated probe
output, each SDF probe dump is a time-window record because EPOCH clears the
sampled particle list after writing. The integrated source is made by
concatenating windows, or equivalently by running one deliberately long probe
window after the end time is known.

Nominal gap:

```text
thin foil rear surface: x_rear = +2.5 um
converter entrance: x_source = x_rear + 20 um
```

Only use `rear+10 um` if the physical model is changed to a closer converter.
Do not switch source plane merely because it reaches a plateau earlier.

## 2. Diagnostic PIC Gate

Purpose: find the end time and source plane before spending high-resolution
production compute.

Current diagnostic settings:

```text
code: EPOCH2D on BSCC
laser: lambda0 = 0.8 um, tau = 30 fs, w0 = 3 um
foil: 5 um CD2, target_y_half = 12 um
density: n_C = 20 nc, n_D = 40 nc, n_e = 160 nc
grid: dx = dy = 25 nm
PPC: electron/deuteron/carbon = 8/8/4
probes: rear+10, rear+20, rear+30, ...
filter: px > 0, E_D > 0.1 MeV
```

Acceptance:

```text
latest probe window contributes <= 5-10% of integrated rear+20 source weight
cumulative mean energy and p95/p99 energy change by <= 5-10%
cumulative theta RMS changes by <= 5-10%
macro-particle statistics are enough for the high-energy tail
downstream boundary is not influencing the accepted probe plane
```

Current status:

```text
1.0 ps: rear+20 has no valid source
2.0 ps: rear+20 is still dominated by newly arriving deuterons
2.5 ps: latest rear+20 window is still 46.8% of the integrated source
3.0 ps: latest rear+20 window is still 25.0% of the integrated source
3.5 ps: running with 64 cores and source-focused probes
```

## 3. Physics Scan

After the diagnostic gate passes, run the first controlled scan:

```text
a0 = {5, 10, 20}
L_pre = {0, 1 um}
foil thickness = 5 um
```

Add `3 um` thickness only if the 5 um result is clearly thickness-sensitive or
suboptimal. This keeps the first scan interpretable.

## 4. Publication PIC Runs

The diagnostic deck is not the final publication deck. For paper-quality source
normalization, rerun accepted cases with stricter numerical settings:

```text
target grid: dx = dy = 20 nm
target PPC: electron/deuteron/carbon = 32/32/16, if memory allows
fallback PPC: 24/24/12 with an explicit convergence note
source: particle probe crossing at the accepted converter entrance
```

Convergence checks:

```text
PPC: compare 16/16/8 vs 32/32/16 on representative cases
grid: compare 25 nm vs 20 nm on representative cases
stress test: include at least one high-a0 / high-yield case
```

Accept the publication setting only if source metrics and downstream DD neutron
yield change by about 10% or less.

## 5. Stage B and Stage C

Stage B converts the deuteron probe source into a DD neutron source using
stopping in CD2 and D-D cross sections. Before final use, validate the
thick-target `Y(E0)` scale against literature/SRIM/PSTAR-style expectations.

Stage C transports the neutron source into Li with OpenMC. Development can run
locally on the M4 Pro; final histories should be driven by tally uncertainty:

```text
integrated TPR relative error < 5%
spatial/energy-bin relative error < 10%, or merge bins / increase histories
```
