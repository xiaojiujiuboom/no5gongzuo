# HPC PIC Plan

## Current Priority

The active Stage 1 strategy is now:

1. Use the completed 3D anchor as the realism/dimensionality reference.
2. Use the formal 2D matrix as the lower-cost parameter scan.
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

Current formal 2D matrix:

- effective jobs: `1855864`, `1855868`, `1855869`, and restart continuations
  `1869667` through `1869670`
- original high-risk jobs `1855865`, `1855866`, `1855867`, and `1855870`
  were cancelled only after `Data/0004.sdf` restart dumps were verified
- `t_end = 6 ps`
- `1` node, `256` ranks
- original low-risk runs use `10 h` walltime; restart continuations use `18 h`
  walltime and `stop_at_walltime = 61200.0`
- `force_final_to_be_restartable = T`
- original low-risk runs keep `stop_at_walltime = 34200.0`
- source planes: `rear+5/10/15/20`, primary `rear+10`
- matrix:
  - fixed `thickness=3 um`, scan `a0={5,10,15,20}`
  - fixed `a0=10`, scan `thickness={1,2,3,4} um`

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
