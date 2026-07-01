#!/bin/bash
set -euo pipefail

CROSS_SECTIONS="${OPENMC_CROSS_SECTIONS:-/Users/oomb/Downloads/mcnp_endfb71/cross_sections.xml}"
PY_OPENMC="${PY_OPENMC:-/opt/miniconda3/bin/conda run -n openmc-env python}"

mkdir -p outputs

python3 moduleA_pic/parametric_beam.py --n 20000 -o outputs/smoke_deuteron_beam.h5
python3 moduleB_source/build_source.py outputs/smoke_deuteron_beam.h5 \
  -o outputs/smoke_neutron_source.h5 --max-particles 5000

$PY_OPENMC moduleC_openmc/run.py \
  --case A --li6 90 \
  --output-dir outputs/openmc_smoke_A \
  --batches 20 --particles 100000 \
  --cross-sections "$CROSS_SECTIONS" \
  --run

$PY_OPENMC moduleC_openmc/run.py \
  --case B --li6 90 \
  --nsrc outputs/smoke_neutron_source.h5 \
  --output-dir outputs/openmc_smoke_B \
  --batches 20 --particles 100000 \
  --cross-sections "$CROSS_SECTIONS" \
  --run

$PY_OPENMC moduleC_openmc/compare_cases.py \
  --case-a outputs/openmc_smoke_A/statepoint.20.h5 \
  --case-b outputs/openmc_smoke_B/statepoint.20.h5 \
  --source-b outputs/smoke_neutron_source.h5 \
  --output-dir outputs/analysis/openmc_smoke_compare

