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

Current particle-source caveat:

- The accepted 3D timing/convergence summaries remain valid, and the final
  `Data/0024.sdf` remains present.
- During the 2026-07-06 quota recovery, the restart boundary SDF files
  `0006.sdf`, `0012.sdf`, and `0020.sdf` were removed from the old 3D chain.
  This was later recognized as too aggressive because `0020.sdf` contains the
  missing `4.75-5.00 ps` particle-probe window needed for a strictly complete
  particle-level `0-6 ps` 3D `deuteron_beam.h5`.
- Local particle-probe CSVs are already available for `0004-0019` and
  `0021-0024`; the only particle-level 3D `rear+10` gap is window `0020`.
- Until a 3D rerun is performed, use 3D as a convergence/dimensionality anchor
  and rely on the complete 2D matrix for the full Stage B/C parameter trends.

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

Primary 2D scan result files:

- `hpc/results/pic2d_scan16x40_20260706/pic2d_scan16x40_rear10_Egt0p4_trends.csv`
- `hpc/results/pic2d_scan16x40_20260706/pic2d_scan16x40_probe_dd_yield_summary.csv`
- `hpc/results/pic2d_scan16x40_20260706/pic2d_scan16x40_probe_dd_yield_windows.csv`
- `hpc/results/pic2d_scan16x40_20260706/pic2d_scan16x40_rear10_a0_scan.png`
- `hpc/results/pic2d_scan16x40_20260706/pic2d_scan16x40_rear10_thickness_scan.png`
- `hpc/results/pic2d_scan16x40_20260706/pic2d_scan16x40_vs_10nm_resolution_check.csv`

Current interpretation:

- The low-cost matrix is useful for trends and candidate selection.
- It is not yet a strict grid-convergence proof. The two completed old `10 nm`
  checks differ in box and PPC as well as grid, so use them only as a warning
  that thin-target cases are numerically sensitive.

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

Removed intermediate restart SDF files from old 3D chain runs and old early 2D
diagnostic SDF files. This reduced project usage to about `47G`, then to about
`26G`, but it also removed 3D restart/probe boundary files that are useful for
strict particle-level source reconstruction. In particular, removing
`Data/0020.sdf` was a mistake for final 3D source extraction; keep all remaining
3D and 2D SDF/probe products unless the user explicitly approves a specific
path.

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

## 2D Full Stage B/C Results

Date: 2026-07-06.

Scope:

- Seven complete `dx=16 nm, dy=40 nm` 2D sources.
- Source plane `rear+10`, collection `0-6 ps`, gate `E_D > 0.4 MeV`.
- Stage B current implementation: CD2 thick-converter `D(d,n)3He` neutron
  branch only.
- Stage C: OpenMC 0.15.0, ENDF/B-VII.1 local HDF5 data,
  `20 batches x 50,000 particles`, `8` OpenMP threads.
- Li cases: natural lithium (`Li6=7.59 at%`) and enriched lithium
  (`Li6=90 at%`).

Natural lithium summary:

| point | D-D n/shot | n mean MeV | frac n >3.1454 MeV | Li6 TPR/n | Li7 TPR/n | Li total T/shot | rel. total T |
|---|---:|---:|---:|---:|---:|---:|---:|
| `a0=10,t=1um` | `3.96e11` | `3.076` | `0.348` | `1.022e-2` | `8.693e-3` | `7.48e9` | `0.084` |
| `a0=10,t=2um` | `1.37e12` | `2.682` | `0.179` | `1.067e-2` | `2.778e-4` | `1.50e10` | `0.168` |
| `a0=5,t=3um` | `7.51e12` | `2.749` | `0.249` | `1.055e-2` | `4.467e-4` | `8.25e10` | `0.928` |
| `a0=10,t=3um` | `8.06e12` | `2.756` | `0.256` | `1.053e-2` | `4.998e-4` | `8.89e10` | `1.000` |
| `a0=15,t=3um` | `1.08e13` | `2.822` | `0.294` | `1.045e-2` | `1.514e-3` | `1.30e11` | `1.456` |
| `a0=20,t=3um` | `1.82e13` | `3.127` | `0.386` | `1.012e-2` | `8.783e-3` | `3.44e11` | `3.863` |
| `a0=10,t=4um` | `2.45e13` | `2.857` | `0.329` | `1.039e-2` | `1.447e-3` | `2.90e11` | `3.265` |

Statistical self-check:

- Maximum OpenMC relative error among all 14 Case B runs:
  - `Li6`: `0.12%`.
  - `Li7`: `0.86%`.
  - split `Li6+Li7` total: `0.17%`.
- These statistics are adequate for trend ranking.

Result files:

- `hpc/results/full_chain_20260706/pic2d_full_chain_openmc_summary.csv`
- `hpc/results/full_chain_20260706/pic2d_full_chain_natural_li_summary.csv`
- `hpc/results/full_chain_20260706/pic2d_full_chain_li6_90_summary.csv`
- `hpc/results/full_chain_20260706/pic2d_stageB_neutron_yield_trends.png`
- `hpc/results/full_chain_20260706/pic2d_full_chain_natural_tpr_trends.png`
- `hpc/results/full_chain_20260706/pic2d_full_chain_li6_90_tpr_trends.png`

## 3D a0=20,t=3um 6 ps Validation Source

Date: 2026-07-08.

This is the complete 3D validation source replacing the earlier incomplete
3D `a0=10,t=3um` particle-level source chain.

Remote run:

- Job `2143600`, `no5_3d_a20_6ps`.
- Run directory:
  `/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag6000fs_a0_20_t_3um_20260707_r001`.
- Status: `COMPLETED`, exit code `0:0`.
- Resources: `512` cores, elapsed `13:42:11`.
- Output: `Data/0000.sdf` through `Data/0023.sdf`; directory size about `16G`.

Local compact products:

`/Volumes/billboom/paperwork/no6/stageB_inputs_20260706/stageB_inputs_3d/pic3d_a0_20_t_3um_6ps`

Extraction and interface:

- source plane: `D_rear10`;
- gate: `E_D > 0.4 MeV`;
- collection: `0-6 ps`;
- PIC `+x` mapped to OpenMC `+z`;
- primary files:
  - `deuteron_beam.h5`;
  - `neutron_source_pstar.h5`;
  - `deuteron_beam_summary.csv`;
  - `neutron_source_summary.csv`;
  - `README.md`.

Key numbers:

| quantity | value |
|---|---:|
| D macro rows | `3,238,030` |
| D total weight | `8.24791e11` |
| D weighted mean energy | `0.548866 MeV` |
| D max energy | `12.390841 MeV` |
| D forward fraction `mu>0.8` | `0.958460` |
| Stage B neutron weight | `2.2645068e6` |
| neutron weighted mean energy | `2.905663 MeV` |
| neutron max energy | `12.416890 MeV` |
| neutron fraction `E>2.82 MeV` | `0.435290` |
| neutron fraction `E>3.1454 MeV` | `0.252885` |
| neutron forward fraction `mu>0.8` | `0.131349` |

Do not delete the remote SDF files or the local HDF5/CSV products without an
explicit backup/approval step.

Stage C validation:

- Date: 2026-07-08.
- Local C4 output:
  `/Volumes/billboom/paperwork/no6/stageB_inputs_20260706/openmc_c4_3d_anchor_20260708`.
- OpenMC library/statistics:
  ENDF/B-VII.1, `100 x 1e6` particles.
- Case A gate passed:
  - natural lithium total TPR/n `0.011190`;
  - enriched lithium total TPR/n `0.128324`;
  - Li7 channel zero for the 2.45 MeV ideal source.
- 3D source descriptors:
  - `frac_E_gt_2p82 = 0.435290`;
  - `frac_E_gt_3p1454 = 0.252885`;
  - `li7_mt205_fluxavg_b = 0.015381`;
  - `frac_mu_gt_0p8 = 0.131349`.
- 3D Case B/Case A total TPR:
  - natural lithium: `1.434950`;
  - enriched lithium: `0.995430`.
- 2D -> 3D correction for the corresponding `a0=20,t=3um` source:
  - natural lithium: `1.540586 -> 1.434950` (`3D/2D = 0.931431`);
  - enriched lithium: `0.986095 -> 0.995430` (`3D/2D = 1.009467`).
- C1 universal-curve check:
  - linear interpolation of existing C1 points predicts natural lithium
    `B/A = 1.377682` and enriched lithium `B/A = 0.990005` at the 3D
    `li7_mt205_fluxavg_b`;
  - measured 3D values are `1.434950` and `0.995430`, respectively;
  - with the production OpenMC statistical error alone, the 3D point is not
    statistically consistent with the interpolated C1 curve. Treat the C1
    curve as trend guidance and use this 3D anchor as the systematic
    validation/correction point.
