# Handoff: CH-Li EPOCH-Geant4 neutron optimization

Last updated: 2026-07-01

## Current goal

Use EPOCH PIC plus Geant4 Monte Carlo to optimize a CH-foil-driven Li neutron source:

```text
maximize  log10(Y_n_exit / E_L)
minimize  tau_exit_FWHM_ps
```

`Y_n_exit` is the weighted number of neutrons crossing the Li rear surface. `tau_exit_FWHM_ps` is the FWHM of the neutron exit-time distribution at the Li rear surface.

## Required reading order for every new session

```text
1. HANDOFF.md
2. project_execution.md
3. configs/baseline.json
4. literature_notes/literature_map.md
5. most recent CSV/JSON summaries under data/objectives/ if present
```

After doing meaningful work, update this file before committing. If a GitHub
remote is configured, push the new commit to GitHub before ending the session.

## Compute strategy

Local machine:

```text
1. EPOCH2D Tier 0 smoke tests.
2. EPOCH2D Tier 1 baseline and 9-12 source-point scans.
3. Geant4 monoenergetic 7Li(p,n) benchmark.
4. EPOCH phase-space -> Geant4 coupling.
5. Local Pareto sorting and optional low-cost BO.
```

HPC:

```text
1. 4-6 selected EPOCH3D validation points.
2. Optional high-resolution 2D reruns if local Tier 1/Tier 2 is too slow.
3. High-stat final Geant4 can run locally or on HPC depending on phase-space size.
```

Do not use 3D as the exploration tool. Use local 2D and Geant4 scans to decide which 3D points are worth paying for.

## Important project decision

Use nested optimization:

```text
Outer expensive EPOCH variables:
  I0_Wcm2, tau_FWHM_fs, d_CH_um, L_pre_um

Inner cheap Geant4 scan:
  D_Li_cm = 0.05, 0.10, 0.20, 0.50, 1.00, 2.00, 3.00
```

This keeps EPOCH evaluations manageable while still producing five-dimensional candidate points for the final Pareto front.

## Files created so far

```text
project_execution.md
literature_notes/literature_map.md
configs/baseline.json
configs/stage0_benchmark_grid.json
configs/stageD_initial_grid.json
analysis/scripts/metrics.py
analysis/scripts/pareto.py
analysis/scripts/generate_initial_design.py
data/objectives/objectives_template.csv
geant4/li7_benchmark/CMakeLists.txt
geant4/li7_benchmark/src/main.cc
geant4/li7_benchmark/scripts/build_with_geant4_config.sh
geant4/li7_benchmark/scripts/run_stage0_grid.py
geant4/li7_benchmark/scripts/collect_stage0.py
README.md
.gitignore
HANDOFF.md
```

## Environment status

Checked on 2026-07-01:

```text
mpirun: found at /opt/homebrew/bin/mpirun
system PATH geant4-config: not found
system PATH cmake: not found before install
Homebrew: found at /opt/homebrew/bin/brew
Homebrew cmake: installed at /opt/homebrew/bin/cmake, version 4.3.4
Homebrew geant4: no formula available
Conda env no5-geant4: installed
Conda Geant4: /opt/miniconda3/envs/no5-geant4/bin/geant4-config, version 11.4.2
Local G4TENDL charged-particle HP data: local_geant4_data/G4TENDL1.4
```

The Conda Geant4 runtime works when commands are launched through:

```bash
conda run -n no5-geant4 <command>
```

Low-energy 7Li(p,n) requires `QGSP_BIC_AllHP` and `G4PARTICLEHPDATA` pointing to
the optional Geant4 `G4TENDL1.4` dataset. `QGSP_BIC_HP` runs but did not trigger
proton inelastic events for this benchmark. `local_geant4_data/` is ignored by
git.

The CMake route currently finds Geant4 but fails inside Conda's Geant4 CMake
config because `G4HDF5Shim.cmake` requires HDF5 thread-safety metadata not
provided by the installed Conda HDF5 package. The working local build path is:

```bash
conda run -n no5-geant4 bash geant4/li7_benchmark/scripts/build_with_geant4_config.sh
```

## Stage 0 Geant4 benchmark status

Added a headless Geant4 application under:

```text
geant4/li7_benchmark/
```

It models:

```text
monoenergetic proton pencil beam -> pure 7Li cylinder -> neutron birth, Li-rear-exit and detector-plane tallies
```

The batch runner:

```text
geant4/li7_benchmark/scripts/run_stage0_grid.py
```

generates the 7 x 7 benchmark grid from `configs/stage0_benchmark_grid.json`.
Python syntax and dry-run command generation passed on 2026-07-01.

Manual `geant4-config` build passed on 2026-07-01:

```text
geant4/build/li7_benchmark_manual/li7_benchmark
```

Smoke run passed on 2026-07-01:

```bash
conda run -n no5-geant4 geant4/build/li7_benchmark_manual/li7_benchmark \
  --energy-MeV 1.5 \
  --thickness-cm 0.1 \
  --events 10 \
  --out-dir runs/geant4/stage0_smoke/Ep_1p5MeV_DLi_0p1cm \
  --physics-list QGSP_BIC_HP
```

The smoke output reported zero neutrons, which is a reasonable threshold sanity
check for 1.5 MeV protons with only 10 events.

Additional physics smoke tests passed after installing `G4TENDL1.4` locally and
using `QGSP_BIC_AllHP`:

```text
5 MeV, 1 cm, 10000 primaries:
  birth_neutron_count = 12
  Y_n_exit = 7
  Y_n_exit_per_primary = 7.0e-4

20 MeV, 1 cm, 10000 primaries:
  birth_neutron_count = 23
  Y_n_exit = 15
  Y_n_exit_per_primary = 1.5e-3
```

The Geant4 summary now also includes diagnostic fields:

```text
primary_li_entry_count
li_process_counts
li_secondary_counts
```

These verified that protons enter Li and that `protonInelastic` appears only
with `QGSP_BIC_AllHP` plus `G4TENDL1.4`.

## Next actions

1. Run the monoenergetic benchmark grid from `configs/stage0_benchmark_grid.json`.
2. Confirm the 7Li(p,n) threshold behavior:

```text
1.5 MeV: nearly zero neutrons
2-3 MeV: neutron production begins
higher Ep: yield increases reasonably
larger D_Li: yield rises but tau_exit_FWHM broadens
```

3. Then run EPOCH2D Tier 0 smoke and Tier 1 baseline from `configs/baseline.json`.
4. Export `proton_phase_space.h5` and couple it into Geant4.

## Commit protocol

Before each commit:

```text
1. Update HANDOFF.md with the latest status.
2. Run available lightweight checks, at minimum:
   python3 -m py_compile analysis/scripts/*.py
3. Commit only source/config/docs, not PDFs or simulation output.
4. Push to GitHub if `git remote -v` shows an origin remote.
```

## GitHub sync protocol

Current remote status:

```text
origin = git@github.com:xiaojiujiuboom/no5gongzuo.git
```

Push status on 2026-07-01:

```text
SSH authentication is working.
main has been pushed to origin/main.
```

When a GitHub repository URL is available:

```text
git remote add origin <github-repo-url>
git push -u origin main
```

For future sessions, after each meaningful update:

```text
1. update HANDOFF.md
2. run lightweight checks
3. commit locally
4. git push origin main
```

If `origin` is missing, ask for the GitHub repo URL before trying to push.
The current GitHub repository is:

```text
https://github.com/xiaojiujiuboom/no5gongzuo
git@github.com:xiaojiujiuboom/no5gongzuo.git
```
