# HPC Run Log

Postprocessing note:

- EPOCH `begin:probe` is a plane-crossing particle diagnostic. Source-code
  checks show `particles.F90` detects a sign change across the probe plane and
  `io/probes.F90` clears `sampled_particles` after each write, so repeated SDF
  probe files are time-window records rather than full-run cumulative totals.
  Build the Stage B source by concatenating all accepted probe windows, or run
  one deliberately long output window after the end time is known.
- For long runs, use `Data/*.sdf` in postprocessing so files beyond `0009.sdf`
  are included.

## pic2d_dd_cd2_a0_5_L_0_t_5um_20260701_r001

- Purpose: first no5 EPOCH2D smoke in dedicated remote workspace.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_a0_5_L_0_t_5um_20260701_r001`
- Job ID: `1271819`
- State: `COMPLETED`, exit code `0:0`
- Runtime: about 7 seconds by Slurm, EPOCH core runtime 3.54 seconds.
- Outputs on remote: `Data/0000.sdf`, `Data/0001.sdf`, `Data/0002.sdf`.
- Local compact copy: `outputs/hpc/pic2d_dd_cd2_a0_5_L_0_t_5um_20260701_r001/` (ignored by git).
- Self-check:
  - SDF reader works.
  - Latest SDF: `0002.sdf`.
  - Deuteron particle diagnostics present: `Particles_Px_deuteron`, `Particles_Py_deuteron`, `Particles_Weight_deuteron`.
  - Deuteron density diagnostic present: `Derived_Number_Density_deuteron`.
  - Extracted forward (`px > 0`) deuterons to `deuteron_phase_space_pxpos.npz`: 16,421 particles.
  - Converted locally to schema-valid `deuteron_beam_smoke.h5`.
  - Built local `neutron_source_smoke.h5` from first 2,000 deuterons; `Y_total = 1.1082e13`, neutron energy range `1.67-10.29 MeV`, unweighted fraction above 2.82 MeV `0.17`.

Notes:

- This is a low-resolution link check, not production physics.
- EPOCH warned about missing `ionisation_energies.table`; no field ionisation is used in this smoke deck, but production decks should set `physics_table_location` explicitly.
- The smoke exposed a useful Stage B guardrail: Bosch-Hale is now zeroed outside its nominal 0.5-4900 keV CM fit range to prevent negative cross sections from out-of-range high-energy smoke particles.

## pic2d_dd_cd2_xscan_a0_5_L_0_t_5um_20260701_r001

- Purpose: low-resolution source-plane diagnostic, not production physics.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_xscan_a0_5_L_0_t_5um_20260701_r001`
- Job ID: `1272786`
- State: `COMPLETED`, exit code `0:0`
- Runtime: about 15 seconds by Slurm, EPOCH core runtime 10.15 seconds.
- Box: `x=[-6,50] um`, `y=[-10,10] um`, `nx=560`, `ny=200`, `t_end=500 fs`.
- Outputs on remote: `Data/0000.sdf` ... `Data/0005.sdf`.
- Plane scan: `rear = +2.5 um`, candidate planes `rear+5,10,15,20,25,30 um`, filter `px>0`, `E_D>0.1 MeV`.

At `t=500 fs`:

| plane | macro D | weight sum | mean E (MeV) | p99 E (MeV) | theta RMS |
|---|---:|---:|---:|---:|---:|
| rear+5 um | 1791 | 6.24e17 | 16.87 | 38.30 | 24.36 deg |
| rear+10 um | 795 | 2.77e17 | 18.14 | 40.08 | 16.55 deg |
| rear+15 um | 100 | 3.48e16 | 19.09 | 32.58 | 10.33 deg |
| rear+20 um | 0 | 0 | n/a | n/a | n/a |

Interpretation:

- At 500 fs, `rear+20 um` has not yet accumulated enough deuterons in this low-resolution diagnostic.
- `rear+5/10/15 um` already show forward deuterons, but the plane statistics are still evolving strongly with position.
- At this point the next pilot was planned for `0.8-1.0 ps`; later wide-target runs showed this was still too early for `rear+20 um`.

## pic2d_dd_cd2_probe1ps_a0_5_L_0_t_5um_20260701_r001

- Purpose: medium-resolution, wide-target probe diagnostic for objective source-plane timing.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe1ps_a0_5_L_0_t_5um_20260701_r001`
- Job ID: `1273446`
- State: `COMPLETED`, exit code `0:0`
- Runtime: 11 minutes 7 seconds by Slurm.
- Box: `x=[-10,60] um`, `y=[-25,25] um`, `dx=dy=25 nm`, `t_end=1 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: `rear+10,20,30,40 um`, deuteron, `E_D > 0.1 MeV`.

At `t=1.0 ps`, only `rear+10 um` produced a probe record:

| probe | macro D | weight sum | mean E (MeV) | p99 E (MeV) | theta RMS |
|---|---:|---:|---:|---:|---:|
| rear+10 um | 154 | 8.38e14 | 5.36 | 6.30 | 5.84 deg |
| rear+20 um | 0 | 0 | n/a | n/a | n/a |

Interpretation:

- `rear+20 um` at `1 ps` is not a valid source plane for this wide-target, medium-resolution setup.
- The early low-resolution x-scan used a narrower target (`target_y_half=5 um`) and likely overestimated the early deuteron front through finite transverse-size effects.

## pic2d_dd_cd2_phasecheck1ps_a0_5_L_0_t_5um_20260701_r002

- Purpose: direct particle-snapshot cross-check for the 1 ps probe run.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_phasecheck1ps_a0_5_L_0_t_5um_20260701_r002`
- Job ID: `1274746`
- State: `COMPLETED`, exit code `0:0`
- Runtime: 11 minutes 10 seconds by Slurm.
- Same physics and grid as the 1 ps probe diagnostic; output includes deuteron phase space.
- Note: `r001` failed before physics due to missing EPOCH stdin for output directory/deck name; the Slurm template now pipes `Data` and `input.deck`.

Plane scan summary:

| time | plane | macro D | weight sum | mean E (MeV) | p99 E (MeV) | theta RMS |
|---:|---|---:|---:|---:|---:|---:|
| 600 fs | rear+5 um | 0 | 0 | n/a | n/a | n/a |
| 800 fs | rear+5 um | 450 | 2.45e15 | 3.62 | 5.06 | 6.26 deg |
| 800 fs | rear+10 um | 0 | 0 | n/a | n/a | n/a |
| 1000 fs | rear+5 um | 9,336 | 5.08e16 | 2.73 | 5.50 | 8.25 deg |
| 1000 fs | rear+10 um | 154 | 8.38e14 | 5.52 | 6.86 | 5.89 deg |
| 1000 fs | rear+15 um | 0 | 0 | n/a | n/a | n/a |

Interpretation:

- Probe output is validated: the `rear+10 um` snapshot count and weight at 1 ps match the probe result.
- At `1 ps`, the deuteron front has only just reached `rear+10 um`; it has not reached `rear+15/20 um`.
- A longer diagnostic is required before choosing the converter entrance source plane.

## pic2d_dd_cd2_probe2ps_a0_5_L_0_t_5um_20260701_r002

- Purpose: longer probe-only diagnostic to test whether the nominal `rear+20 um` converter entrance has a stable cumulative deuteron source.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe2ps_a0_5_L_0_t_5um_20260701_r002`
- Job ID: `1274749`
- State: `COMPLETED`, exit code `0:0`
- Runtime: 44 minutes 15 seconds by Slurm; EPOCH core runtime 44 minutes 11 seconds.
- Box: `x=[-10,80] um`, `y=[-30,30] um`, `dx=dy=25 nm`, `t_end=2 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: `rear+10,20,30,40,50,60 um`, deuteron, `E_D > 0.1 MeV`.
- Local compact copy: `outputs/hpc/pic2d_dd_cd2_probe2ps_a0_5_L_0_t_5um_20260701_r002/` (ignored by git).
- Note: `r001` failed before physics due to the old Slurm stdin issue; `r002` uses the fixed template.

Probe summary:

| time | plane | macro D | weight sum | mean E (MeV) | p99 E (MeV) | theta RMS |
|---:|---|---:|---:|---:|---:|---:|
| 1000 fs | rear+10 um | 160 | 8.71e14 | 5.30 | 6.29 | 5.67 deg |
| 1250 fs | rear+10 um | 4,697 | 2.56e16 | 3.88 | 5.69 | 8.57 deg |
| 1500 fs | rear+10 um | 32,374 | 1.76e17 | 3.21 | 4.95 | 11.06 deg |
| 1500 fs | rear+20 um | 396 | 2.16e15 | 6.49 | 8.07 | 8.61 deg |
| 1750 fs | rear+10 um | 69,801 | 3.80e17 | 2.81 | 4.88 | 15.26 deg |
| 1750 fs | rear+20 um | 4,379 | 2.38e16 | 5.24 | 6.98 | 9.42 deg |
| 1750 fs | rear+30 um | 42 | 2.29e14 | 8.00 | 8.92 | 6.37 deg |
| 2000 fs | rear+10 um | 95,700 | 5.21e17 | 2.52 | 4.76 | 20.25 deg |
| 2000 fs | rear+20 um | 22,911 | 1.25e17 | 4.58 | 6.74 | 10.92 deg |
| 2000 fs | rear+30 um | 788 | 4.29e15 | 6.55 | 8.25 | 9.71 deg |

Interpretation:

- `rear+20 um` is still not complete at `2 ps`: from 1.75 ps to 2.00 ps the probe-window weight increases by about 5.2x and the weighted mean energy drops from 5.24 MeV to 4.58 MeV.
- This is the expected high-energy-front/low-energy-body behavior. Early `rear+20 um` windows are biased toward faster deuterons and should not be used as the final integrated source.
- `rear+30 um` at 2 ps is only the leading front and has too little weight/statistics.
- A 2.5 ps long-box probe diagnostic was submitted as `pic2d_dd_cd2_probe2p5ps_a0_5_L_0_t_5um_20260701_r001` (Job ID `1277750`) to test whether `rear+20 um` reaches a plateau.

## pic2d_dd_cd2_probe2p5ps_a0_5_L_0_t_5um_20260701_r001

- Purpose: extend the probe-only source-timing diagnostic after `rear+20 um` remained incomplete at 2 ps.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe2p5ps_a0_5_L_0_t_5um_20260701_r001`
- Job ID: `1277750`
- State: `COMPLETED`, exit code `0:0`
- Runtime: 1 hour 51 seconds by Slurm; EPOCH core runtime 1 hour 41.76 seconds.
- Box: `x=[-10,90] um`, `y=[-30,30] um`, `dx=dy=25 nm`, `t_end=2.5 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: `rear+10,20,30,40,50,60,70 um`, deuteron, `E_D > 0.1 MeV`.
- Integrated analysis: `tools/integrate_probe_sdf.py Data/*.sdf -o deuteron_probe_integrated.csv`.

Selected `rear+20 um` time-window and integrated metrics:

| time | window weight | integrated weight | latest-window fraction | window mean E | integrated mean E | window theta RMS | integrated theta RMS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1500 fs | 2.14e15 | 2.14e15 | 1.000 | 6.48 MeV | 6.48 MeV | 8.24 deg | 8.24 deg |
| 1750 fs | 2.30e16 | 2.51e16 | 0.915 | 5.24 MeV | 5.35 MeV | 9.54 deg | 9.44 deg |
| 2000 fs | 1.25e17 | 1.51e17 | 0.833 | 4.58 MeV | 4.71 MeV | 11.01 deg | 10.76 deg |
| 2250 fs | 2.58e17 | 4.09e17 | 0.632 | 4.05 MeV | 4.29 MeV | 13.95 deg | 12.87 deg |
| 2500 fs | 3.59e17 | 7.68e17 | 0.468 | 3.57 MeV | 3.95 MeV | 17.70 deg | 15.32 deg |

Interpretation:

- `rear+20 um` is not complete by 2.5 ps. The latest 250 fs window still contributes 46.8% of the integrated source weight, far above the 5-10% gate.
- The window mean energy continues to decrease and the angular RMS continues to broaden, so the late-arriving lower-energy/wider-angle deuterons are still important.
- `rear+30/40/50 um` remain later-arrival cross-checks rather than accepted source planes for this geometry.
- A 3 ps long-box probe diagnostic was submitted as `pic2d_dd_cd2_probe3ps_a0_5_L_0_t_5um_20260701_r001` (Job ID `1281140`).

## pic2d_dd_cd2_probe3ps_a0_5_L_0_t_5um_20260701_r001

- Purpose: test whether the nominal `rear+20 um` source reaches completion after the 2.5 ps diagnostic failed the late-window gate.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe3ps_a0_5_L_0_t_5um_20260701_r001`
- Job ID: `1281140`
- State: `COMPLETED`, exit code `0:0`
- Runtime: 2 hours 39 minutes 21 seconds by Slurm.
- Box: `x=[-10,110] um`, `y=[-35,35] um`, `dx=dy=25 nm`, `t_end=3 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: `rear+10,20,30,40,50,60,70,80,90 um`, deuteron, `E_D > 0.1 MeV`.
- Local compact copy: `outputs/hpc/pic2d_dd_cd2_probe3ps_a0_5_L_0_t_5um_20260701_r001/` (ignored by git).

Selected `rear+20 um` integrated metrics:

| time | window weight | integrated weight | latest-window fraction | window mean E | integrated mean E | window theta RMS | integrated theta RMS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1500 fs | 2.00e15 | 2.00e15 | 1.000 | 6.60 MeV | 6.60 MeV | 8.62 deg | 8.62 deg |
| 1750 fs | 2.28e16 | 2.48e16 | 0.919 | 5.23 MeV | 5.34 MeV | 9.29 deg | 9.23 deg |
| 2000 fs | 1.25e17 | 1.49e17 | 0.834 | 4.58 MeV | 4.70 MeV | 10.85 deg | 10.60 deg |
| 2250 fs | 2.61e17 | 4.10e17 | 0.636 | 4.05 MeV | 4.29 MeV | 13.96 deg | 12.84 deg |
| 2500 fs | 3.61e17 | 7.72e17 | 0.468 | 3.57 MeV | 3.95 MeV | 17.71 deg | 15.31 deg |
| 2750 fs | 4.05e17 | 1.18e18 | 0.344 | 3.15 MeV | 3.68 MeV | 21.68 deg | 17.76 deg |
| 3000 fs | 3.93e17 | 1.57e18 | 0.250 | 2.78 MeV | 3.45 MeV | 25.34 deg | 19.94 deg |

Interpretation:

- `rear+20 um` is still not complete at 3 ps. The latest 250 fs window remains 25.0% of the integrated source, above the 5-10% gate.
- The integrated mean energy and angular RMS are still moving because late, lower-energy, wider-angle deuterons are still arriving.
- A source-focused 3.5 ps diagnostic was submitted with 64 MPI ranks as `pic2d_dd_cd2_probe3p5ps_source_a0_5_L_0_t_5um_20260702_r001` (Job ID `1324731`). It keeps only `rear+10/20/30/40/50` probes to reduce probe-output overhead.

## pic2d_dd_cd2_probe3p5ps_source_a0_5_L_0_t_5um_20260702_r001

- Purpose: source-completion diagnostic after the 3 ps run still failed the late-window gate at `rear+20 um`.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe3p5ps_source_a0_5_L_0_t_5um_20260702_r001`
- Job ID: `1324731`
- State: `COMPLETED`, exit code `0:0`.
- Runtime: 1 hour 12 minutes 21 seconds by Slurm.
- MPI ranks: 64 on one 256-CPU node.
- Box: `x=[-10,90] um`, `y=[-40,40] um`, `dx=dy=25 nm`, `t_end=3.5 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: source-focused `rear+10,20,30,40,50 um`, deuteron, `E_D > 0.1 MeV`.
- Rationale: the 3 ps run used 32 ranks and many far downstream probes. This follow-up increases ranks and removes far probes to reduce wall time and probe-output overhead while preserving the accepted-source question.

Selected `rear+20 um` integrated metrics:

| time | window weight | integrated weight | latest-window fraction | window mean E | integrated mean E | window theta RMS | integrated theta RMS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1500 fs | 2.09e15 | 2.09e15 | 1.000 | 6.54 MeV | 6.54 MeV | 8.52 deg | 8.52 deg |
| 1750 fs | 2.40e16 | 2.60e16 | 0.920 | 5.21 MeV | 5.32 MeV | 9.35 deg | 9.28 deg |
| 2000 fs | 1.28e17 | 1.54e17 | 0.830 | 4.57 MeV | 4.70 MeV | 10.89 deg | 10.63 deg |
| 2250 fs | 2.62e17 | 4.16e17 | 0.631 | 4.03 MeV | 4.28 MeV | 14.00 deg | 12.86 deg |
| 2500 fs | 3.59e17 | 7.75e17 | 0.464 | 3.56 MeV | 3.95 MeV | 17.73 deg | 15.31 deg |
| 2750 fs | 4.06e17 | 1.18e18 | 0.344 | 3.14 MeV | 3.67 MeV | 21.75 deg | 17.79 deg |
| 3000 fs | 3.94e17 | 1.58e18 | 0.250 | 2.77 MeV | 3.44 MeV | 25.61 deg | 20.03 deg |
| 3250 fs | 3.49e17 | 1.92e18 | 0.181 | 2.46 MeV | 3.27 MeV | 29.04 deg | 21.94 deg |
| 3500 fs | 2.96e17 | 2.22e18 | 0.133 | 2.18 MeV | 3.12 MeV | 31.71 deg | 23.48 deg |

Final-by-probe cross-check at 3.5 ps:

| probe | integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---|---:|---:|---:|---:|
| rear+10 um | 3.24e18 | 0.050 | 2.23 MeV | 29.54 deg |
| rear+20 um | 2.22e18 | 0.133 | 3.12 MeV | 23.48 deg |
| rear+30 um | 1.28e18 | 0.244 | 3.97 MeV | 18.13 deg |
| rear+40 um | 5.98e17 | 0.391 | 4.82 MeV | 13.79 deg |
| rear+50 um | 1.94e17 | 0.609 | 5.64 MeV | 10.65 deg |

Interpretation:

- `rear+20 um` is approaching completion but still misses the strict gate at 3.5 ps. The final 250 fs window contributes 13.3% of the cumulative source, above the target `<= 5-10%`.
- The trend is physically consistent: late-arriving deuterons have lower mean energy and broader angle, so ending at 3.5 ps would slightly bias the Stage B source high in energy and narrow in angle.
- A 4.0 ps source-focused diagnostic was resubmitted with 160 MPI ranks as `pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r002` (Job ID `1348703`) after the 64-rank job was cancelled to shorten wall time.

## pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r001

- Purpose: final source-completion check after the 3.5 ps diagnostic came close but remained above the late-window gate.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r001`
- Job ID: `1346456`
- State: `CANCELLED` after about 6 seconds; no accepted physics data.
- MPI ranks: 64 on one 256-CPU node.
- Box: `x=[-10,90] um`, `y=[-40,40] um`, `dx=dy=25 nm`, `t_end=4.0 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: source-focused `rear+10,20,30,40,50 um`, deuteron, `E_D > 0.1 MeV`.
- Acceptance target: `rear+20 um` final-window fraction `<= 10%`, with cumulative mean energy and theta RMS changing by no more than about `5-10%` after appending the last window.
- Reason for cancellation: user requested a wall-time target near 30 minutes. The same physics case was resubmitted with 160 MPI ranks.

## pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r002

- Purpose: faster 4.0 ps source-completion check with unchanged physics and higher MPI rank count.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r002`
- Job ID: `1348703`
- State: `CANCELLED` after about 40 seconds; no accepted physics data.
- MPI ranks: 160 on one 256-CPU node.
- Box: `x=[-10,90] um`, `y=[-40,40] um`, `dx=dy=25 nm`, `t_end=4.0 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: source-focused `rear+10,20,30,40,50 um`, deuteron, `E_D > 0.1 MeV`.
- Wall-time estimate: scaling from the 3.5 ps / 64-rank run gives an ideal estimate near 30 minutes; practical runtime may be closer to 30-45 minutes because probe and MPI overhead do not scale perfectly.
- Acceptance target: `rear+20 um` final-window fraction `<= 10%`, with cumulative mean energy and theta RMS changing by no more than about `5-10%` after appending the last window.
- Reason for cancellation: the Slurm script did not explicitly set the partition. The cluster engineer recommended adding `#SBATCH -p amd_m9_768`, cancelling existing jobs, and resubmitting.

## pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r003

- Purpose: temporary 64-rank backup queue attempt while the 160-rank job was pending.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r003`
- Job ID: `1353498`
- State: `CANCELLED` before start; no physics data.
- MPI ranks: 64 on one 256-CPU node.
- Box: `x=[-10,90] um`, `y=[-40,40] um`, `dx=dy=25 nm`, `t_end=4.0 ps`.
- Reason for cancellation: replaced by an explicitly partitioned 160-rank submission after cluster-engineer feedback.

## pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r004

- Purpose: 4.0 ps source-completion check with unchanged physics, 160 MPI ranks, and explicit Slurm partition selection.
- Remote run directory: `~/pic/no5_dd_li_tpr/runs/pic2d_dd_cd2_probe4ps_source_a0_5_L_0_t_5um_20260702_r004`
- Job ID: `1355962`
- State at submission check: `PENDING`.
- Slurm partition: `amd_m9_768` explicitly set with `#SBATCH -p amd_m9_768`.
- MPI ranks: 160 on one 256-CPU node.
- Box: `x=[-10,90] um`, `y=[-40,40] um`, `dx=dy=25 nm`, `t_end=4.0 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: source-focused `rear+10,20,30,40,50 um`, deuteron, `E_D > 0.1 MeV`.
- Wall-time estimate: about 30-45 minutes once scheduled.
- Acceptance target: `rear+20 um` final-window fraction `<= 10%`, with cumulative mean energy and theta RMS changing by no more than about `5-10%` after appending the last window.
