# PIC Source Extraction Criteria

The PIC source for Stage B is defined as the deuteron phase space crossing an
external converter entrance plane, not as all deuterons remaining inside the PIC
box at a chosen snapshot. EPOCH particle-probe dumps are treated as time-window
records; the source is built by concatenating all accepted probe windows.

## Nominal Interface

```text
thin CD2 rear surface: x_rear = +2.5 um for a 5 um foil centered at x=0
converter entrance:   x_sample = x_rear + 20 um = 22.5 um
```

## Objective Acceptance Criteria

Before using a PIC case for paper figures, verify all of the following:

1. Time completeness: the latest probe time window contributes less than about
   5-10% of the integrated source weight at the chosen plane.
2. Cumulative stability: cumulative source metrics after appending the latest
   window differ by less than 5-10% from the previous cumulative source. The
   comparison window is set by the diagnostic, not by a fixed assumed end time.
3. Plane stability: metrics at `rear+20 um` and `rear+30 um` differ by less
   than 5-10% after accounting for particles that have not yet arrived.
4. Box-size safety: `x_max` is at least 10-15 um downstream of the farthest
   diagnostic plane, so high-energy deuterons cross the plane before they are
   lost at the open boundary.
5. Resolution/PPC convergence: repeat at a finer grid and/or higher PPC until
   the deuteron spectrum, angular distribution, and high-energy tail are stable
   within the target tolerance.

Metrics:

```text
forward deuteron total weight
weighted mean energy
weighted p95/p99 energy
maximum energy with enough particle statistics
angular mean and RMS
time-window contribution to the integrated source
integrated energy spectrum dN/dE
integrated angle distribution dN/dtheta
```

## Diagnostic Strategy

Use EPOCH particle probes whenever possible:

```text
probe planes: rear+10, rear+20, rear+30, rear+40 um, extended if needed
species: deuteron
filter in postprocessing: px > 0, E_D > 0.1 MeV
```

Snapshot filtering (`x > x_sample`) is only a fallback or cross-check, because
fast particles can leave the box before the final snapshot.

Use `Data/*.sdf` rather than `Data/000*.sdf` when postprocessing long runs, so
files such as `0010.sdf` are included.
