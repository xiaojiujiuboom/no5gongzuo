# CH-Li neutron optimization project

Start every handoff by reading:

```text
HANDOFF.md
project_execution.md
literature_notes/literature_map.md
```

Project objective:

```text
CH foil + intense laser -> TNSA protons -> 7Li converter -> neutron yield and FWHM optimization
```

Compute split:

```text
Local:
  EPOCH2D smoke / baseline / medium-resolution source scans
  Geant4 Li(p,n) benchmark and local converter scans
  phase-space coupling and analysis scripts

HPC:
  selected EPOCH3D validation points only
  optional high-resolution 2D reruns if local 2D is too slow
```

Tracked content:

```text
configs/                 parameter cards and scan grids
analysis/scripts/        post-processing and initial-design tools
geant4/li7_benchmark/    Stage 0 pure 7Li(p,n) benchmark app
literature_notes/        notes distilled from the PDFs
project_execution.md     unified execution plan
HANDOFF.md               latest project state and next actions
```

Large outputs, PDFs, phase-space dumps and simulation runs are intentionally ignored by git.

Stage 0 Geant4 benchmark entry point:

```bash
cmake -S geant4/li7_benchmark -B geant4/build/li7_benchmark
cmake --build geant4/build/li7_benchmark -j
python3 geant4/li7_benchmark/scripts/run_stage0_grid.py \
  --exe geant4/build/li7_benchmark/li7_benchmark \
  --grid configs/stage0_benchmark_grid.json
```
