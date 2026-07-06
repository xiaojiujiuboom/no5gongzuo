# Important HPC Runs

Last updated: 2026-07-05 Europe/Vienna / 2026-07-06 CST.

SSH:

```bash
ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes -p 22 -l 'm9s003861@BSCC-M9' ssh.cn-hongkong-1.paracloud.com
```

Remote project root:

```text
/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr
```

Local project root:

```text
/Volumes/billboom/paperwork/no5
```

## Accepted 3D Anchor

Physics point:

- `a0 = 10`
- CD2 target thickness `3 um`
- 3D box `x=-6..26 um`, `y,z=-10..10 um`
- grid `2000 x 250 x 250`
- PPC `electron/deuteron/carbon = 16/32/4`
- source plane used for Stage 2: `rear+10`
- accepted collection time: `6 ps`

Decision:

- The accepted 3D Stage 1 source is the cumulative `0-6 ps` `rear+10`
  deuteron probe source.
- The stopping criterion is D-D-yield weighted, not raw deuteron count.
- At `E_D >= 0.4 MeV`, the final `5.75-6.00 ps` window contributes `5.57%`
  of the cumulative `0-6 ps` D-D-yield-weighted source, below the `10%`
  criterion.
- The normalized `0-5 ps` vs `0-6 ps` D-D-yield-weighted spectrum is stable:
  total-variation distance `0.0128`, cosine similarity `0.99967`.

Key 3D job chain:

| job | run | state | purpose |
|---:|---|---|---|
| `1523494` | `pic3d_stage1_smoke50fs_2000x250x250_a0_10_t_3um_20260703_r001` | completed | 50 fs parser/resource smoke test |
| `1559752` | `pic3d_stage1_benchmark1500fs_2000x250x250_a0_10_t_3um_20260704_r001` | completed | 1.5 ps first 3D benchmark; showed source not yet collected |
| `1631093` | `pic3d_stage1_source_diag3000fs_finalrestart_2000x250x250_a0_10_t_3um_20260704_r001` | cancelled after checkpoint | produced restartable `0006.sdf` near `1.63 ps` |
| `1676859` | `pic3d_stage1_source_diag3000fs_restart0006file_2000x250x250_a0_10_t_3um_20260704_r003` | completed | continuation to `3 ps`; final restart `0012.sdf` |
| `1721080` | `pic3d_stage1_source_diag4000fs_restart0012file_2000x250x250_a0_10_t_3um_20260705_r004` | completed | continuation to `5 ps`; final restart `0020.sdf` |
| `1837542` | `pic3d_stage1_source_diag6000fs_restart0020file_2000x250x250_a0_10_t_3um_20260706_r005` | failed | symlink restart MPI-IO failure; not a physics run |
| `1837996` | `pic3d_stage1_source_diag6000fs_restart0020hardlink_2000x250x250_a0_10_t_3um_20260706_r006` | completed | accepted 5-6 ps continuation; proves 6 ps convergence |

Primary 3D result files:

- `hpc/results/pic3d_stage1_rear10_6ps_dd_yield_convergence_summary.csv`
- `hpc/results/pic3d_stage1_rear10_6ps_dd_yield_windows.csv`
- `hpc/results/pic3d_stage1_rear10_5ps_vs_6ps_spectrum_summary.csv`
- `hpc/results/pic3d_stage1_rear10_5ps_vs_6ps_normalized_spectrum.png`

## Current 2D Matrix

Purpose:

- Use 2D as the lower-cost parameter scan.
- Use the accepted 3D source above as the dimensionality anchor.
- Treat 2D mainly as trend/optimization evidence; do not claim raw 2D absolute
  yield as the final physical yield without 3D anchoring.

Current low-cost 2D settings:

- box `x=-6..26 um`, `y=-10..10 um`, matching the accepted 3D anchor footprint
- grid `2000 x 500`, `dx=16 nm`, `dy=40 nm`
- PPC `electron/deuteron/carbon = 16/32/4`, matching the accepted 3D anchor PPC
- probes `rear+2/5/10/15/20`
- primary source plane `rear+10`
- `t_end = 6 ps`
- `dt_snapshot = 250 fs`
- Slurm `amd_m9_768`, `1` node, `64` ranks, walltime `18 h`
- final output is restartable: `force_final_to_be_restartable = T`
- `stop_at_walltime = 61200 s`
- the 18 h walltime is an upper bound; normal completion should stop billing
  before that. Hard cap for all seven jobs at full walltime is about `806 CNY`
  at `0.1 CNY/core-hour`; expected cost is lower.

Current 7 active/effective 2D scan points after cost-control reset:

| job | run | a0 | thickness um | state at latest check | node |
|---:|---|---:|---:|---|---|
| `1937305` | `pic2d_stage1_scan6ps_16x40nm_a0_05_t_3um_20260706_r001` | 5 | 3 | COMPLETED, elapsed `02:44:09` | `wqd10nbc06c05` |
| `1937306` | `pic2d_stage1_scan6ps_16x40nm_a0_10_t_1um_20260706_r001` | 10 | 1 | COMPLETED, elapsed `00:20:55` | `wqd10nbc06c12` |
| `1937307` | `pic2d_stage1_scan6ps_16x40nm_a0_10_t_2um_20260706_r001` | 10 | 2 | COMPLETED, elapsed `02:23:43` | `wqd10nbc06c13` |
| `1937308` | `pic2d_stage1_scan6ps_16x40nm_a0_10_t_3um_20260706_r001` | 10 | 3 | COMPLETED, elapsed `02:21:14` | `wqd10nbc07c11` |
| `1937309` | `pic2d_stage1_scan6ps_16x40nm_a0_15_t_3um_20260706_r001` | 15 | 3 | COMPLETED, elapsed `02:10:46` | `wqd10nbc07c14` |
| `1937310` | `pic2d_stage1_scan6ps_16x40nm_a0_20_t_3um_20260706_r001` | 20 | 3 | COMPLETED, elapsed `02:03:53` | `wqd10nbc07c15` |
| `1937311` | `pic2d_stage1_scan6ps_16x40nm_a0_10_t_4um_20260706_r001` | 10 | 4 | COMPLETED, elapsed `02:18:41` | `wqd10nbc07c15` |

Final SDF self-check:

- all seven final files are `Data/0023.sdf`;
- all seven final SDF headers report `time = 6.000040 ps`;
- all seven final SDF headers report `restart_flag = True`;
- total measured compute for this 7-point matrix is `920.91 core-hours`,
  about `92.09 CNY` at `0.1 CNY/core-hour`.

The previous `dx=dy=10 nm` large-box matrix was stopped because the slow points
were more expensive than the 3D anchor. Two completed 10 nm points are kept as
resolution checks:

| job | run | a0 | thickness um | status |
|---:|---|---:|---:|---|
| `1873138` | `pic2d_stage1_formal6ps_10nm_a0_10_t_1um_20260706_r002` | 10 | 1 | completed to `6 ps` |
| `1873136` | `pic2d_stage1_formal6ps_10nm_a0_10_t_2um_20260706_r002` | 10 | 2 | completed to `6 ps` |

The other slow 10 nm runs were cancelled after restart dumps were verified:

| job | point | restartable physical time |
|---:|---|---:|
| `1874262` | `a0=5,t=3um` | `2.352 ps` |
| `1869667` | `a0=10,t=3um` | `2.583 ps` |
| `1873137` | `a0=15,t=3um` | `2.372 ps` |
| `1869669` | `a0=20,t=3um` | `2.353 ps` |
| `1869670` | `a0=10,t=4um` | `2.409 ps` |

Pre-restart walltime-risk status at about elapsed `01:47:54`:

| job | point | latest physical time | latest ETA | action |
|---:|---|---:|---:|---|
| `1855864` | `a0=5,t=3um` | `1.17 ps` | `7h19m` | continue; still inside 10 h walltime but slower than early ETA |
| `1855865` | `a0=10,t=3um` | `0.94 ps` | `8h49m` | restart `Data/0003.sdf` confirmed |
| `1855866` | `a0=15,t=3um` | `0.85 ps` | `10h16m` | restart `Data/0003.sdf` confirmed |
| `1855867` | `a0=20,t=3um` | `0.76 ps` | `11h21m` | restart `Data/0003.sdf` confirmed |
| `1855868` | `a0=10,t=1um` | `3.81 ps` | `1h02m` | continue |
| `1855869` | `a0=10,t=2um` | `2.20 ps` | `3h03m` | continue |
| `1855870` | `a0=10,t=4um` | `0.99 ps` | `9h05m` | restart `Data/0003.sdf` confirmed |

The `Data/DUMP` requests were placed in the four high-risk run directories on
2026-07-06 CST because Slurm denied live walltime extension:

```text
Access/permission denied for job 1855865
Access/permission denied for job 1855866
Access/permission denied for job 1855867
Access/permission denied for job 1855870
```

The requests were processed successfully. Each high-risk run now has
`Data/restart.visit` pointing to `0003.sdf`:

| job | restart dump | size |
|---:|---|---:|
| `1855865` | `Data/0003.sdf` | `1.9G` |
| `1855866` | `Data/0003.sdf` | `1.9G` |
| `1855867` | `Data/0003.sdf` | `1.9G` |
| `1855870` | `Data/0003.sdf` | `2.2G` |

After the user requested not to risk walltime loss, a second DUMP was requested
and verified. `Data/restart.visit` lists `0004.sdf` for all four high-risk
original runs. Those original jobs were then cancelled after about `01:55:01`,
and 18 h continuation jobs were submitted from hard-linked `Data/0004.sdf`
files:

| old job | new job | restart run | restart file |
|---:|---:|---|---|
| `1855865` | `1869667` | `pic2d_stage1_formal6ps_10nm_a0_10_t_3um_restart0004_20260706_r002` | `Data/0004.sdf` |
| `1855866` | `1869668` | `pic2d_stage1_formal6ps_10nm_a0_15_t_3um_restart0004_20260706_r002` | `Data/0004.sdf` |
| `1855867` | `1869669` | `pic2d_stage1_formal6ps_10nm_a0_20_t_3um_restart0004_20260706_r002` | `Data/0004.sdf` |
| `1855870` | `1869670` | `pic2d_stage1_formal6ps_10nm_a0_10_t_4um_restart0004_20260706_r002` | `Data/0004.sdf` |

The continuation decks use:

```text
restart_snapshot = 0004.sdf
stop_at_walltime = 61200.0
Slurm walltime = 18:00:00
```

The r002 jobs were verified to start from the checkpoint: each printed
`Load from restart dump OK`. EPOCH also prints warnings such as
`Particle species "D_rear10" from restart dump not found in input deck.
Ignoring.` These refer to particle-probe records stored in the restart SDF, not
to the physical deuteron species. For analysis, do not use the r002 directory
alone. Merge the original r001 probe/output files up to `0004.sdf` with the r002
continuation outputs after the restart.

Remote run directory pattern:

```text
/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/runs/<run_id>
```

## Remote Files Not To Delete

Remote project root:

```text
/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr
```

Critical completed 3D anchor:

```text
runs/pic3d_stage1_source_diag6000fs_restart0020hardlink_2000x250x250_a0_10_t_3um_20260706_r006
```

Keep its `Data/0024.sdf`, `Data/restart.visit`, probe SDF files, `input.deck`,
and `submit.slurm`; this is the accepted 6 ps 3D reference.

Critical active 2D runs:

```text
runs/pic2d_stage1_scan6ps_16x40nm_a0_05_t_3um_20260706_r001
runs/pic2d_stage1_scan6ps_16x40nm_a0_10_t_1um_20260706_r001
runs/pic2d_stage1_scan6ps_16x40nm_a0_10_t_2um_20260706_r001
runs/pic2d_stage1_scan6ps_16x40nm_a0_10_t_3um_20260706_r001
runs/pic2d_stage1_scan6ps_16x40nm_a0_15_t_3um_20260706_r001
runs/pic2d_stage1_scan6ps_16x40nm_a0_20_t_3um_20260706_r001
runs/pic2d_stage1_scan6ps_16x40nm_a0_10_t_4um_20260706_r001
```

Keep the completed 10 nm resolution-check runs:

```text
runs/pic2d_stage1_formal6ps_10nm_a0_10_t_1um_20260706_r002
runs/pic2d_stage1_formal6ps_10nm_a0_10_t_2um_20260706_r002
```

The other paused 10 nm run directories may still contain useful partial
restart/probe data. Do not delete them casually; if space pressure returns,
delete only after confirming no current analysis references them.

Disk snapshot on 2026-07-06 CST:

```text
/publicfs10 filesystem: 5.8P total, 1.8P used, 4.1P available, 31% used
project directory: /publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr = 38G
```

The quota commands available to the user account did not report a smaller
explicit quota. Treat `/publicfs10` free space and project `du` as the current
operational check, and recheck before launching additional 3D runs.

Later on 2026-07-06 CST, hidden quota limits did trigger MPI-IO
`Disk quota exceeded` failures. Cleanup log:

```text
/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/CLEANUP_20260706_QUOTA.txt
```

Removed obsolete intermediate restart SDF files from old 3D chain runs and old
early 2D diagnostic SDF files. Kept accepted 3D `r006`, current formal 2D runs,
and restart files needed by hard-linked continuations. Project usage dropped to
about `47G`, then to about `26G` after removing the accepted 3D run's obsolete
input restart `Data/0020.sdf`, superseded `0003.sdf` restart dumps, and the bad
partial `a0=5` runtime DUMP output.

Quota-failed jobs and replacements:

| failed job | point | failure | replacement |
|---:|---|---|---:|
| `1855864` | `a0=5,t=3um` | stuck after quota failure while writing runtime DUMP; no valid `restart.visit` | `1874262` full rerun |
| `1855868` | `a0=10,t=1um` | quota failure near `4.97 ps`, no valid restart | `1873138` full rerun |
| `1855869` | `a0=10,t=2um` | quota failure near `2.73 ps`, no valid restart | `1873136` full rerun |
| `1869668` | `a0=15,t=3um` | quota failure after restart | `1873137` restart from `0004.sdf` |

Monitoring command for the current effective 7 scan points:

```bash
squeue -j 1874262,1873138,1873136,1869667,1873137,1869669,1869670 \
  -o "%.18i %.9P %.22j %.10T %.12M %.12l %.6D %.5C %R"
```

Immediate postprocessing after completion:

1. Check Slurm completion, exit codes, MaxRSS, runtime, and Data size.
2. Run probe metrics for all `Data/*.sdf`, with both all-energy and
   `E_D >= 0.4 MeV` gates.
3. Compute `rear+10` D-D-yield-weighted final-window convergence.
4. Compare normalized spectra, especially `0-5 ps` vs `0-6 ps` if needed.
5. Rank scan points by D-D-yield-weighted source quality, neutron source above
   the Li7 threshold-relevant energy region, angular concentration, and cost.
