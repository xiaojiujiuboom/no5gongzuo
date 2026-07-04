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

## 2026-07-03 resource-controlled Stage 1 3D benchmark inputs

- After reviewing `/Volumes/billboom/paperwork/tritium/EXECUTION_stage1_pic.md`,
  the no5 3D PIC strategy is narrowed to one information-rich benchmark before
  any production scan:
  - four native EPOCH3D deuteron probes at `rear+5/10/15/20 um`
  - deuteron energy distribution output every snapshot
  - no field grids, no full particle dumps, no periodic restart dumps
  - use the benchmark to choose the collection plane, necessary `t_end`, and
    whether the `y/z = +/-10 um` transverse box clips the beam
- Two review-ready EPOCH3D input templates were added:
  - `hpc/templates/epoch3d_stage1_benchmark_3um_512_smoke.deck`
  - `hpc/templates/epoch3d_stage1_benchmark_3um_512_full.deck`
- Shared physics/settings:
  - CD2 target: `3 um` thick, transverse half-width `5 um`
  - box: `x=[-6,26] um`, `y,z=[-10,10] um`
  - grid: `nx,ny,nz = 2000,250,250`, giving `dx=16 nm`,
    `dy=dz=80 nm`
  - PPC `electron/deuteron/carbon = 16/32/4`; deuterons remain prioritized
  - forced MPI topology `nprocx,nprocy,nprocz = 32,4,4` for `512` ranks
  - `full_dump_every = -1`, `restart_dump_every = -1`,
    `force_final_to_be_restartable = F`
- Scale estimate:
  - cells: `1.25e8`
  - active target cells: about `2.93e6`
  - macro-particles: about `1.52e8`
  - this is about `26%` of the `3000x400x400` benchmark in both grid cells and
    macro-particles, while retaining the four-probe 3D benchmark logic
- At commit `102123b`, these files were input review artifacts only. The
  smoke template was later submitted as
  `pic3d_stage1_smoke50fs_2000x250x250_a0_10_t_3um_20260703_r001`.

## pic3d_stage1_smoke50fs_2000x250x250_a0_10_t_3um_20260703_r001

- Purpose: low-cost 50 fs EPOCH3D smoke test for the resource-controlled Stage
  1 benchmark input before any 1500 fs benchmark submission.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_stage1_smoke50fs_2000x250x250_a0_10_t_3um_20260703_r001`
- Job ID: `1523494`
- Final state: `COMPLETED`, exit code `0:0`.
- Runtime: `00:05:13`; EPOCH core runtime `4 minutes, 46.48 seconds`.
- Approximate cost: `44.5` core-hours, about `4.5 CNY` at
  `0.1 CNY/core-hour`.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime
  `1:00:00`.
- Full-walltime cost cap: `512` core-hours, about `51.2 CNY` at
  `0.1 CNY/core-hour`; actual billing should stop when the job exits.
- Submitted input:
  `hpc/templates/epoch3d_stage1_benchmark_3um_512_smoke.deck`
- Key checks before submission:
  - `nx,ny,nz = 2000,250,250`
  - `nprocx,nprocy,nprocz = 32,4,4`
  - `t_end = 50 fs`, `dt_snapshot = 50 fs`
  - PPC `electron/deuteron/carbon = 16/32/4`
  - four deuteron probes at `rear+5/10/15/20 um`
  - particle probes and deuteron distribution function only
  - `full_dump_every = -1`, `restart_dump_every = -1`,
    `force_final_to_be_restartable = F`
  - uploaded deck is ASCII-only and comment-free.
  - no old no5 jobs were running or pending before submission.
- Completion checks:
  - EPOCH3D v4.20.1 parsed the deck and entered the time loop normally.
  - Processor subdivision was exactly `32 x 4 x 4`.
  - Loaded macro-particles: electron `47,000,000`, deuteron `94,000,000`,
    carbon `11,750,000`; total `152,750,000`, matching the reduced-grid
    estimate.
  - The run reached `50 fs` and wrote `Data/0000.sdf`, `deck.status`,
    `epoch3d.dat`, and `normal.visit`.
  - Output size stayed tiny (`Data/0000.sdf` about `18 KB`) because field grids,
    full particle dumps, and restart dumps are disabled.
  - `sacct` reported `COMPLETED` for the batch, extern, and MPI steps. Batch
    MaxRSS was about `52,661,352K`; the MPI step MaxRSS was about
    `52,708,996K`.
  - `slurm.err` contains repeated `ieee_inexact` warnings at normal Fortran
    stop. No NaN, OOM, kill, or nonzero exit was observed.
- Linear extrapolation from the smoke:
  - about `6.26 s/fs`
  - `1500 fs` benchmark estimate about `2.6 h`
  - estimated cost about `134 CNY` before safety margin
- Decision: smoke passed as a run-layer validation. The next physics step is
  the `1500 fs` four-probe benchmark, not production scanning.

## pic3d_stage1_benchmark1500fs_2000x250x250_a0_10_t_3um_20260704_r001

- Purpose: first physics-decision EPOCH3D benchmark after the successful
  `50 fs` smoke. This run is intended to choose the deuteron collection plane,
  check whether `1500 fs` is long enough, and verify transverse box adequacy
  from the four rear probes.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_stage1_benchmark1500fs_2000x250x250_a0_10_t_3um_20260704_r001`
- Job ID: `1559752`
- Final state: `COMPLETED`, exit code `0:0`.
- Runtime: Slurm elapsed `02:47:33`; EPOCH core runtime `2 hours,
  47 minutes, 4.30 seconds`.
- Approximate cost: `1430` core-hours, about `143 CNY` at
  `0.1 CNY/core-hour`.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime
  `4:00:00`.
- Full-walltime cost cap: `2048` core-hours, about `204.8 CNY` at
  `0.1 CNY/core-hour`.
- Smoke-based linear estimate: about `2.6 h`, about `134 CNY`, before queue and
  runtime variability.
- Submitted input:
  `hpc/templates/epoch3d_stage1_benchmark_3um_512_full.deck`
- Key settings:
  - `nx,ny,nz = 2000,250,250`
  - `nprocx,nprocy,nprocz = 32,4,4`
  - `t_end = 1500 fs`, `dt_snapshot = 250 fs`
  - PPC `electron/deuteron/carbon = 16/32/4`
  - four deuteron probes at `rear+5/10/15/20 um`
  - particle probes and deuteron distribution function only
  - `full_dump_every = -1`, `restart_dump_every = -1`,
    `force_final_to_be_restartable = F`
- Completion checks:
  - EPOCH3D completed normally with `Exit status: 0`; no NaN, OOM, kill, or
    nonzero exit was observed.
  - `slurm.err` contains repeated `ieee_inexact` warnings at normal Fortran
    stop, matching the earlier smoke run behavior.
  - Slurm MaxRSS was about `52,750,636K` for the MPI step, far below the
    two-node memory allocation.
  - Output stayed small: `Data/0000.sdf` through `Data/0005.sdf`, total
    `4.7M`; no restart/full particle dump was produced.
  - Python `sdf_helper`/`sdf.read` segfaulted on these 3D SDF files, so a small
    temporary C reader against the EPOCH SDF/C library was used for block and
    probe summaries.
- SDF/probe summary:
  - Snapshots were written at about `250, 500, 750, 1000, 1250, 1500 fs`.
  - Every SDF contains `deuteron_en/deuteron` with `1000` bins.
  - Probe blocks appear only after ions reach the planes:
    - `750 fs`: `D_rear05` first appears with `1` macro-particle.
    - `1000 fs`: `D_rear05` has `511` macro-particles.
    - `1250 fs`: `D_rear05` has `6092`, `D_rear10` has `3`.
    - `1500 fs`: `D_rear05` has `17609`, `D_rear10` has `156`.
    - `D_rear15` and `D_rear20` are absent through `1500 fs`.
  - `D_rear05` cumulative through `1500 fs`: `24213` macro-particles,
    total weight `6.16753536e9`, cumulative mean energy about `0.464 MeV`,
    observed max about `1.095 MeV`.
  - `D_rear10` cumulative through `1500 fs`: `159` macro-particles, total
    weight `4.050048e7`, cumulative mean energy about `0.954 MeV`, observed max
    about `1.307 MeV`.
  - The final `250 fs` window still contributes `72.7%` of cumulative
    `D_rear05` weight and `98.1%` of cumulative `D_rear10` weight, so `1500 fs`
    is not yet a converged source-collection time.
  - No meaningful high-energy `E_D > 9.8 MeV` tail was observed in this
    `a0=10`, `3 um` benchmark probe sample.
- Small analysis artifacts committed under `hpc/results/`:
  - `pic3d_stage1_benchmark1500fs_20260704_sdf_block_summary.csv`
  - `pic3d_stage1_benchmark1500fs_20260704_probe_metrics.csv`
  - `pic3d_stage1_benchmark1500fs_20260704_probe_cumulative_summary.csv`
- Decision:
  - This run passed as a resource-controlled 3D benchmark, validating the
    `2000x250x250`, D-prioritized PPC, four-probe workflow on `512` ranks.
  - It should not be used as the final Stage 1 source at `rear+10/15/20` because
    the late probe windows are not saturated.
  - The next Stage 1 physics run should extend to at least `3000 fs`; `3500` to
    `4000 fs` is more defensible if the source plane remains `rear+20`.
    Linear extrapolation from this benchmark gives about `95 CNY/ps` at
    `512` ranks.
  - To avoid wasting this cost again, the next long-run template should write a
    restartable final dump only, not periodic restart dumps. This preserves a
    continuation point at `t_end` while keeping intermediate I/O light. The
    prepared template is
    `hpc/templates/epoch3d_stage1_source_diag_3ps_final_restart.deck`.

## Previous paused state after user input review request

- User asked to stop submitting jobs and review the input deck first.
- All no5 3D PIC jobs are stopped or pending-free at this point; only unrelated
  `antid3` jobs remain in the user queue.
- The active template `hpc/templates/epoch3d_dd_cd2_source_compact.deck` is now
  a reduced-grid candidate, not an approved production deck:
  - `nx,ny,nz = 1690,400,400`
  - box `x=[-8,30] um`, `y,z=[-10,10] um`
  - CD2 `target_half = 5 um`, i.e. `10 um x 10 um` transverse target
  - PPC `electron/deuteron/carbon = 8/16/4`
  - source plane remains `rear+20 um`
  - periodic restart disabled; final output remains restartable
- Rationale for the reduced candidate:
  - Old no5 compact deck: `5.00e8` cells and about `6.75e8` macro-particles.
  - User's previous M4 Pro 3D deck: about `1.10e8` cells and about `8.70e7`
    estimated macro-particles.
  - Reduced no5 candidate: about `2.70e8` cells and about `1.49e8`
    macro-particles. This is still larger than the M4 deck, but much closer
    than the previous no5 candidate.
- User noted that the study focuses on deuterons, so before the next submission
  consider increasing D PPC relative to electrons/carbon, for example
  `8/24/4` or `8/32/4`, and re-estimate memory. Do not submit until the user
  approves the reviewed input.

## pic3d_dd_cd2_microbench100fs_reduced_a0_10_t_3um_20260703_r006

- Purpose: reduced-grid/PPC input preview after comparing no5 against the
  user's existing M4 Pro 3D deck.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_dd_cd2_microbench100fs_reduced_a0_10_t_3um_20260703_r006`
- Job ID: `1476316`
- Final state: `CANCELLED` before start at user request; cost zero.
- Slurm: partition `amd_m9_768`, `1` node, `256` MPI ranks, walltime `2:00:00`.
- The run was accidentally submitted before the user's interruption completed,
  was still `PENDING`, and was immediately cancelled before any allocation.
- Proposed input settings:
  - comment-free uploaded `input.deck`
  - `nx,ny,nz = 1690,400,400`
  - `x=[-8,30] um`, `y,z=[-10,10] um`
  - `target_half = 5 um`
  - `nparticles_per_cell electron/deuteron/carbon = 8/16/4`
  - `t_end = 100 fs`
  - `dt_snapshot = 50 fs`
  - `nprocx,nprocy,nprocz = 16,4,4`
  - `full_dump_every = -1`
  - `restart_dump_every = -1`
  - `force_final_to_be_restartable = T`

## pic3d_dd_cd2_microbench100fs_a0_10_t_3um_20260703_r005

- Purpose: comment-free two-node benchmark with forced processor topology after
  `r004` was cancelled before start.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_dd_cd2_microbench100fs_a0_10_t_3um_20260703_r005`
- Job ID: `1475280`
- Final state: `CANCELLED` before start at user request; cost zero.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime `1:30:00`.
- This heavier benchmark was replaced by the reduced-grid input review path.

## pic3d_dd_cd2_microbench100fs_a0_10_t_3um_20260703_r004

- Purpose: comment-free rerun of the two-node repair microbenchmark after
  `r003` showed that even ASCII comments before EPOCH3D blocks can trigger the
  parser failure seen in `r001`.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_dd_cd2_microbench100fs_a0_10_t_3um_20260703_r004`
- Job ID: `1473749`
- Final state: `CANCELLED` before start; cost zero.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime `1:30:00`.
- Cost cap at full walltime: `768` core-hours, about `76.8 CNY` at
  `0.1 CNY/core-hour`.
- Input deck is generated by stripping comments/blank lines from the
  ASCII-safe template before upload. The first line is `begin:constant`.
- Same physics and output policy as `r003`: full 3D grid/PPC unchanged,
  `t_end = 100 fs`, `dt_snapshot = 50 fs`, periodic restart disabled, final
  output restartable.
- Cancellation reason:
  - Re-examining `r002` showed that EPOCH's automatic processor topology was
    `1 x 2 x 128` for 256 ranks. That leaves the full `x` extent on every rank
    and cuts `z` into very thin slabs, increasing ghost/halo and communication
    buffer overhead.
  - A cleaner two-node benchmark should force a more isotropic topology instead
    of repeating the same automatic layout behavior.

## pic3d_dd_cd2_microbench100fs_a0_10_t_3um_20260703_r003

- Purpose: repair microbenchmark after `r002` showed that one node has no memory
  headroom and is OOM-killed at the first restart-like output.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_dd_cd2_microbench100fs_a0_10_t_3um_20260703_r003`
- Job ID: `1449565`
- Final state: `FAILED`, exit code `14:0`.
- Runtime: `00:00:46`; this failed before physics.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime `1:30:00`.
- Cost cap at full walltime: `768` core-hours, about `76.8 CNY` at
  `0.1 CNY/core-hour`.
- Deck changes relative to the production candidate:
  - `t_end = 100 fs`
  - `dt_snapshot = 50 fs`
  - `full_dump_every = -1`
  - `restart_dump_every = -1`
  - `force_final_to_be_restartable = T`
  - `physics_table_location` set to the BSCC EPOCH3D table path.
- Rationale:
  - Keep full 3D physical grid/PPC unchanged.
  - Use two nodes to reduce per-node memory.
  - Avoid making file `0000.sdf` restartable; `r002` showed that the first
    restart-like dump on one node can push memory over the node limit.
  - Still test one normal output at `50 fs` and a final restartable output at
    `100 fs`.
- Production is **not** submitted until this two-node memory/output test passes.
- Failure diagnosis:
  - EPOCH3D again rejected the deck at the first block line with
    `Value "constant" in element "" is invalid and cannot be parsed`.
  - `r002` had parsed only because its submitted input deck was fully
    comment-stripped.
  - Practical rule: all EPOCH3D run input files for this project must be
    comment-stripped before submission. Human-readable templates may keep
    comments, but uploaded `input.deck` should not.

## pic3d_dd_cd2_microbench300fs_a0_10_t_3um_20260703_r002

- Purpose: ASCII/comment-stripped rerun of the first full-size EPOCH3D
  compact-deck microbenchmark.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_dd_cd2_microbench300fs_a0_10_t_3um_20260703_r002`
- Job ID: `1417631`
- Final state: `OUT_OF_MEMORY`, exit code `0:125`.
- Start time: `2026-07-03T07:08:25` on node `wqd10nbf04c01`.
- End time: `2026-07-03T09:02:55`.
- Runtime: `01:54:30`; allocated `256` CPUs; cost about `488.5` core-hours,
  or `48.9 CNY` at `0.1 CNY/core-hour`.
- Slurm: partition `amd_m9_768`, `1` node, `256` MPI ranks, walltime `2:00:00`.
- Cost cap at full walltime: `512` core-hours, about `51.2 CNY` at
  `0.1 CNY/core-hour`.
- Difference from `r001`: all comments were stripped before submission. A
  small-grid parser test passed with the same syntax after comments were
  stripped, confirming the `r001` failure was a deck-parser/comment issue rather
  than a physics-expression issue.
- Same physics dimensions and 300 fs benchmark purpose as `r001`.
- Early runtime check:
  - EPOCH3D input parsing passed.
  - Initial conditions were valid.
  - Loaded macro-particles: electron `192,960,000`, deuteron `385,920,000`,
    carbon `96,480,000`.
  - The job entered the time loop and reached about `94.9 fs` by iteration
    `1700`.
- Failure diagnosis:
  - Slurm reported `MaxRSS = 707,781,536K` for the batch step, leaving no safe
    memory headroom on a 768 GB node.
  - The job was killed by an OOM event while producing the first large output:
    `Data/0000.sdf` was about `36 GB` and contained restart-like field data.
  - The partial `Data/0000.sdf` was deleted after diagnosis because it is not a
    usable physics output.
  - `restart_dump_every > 0` makes file number `0` restartable because the file
    index starts at zero, so periodic restart dumps are unsafe for this setup.
- Decision:
  - Do not submit a one-node 2.5 ps production run.
  - Use two nodes and disable periodic restarts; keep only final restartability.
  - Validate the revised output/restart policy with `r003` before production.

## pic3d_dd_cd2_microbench300fs_a0_10_t_3um_20260703_r001

- Purpose: first full-size EPOCH3D compact-deck microbenchmark after the
  2026-07-03 strategy reset to 3D-first source anchoring.
- This is **not** a production deuteron source. It is a cost/memory/syntax/output
  benchmark before any 2.5 ps 3D source submission.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_dd_cd2_microbench300fs_a0_10_t_3um_20260703_r001`
- Job ID: `1417042`
- Final state: `FAILED`, exit code `14:0`.
- Runtime: `00:00:35` by Slurm; about `2.5` core-hours, or roughly `0.25 CNY`
  at `0.1 CNY/core-hour`.
- Failure mode: EPOCH3D rejected the deck while parsing `begin:constant`.
  Small-grid testing showed the same deck parses after comments are stripped, so
  the practical fix is to keep EPOCH input decks ASCII/comment-safe.
- Slurm: partition `amd_m9_768`, `1` node, `256` MPI ranks, walltime `2:00:00`.
- Cost cap at full walltime: `512` core-hours, about `51.2 CNY` at
  `0.1 CNY/core-hour`.
- Deck basis: `hpc/templates/epoch3d_dd_cd2_source_compact.deck`.
- Run-specific deck changes:
  - `t_end = 300 fs`
  - `dt_snapshot = 100 fs`
  - `restart_dump_every = 3`
  - `stdout_frequency = 100`
- Physics dimensions left unchanged from the compact deck:
  - `a0 = 10`
  - `target = 3 um CD2`
  - `x = [-10, 35] um`, `nx = 2000`, `dx = 22.5 nm`
  - `y,z = [-10, 10] um`, `ny = nz = 500`, `dy = dz = 40 nm`
  - source plane remains `rear+20 um`
- Acceptance/decision criteria after completion:
  - EPOCH3D starts cleanly and exits normally.
  - Wall-clock per simulated fs supports a credible 2.5 ps estimate.
  - Memory and scratch use fit one `amd_m9_768` node with margin.
  - Probe/dist_fn output and final restart behavior are verified.
  - If the benchmark fails or is too expensive, do not submit production 3D
    without revising the deck or resource plan.

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
- State: `COMPLETED`, exit code `0:0`.
- Runtime: 38 minutes 32 seconds by Slurm; EPOCH core runtime 38 minutes 18.11 seconds.
- Slurm partition: `amd_m9_768` explicitly set with `#SBATCH -p amd_m9_768`.
- MPI ranks: 160 on one 256-CPU node.
- Box: `x=[-10,90] um`, `y=[-40,40] um`, `dx=dy=25 nm`, `t_end=4.0 ps`.
- Target: 5 um CD2, transverse half-width 12 um, real-density `n_C=20 nc`, `n_D=40 nc`, `n_e=160 nc`.
- PPC: electron/deuteron/carbon = 8/8/4.
- Probe planes: source-focused `rear+10,20,30,40,50 um`, deuteron, `E_D > 0.1 MeV`.
- Wall-time estimate: about 30-45 minutes once scheduled.
- Acceptance target: `rear+20 um` final-window fraction `<= 10%`, with cumulative mean energy and theta RMS changing by no more than about `5-10%` after appending the last window.

Selected `rear+20 um` integrated metrics:

| time | window weight | integrated weight | latest-window fraction | window mean E | integrated mean E | window theta RMS | integrated theta RMS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1500 fs | 2.24e15 | 2.24e15 | 1.000 | 6.44 MeV | 6.44 MeV | 8.51 deg | 8.51 deg |
| 1750 fs | 2.37e16 | 2.60e16 | 0.914 | 5.21 MeV | 5.31 MeV | 9.39 deg | 9.31 deg |
| 2000 fs | 1.27e17 | 1.53e17 | 0.830 | 4.58 MeV | 4.70 MeV | 10.90 deg | 10.64 deg |
| 2250 fs | 2.64e17 | 4.17e17 | 0.634 | 4.04 MeV | 4.28 MeV | 14.03 deg | 12.89 deg |
| 2500 fs | 3.63e17 | 7.80e17 | 0.465 | 3.56 MeV | 3.95 MeV | 17.79 deg | 15.37 deg |
| 2750 fs | 4.02e17 | 1.18e18 | 0.340 | 3.14 MeV | 3.67 MeV | 21.81 deg | 17.83 deg |
| 3000 fs | 3.96e17 | 1.58e18 | 0.251 | 2.77 MeV | 3.44 MeV | 25.59 deg | 20.06 deg |
| 3250 fs | 3.51e17 | 1.93e18 | 0.182 | 2.46 MeV | 3.26 MeV | 29.12 deg | 21.99 deg |
| 3500 fs | 2.95e17 | 2.22e18 | 0.133 | 2.18 MeV | 3.12 MeV | 31.71 deg | 23.51 deg |
| 3750 fs | 2.40e17 | 2.46e18 | 0.097 | 1.94 MeV | 3.01 MeV | 33.90 deg | 24.71 deg |
| 4000 fs | 1.91e17 | 2.66e18 | 0.072 | 1.73 MeV | 2.91 MeV | 35.46 deg | 25.64 deg |

Final-by-probe cross-check at 4.0 ps:

| probe | integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---|---:|---:|---:|---:|
| rear+10 um | 3.45e18 | 0.025 | 2.17 MeV | 30.74 deg |
| rear+20 um | 2.66e18 | 0.072 | 2.91 MeV | 25.64 deg |
| rear+30 um | 1.83e18 | 0.137 | 3.58 MeV | 20.78 deg |
| rear+40 um | 1.10e18 | 0.226 | 4.25 MeV | 16.63 deg |
| rear+50 um | 5.63e17 | 0.353 | 4.94 MeV | 13.21 deg |

Interpretation:

- The nominal converter-entrance source plane `rear+20 um` passes the time-completeness gate at 4.0 ps: the final 250 fs probe window is 7.19% of the integrated source weight, below the `<= 10%` threshold.
- The accepted baseline source definition for the first physics scan is therefore the concatenated deuteron phase space crossing `rear+20 um` from the start of the run through 4.0 ps, not a final-frame snapshot.
- Farther planes remain useful diagnostics but are not complete at 4.0 ps; `rear+30 um` still has a 13.7% latest-window fraction.

## First 4 ps PIC Physics Scan Submission

- Purpose: first controlled scan after accepting the `rear+20 um`, `0-4.0 ps` deuteron source definition.
- Submitted manifest: `hpc/pic_scan4ps_first_20260702_jobs.csv`
- Remote root: `~/pic/no5_dd_li_tpr/runs/`
- Slurm partition: `amd_m9_768`
- MPI ranks per case: 160
- PPC: electron/deuteron/carbon = 16/16/8.
- Box and probes: same accepted 4 ps source deck geometry, with source-focused probes at `rear+10,20,30,40,50 um`.
- Preplasma model: for `L_pre > 0`, a front-side exponential CD2 preplasma ramp extends from `target_front - 5 L_pre` to `target_front`; the solid foil remains from `target_front` to `target_rear`.

Submitted cases:

| run_id | job_id | a0 | L_pre | thickness |
|---|---:|---:|---:|---:|
| `pic2d_dd_cd2_scan4ps_a0_5_L_0_t_5um_20260702_r001` | 1367961 | 5 | 0 um | 5 um |
| `pic2d_dd_cd2_scan4ps_a0_5_L_1_t_5um_20260702_r001` | 1367962 | 5 | 1 um | 5 um |
| `pic2d_dd_cd2_scan4ps_a0_10_L_0_t_5um_20260702_r001` | 1367957 | 10 | 0 um | 5 um |
| `pic2d_dd_cd2_scan4ps_a0_10_L_1_t_5um_20260702_r001` | 1367958 | 10 | 1 um | 5 um |
| `pic2d_dd_cd2_scan4ps_a0_20_L_0_t_5um_20260702_r001` | 1367959 | 20 | 0 um | 5 um |
| `pic2d_dd_cd2_scan4ps_a0_20_L_1_t_5um_20260702_r001` | 1367960 | 20 | 1 um | 5 um |

Post-run acceptance checks:

- Parse every case with `tools/analyze_probe_sdf.py Data/*.sdf` and `tools/integrate_probe_sdf.py Data/*.sdf`.
- Check `rear+20 um` latest-window fraction, cumulative mean energy, and cumulative theta RMS.
- Cases failing the `<= 10%` final-window gate should be extended in time before they are used in Stage B.

### pic2d_dd_cd2_scan4ps_a0_10_L_0_t_5um_20260702_r001

- Job ID: `1367957`
- State: `COMPLETED`, exit code `0:0`.
- Runtime: 57 minutes 47 seconds by Slurm.
- Result: failed the accepted-source time-completeness gate at `rear+20 um`.

Selected `rear+20 um` integrated metrics:

| time | window weight | integrated weight | latest-window fraction | window mean E | integrated mean E | window theta RMS | integrated theta RMS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1750 fs | 5.63e14 | 5.63e14 | 1.000 | 4.05 MeV | 4.05 MeV | 8.81 deg | 8.81 deg |
| 2000 fs | 4.55e15 | 5.11e15 | 0.890 | 3.40 MeV | 3.47 MeV | 10.65 deg | 10.47 deg |
| 2250 fs | 2.27e16 | 2.78e16 | 0.816 | 2.81 MeV | 2.93 MeV | 9.94 deg | 10.04 deg |
| 2500 fs | 6.99e16 | 9.77e16 | 0.715 | 2.48 MeV | 2.61 MeV | 10.85 deg | 10.62 deg |
| 2750 fs | 1.26e17 | 2.24e17 | 0.563 | 2.22 MeV | 2.39 MeV | 12.91 deg | 11.97 deg |
| 3000 fs | 1.86e17 | 4.09e17 | 0.453 | 2.02 MeV | 2.22 MeV | 15.47 deg | 13.67 deg |
| 3250 fs | 2.28e17 | 6.37e17 | 0.358 | 1.83 MeV | 2.08 MeV | 18.18 deg | 15.43 deg |
| 3500 fs | 2.51e17 | 8.88e17 | 0.283 | 1.66 MeV | 1.96 MeV | 20.96 deg | 17.18 deg |
| 3750 fs | 2.60e17 | 1.15e18 | 0.226 | 1.51 MeV | 1.86 MeV | 23.58 deg | 18.82 deg |
| 4000 fs | 2.54e17 | 1.40e18 | 0.181 | 1.37 MeV | 1.77 MeV | 25.87 deg | 20.28 deg |

Interpretation:

- The final 250 fs window contributes 18.1% of the integrated `rear+20 um` source weight, above the `<= 10%` gate.
- This case is not accepted for Stage B at 4 ps. A 5 ps extension was submitted as `pic2d_dd_cd2_scan5ps_a0_10_L_0_t_5um_20260703_r001` (Job ID `1377658`).

### pic2d_dd_cd2_scan4ps_a0_20_L_0_t_5um_20260702_r001

- Job ID: `1367959`
- State: `COMPLETED`, exit code `0:0`.
- Runtime: 1 hour 2 minutes 38 seconds by Slurm.
- Result: failed the accepted-source time-completeness gate at `rear+20 um`.

Final `rear+20 um` integrated metrics at 4.0 ps:

| integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---:|---:|---:|---:|
| 1.68e18 | 0.142 | 1.73 MeV | 21.47 deg |

Final-by-probe cross-check at 4.0 ps:

| probe | integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---|---:|---:|---:|---:|
| rear+10 um | 2.86e18 | 0.063 | 1.17 MeV | 28.17 deg |
| rear+20 um | 1.68e18 | 0.142 | 1.73 MeV | 21.47 deg |
| rear+30 um | 8.10e17 | 0.242 | 2.27 MeV | 16.09 deg |
| rear+40 um | 3.04e17 | 0.376 | 2.79 MeV | 12.06 deg |
| rear+50 um | 7.53e16 | 0.554 | 3.34 MeV | 10.06 deg |

High-energy-tail check for the Bosch-Hale upper range:

- Cumulative `rear+20 um` deuteron weight with `E_D > 9.8 MeV`: 1.25e14.
- Cumulative fraction with `E_D > 9.8 MeV`: 7.47e-5.
- High-energy macro-particles above the threshold: 46.
- Interpretation: the above-threshold tail is far below the 1% action threshold for this 4 ps output, so the current Bosch-Hale cutoff is not an immediate blocker for this case. Recheck the accepted 5 ps `a0=20` source before final Stage B production.

The final 250 fs window contributes 14.2% of the integrated `rear+20 um` source weight, above the `<= 10%` gate. This case is not accepted for Stage B at 4 ps. A 5 ps extension was submitted as `pic2d_dd_cd2_scan5ps_a0_20_L_0_t_5um_20260703_r001` (Job ID `1380981`).

### pic2d_dd_cd2_scan4ps_a0_5_L_0_t_5um_20260702_r001

- Job ID: `1367961`
- State: `COMPLETED`, exit code `0:0`.
- Runtime: 1 hour 7 minutes 57 seconds by Slurm.
- Result: failed the accepted-source time-completeness gate at `rear+20 um`.

Final `rear+20 um` integrated metrics at 4.0 ps:

| integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---:|---:|---:|---:|
| 1.19e18 | 0.216 | 1.84 MeV | 19.11 deg |

Final-by-probe cross-check at 4.0 ps:

| probe | integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---|---:|---:|---:|---:|
| rear+10 um | 2.47e18 | 0.100 | 1.18 MeV | 26.49 deg |
| rear+20 um | 1.19e18 | 0.216 | 1.84 MeV | 19.11 deg |
| rear+30 um | 4.27e17 | 0.371 | 2.49 MeV | 13.45 deg |
| rear+40 um | 9.51e16 | 0.571 | 3.15 MeV | 9.79 deg |
| rear+50 um | 9.92e15 | 0.663 | 3.94 MeV | 9.40 deg |

Interpretation:

- The final 250 fs window contributes 21.6% of the integrated `rear+20 um` source weight, above the `<= 10%` gate.
- Although the earlier lower-PPC 4 ps diagnostic passed the time gate, the formal 16/16/8 PPC scan point must be judged on its own output. This case is not accepted for Stage B at 4 ps.
- A 5 ps extension was submitted as `pic2d_dd_cd2_scan5ps_a0_5_L_0_t_5um_20260703_r001` (Job ID `1381095`).

### pic2d_dd_cd2_scan5ps_a0_10_L_0_t_5um_20260703_r001

- Job ID: `1377658`
- State: `COMPLETED`, exit code `0:0`.
- Runtime: 1 hour 18 minutes 55 seconds for the EPOCH core.
- Purpose: source-completion extension for the 4 ps `a0=10, L_pre=0` scan point, which had failed with a final-window fraction of 18.1%.
- Result: accepted for Stage B source generation at `rear+20 um`, integrated from the start through 5.0 ps.

Selected `rear+20 um` integrated metrics:

| time | window weight | integrated weight | latest-window fraction | window mean E | integrated mean E | window theta RMS | integrated theta RMS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4000 fs | 2.54e17 | 1.40e18 | 0.181 | 1.37 MeV | 1.77 MeV | 25.87 deg | 20.28 deg |
| 4250 fs | 2.39e17 | 1.64e18 | 0.146 | 1.25 MeV | 1.70 MeV | 28.00 deg | 21.58 deg |
| 4500 fs | 2.17e17 | 1.86e18 | 0.117 | 1.13 MeV | 1.63 MeV | 29.60 deg | 22.66 deg |
| 4750 fs | 1.93e17 | 2.05e18 | 0.094 | 1.04 MeV | 1.57 MeV | 31.13 deg | 23.59 deg |
| 5000 fs | 1.72e17 | 2.22e18 | 0.077 | 0.95 MeV | 1.53 MeV | 32.52 deg | 24.40 deg |

Final-by-probe cross-check at 5.0 ps:

| probe | integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---|---:|---:|---:|---:|
| rear+10 um | 3.20e18 | 0.030 | 1.09 MeV | 30.34 deg |
| rear+20 um | 2.22e18 | 0.077 | 1.53 MeV | 24.40 deg |
| rear+30 um | 1.36e18 | 0.138 | 1.93 MeV | 19.36 deg |
| rear+40 um | 7.08e17 | 0.219 | 2.34 MeV | 15.09 deg |
| rear+50 um | 2.97e17 | 0.340 | 2.77 MeV | 11.81 deg |

Interpretation:

- The nominal converter-entrance source plane `rear+20 um` passes the time-completeness gate at 5.0 ps: the final 250 fs window is 7.72% of the integrated source weight, below the `<= 10%` threshold.
- The accepted source for this scan point is the concatenated deuteron phase space crossing `rear+20 um` from the start through 5.0 ps, not the 4.0 ps output.
- Farther downstream planes remain incomplete at 5.0 ps and are diagnostics only for this run.

### pic2d_dd_cd2_scan5ps_a0_5_L_0_t_5um_20260703_r001

- Job ID: `1381095`
- State: `COMPLETED`, exit code `0:0`.
- Runtime: 1 hour 14 minutes 33 seconds by Slurm.
- Purpose: source-completion extension for the 4 ps `a0=5, L_pre=0` formal PPC scan point, which had failed with a final-window fraction of 21.6%.
- Result: accepted for Stage B source generation at `rear+20 um`, integrated from the start through 5.0 ps.

Selected `rear+20 um` integrated metrics:

| time | window weight | integrated weight | latest-window fraction | window mean E | integrated mean E | window theta RMS | integrated theta RMS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4000 fs | 2.57e17 | 1.19e18 | 0.216 | 1.48 MeV | 1.84 MeV | 24.12 deg | 19.11 deg |
| 4250 fs | 2.49e17 | 1.43e18 | 0.174 | 1.35 MeV | 1.76 MeV | 26.38 deg | 20.56 deg |
| 4500 fs | 2.33e17 | 1.67e18 | 0.140 | 1.23 MeV | 1.68 MeV | 28.26 deg | 21.80 deg |
| 4750 fs | 2.12e17 | 1.88e18 | 0.113 | 1.12 MeV | 1.62 MeV | 30.03 deg | 22.88 deg |
| 5000 fs | 1.92e17 | 2.07e18 | 0.092 | 1.02 MeV | 1.56 MeV | 31.47 deg | 23.80 deg |

Final-by-probe cross-check at 5.0 ps:

| probe | integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---|---:|---:|---:|---:|
| rear+10 um | 3.10e18 | 0.037 | 1.10 MeV | 30.00 deg |
| rear+20 um | 2.07e18 | 0.092 | 1.56 MeV | 23.80 deg |
| rear+30 um | 1.19e18 | 0.161 | 2.00 MeV | 18.56 deg |
| rear+40 um | 5.77e17 | 0.256 | 2.44 MeV | 14.18 deg |
| rear+50 um | 2.13e17 | 0.394 | 2.91 MeV | 10.85 deg |

Interpretation:

- The nominal converter-entrance source plane `rear+20 um` passes the time-completeness gate at 5.0 ps: the final 250 fs window is 9.25% of the integrated source weight, below the `<= 10%` threshold.
- The accepted source for this scan point is the concatenated deuteron phase space crossing `rear+20 um` from the start through 5.0 ps, not the 4.0 ps output.
- Farther downstream planes remain incomplete at 5.0 ps and are diagnostics only for this run.

### pic2d_dd_cd2_scan5ps_a0_20_L_0_t_5um_20260703_r001

- Job ID: `1380981`
- State: `COMPLETED`, exit code `0:0`.
- Runtime: 1 hour 26 minutes 15 seconds by Slurm.
- Purpose: source-completion extension for the 4 ps `a0=20, L_pre=0` scan point, which had failed with a final-window fraction of 14.2%.
- Result: accepted for Stage B source generation at `rear+20 um`, integrated from the start through 5.0 ps.

Selected `rear+20 um` integrated metrics:

| time | window weight | integrated weight | latest-window fraction | window mean E | integrated mean E | window theta RMS | integrated theta RMS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4000 fs | 2.39e17 | 1.68e18 | 0.142 | 1.26 MeV | 1.73 MeV | 27.98 deg | 21.47 deg |
| 4250 fs | 2.17e17 | 1.89e18 | 0.115 | 1.14 MeV | 1.66 MeV | 29.62 deg | 22.55 deg |
| 4500 fs | 1.94e17 | 2.09e18 | 0.093 | 1.04 MeV | 1.60 MeV | 31.05 deg | 23.47 deg |
| 4750 fs | 1.71e17 | 2.26e18 | 0.076 | 0.95 MeV | 1.55 MeV | 32.26 deg | 24.25 deg |
| 5000 fs | 1.50e17 | 2.41e18 | 0.062 | 0.87 MeV | 1.51 MeV | 33.35 deg | 24.91 deg |

Final-by-probe cross-check at 5.0 ps:

| probe | integrated weight | latest-window fraction | integrated mean E | integrated theta RMS |
|---|---:|---:|---:|---:|
| rear+10 um | 3.31e18 | 0.024 | 1.11 MeV | 30.59 deg |
| rear+20 um | 2.41e18 | 0.062 | 1.51 MeV | 24.91 deg |
| rear+30 um | 1.56e18 | 0.111 | 1.88 MeV | 20.04 deg |
| rear+40 um | 9.03e17 | 0.173 | 2.26 MeV | 16.03 deg |
| rear+50 um | 4.46e17 | 0.261 | 2.65 MeV | 12.82 deg |

High-energy-tail check for the Bosch-Hale upper range:

- Cumulative `rear+20 um` deuteron weight with `E_D > 9.8 MeV`: 1.25e14.
- Cumulative fraction with `E_D > 9.8 MeV`: 5.20e-5.
- High-energy macro-particles above the threshold: 46.
- Interpretation: the accepted 5 ps source remains far below the 1% action threshold for the Bosch-Hale upper-range cutoff. The current cutoff is not a blocker for this accepted source.

Interpretation:

- The nominal converter-entrance source plane `rear+20 um` passes the time-completeness gate at 5.0 ps: the final 250 fs window is 6.22% of the integrated source weight, below the `<= 10%` threshold.
- The accepted source for this scan point is the concatenated deuteron phase space crossing `rear+20 um` from the start through 5.0 ps, not the 4.0 ps output.
- Farther downstream planes remain incomplete at 5.0 ps and are diagnostics only for this run.

## L_pre=1 4 ps Scan Timeout Incident

The three first-scan `L_pre=1 um` jobs were submitted with a 4 hour Slurm walltime and all reached that walltime before finishing. These partial outputs are not accepted as Stage B sources.

| run_id | job_id | state | elapsed | last reported simulation time | last ETA before timeout | estimated cost at 0.1 CNY/core-hour |
|---|---:|---|---:|---:|---:|---:|
| `pic2d_dd_cd2_scan4ps_a0_5_L_1_t_5um_20260702_r001` | 1367962 | TIMEOUT | 4:00:09 | 3.41 ps | 0:41:10 | 64.04 CNY |
| `pic2d_dd_cd2_scan4ps_a0_10_L_1_t_5um_20260702_r001` | 1367958 | TIMEOUT | 4:00:09 | 2.96 ps | 1:23:48 | 64.04 CNY |
| `pic2d_dd_cd2_scan4ps_a0_20_L_1_t_5um_20260702_r001` | 1367960 | TIMEOUT | 4:00:10 | 2.73 ps | 1:49:10 | 64.04 CNY |

Cost note:

- These three timed-out runs consumed about 1,921 core-hours, or about 192 CNY at 0.1 CNY/core-hour, without producing accepted source outputs.
- The partial SDF/probe files may be used only for rough trend inspection and runtime estimation. They must not be used as accepted physics sources.

Process correction:

- Do not submit production PIC scans with an optimistic hard walltime. Set walltime from observed EPOCH ETA plus safety margin, or run a short benchmark first.
- The first-scan config now marks walltime as required per submission, and the renderer no longer has a walltime default. It refuses to render Slurm files unless `--hours` is provided explicitly.
- Future `L_pre=1` reruns should either use at least 8 h walltime or first benchmark a higher-rank run to prove the higher rank count reduces wall-clock time enough to justify its cost.
