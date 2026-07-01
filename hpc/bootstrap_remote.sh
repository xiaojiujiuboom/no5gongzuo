#!/bin/bash
set -euo pipefail

REMOTE_ROOT="${1:-$HOME/pic/no5_dd_li_tpr}"

mkdir -p \
  "$REMOTE_ROOT/bundles" \
  "$REMOTE_ROOT/runs" \
  "$REMOTE_ROOT/results" \
  "$REMOTE_ROOT/logs" \
  "$REMOTE_ROOT/tools" \
  "$REMOTE_ROOT/archive"

cat > "$REMOTE_ROOT/README_REMOTE.txt" <<'EOF'
no5_dd_li_tpr remote workspace

Purpose:
  Laser-driven D-D neutron source -> external Li target tritium production.

Layout:
  bundles/  uploaded run bundles
  runs/     expanded active runs, one directory per run_id
  results/  compact results copied out of runs
  logs/     bookkeeping logs
  tools/    helper scripts
  archive/  inactive old runs

Rules:
  - Do not mix unrelated projects here.
  - Do not overwrite existing run directories.
  - Keep large SDF files on HPC.
  - Return compact products only: deuteron_beam.h5, summary.json, metrics.json,
    quicklook plots, small CSV files.
EOF

printf "initialized %s\n" "$REMOTE_ROOT"

