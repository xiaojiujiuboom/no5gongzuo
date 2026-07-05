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

## Current Formal 2D Matrix

Purpose:

- Use 2D as the lower-cost parameter scan.
- Use the accepted 3D source above as the dimensionality anchor.
- Treat 2D mainly as trend/optimization evidence; do not claim raw 2D absolute
  yield as the final physical yield without 3D anchoring.

Common 2D settings:

- box `x=-6..36 um`, `y=-15..15 um`
- grid `4200 x 3000`, `dx=dy=10 nm`
- PPC `electron/deuteron/carbon = 16/48/8`
- probes `rear+5/10/15/20`
- primary source plane `rear+10`
- `t_end = 6 ps`
- `dt_snapshot = 250 fs`
- Slurm `amd_m9_768`, `1` node, `256` ranks, walltime `10 h`
- final output is restartable: `force_final_to_be_restartable = T`
- `stop_at_walltime = 34200 s`

Current 7 active 2D jobs:

| job | run | a0 | thickness um | state at latest check | node |
|---:|---|---:|---:|---|---|
| `1855864` | `pic2d_stage1_formal6ps_10nm_a0_05_t_3um_20260706_r001` | 5 | 3 | RUNNING | `wqd10nbd04c18` |
| `1855865` | `pic2d_stage1_formal6ps_10nm_a0_10_t_3um_20260706_r001` | 10 | 3 | RUNNING | `wqd10nbd05c15` |
| `1855866` | `pic2d_stage1_formal6ps_10nm_a0_15_t_3um_20260706_r001` | 15 | 3 | RUNNING | `wqd10nbd07c08` |
| `1855867` | `pic2d_stage1_formal6ps_10nm_a0_20_t_3um_20260706_r001` | 20 | 3 | RUNNING | `wqd10nbd07c11` |
| `1855868` | `pic2d_stage1_formal6ps_10nm_a0_10_t_1um_20260706_r001` | 10 | 1 | RUNNING | `wqd10nbd07c16` |
| `1855869` | `pic2d_stage1_formal6ps_10nm_a0_10_t_2um_20260706_r001` | 10 | 2 | RUNNING | `wqd10nbd08c06` |
| `1855870` | `pic2d_stage1_formal6ps_10nm_a0_10_t_4um_20260706_r001` | 10 | 4 | RUNNING | `wqd10nbd08c20` |

Remote run directory pattern:

```text
/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/runs/<run_id>
```

Monitoring command:

```bash
squeue -j 1855864,1855865,1855866,1855867,1855868,1855869,1855870 \
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
