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
