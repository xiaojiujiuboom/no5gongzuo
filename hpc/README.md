# HPC PIC Plan

## Current Priority

The active Stage 1 strategy is now:

1. Use the completed 3D anchor as the realism/dimensionality reference.
2. Use a 3D-matched, lower-cost 2D matrix as the parameter scan.
3. Feed the accepted `rear+10`, D-D-yield-weighted deuteron source into
   Stage B and Stage C after the 2D scan is postprocessed.

Accepted 3D anchor:

- `a0=10`, CD2 thickness `3 um`
- `2000 x 250 x 250`, PPC `electron/deuteron/carbon = 16/32/4`
- source plane: `rear+10`
- accepted collection time: `6 ps`
- accepted by D-D-yield-weighted final-window criterion:
  `5.75-6.00 ps / 0-6 ps = 5.57%` for `E_D >= 0.4 MeV`
- key job: `1837996`

Current low-cost 2D matrix:

- current effective jobs: `1937305`, `1937306`, `1937307`, `1937308`,
  `1937309`, `1937310`, and `1937311`, all completed normally
- `t_end = 6 ps`
- box `x=-6..26 um`, `y=-10..10 um`
- grid `2000 x 500`, `dx=16 nm`, `dy=40 nm`
- PPC `electron/deuteron/carbon = 16/32/4`, matching the 3D anchor PPC
- `1` node, `64` ranks
- Slurm walltime `18 h`, EPOCH `stop_at_walltime = 61200.0`
- `force_final_to_be_restartable = T`
- source planes: `rear+2/5/10/15/20`, primary `rear+10`
- matrix:
  - fixed `thickness=3 um`, scan `a0={5,10,15,20}`
  - fixed `a0=10`, scan `thickness={1,2,3,4} um`

The earlier `dx=dy=10 nm` large-box 2D matrix was stopped for cost control.
Completed `a0=10,t=1um` and `a0=10,t=2um` 10 nm runs are kept as resolution
checks. The other slow 10 nm runs were cancelled after restart dumps were
verified, so their partial data remain available but are not the main scan.

Measured cost for the new 7-point matrix:

- all seven jobs reached `6.00004 ps` with final restartable `Data/0023.sdf`;
- total charged compute estimate: `920.91 core-hours`;
- at `0.1 CNY/core-hour`, total cost is about `92.09 CNY`;
- the submitted `18 h` walltime was only a safety cap, not the billing duration.

See `hpc/IMPORTANT_RUNS.md` for the authoritative job/resource index.

## Walltime Protection

Running Slurm jobs cannot currently be extended by the user account:
`scontrol update JobId=<id> TimeLimit=...` returns `Access/permission denied`.

For long/risky jobs:

- submit with generous Slurm walltime up front;
- set EPOCH `stop_at_walltime` safely before Slurm walltime;
- set `force_final_to_be_restartable = T`;
- if a running job becomes risky, request an EPOCH restart dump with:

```bash
touch Data/DUMP
```

Current high-risk 2D jobs handled by restart continuation:

- `1855865` -> `1869667`: `a0=10`, `thickness=3 um`
- `1855866` -> `1869668`: `a0=15`, `thickness=3 um`
- `1855867` -> `1869669`: `a0=20`, `thickness=3 um`
- `1855870` -> `1869670`: `a0=10`, `thickness=4 um`

The continuation runs use hard-linked `Data/0004.sdf`, explicit
`restart_snapshot = 0004.sdf`, Slurm walltime `18:00:00`, and EPOCH
`stop_at_walltime = 61200.0`.

All four restart continuations printed `Load from restart dump OK`. For
postprocessing, merge each original r001 directory through `0004.sdf` with its
r002 continuation outputs; do not treat the r002 directory alone as the full
0-6 ps history.

Important remote files and directories that must be preserved are listed in
`hpc/IMPORTANT_RUNS.md`.

## Quota Recovery

On 2026-07-06 CST, several jobs failed with MPI-IO messages containing
`Disk quota exceeded`, even though `/publicfs10` had large global free space.
This means the account or project is subject to a smaller hidden quota.

Immediate recovery:

- removed obsolete intermediate 3D restart SDF files and old early 2D diagnostic
  SDF files;
- kept accepted 3D anchor `r006`, active formal 2D runs, input decks, Slurm
  logs, and restart files needed by hard-linked continuations;
- project usage dropped from about `94G` to about `26G` after a second cleanup;
- replacement jobs submitted:
  - `1855864` -> `1874262` full rerun, `a0=5,t=3um`
  - `1855868` -> `1873138` full rerun, `a0=10,t=1um`
  - `1855869` -> `1873136` full rerun, `a0=10,t=2um`
  - `1869668` -> `1873137` restart continuation, `a0=15,t=3um`

## Remote Layout

Remote project root:

```text
~/pic/no5_dd_li_tpr
```

Optional local SSH config template:

```bash
cat hpc/ssh_config.example >> ~/.ssh/config
```

The verified SSH user is `m9s003861@BSCC-M9`. The web login email is not the
SSH user.

Initialize it after logging into the supercomputer:

```bash
bash hpc/bootstrap_remote.sh ~/pic/no5_dd_li_tpr
```

Or from the local machine after SSH key login works:

```bash
ssh blsc-m9-no5 'bash -s' < hpc/bootstrap_remote.sh
```

Each run should export only compact diagnostics back to this repo:

```text
small CSV summaries
quicklook plots
deuteron_beam.h5 / neutron_source.h5 only when needed
```

Keep full SDF output on the supercomputer unless a specific file is needed for debugging.
