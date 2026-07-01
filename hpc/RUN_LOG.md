# HPC Run Log

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
- The next pilot should run to `0.8-1.0 ps`; use `rear+20 um` as the nominal converter entrance and compare `rear+10/20/30 um` plus `0.6/0.8/1.0 ps` snapshots for stability.
