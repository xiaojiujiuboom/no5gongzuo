# Li7 monoenergetic proton benchmark

This is the Stage 0 Geant4 benchmark for the CH-Li neutron optimization project.

Purpose:

```text
monoenergetic proton pencil beam -> pure 7Li converter -> neutron yield and timing
```

Geometry convention:

```text
Geant4 z axis corresponds to project x / beam direction.
source plane: z = source_z
Li front:     z = source_z + source_to_li_front_cm
Li rear:      z = Li front + D_Li_cm
detector:     z = Li rear + detector_distance_behind_li_cm
```

Build:

```bash
cmake -S geant4/li7_benchmark -B geant4/build/li7_benchmark
cmake --build geant4/build/li7_benchmark -j
```

Current macOS/Conda fallback build:

```bash
conda run -n no5-geant4 bash geant4/li7_benchmark/scripts/build_with_geant4_config.sh
```

This writes:

```text
geant4/build/li7_benchmark_manual/li7_benchmark
```

On 2026-07-01 the Conda Geant4 11.4.2 CMake package finds Geant4 but is
blocked by its HDF5 thread-safety check. The `geant4-config` fallback above is
therefore the working local build route on this machine.

Low-energy 7Li(p,n) needs charged-particle ParticleHP data. On this machine
`G4TENDL1.4` was downloaded from the Geant4 data server into:

```text
local_geant4_data/G4TENDL1.4
```

`local_geant4_data/` is intentionally ignored by git. The grid runner
automatically sets `G4PARTICLEHPDATA` to that path when it exists.

Run one debug point:

```bash
geant4/build/li7_benchmark/li7_benchmark \
  --energy-MeV 5 \
  --thickness-cm 1 \
  --events 10000 \
  --out-dir runs/geant4/stage0_debug/Ep_5MeV_DLi_1cm
```

Using the local Conda fallback executable:

```bash
G4PARTICLEHPDATA="$PWD/local_geant4_data/G4TENDL1.4" \
  conda run -n no5-geant4 geant4/build/li7_benchmark_manual/li7_benchmark \
  --energy-MeV 5 \
  --thickness-cm 1 \
  --events 10000 \
  --out-dir runs/geant4/stage0_debug/Ep_5MeV_DLi_1cm \
  --physics-list QGSP_BIC_AllHP
```

Run the configured Stage 0 grid:

```bash
python3 geant4/li7_benchmark/scripts/run_stage0_grid.py \
  --exe geant4/build/li7_benchmark/li7_benchmark \
  --grid configs/stage0_benchmark_grid.json \
  --events-key N_primary_debug
```

For the local Conda fallback:

```bash
conda run -n no5-geant4 python3 geant4/li7_benchmark/scripts/run_stage0_grid.py \
  --exe geant4/build/li7_benchmark_manual/li7_benchmark \
  --grid configs/stage0_benchmark_grid.json \
  --events-key N_primary_debug
```

Outputs per case:

```text
summary.json
birth_neutron_time_hist.csv
exit_neutron_time_hist.csv
detector_neutron_time_hist.csv
```

The primary physics list is read from `configs/stage0_benchmark_grid.json`. The
default project preference is `QGSP_BIC_AllHP`; `QGSP_BIC_HP` runs but does not
activate the required low-energy charged-particle HP p+Li channel in this local
benchmark.
