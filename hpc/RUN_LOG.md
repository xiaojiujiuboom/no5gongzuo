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

Submission walltime policy:

- For expensive 3D PIC jobs, do not set Slurm walltime close to the runtime
  estimate. Use a generous upper bound, typically about `2x` the estimate and
  at least `4-6 h` above it for production-like runs.
- The scheduler walltime is an upper limit, not a request to keep billing after
  the program exits. A larger limit can increase queue wait, but it prevents a
  much worse failure mode: a hard scheduler kill just before EPOCH writes the
  restartable final dump.
- Pair long Slurm limits with EPOCH `stop_at_walltime` set safely before the
  Slurm limit, so EPOCH can stop through its normal path and force an output
  instead of being killed. For an `18:00:00` Slurm job, use about
  `stop_at_walltime = 61200.0` seconds (`17 h`).

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

## pic3d_stage1_source_diag3000fs_finalrestart_2000x250x250_a0_10_t_3um_20260704_r001

- Purpose: 3 ps Stage 1 source-plane diagnostic with `rear+10 um` as the
  preferred source-plane candidate, while retaining `rear+2/5/15/20 um` probes
  to answer sheath-region and far-plane reviewer questions.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag3000fs_finalrestart_2000x250x250_a0_10_t_3um_20260704_r001`
- Job ID: `1631093`
- State after submission: `PENDING`.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime
  `8:00:00`.
- Cost cap at full walltime: `4096` core-hours, about `409.6 CNY` at
  `0.1 CNY/core-hour`.
- Expected runtime/cost from the completed 1.5 ps benchmark: about `5.6 h`
  plus final restart I/O, roughly `290-330 CNY`.
- Submitted input:
  `hpc/templates/epoch3d_stage1_source_diag_3ps_final_restart.deck`
- Key settings:
  - `nx,ny,nz = 2000,250,250`
  - `nprocx,nprocy,nprocz = 32,4,4`
  - `t_end = 3000 fs`, `dt_snapshot = 250 fs`
  - future submissions should use a much wider Slurm walltime, e.g.
    `18:00:00`, with `stop_at_walltime = 61200.0` seconds so EPOCH can stop
    inside its own normal output path before a scheduler kill
  - PPC `electron/deuteron/carbon = 16/32/4`
  - deuteron probes at `rear+2/5/10/15/20 um`
  - particle probes and deuteron distribution function only
  - `full_dump_every = -1`, `restart_dump_every = -1`
  - `force_final_to_be_restartable = T`
- Restart note:
  - This run writes no intermediate restart dumps. If it reaches `t_end` and
    writes the final dump successfully, that final SDF should be restartable and
    can be used to extend the same run to `4 ps` without starting from `0`.
  - If the job is killed before `t_end`, there is no intermediate restart point.
  - While Job `1631093` was already running, an attempted Slurm TimeLimit
    extension to `10:00:00` returned `Access/permission denied`; ordinary user
    permissions cannot raise the walltime of the active job. The submitted deck
    also cannot inherit the newly added `stop_at_walltime` guard because EPOCH
    reads this value at startup. Future long runs should use a walltime far
    above the estimate and keep an EPOCH stop guard before the Slurm limit.
  - During runtime, the shrinking walltime margin showed that the final
    restartable dump might not have enough time to complete safely. EPOCH source
    inspection confirmed that an empty `Data/DUMP` file requests a restartable
    dump without stopping the job. A `Data/DUMP` request was therefore issued
    while the run was near `1.61 ps`. It produced `Data/0006.sdf` of about
    `17G`; `Data/restart.visit` points to `0006.sdf`, giving a usable
    continuation point around `1.63 ps` even if the 3 ps run later hits the
    Slurm walltime.
- Final state update:
  - The run was intentionally cancelled after the restartable `0006.sdf`
    checkpoint was complete, instead of gambling on the shrinking 8 h walltime
    margin.
  - Slurm state: `CANCELLED by 11003861`; elapsed `04:25:08`.
  - Continuation is handled by
    `pic3d_stage1_source_diag3000fs_restart0006_2000x250x250_a0_10_t_3um_20260704_r002`.
- Acceptance checks after completion:
  - `D_rear10` should have enough cumulative macro-particles for stable
    spectrum/angle statistics.
  - The final-window fraction should fall below about `5-10%` for the chosen
    source plane, or the run should be extended from the final restart.
  - Compare `rear+5` to `rear+10`: if spectrum and angular RMS are stable, use
    `rear+10` or the closest stable plane as the Stage 2 source.
  - Check `rear+15/20` only to justify that a farther plane is not required, or
    to decide whether a 4 ps continuation is needed.

## pic3d_stage1_source_diag3000fs_restart0006_2000x250x250_a0_10_t_3um_20260704_r002

- Purpose: continuation of the 3 ps Stage 1 source diagnostic from the
  restartable checkpoint `Data/0006.sdf` written during Job `1631093`.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag3000fs_restart0006_2000x250x250_a0_10_t_3um_20260704_r002`
- Job ID: `1666070`.
- Final state: `FAILED`, exit code `16:0`, elapsed `00:00:15`.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime
  `18:00:00`.
- Restart setup:
  - `Data/0006.sdf` is a symlink to the completed checkpoint in the previous
    run directory, avoiding an unnecessary 17 GB copy.
  - The continuation deck adds `restart_snapshot = 6`.
  - It keeps `t_end = 3000 fs`, so EPOCH should continue from about `1.63 ps`
    to `3.0 ps` rather than restarting from zero.
  - It adds `stop_at_walltime = 61200.0` seconds for an EPOCH-controlled stop
    before the 18 h Slurm limit.
- Rationale:
  - Cancelling Job `1631093` after a verified restartable dump avoids risking
    a hard 8 h walltime kill during the final restart write.
  - The cost already spent is not wasted because the continuation starts from
    the saved checkpoint.
- Failure diagnosis:
  - EPOCH started but aborted before physics with
    `SDF file Data/ is not a restart dump. Unable to continue.`
  - The checkpoint itself is valid: a small SDF header checker read
    `Data/0006.sdf` as `code=Epoch3d`, `step=33470`,
    `time=1.6329268104815327e-12`, `restart_flag=1`.
  - The failure is therefore the numeric restart deck syntax
    `restart_snapshot = 6`, not a corrupt checkpoint.
  - The next continuation run uses explicit filename syntax
    `restart_snapshot = 0006.sdf`.

## pic3d_stage1_source_diag3000fs_restart0006file_2000x250x250_a0_10_t_3um_20260704_r003

- Purpose: corrected continuation from the verified restartable checkpoint
  `Data/0006.sdf`, using explicit filename restart syntax.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag3000fs_restart0006file_2000x250x250_a0_10_t_3um_20260704_r003`
- Job ID: `1676859`.
- Final state: `COMPLETED`, exit code `0:0`.
- Runtime: Slurm elapsed `03:40:55`; EPOCH core runtime `3 hours, 27 minutes,
  54.45 seconds`.
- Approximate cost: `1885` core-hours, about `188.5 CNY` at
  `0.1 CNY/core-hour`. The combined r001/r002/r003 cost through 3 ps is about
  `415 CNY`.
- Submission note: the pending job was updated in place from `18:00:00` to
  `10:00:00` walltime to improve scheduling while still leaving more than `2x`
  the expected continuation runtime.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime
  `10:00:00`.
- Restart setup:
  - `Data/0006.sdf` is symlinked to the completed checkpoint in r001.
  - The continuation deck uses `restart_snapshot = 0006.sdf`.
  - `t_end = 3000 fs` remains unchanged.
  - `stop_at_walltime = 32400.0` seconds (`9 h`) is used as a guard before the
    10 h Slurm limit.
- Completion checks:
  - Restart succeeded: EPOCH printed `Load from restart dump OK` and continued
    from `time = 1.6329268104815327 ps`.
  - Final file `Data/0012.sdf` has `time = 3.0000090380444037 ps`,
    `step = 61491`, `restart_flag = 1`, and about `17G` size.
  - Output files in the continuation directory are `0007.sdf` through
    `0012.sdf`; `0012.sdf` is a restartable final dump suitable for another
    continuation.
  - Small analysis artifacts were copied locally under `hpc/results/`:
    - `pic3d_stage1_diag3000fs_restart_20260705_sdf_block_summary.csv`
    - `pic3d_stage1_diag3000fs_restart_20260705_probe_metrics.csv`
    - `pic3d_stage1_diag3000fs_restart_20260705_probe_cumulative_summary.csv`
- 3 ps source-plane decision:
  - `rear+10` is not yet a converged source at 3 ps. Its final 250 fs window
    contributes about `54.5%` of cumulative probe weight.
  - Other final-window fractions are also too high: `rear+5` about `39.4%`,
    `rear+15` about `50.9%`, and `rear+20` about `73.8%`.
  - The late windows are lower energy, but using this as a final source would
    be hard to defend under the pre-set `5-10%` convergence criterion.
  - Decision: extend from the restartable 3 ps final dump. The first extension
    was prepared as a 4 ps job, then updated in place to 5 ps before it started
    after user direction.

## pic3d_stage1_source_diag4000fs_restart0012file_2000x250x250_a0_10_t_3um_20260705_r004

- Purpose: 5 ps continuation of the Stage 1 source-plane diagnostic because
  the 3 ps rear-plane probe windows are not time-converged. The remote run
  directory name still contains `4000fs` because the pending job was updated in
  place before start rather than cancelled and resubmitted.
- Remote run directory:
  `~/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag4000fs_restart0012file_2000x250x250_a0_10_t_3um_20260705_r004`
- Job ID: `1721080`.
- State after update: `PENDING`.
- Job name after update: `no5_s1_3d_5ps`.
- Slurm: partition `amd_m9_768`, `2` nodes, `512` MPI ranks, walltime
  `10:00:00`.
- Restart setup:
  - `Data/0012.sdf` is symlinked to r003's completed restartable final dump.
  - SDF header check before submission: `restart_flag = 1`,
    `time = 3.0000090380444037 ps`.
  - The continuation deck uses `restart_snapshot = 0012.sdf`.
  - `t_end = 5000 fs`.
  - `stop_at_walltime = 32400.0` seconds (`9 h`) guards the 10 h Slurm limit.
- Runtime estimate:
  - Based on r003, continuing from 3 ps to 5 ps should take roughly `5.5-6 h`
    plus final restart I/O, within the `10 h` walltime.
- 2026-07-05 status update:
  - Before allocation, the job was put on user hold with
    `scontrol hold 1721080`; Slurm now reports `PENDING (JobHeldUser)`.
  - Reason: the 3 ps probe data show a potentially more important physics
    issue than source-time completeness. The energetic deuterons arrive early,
    while later windows are lower energy; extending to 5 ps mostly adds slow
    low-energy deuterons and is unlikely to create a missing multi-MeV tail.
  - The hold is reversible. Before releasing or replacing this continuation,
    reassess whether the current `a0=10`, `3 um` solid-CD2, no-preplasma 3D
    setup is energetic enough for the DD-neutron / Li-TPR objective.
- 2026-07-05 release update:
  - After discussion, the project keeps the solid-CD2 baseline rather than
    switching immediately to a foam/CSA route.
  - Rationale: sub-MeV to MeV deuterons are not useless for the present
    workflow; forward D-D neutrons can still exceed the `7Li(n,n'T)` threshold,
    although the total yield may be lower than a tens-of-MeV deuteron source.
  - The 5 ps continuation is therefore needed for source completeness, not for
    increasing the deuteron energy. At 3 ps, the latest probe windows still
    contribute too much of the cumulative source weight, especially at
    `rear+10/15/20`.
  - The job was released with `scontrol release 1721080` and returned to
    pending scheduling.
- 2026-07-05 DD-yield-weighted correction:
  - The earlier final-window fractions were particle-weight fractions, not
    DD-yield-weighted fractions. A dedicated SDF/C reader was added to compute
    per-probe-window `sum(weight * Y_DDn(E))`, using the current Stage 2
    `D(d,n)3He` thick-target yield kernel from `moduleB_source/thick_target.py`.
  - This is the correct convergence diagnostic for the Stage 2 neutron branch
    under the current provisional CD2 stopping table; it is still not the final
    absolute-yield model.

| probe | last-window particle-weight fraction | last-window DD(n)-yield fraction | cumulative weighted mean E | observed Emax |
|---|---:|---:|---:|---:|
| rear+2 um | 27.1% | 31.9% | 0.159 MeV | 1.00 MeV |
| rear+5 um | 39.4% | 38.0% | 0.210 MeV | 1.09 MeV |
| rear+10 um | 54.5% | 40.5% | 0.370 MeV | 1.31 MeV |
| rear+15 um | 50.9% | 34.6% | 0.550 MeV | 1.35 MeV |
| rear+20 um | 73.8% | 62.1% | 0.827 MeV | 1.37 MeV |

  - Interpretation: yield weighting reduces the apparent late-window
    importance because the late deuterons are generally lower energy, but the
    3 ps source is still not accepted under the `5-10%` yield-convergence gate.
    The 5 ps continuation remains justified as a source-completeness run.
- 2026-07-05 rear+10 phase-space check:
  - Because the `rear+10` DD(n)-weighted window contribution rebounded at
    `3 ps`, a point-probe phase-space extractor was added to read the probe
    crossing positions, momenta, weights, energy, and angles.
  - Checked `D_rear10` windows at `2500`, `2750`, and `3000 fs`.
  - Artifacts:
    - `hpc/results/pic3d_stage1_rear10_phase_space_2500_3000fs.png`
    - `hpc/results/pic3d_stage1_rear10_phase_space_2500_3000fs_marginals.png`
    - `hpc/results/pic3d_stage1_rear10_phase_space_2500_3000fs_summary.csv`

| time | weight | E_mean | E_p95 | Emax | theta_p90 | theta<20deg | r_p90 | r<5um |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2500 fs | 3.95e9 | 0.395 MeV | 0.513 MeV | 0.704 MeV | 15.0 deg | 97.9% | 3.86 um | 96.8% |
| 2750 fs | 7.79e9 | 0.354 MeV | 0.485 MeV | 0.698 MeV | 16.8 deg | 96.5% | 5.43 um | 85.6% |
| 3000 fs | 1.95e10 | 0.335 MeV | 0.500 MeV | 0.797 MeV | 19.4 deg | 91.4% | 6.31 um | 75.4% |

  - Interpretation: the `3 ps` rebound is not a narrow clean-beam tail. It is a
    second, broader forward deuteron wave/plume reaching `rear+10`: transverse
    size and angular spread both grow from `2.5` to `3.0 ps`.
  - It is still dominantly forward at `rear+10` (`91%` of the weight remains
    within `20 deg` at `3 ps`), so it is not random backward plasma. However,
    calling `rear+10` a clean detached beam would be too strong. The 5 ps
    continuation should be used to decide whether a farther/cleaner plane such
    as `rear+15` or `rear+20` is preferable for Stage 2, or whether the physical
    converter is intentionally modeled as being close enough to intercept this
    expanding plume.
- 2026-07-05 Stage B/C chain smoke from 3 ps `rear+10`:
  - Built a gated deuteron source from all `D_rear10` probe windows through
    `3 ps`, with `E_D > 0.4 MeV`.
  - PIC +x was mapped to the downstream +z convention used by Stage B/C:
    `dir = (py, pz, px) / |p|`.
  - Local outputs:
    - `outputs/pic3d_3ps_rear10_Egt0p4/deuteron_beam.h5`
    - `outputs/pic3d_3ps_rear10_Egt0p4/neutron_source.h5`
    - `outputs/pic3d_3ps_rear10_Egt0p4/openmc_case_A_li6_90/`
    - `outputs/pic3d_3ps_rear10_Egt0p4/openmc_case_B_li6_90/`
  - Small committed summaries:
    - `hpc/results/pic3d_3ps_rear10_Egt0p4_chain_summary.csv`
    - `hpc/results/pic3d_3ps_rear10_Egt0p4_openmc_case_comparison_li6_90.csv`
    - `hpc/results/pic3d_3ps_rear10_Egt0p4_openmc_case_comparison_li6_7p59.csv`
    - `hpc/results/pic3d_3ps_rear10_Egt0p4_case_B_source_stats.csv`

| stage | key result |
|---|---:|
| gated deuteron source | 46,358 macro-D, weight 1.18e10 D/shot |
| gated deuteron energy | weighted mean 0.492 MeV, max 1.307 MeV |
| Stage B neutron source | 8.35e4 n/shot in the current CD2 D(d,n) model |
| Stage B neutron spectrum | weighted mean 2.644 MeV, max 4.084 MeV |
| Stage B threshold tail | 35.6% of neutron weight above 2.82 MeV |
| OpenMC Case A Li6 TPR | 1.283e-1 per source neutron |
| OpenMC Case A Li7 TPR | 0, as expected for 2.45 MeV ideal source |
| OpenMC Case B Li6 TPR | 1.298e-1 per source neutron |
| OpenMC Case B Li7 TPR | 8.317e-6 per source neutron |

  - Verification:
    - `python tests/test_gates.py` passed.
    - `moduleB_source/build_source.py` completed with the real PIC-derived
      `deuteron_beam.h5`.
    - OpenMC 0.15.0 Case A and Case B both ran with
      `20 batches x 50,000 particles` using
      `/Users/oomb/Downloads/mcnp_endfb71/cross_sections.xml`.
    - `TPR_Li6` and `TPR_Li7` separated tallies were produced.
  - Natural-lithium (`Li6=7.59 at%`) A/B was also run with the same source and
    statistics. Results:
    - Case A: `TPR_Li6 = 1.120e-2`, `TPR_Li7 = 0`.
    - Case B: `TPR_Li6 = 1.074e-2`, `TPR_Li7 = 7.147e-5`.
  - Boundary: this smoke uses the currently implemented CD2 `D(d,n)3He`
    neutron branch only. The direct `D(d,p)T` triton branch and TiD2 converter
    baseline remain planned implementation work before final physics claims.

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

## Li7 MT205 / H3-production Nuclear-Data Check

Date: 2026-07-05.

Purpose:

- Replace the older informal `>2.82 MeV` Li7 threshold wording with the actual
  OpenMC HDF5 tally threshold used by the current calculations.
- Confirm what OpenMC `H3-production` means for `Li7`, and whether it can be
  described as a pure single `(n,n'alpha)T` channel.
- Run the same natural-lithium Case A/B OpenMC smoke case with four nuclear-data
  libraries to estimate the `Li7` tritium-production library spread.

Findings from the HDF5 data:

- In all four checked libraries, `Li7/reactions/reaction_205` has
  `mt = 205`, `label = (n,Xt)`, and `redundant = 1`.
- The 294 K MT205 cross section starts at `3.1454 MeV` in all four checked
  `Li7.h5` files.
- The maximum tabulated MT205 cross section in these checked files is
  approximately `0.3805 barn` at `7.5 MeV`.
- Interpretation: OpenMC `H3-production` is a total tritium-production score.
  For `Li7` it maps to MT205 `(n,Xt)` in these HDF5 libraries, not an exclusive
  single-channel tally. In the few-MeV `Li7` threshold region it is physically
  dominated by the threshold tritium-production channel, so the paper should say
  "total tritium production, dominated by `7Li(n,n'alpha)T`" rather than claiming
  an exclusive `(n,n'alpha)T` tally.

PIC-derived source statistic with the corrected threshold:

| source | value |
|---|---:|
| `neutron_source.h5` particles | 46,358 |
| `Y_total` | 8.3513e4 n/shot |
| weighted mean energy | 2.6441 MeV |
| max energy | 4.0840 MeV |
| weight fraction above 3.1454 MeV | 0.13736 |
| weight fraction above 3.1454 MeV and `mu > 0.8` | 0.08877 |

Four-library natural-lithium Case B `Li7` results:

| library | `TPR_Li7` per source neutron | relative error |
|---|---:|---:|
| `endfb71_lanl` | 7.147324e-05 | 0.004220 |
| `fendl32` | 7.147632e-05 | 0.004221 |
| `endfb80` | 7.144851e-05 | 0.004216 |
| `jeff33` | 7.147632e-05 | 0.004221 |

Library spread summary:

- Mean `TPR_Li7`: `7.146860e-05` per source neutron.
- Min/max: `7.144851e-05` to `7.147632e-05`.
- Relative half range: `1.9458e-4`, i.e. about `0.0195%`.
- The library spread is much smaller than the current Monte Carlo statistical
  uncertainty for this smoke case.
- Case A `Li7` remains exactly zero in the OpenMC tallies, as expected because
  the ideal 2.45 MeV D-D source is below the 3.1454 MeV MT205 threshold.

Path-switch verification:

- The four libraries did switch to four distinct `Li7.h5` files. Their sizes and
  SHA-256 prefixes differ:
  - `endfb71_lanl`: `/Users/oomb/Downloads/mcnp_endfb71/Li7.h5`,
    `sha256[:16] = 0aff92a1da5b7c5f`.
  - `fendl32`: `/Volumes/billboom/openmc_data/libs/fendl32/neutron/Li7.h5`,
    `sha256[:16] = f261968904018a39`.
  - `endfb80`: `/Volumes/billboom/openmc_data/libs/endfb80/neutron/Li7.h5`,
    `sha256[:16] = a2a5a7a5901628c7`.
  - `jeff33`: `/Volumes/billboom/openmc_data/libs/jeff33/Li7.h5`,
    `sha256[:16] = f8ca454e45fb5ff3`.
- However, the MT205 cross section itself is identical in the source-relevant
  near-threshold region:

| library | sigma(3 MeV) b | sigma(4 MeV) b | sigma(5 MeV) b | sigma(20 MeV) b |
|---|---:|---:|---:|---:|
| `endfb71_lanl` | 0 | 0.03728221 | 0.101351 | 0.1951517 |
| `fendl32` | 0 | 0.03728221 | 0.101351 | 0.11756144 |
| `endfb80` | 0 | 0.03728221 | 0.101351 | 0.1951517 |
| `jeff33` | 0 | 0.03728221 | 0.101351 | 0.1951517 |

- Dense interpolation over `3.1454-20 MeV` shows essentially zero spread from
  threshold through 14 MeV, and the first large spread appears near 20 MeV
  where FENDL-3.2 is lower.
- Therefore the `~0.02%` Case B `Li7` library spread is not a fake path-switch
  artifact. It is a consequence of this specific PIC-DD source reaching only
  `4.084 MeV`, which samples the near-threshold interval where the checked
  libraries use the same MT205 curve.
- Paper wording should be: "For the present source, which populates only the
  3.1-4.1 MeV `Li7` threshold window, the checked libraries give nearly
  identical MT205 tritium production. Larger library separation exists at much
  higher neutron energies and is not probed by this source."

Generated local result files:

- `hpc/results/pic3d_3ps_rear10_Egt0p4_li7_mt205_xs_libraries.csv`
- `hpc/results/pic3d_3ps_rear10_Egt0p4_li7_mt205_library_summary.csv`
- `hpc/results/pic3d_3ps_rear10_Egt0p4_li7_mt205_point_check.csv`
- `hpc/results/pic3d_3ps_rear10_Egt0p4_li7_mt205_xs_with_neutron_spectrum.png`
- `hpc/results/pic3d_3ps_rear10_Egt0p4_li7_tpr_library_uncertainty.csv`
- `hpc/results/pic3d_3ps_rear10_Egt0p4_li7_tpr_library_uncertainty_band.csv`
- `hpc/results/pic3d_3ps_rear10_Egt0p4_li7_tpr_library_uncertainty.png`

Verification:

- `python tests/test_gates.py` passed after the threshold constant was moved to
  `moduleC_openmc/nuclear_data.py`.
- FENDL-3.2, ENDF/B-VIII.0, and JEFF-3.3 clean OpenMC reruns completed with no
  missing-library warnings after full extraction.

## Rear+10 3 ps vs 4 ps Normalized Spectrum Check

Date: 2026-07-05.

Purpose:

- Compare the normalized source-spectrum shape at `rear+10` between the
  accepted 0-3 ps source and the partial 0-4 ps source.
- Avoid using raw particle-count growth as a convergence criterion. The primary
  comparison weights each deuteron by `weight * Y_DD(E)`, where `Y_DD(E)` is the
  same thick-target D-D yield model used in Stage B.

Inputs:

- 0-3 ps phase-space CSVs:
  `hpc/results/phase_space/rear10_0to3ps/*_D_rear10_phase.csv`.
- 3-4 ps phase-space CSVs extracted from Job `1721080`,
  `Data/0013.sdf` through `Data/0016.sdf`, using
  `sdf_probe_phase_space_extract`.
- Main Stage B source gate: `px > 0`, `E_D > 0.4 MeV`.

Main `E_D > 0.4 MeV` result:

| source | metric | total | mean E MeV | p50 MeV | p90 MeV | p95 MeV | p99 MeV | max MeV |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0-3 ps | D-D yield weighted | 8.3513e4 | 0.5386 | 0.4937 | 0.6947 | 0.7929 | 0.9839 | 1.3073 |
| 3-4 ps only | D-D yield weighted | 6.1439e5 | 0.4892 | 0.4655 | 0.5752 | 0.6098 | 0.6818 | 0.8924 |
| 0-4 ps | D-D yield weighted | 6.9790e5 | 0.4951 | 0.4681 | 0.5856 | 0.6277 | 0.7452 | 1.3073 |

Shape metrics for normalized `Y_DD(E)`-weighted spectra, 0-3 ps vs 0-4 ps:

- L1 distance: `0.27635`.
- Total-variation distance: `0.13818`.
- Jensen-Shannon distance: `0.18601`.
- Cosine similarity: `0.98548`.

Interpretation:

- The 3-4 ps contribution is not a newly growing high-energy tail. It is a
  softer late population: its `Y_DD`-weighted `p99` is only `0.6818 MeV`, and
  no `E_D > 1 MeV` particles were seen in that added window.
- However, for the `E_D > 0.4 MeV` accepted-source gate, the 3-4 ps window still
  contributes `88.0%` of the 0-4 ps D-D-yield-weighted total. Therefore 3 ps is
  not a good final normalization time for absolute yield.
- The 0-4 ps normalized shape is already close to the 0-3 ps shape in cosine
  similarity, but it is measurably shifted toward lower energies. The 5 ps
  continuation is justified to determine whether the late soft component is
  saturating.

All-energy sanity check:

- Without the `E_D > 0.4 MeV` gate, the same conclusion holds more strongly:
  the 3-4 ps contribution carries `90.7%` of the 0-4 ps D-D-yield-weighted
  total, but is softer than the 0-3 ps distribution.
- The all-energy 0-3 ps vs 0-4 ps `Y_DD`-weighted total-variation distance is
  `0.14419`, and cosine similarity is `0.97327`.

Generated files:

- `hpc/tools/compare_rear10_spectrum_3ps_4ps.py`
- `hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_normalized_spectrum.csv`
- `hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_spectrum_summary.csv`
- `hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_normalized_spectrum.png`
- `hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_allE_normalized_spectrum.csv`
- `hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_allE_spectrum_summary.csv`
- `hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_allE_normalized_spectrum.png`

## Rear+10 5 ps D-D Yield-Weighted Convergence Check

Date: 2026-07-05 / 2026-07-06 CST on BSCC.

Run:

- Remote directory:
  `/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag4000fs_restart0012file_2000x250x250_a0_10_t_3um_20260705_r004`.
- Slurm Job `1721080`, `amd_m9_768`, 2 nodes / 512 ranks.
- Completed normally in `04:48:07`, exit code `0:0`.
- Final restartable dump: `Data/0020.sdf`, time `5.000015 ps`, size about
  `14G`.
- Peak memory reported by `sacct` was about `342 GB`, comfortably below the
  768 GB node memory envelope for the two-node run.

Method:

- Use `sdf_probe_dd_yield_metrics` directly on SDF probe blocks, avoiding large
  CSV extraction where possible.
- The tool now supports `--e-min-MeV value`; this was used to compute both
  all-energy and Stage-B-gated (`E_D >= 0.4 MeV`) D-D-yield-weighted window
  contributions.
- Decision criterion remains: do not accept a final source time for absolute
  yield if the final 250 fs window contributes more than about `10%` of the
  cumulative D-D-yield-weighted total.

Rear+10 `E_D >= 0.4 MeV` result:

| interval | D-D-yield-weighted contribution |
|---|---:|
| 0-3 ps | 8.3513e4 |
| 3-4 ps | 6.1439e5 |
| 4-5 ps | 1.1987e6 |
| 0-5 ps total | 1.8966e6 |
| 4.75-5.00 ps final window | 2.7904e5 |

Fractions:

- 3-4 ps fraction of 0-5 ps: `32.4%`.
- 4-5 ps fraction of 0-5 ps: `63.2%`.
- Final 250 fs fraction of 0-5 ps: `14.7%`.
- Final 250 fs fraction of the 4-5 ps increment: `23.3%`.

All-energy sanity check:

- 4-5 ps fraction of 0-5 ps: `65.5%`.
- Final 250 fs fraction of 0-5 ps: `16.6%`.

Interpretation:

- 5 ps is not accepted as the final source-collection time for absolute yield.
  The final window is smaller than the earlier 4-5 ps windows, but still above
  the 10% acceptance target.
- The late population is still soft. For `E_D >= 0.4 MeV`, the 4-5 ps windows
  have mean energies around `0.466-0.470 MeV`, with max energies below
  `0.95 MeV` at rear+10; this is not a newly growing high-energy tail.
- Because `Data/0020.sdf` is restartable, the correct response is a minimal
  restart continuation rather than rerunning 0-5 ps.

Continuation submitted:

- New remote directory:
  `/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag6000fs_restart0020file_2000x250x250_a0_10_t_3um_20260706_r005`.
- Slurm Job `1837542`, submitted to `amd_m9_768`, 2 nodes / 512 ranks.
- `restart_snapshot = 0020.sdf`, `t_end = 6000 fs`,
  `dt_snapshot = 250 fs`, final dump restartable.
- Walltime set to `8:00:00`; `stop_at_walltime = 25200 s`.

Update:

- Job `1837542` failed after `00:00:30` while loading the `Data/0020.sdf`
  restart through a symlink. Error: `MPI_ERR_TRUNCATE` from MPI-IO on
  `Data/0020.sdf`.
- Header check on the source `Data/0020.sdf` remains valid:
  `restart_flag=1`, `time=5.000015 ps`, `nblocks=71`. Therefore the current
  working assumption is an MPI-IO/path issue, not a corrupt 5 ps restart file.
- Retry Job `1837996` was submitted in
  `/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag6000fs_restart0020hardlink_2000x250x250_a0_10_t_3um_20260706_r006`,
  using a hard link to the same `Data/0020.sdf` instead of a symlink.
- Expected wall-clock after allocation is about `2.3-2.7 h`, based on the
  observed 3 ps to 5 ps continuation timing.

Generated files:

- `hpc/results/pic3d_stage1_rear10_5ps_dd_yield_windows.csv`
- `hpc/results/pic3d_stage1_rear10_5ps_dd_yield_convergence_summary.csv`

## Rear+10 4 ps vs 5 ps Normalized Spectrum Check

Date: 2026-07-05 / 2026-07-06 CST.

Purpose:

- Determine whether extending the cumulative source from 4 ps to 5 ps changes
  the normalized spectral shape, or mainly increases the absolute normalization.
- Primary comparison is `rear+10`, `E_D >= 0.4 MeV`, `weight * Y_DD(E)`
  normalized energy spectra.

Method:

- Added `sdf_probe_energy_hist`, a C SDF tool that bins probe-particle energy
  directly from SDF files without exporting multi-GB phase-space CSVs.
- The 4-5 ps increment was histogrammed from `Data/0017.sdf` through
  `Data/0020.sdf`.
- The 0-4 ps raw histograms were reconstructed from the existing 0-4 ps
  normalized spectrum and its stored total weights.

Main `E_D >= 0.4 MeV` result:

| source | metric | total | mean E MeV | p50 MeV | p90 MeV | p95 MeV | p99 MeV |
|---|---|---:|---:|---:|---:|---:|---:|
| 0-4 ps | D-D yield weighted | 6.9790e5 | 0.4953 | 0.4681 | 0.5856 | 0.6277 | 0.7452 |
| 4-5 ps only | D-D yield weighted | 1.1987e6 | 0.4889 | 0.4635 | 0.5766 | 0.6142 | 0.6897 |
| 0-5 ps | D-D yield weighted | 1.8966e6 | 0.4913 | 0.4652 | 0.5800 | 0.6193 | 0.7069 |

Shape metrics for normalized `Y_DD(E)`-weighted spectra, 0-4 ps vs 0-5 ps:

- L1 distance: `0.03321`.
- Total-variation distance: `0.01660`.
- Jensen-Shannon distance: `0.02880`.
- Cosine similarity: `0.99962`.

Interpretation:

- The normalized `E_D >= 0.4 MeV` source spectrum is effectively stable by
  5 ps. The 4-5 ps-only spectrum nearly overlaps the 0-4 ps and 0-5 ps spectra.
- The late contribution is still soft: the 4-5 ps-only `Y_DD`-weighted `p99`
  is `0.6897 MeV`, and it does not add an `E_D > 1 MeV` tail.
- However, absolute normalization is not converged at 5 ps. The 4-5 ps window
  carries `63.2%` of the 0-5 ps `E_D >= 0.4 MeV` D-D-yield-weighted total, and
  the 4.75-5.00 ps final window still carries `14.7%`.
- Practical stopping rule:
  - For spectral-shape studies, 5 ps is already sufficient and 4 ps is close.
  - For absolute yield reporting, continue until the final 250 fs
    D-D-yield-weighted window is below `10%` of cumulative yield and the
    normalized spectrum remains stable. Based on the current trend, 6 ps is
    likely to satisfy the 10% criterion; `5%` would be a more conservative
    optional target.

All-energy sanity check:

- 0-4 ps vs 0-5 ps `Y_DD`-weighted total-variation distance: `0.03117`.
- Cosine similarity: `0.99831`.
- The all-energy result has the same interpretation: continuing from 4 ps to
  5 ps mainly changes the normalization, while the useful spectral shape is
  already stable.

Generated files:

- `hpc/tools/sdf_probe_energy_hist.c`
- `hpc/tools/compare_rear10_spectrum_4ps_5ps.py`
- `hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_normalized_spectrum.csv`
- `hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_spectrum_summary.csv`
- `hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_normalized_spectrum.png`
- `hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_allE_normalized_spectrum.csv`
- `hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_allE_spectrum_summary.csv`
- `hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_allE_normalized_spectrum.png`

## Rear+10 5 ps vs 6 ps Absolute-Yield Convergence Check

Date: 2026-07-05 / 2026-07-06 CST.

Purpose:

- Decide whether the `a0=10`, `3 um` 3D anchor source should stop at 6 ps or
  continue to 7 ps.
- Use D-D-yield-weighted convergence, not raw deuteron-count convergence,
  because Stage 2 is driven by `weight * Y_DD(E)`.

Completed run:

- Run directory:
  `/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/runs/pic3d_stage1_source_diag6000fs_restart0020hardlink_2000x250x250_a0_10_t_3um_20260706_r006`.
- Job ID: `1837996`.
- Final state: `COMPLETED`, exit code `0:0`.
- Slurm elapsed: `02:06:32` on `2` nodes / `512` ranks.
- Approximate cost: `1080` core-hours, about `108 CNY` at
  `0.1 CNY/core-hour`.
- Peak memory from `sacct`: MPI step about `243 GB`, safely below the
  two-node memory allocation.
- Output: `Data/0021.sdf` through `Data/0024.sdf`; the final `0024.sdf` is a
  restartable dump of about `13 GB`.

Main `rear+10`, `E_D >= 0.4 MeV` result:

| quantity | value |
|---|---:|
| D-D-yield-weighted total, 0-5 ps | `1.8966e6` |
| D-D-yield-weighted increment, 5-6 ps | `7.8243e5` |
| D-D-yield-weighted total, 0-6 ps | `2.6791e6` |
| 5-6 ps increment / 0-6 ps total | `29.2%` |
| final 5.75-6.00 ps window / 0-6 ps total | `5.57%` |
| final 5.75-6.00 ps window / 5-6 ps increment | `19.1%` |

Spectral-shape check:

- 0-5 ps vs 0-6 ps `Y_DD(E)`-weighted total-variation distance: `0.0128`.
- Jensen-Shannon distance: `0.0131`.
- Cosine similarity: `0.99967`.
- The 5-6 ps-only spectrum remains soft and stable:
  - mean `0.484 MeV`
  - p90 `0.571 MeV`
  - p99 `0.691 MeV`
  - no new `E_D > 1 MeV` tail in the binned result.

Decision:

- Accept `6 ps` as the 3D anchor collection time for absolute-yield reporting
  at `rear+10`, under the strict final-window criterion
  `last 250 fs / cumulative Y_DD-weighted source < 10%`.
- Do not extend this same 3D anchor to 7 ps. Further extension would mostly
  refine normalization at high cost while the normalized source spectrum is
  already stable.
- The next resource focus is the formal 2D scan, with this 3D point used as the
  dimensionality anchor and source-extraction validation.

Generated files:

- `hpc/tools/compare_rear10_spectrum_5ps_6ps.py`
- `hpc/results/pic3d_stage1_rear10_5ps_vs_6ps_normalized_spectrum.csv`
- `hpc/results/pic3d_stage1_rear10_5ps_vs_6ps_spectrum_summary.csv`
- `hpc/results/pic3d_stage1_rear10_5ps_vs_6ps_normalized_spectrum.png`
- `hpc/results/pic3d_stage1_rear10_5ps_vs_6ps_allE_normalized_spectrum.csv`
- `hpc/results/pic3d_stage1_rear10_5ps_vs_6ps_allE_spectrum_summary.csv`
- `hpc/results/pic3d_stage1_rear10_5ps_vs_6ps_allE_normalized_spectrum.png`
- `hpc/results/pic3d_stage1_rear10_6ps_dd_yield_windows.csv`
- `hpc/results/pic3d_stage1_rear10_6ps_dd_yield_convergence_summary.csv`

## Formal 2D Scan Pilot

Date: 2026-07-06 CST.

Purpose:

- Start the cheaper parameter-scan branch after the 3D anchor demonstrated the
  source extraction and spectrum-stability workflow.
- Submit only one formal 2D pilot before launching the full 7-point scan, so
  the actual runtime, memory, probe output size, and parser behavior are known.

Submitted pilot:

- Run directory:
  `/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/runs/pic2d_stage1_formal5ps_10nm_a0_10_t_3um_20260706_r001`.
- Slurm Job `1846890`, `amd_m9_768`, 1 node / 160 ranks, walltime `6:00:00`.
- Physics point: `a0=10`, `CD2 thickness=3 um`, no preplasma.
- Box: `x=-6..36 um`, `y=-15..15 um`.
- Grid: `nx=4200`, `ny=3000`, i.e. `dx=dy=10 nm`.
- Target: front at `x=0`, rear at `x=thickness`, half-width `5 um`.
- PPC: electron/deuteron/carbon = `16/48/8`.
- Probes: `rear+5`, `rear+10`, `rear+15`, `rear+20`.
- `t_end=5 ps`, `dt_snapshot=250 fs`, probe and deuteron energy distribution
  outputs only.

Rationale:

- The old 2D diagnostic box (`x=-10..90 um`, `y=+-40 um`) was oversized for the
  current source-plane strategy and was intended for early far-probe diagnosis.
- The new 2D box follows the 3D anchor geometry more closely while keeping
  enough downstream space for `rear+20` and transverse margin beyond the
  `+-10 um` 3D transverse box.
- `10 nm` resolves the cold and relativistic skin-depth scale better than the
  earlier `25 nm` diagnostic grid. The first pilot will determine whether this
  accuracy is affordable for the 7-point scan.

Update after 3D 6 ps convergence:

- The 3D anchor reached the D-D-yield-weighted 10% final-window convergence
  criterion at 6 ps. To keep the 2D/3D comparison consistent, the formal 2D
  matrix was upgraded from 5 ps to 6 ps before the pilot finished.
- The running 5 ps pilot, Job `1846890`, was cancelled after `01:18:27`, at
  about `1.19 ps`. Approximate sunk cost was `209` core-hours, about `21 CNY`.
  This was preferred over completing a 5 ps job that would not match the new
  formal 6 ps matrix.
- The 2D template now uses `t_end = 6000 fs`, `stop_at_walltime = 34200 s`,
  `full_dump_every = -1`, `restart_dump_every = -1`, and
  `force_final_to_be_restartable = T`.
- The Slurm template now uses one full `amd_m9_768` node with `256` MPI ranks
  and a `10:00:00` walltime. This should reduce wall-clock time relative to
  160 ranks while avoiding the likely communication/cost penalty of a 512-rank
  two-node 2D run. The 10 h walltime is an upper bound, not a billing duration
  after normal completion.

Submitted 6 ps matrix:

| run | job | a0 | thickness um | state at submission |
|---|---:|---:|---:|---|
| `pic2d_stage1_formal6ps_10nm_a0_05_t_3um_20260706_r001` | `1855864` | 5 | 3 | PENDING |
| `pic2d_stage1_formal6ps_10nm_a0_10_t_3um_20260706_r001` | `1855865` | 10 | 3 | PENDING |
| `pic2d_stage1_formal6ps_10nm_a0_15_t_3um_20260706_r001` | `1855866` | 15 | 3 | PENDING |
| `pic2d_stage1_formal6ps_10nm_a0_20_t_3um_20260706_r001` | `1855867` | 20 | 3 | PENDING |
| `pic2d_stage1_formal6ps_10nm_a0_10_t_1um_20260706_r001` | `1855868` | 10 | 1 | PENDING |
| `pic2d_stage1_formal6ps_10nm_a0_10_t_2um_20260706_r001` | `1855869` | 10 | 2 | PENDING |
| `pic2d_stage1_formal6ps_10nm_a0_10_t_4um_20260706_r001` | `1855870` | 10 | 4 | PENDING |

Immediate monitoring plan:

- Once the first 256-rank job starts, check parser success, processor topology,
  initial load-balance redistribution, ETA, memory, and output size.
- If the first started job shows severe 256-rank inefficiency or abnormal I/O,
  pause/cancel still-pending siblings before large cost accumulates.
- On completion, analyze all probes using the same D-D-yield-weighted
  final-window criterion used for the 3D anchor, with `rear+10` as the primary
  source plane and `rear+5/15/20` as source-plane robustness checks.

Runtime walltime-risk update:

- The 7-job matrix started running on 2026-07-06 CST.
- At elapsed `01:47:54`, all jobs were still `RUNNING` with no stderr output.
- Live Slurm walltime extension was attempted for the jobs closest to or above
  the 10 h walltime:
  - `1855865` (`a0=10,t=3um`)
  - `1855866` (`a0=15,t=3um`)
  - `1855867` (`a0=20,t=3um`)
  - `1855870` (`a0=10,t=4um`)
- Slurm denied all live extensions with `Access/permission denied`.
- To avoid losing the already-spent compute, an EPOCH runtime restart-dump
  request was placed in each high-risk run directory by creating `Data/DUMP`.
  The jobs continue running; if any stop before 6 ps, continue from the latest
  restart dump instead of rerunning from zero.
- The DUMP requests were confirmed processed: `Data/restart.visit` points to
  `0003.sdf` in all four high-risk runs. The restart dump sizes are about
  `1.9G` for `1855865`, `1855866`, and `1855867`, and about `2.2G` for
  `1855870`.
- Latest walltime-risk snapshot:
  - `1855864`: `1.17 ps`, ETA `7h19m`, continue; slower than early ETA
    but still inside the 10 h walltime.
  - `1855865`: `0.94 ps`, ETA `8h49m`, restart `Data/0003.sdf` confirmed.
  - `1855866`: `0.85 ps`, ETA `10h16m`, restart `Data/0003.sdf` confirmed.
  - `1855867`: `0.76 ps`, ETA `11h21m`, restart `Data/0003.sdf` confirmed.
  - `1855868`: `3.81 ps`, ETA `1h02m`, continue.
  - `1855869`: `2.20 ps`, ETA `3h03m`, continue.
  - `1855870`: `0.99 ps`, ETA `9h05m`, restart `Data/0003.sdf` confirmed.

Restart-continuation action:

- A second runtime `Data/DUMP` request was placed for the four high-risk jobs
  so cancellation would not fall back to the older `0003.sdf` checkpoint.
- The second DUMP completed on 2026-07-06 CST. In all four original run
  directories, `Data/restart.visit` lists both `0003.sdf` and `0004.sdf`.
- Verified `Data/0004.sdf` sizes:
  - `1855865`: about `1.9G`
  - `1855866`: about `1.9G`
  - `1855867`: about `1.9G`
  - `1855870`: about `2.2G`
- Four continuation directories were created with hard-linked `Data/0004.sdf`
  files, explicit `restart_snapshot = 0004.sdf`, Slurm walltime `18:00:00`,
  and EPOCH `stop_at_walltime = 61200.0`.
- The original high-risk jobs were cancelled after about `01:55:01` runtime:
  - `1855865` -> `1869667`
  - `1855866` -> `1869668`
  - `1855867` -> `1869669`
  - `1855870` -> `1869670`
- At submission check, the four continuation jobs were `PENDING`; the three
  lower-risk original jobs `1855864`, `1855868`, and `1855869` continued running.
- Follow-up check showed all four continuation jobs started running and printed
  `Load from restart dump OK`.
- EPOCH printed warnings that particle species such as `D_rear05` from the
  restart dump were not found in the input deck. These are particle-probe output
  records stored in the restart SDF, not the physical `deuteron` species. The
  postprocessing rule is therefore: merge r001 outputs through `0004.sdf` with
  r002 outputs after restart; do not analyze the r002 directory alone as a full
  0-6 ps source.
- Disk check at the same time: `/publicfs10` had about `4.1P` free and the
  project directory used about `94G`; no smaller account quota was reported by
  the available quota commands.

Quota failure and recovery:

- At about 2026-07-06 05:44 CST, several jobs failed with MPI-IO messages:
  `mca_fbtl_posix_pwritev: error in (p)write(v):Disk quota exceeded`.
  The filesystem still reported about `4.1P` globally free, so this is a hidden
  account/project quota, not global disk exhaustion.
- Failed jobs:
  - `1855868` (`a0=10,t=1um`) failed after `02:25:15`, near `4.97 ps`; no
    valid restart checkpoint was available.
  - `1855869` (`a0=10,t=2um`) failed after `02:23:41`, near `2.73 ps`; no
    valid restart checkpoint was available.
  - `1869668` (`a0=15,t=3um` restart continuation) failed after `00:24:43`
    after successfully loading `Data/0004.sdf`.
- Cleanup was performed on remote:
  `/publicfs10/fs10-m9/home/m9s003861/pic/no5_dd_li_tpr/CLEANUP_20260706_QUOTA.txt`.
  Obsolete intermediate 3D restart SDF files and old early 2D diagnostic SDF
  files were removed. Accepted 3D `r006`, active formal 2D runs, input decks,
  Slurm logs, and restart files needed by hard-linked continuations were kept.
  Project usage dropped from about `94G` to about `47G`.
- Replacement jobs submitted:
  - `1873138`: full rerun for `a0=10,t=1um`, replacing `1855868`.
  - `1873136`: full rerun for `a0=10,t=2um`, replacing `1855869`.
  - `1873137`: restart rerun for `a0=15,t=3um`, replacing `1869668`, again
    using original r001 `Data/0004.sdf`.
- Job `1855864` (`a0=5,t=3um`) became walltime-risky. Live TimeLimit extension
  was denied. A runtime `Data/DUMP` was requested, but as of this entry no
  `Data/restart.visit` had been created, so the job must not be cancelled yet.

Additional quota cleanup and a0=5 rerun:

- Job `1855864` stopped making progress after writing a partial runtime DUMP:
  stdout, stderr, and `Data/0005.sdf` stopped updating around 2026-07-06
  05:37 CST. `Data/0005.sdf` had no accompanying `Data/restart.visit`, so it was
  not accepted as a continuation checkpoint.
- Removed additional obsolete files:
  - accepted 3D r006 input restart `Data/0020.sdf`; the final accepted
    `Data/0024.sdf` remains kept;
  - superseded 2D original-run `Data/0003.sdf` restart dumps for the jobs that
    already have verified `Data/0004.sdf` continuations;
  - the bad partial `a0=5` `Data/0005.sdf`.
- Project usage dropped to about `26G`.
- `1855864` was cancelled and replacement full rerun `1874262` was submitted
  with Slurm walltime `18:00:00` and `stop_at_walltime = 61200.0`.
