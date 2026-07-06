# PIC Parameter Justification and Production Gate

This note records the defensible PIC setup for the DD-neutron source stage.
The goal is not to make the cheapest deck that runs, but to define a source
that can survive review questions about geometry, extraction time, resolution,
particle statistics, and normalization.

## Physical Model

- Interaction type: thin CD2 foil producing an accelerated deuteron beam.
- Downstream source definition: deuteron phase space crossing the entrance
  plane of an external CD2 converter for the current paper. TiD2 is a future
  material extension, not the current baseline claim.
- The source is not defined by all ions remaining inside the PIC box at one
  late snapshot, because the fastest particles can leave the box before the
  final dump.
- Particle-probe SDF files are interpreted as time-window records. The Stage B
  source is made by concatenating all accepted probe windows, then integrating
  the resulting phase space.

## Baseline Target and Laser

Use a real-density CD2 slab as the baseline:

```text
lambda0 = 0.8 um
tau = 30 fs
w0 = 3 um
target thickness = 5 um
target transverse half-width >= 12 um
n_C = 20 nc
n_D = 40 nc
n_e = 160 nc
```

At 0.8 um, `nc ~= 1.74e21 cm^-3`, so this corresponds to
`n_C ~= 3.5e22 cm^-3`, `n_D ~= 7.0e22 cm^-3`, and
`n_e ~= 2.8e23 cm^-3`, consistent with solid-density CD2 to the accuracy
needed for this stage.

The first physics scan should vary laser strength and preplasma scale length
before varying every possible target parameter:

```text
a0 = {5, 10, 20}
L_pre = {0, 1 um}
target thickness = 5 um
```

Only add `3 um` thickness after checking that the source metrics are sensitive
to thickness or that the 5 um baseline is clearly suboptimal.

Treat this as a two-tier workflow:

```text
diagnostic / source-timing tier: 25 nm, lower PPC, probe-only where possible
publication tier: rerun accepted cases at higher PPC and/or finer grid
```

The diagnostic tier chooses geometry, end time, and source plane. It is not the
final evidence for source normalization.

## Source Plane and End Time

Nominal converter entrance:

```text
x_rear = +2.5 um
x_sample = x_rear + 20 um = 22.5 um
```

Before production, use particle probes at:

```text
rear+10, rear+20, rear+30, rear+40 um
```

The chosen source plane is accepted only when:

- the latest probe window contributes less than about 5-10% of the integrated
  source weight;
- cumulative weighted mean energy and p95/p99 energy change by less than about
  5-10% after adding the latest window;
- cumulative angular RMS changes by less than about 5-10% after adding the
  latest window;
- the downstream boundary is at least 10-15 um beyond the farthest plane used;
- the high-energy tail has enough macro-particle statistics to quote.

If `rear+20 um` is still changing strongly at a diagnostic end time, extend
the probe run until the cumulative source metrics plateau. Do not force a
final snapshot source.

## Numerical Resolution

Diagnostic deck:

```text
dx = dy = 25 nm
PPC: electron/deuteron/carbon = 8/8/4
x = [-10, 60-90] um depending on probe distance
y = [-25, 30] um depending on probe distance
t_end = 4.0 ps for the accepted rear+20 um source extraction
```

This is enough to locate the source plane and time, but it is not the final
convergence claim.

Physics-scan baseline:

```text
dx = dy = 25 nm
PPC: electron/deuteron/carbon = 16/16/8
same or larger box as accepted by the diagnostic
particle probes enabled at accepted source plane and neighbors
```

Publication baseline after the scan:

```text
dx = dy = 20 nm
PPC: electron/deuteron/carbon = 32/32/16 if queue/memory allow
same accepted source plane and end-time criteria
```

Convergence checks:

```text
PPC convergence: repeat representative cases at 16/16/8 and 32/32/16
grid convergence: repeat representative cases at 25 nm and 20 nm
stress case: repeat at least one high-yield/high-a0 case with a stricter setup
```

Accept production settings only if the source metrics and thick-target DD
neutron yield change by less than the target tolerance, nominally 10% for the
first paper-quality pass.

## Handoff to Stage B and C

Stage B uses the probe-crossing deuteron phase space, documented stopping, and
D-D cross sections to build the `D(d,n)3He` neutron source for OpenMC. Current
paper scope is CD2 converter, per-source-neutron Li TPR. Thick-target yields
`Y(E0)` must be checked against ENDF/NRL cross sections and SRIM/PSTAR-style
stopping before any absolute `T/shot` result is treated as final. The
`D(d,p)T` direct triton branch and TiD2 material model are future extensions.

Stage C uses only the neutron source in OpenMC with Li tallies. Integrated TPR
needs relative error below 5%; spatial or energy-resolved bins should be below
about 10%, otherwise merge bins or increase histories.
