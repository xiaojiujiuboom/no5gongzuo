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
README.md
.gitignore
HANDOFF.md
```

## Environment status

Checked on 2026-06-30:

```text
mpirun: found at /opt/homebrew/bin/mpirun
geant4-config: not found in PATH
cmake: not found in PATH
```

Geant4/CMake need to be installed or added to PATH before the Stage 0 benchmark can run.

## Next actions

1. Install or expose CMake and Geant4 in PATH.
2. Build a minimal headless Geant4 application for pure 7Li slab/cylinder.
3. Run the monoenergetic benchmark grid from `configs/stage0_benchmark_grid.json`.
4. Confirm the 7Li(p,n) threshold behavior:

```text
1.5 MeV: nearly zero neutrons
2-3 MeV: neutron production begins
higher Ep: yield increases reasonably
larger D_Li: yield rises but tau_exit_FWHM broadens
```

5. Then run EPOCH2D Tier 0 smoke and Tier 1 baseline from `configs/baseline.json`.
6. Export `proton_phase_space.h5` and couple it into Geant4.

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
origin = https://github.com/xiaojiujiuboom/no5gongzuo.git
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
```
