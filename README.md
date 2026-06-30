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
literature_notes/        notes distilled from the PDFs
project_execution.md     unified execution plan
HANDOFF.md               latest project state and next actions
```

Large outputs, PDFs, phase-space dumps and simulation runs are intentionally ignored by git.

