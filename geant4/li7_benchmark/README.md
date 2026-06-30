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

Run one debug point:

```bash
geant4/build/li7_benchmark/li7_benchmark \
  --energy-MeV 5 \
  --thickness-cm 1 \
  --events 10000 \
  --out-dir runs/geant4/stage0_debug/Ep_5MeV_DLi_1cm
```

Run the configured Stage 0 grid:

```bash
python3 geant4/li7_benchmark/scripts/run_stage0_grid.py \
  --exe geant4/build/li7_benchmark/li7_benchmark \
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
default project preference is `QGSP_BIC_AllHP`; if the installed Geant4 build
does not provide that reference list, try `QGSP_BIC_HP` first.

