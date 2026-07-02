# Formal Run Plan

This is the reviewer-facing decision path for the no5 DD-neutron / Li TPR
project. It intentionally separates diagnostic runs from publication runs.

## 0. Current Strategy Override

As of 2026-07-03, the project strategy is changed:

```text
3D PIC anchor first -> Stage B source generation -> Stage C OpenMC response
```

The previous 2D six-point PIC matrix is no longer the publication backbone.
Existing accepted `L_pre=0` 2D sources remain useful for software bring-up,
comparison, and parametric source bracketing. The timed-out `L_pre=1` 2D
outputs are not accepted sources.

Before any full 3D source run:

```text
run a 300 fs 3D microbenchmark
measure wall-clock per fs, memory, scratch, and restart behavior
verify rear+20 probe output and transverse boundary adequacy
choose walltime explicitly from the benchmark plus margin
```

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
3.5 ps: latest rear+20 window is 13.3%; close but still above the gate
4.0 ps: latest rear+20 window is 7.19%; accepted for first physics scan
```

## 3. 2D Physics Scan Status

The original first controlled 2D scan was:

```text
a0 = {5, 10, 20}
L_pre = {0, 1 um}
foil thickness = 5 um
source plane = rear+20 um
source integration time = 0-4.0 ps
```

Status:

```text
L_pre=0, a0={5,10,20}: accepted 5 ps rear+20 sources exist.
L_pre=1, a0={5,10,20}: 4 ps jobs timed out and are not accepted.
```

Do not automatically rerun the high-resolution `L_pre=1` matrix. If preplasma
is needed later, rerun only after the Stage B/C result shows why it matters,
and after a cheaper benchmark sets walltime and resolution.

## 4. 3D PIC Anchor Runs

Use `hpc/templates/epoch3d_dd_cd2_source_compact.deck` as the current starting
point. The first run is not a production source; it is a 300 fs benchmark.

```text
first 3D case: a0=10
purpose: source realism anchor, not a full parameter scan
source: rear+20 um deuteron probe
gate: yield-weighted source completeness, not raw deuteron weight alone
restart: required before long production submission
```

The reviewer-facing credibility argument is:

```text
3D gives a realistic source anchor.
Parametric source scans bracket source distortion and carry the robustness argument.
2D results are supporting comparisons, not final realism claims.
```

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
