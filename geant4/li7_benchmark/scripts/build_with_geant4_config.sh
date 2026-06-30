#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
GEANT4_CONFIG="${GEANT4_CONFIG:-/opt/miniconda3/envs/no5-geant4/bin/geant4-config}"
BUILD_DIR="${BUILD_DIR:-${ROOT_DIR}/geant4/build/li7_benchmark_manual}"
EXE="${EXE:-${BUILD_DIR}/li7_benchmark}"

if [[ ! -x "${GEANT4_CONFIG}" ]]; then
  echo "geant4-config not found or not executable: ${GEANT4_CONFIG}" >&2
  echo "Set GEANT4_CONFIG=/path/to/geant4-config and retry." >&2
  exit 1
fi

G4_PREFIX="$("${GEANT4_CONFIG}" --prefix)"
mkdir -p "${BUILD_DIR}"

c++ -std=c++17 \
  "${ROOT_DIR}/geant4/li7_benchmark/src/main.cc" \
  -o "${EXE}" \
  -Wl,-rpath,"${G4_PREFIX}/lib" \
  $("${GEANT4_CONFIG}" --cflags) \
  $("${GEANT4_CONFIG}" --libs)

echo "Built ${EXE}"
