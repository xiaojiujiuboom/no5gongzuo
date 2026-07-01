# CH-Li EPOCH-Geant4 neutron optimization execution pack

## 1. Unified project target

This project should be run as a staged end-to-end optimization chain:

```text
EPOCH 2D/3D PIC:
  intense laser -> CH foil -> TNSA proton phase space

Geant4 Monte Carlo:
  weighted/resampled protons -> pure 7Li converter -> neutron yield and timing

Optimization:
  find Pareto front between forward neutron yield per laser energy and forward-pulse FWHM
```

Scope note updated on 2026-07-01:

```text
Return to the original BO direction:

laser -> CH foil -> TNSA proton source -> converter -> directional neutron
yield and FWHM.

The project should not stop at a Li-thickness scan, because thickness scans have
already been explored extensively. The thickness scan remains useful as a cheap
inner Geant4 scan for each expensive EPOCH source point. The outer BO target is
the CH-source parameter space.
```

Primary objectives:

```text
maximize  log10(Y_n_forward_detector / E_L)
minimize  tau_forward_detector_FWHM_ps
```

Definitions:

```text
Y_n_forward_detector:
  weighted number of neutrons crossing the finite-radius forward detector plane
  behind the converter

Y_n_exit:
  weighted number of neutrons crossing the rear surface of the Li converter;
  diagnostic, not the primary BO yield

tau_forward_detector_FWHM_ps:
  full width at half maximum of the forward detector neutron time distribution

tau_exit_FWHM_ps:
  full width at half maximum of the neutron exit-time distribution at the Li rear surface;
  diagnostic for separating converter broadening from detector/TOF broadening

E_L:
  laser energy used for the EPOCH source point
```

Use a finite-radius detector plane 10 cm behind the converter as the directional
objective surface. Also record the Li rear-surface exit distribution so that the
intrinsic converter broadening can be separated from detector time-of-flight
broadening.

## 2. Decision that resolves the two existing md documents

Use a nested optimization design:

```text
Outer expensive source variables, evaluated by EPOCH:
  I0_Wcm2, tau_fs, d_CH_um, L_pre_um

Inner cheap converter scan, evaluated by Geant4 for each EPOCH source:
  D_Li_cm
```

This is better than treating `D_Li_cm` as a full BO variable because each costly EPOCH run can feed a full Li-thickness yield-FWHM curve. The final candidate table still contains five coordinates:

```text
I0_Wcm2, tau_fs, d_CH_um, L_pre_um, D_Li_cm
```

but BO should initially propose only the four EPOCH variables. `D_Li_cm` is then scanned on a fixed log-spaced grid.

## 3. Literature integration

### 3.1 `2604.23913v2.pdf`

This is the closest scientific reference for our workflow. It demonstrates an integrated chain using hydrodynamics, EPOCH PIC and Geant4 Monte Carlo for laser-driven neutron generation. The paper reports:

```text
laser:
  lambda0 = 0.8 um
  duration about 25-30 fs
  intensity about 1e20-2e20 W/cm2
  focal radius about 5 um

converter:
  LiF/LiD/Be blocks
  distance from source about 1 cm
  thickness 1-2 cm

MC:
  QGSP_BIC_AllHP / high-precision hadronic physics
  TENDL cross-section data
```

For this project, it supports:

```text
1. importing all PIC ion positions, momenta, energies and weights into Geant4;
2. recording both neutron birth-time and rear-surface exit-time distributions;
3. using Li-exit FWHM as a converter/source diagnostic;
4. expecting production-time FWHM around 70-100 ps and converter-exit FWHM around 460-670 ps for cm-scale converters under similar femtosecond laser conditions;
5. using yield per joule as the fair yield metric when laser energy changes.
6. using QGSP_BIC_AllHP with TENDL charged-particle data for sub-200 MeV proton reactions;
7. keeping BO focused on expensive CH-source variables while using low-dimensional converter scans as inner evaluations;
8. motivating forward detector yield/FWHM as an application-facing objective while keeping rear-surface timing as a diagnostic.
```

### 3.2 `2503.12154v1.pdf`

This reference is not about neutrons, but it is useful methodologically. It shows that a plasma accelerator source can be integrated into Geant4 as a generated source term, either from an input file or a surrogate model. For our first version, do not start with ML surrogate injection. Use the simpler input-file source:

```text
EPOCH proton_phase_space.h5 -> Geant4 PrimaryGeneratorAction
```

Later, after roughly 30-100 validated EPOCH source points, a surrogate source can be trained and exported to ONNX if faster Geant4 studies are needed.

### 3.3 `045036_1_5.0316772.pdf`

This paper is about p-B alpha production rather than Li neutron production, but it is a useful pitcher-catcher template. Its main transferable points are:

```text
1. EPOCH can provide an ion spectrum and phase-space source for a downstream Monte Carlo catcher;
2. the Monte Carlo stage must include stopping power, scattering and energy-dependent nuclear cross sections;
3. the paper validates the MC input by plotting the injected proton spectrum against the EPOCH spectrum;
4. it explains yield in terms of the incident proton spectrum, reaction cross section and stopping power.
```

For our paper, the analogous explanation is:

```text
Li neutron yield is controlled by the number of protons above the 7Li(p,n) threshold, their stopping path in Li, the angle/spot-size overlap with the converter, and the energy-dependent reaction probability.
```

## 4. Baseline parameter card

Use this as the first real coupled point after Geant4 benchmark and EPOCH smoke test:

```text
Laser:
  lambda0_um = 0.8
  I0_Wcm2 = 2.0e20
  a0 approximately 9.7
  tau_fs = 30
  w0_um = 5
  incidence = normal
  polarization = linear

CH foil:
  x_front_um = 20
  d_CH_um = 1.0
  n_e = 200 nc
  n_C6+ = 28.57 nc
  n_H+ = 28.57 nc
  Te_eV = 10
  Ti_eV = 10
  L_pre_um = 0.2

EPOCH 2D Tier 1:
  box = 60 um x 40 um
  x_front_um = 15
  x_diag_um = 50
  dx_um = 0.02
  dy_um = 0.05
  t_end_fs = 700-800
  ppc = 8-16 per species

Geant4:
  source plane x = 0
  Li front surface x = 1 cm
  Li material = pure 7Li
  Li density = 0.534 g/cm3
  Li radius = 2 cm
  D_Li_cm grid = 0.05, 0.10, 0.20, 0.50, 1.00, 2.00, 3.00
  detector plane = 10 cm behind Li rear surface
  detector radius = 2 cm
  physics list = QGSP_BIC_AllHP
  charged-particle HP data = G4TENDL1.4
```

## 5. Phase gates

### Gate A: Geant4 benchmark

Run monoenergetic pencil protons into pure 7Li:

```text
Ep_MeV = 1.5, 2, 3, 5, 10, 20, 40
D_Li_cm = 0.05, 0.10, 0.20, 0.50, 1.00, 2.00, 3.00
```

Pass criteria:

```text
1. 1.5 MeV gives nearly zero neutrons;
2. 2-3 MeV begins producing neutrons;
3. yield rises with Ep and then shows physically reasonable saturation/transport effects;
4. Li thickness increases yield but also broadens tau_exit_FWHM;
5. relative statistical error is stored.
```

### Gate B: EPOCH source

Pass criteria:

```text
1. baseline CH source gives Ep_max > 5-10 MeV;
2. Np(Ep > 2 MeV), Np(Ep > 5 MeV), Np(Ep > 10 MeV) are recorded;
3. proton phase-space exporter conserves total weight;
4. diagnostic plane captures outgoing protons before boundary artifacts return.
```

### Gate C: coupled source-to-converter

Pass criteria:

```text
1. Geant4 injected proton spectrum matches EPOCH exported spectrum;
2. baseline source gives nonzero Y_n_exit;
3. D_Li scan gives a visible forward-yield/FWHM trade-off;
4. exit-time and detector-time FWHM differ in the expected direction, with detector-time broader.
```

Only after Gate C should BO be started.

## 6. Data contracts

### 6.1 EPOCH phase-space HDF5

Required datasets:

```text
/x_um
/y_um
/px_SI or /px_mc
/py_SI or /py_mc
/energy_MeV
/weight
/time_fs
```

Optional for 3D EPOCH:

```text
/z_um
/pz_SI or /pz_mc
```

Required attributes:

```text
source = "EPOCH2D" or "EPOCH3D"
x_diag_um
weight_units
momentum_units
laser_energy_J
```

### 6.2 2D-to-3D reconstruction

For 2D exploration:

```text
r = abs(y_2D)
phi ~ Uniform(0, 2pi)
y_3D = r cos(phi)
z_3D = r sin(phi)
py_3D = py_2D cos(phi)
pz_3D = py_2D sin(phi)
px_3D = px_2D
```

Absolute yield from this reconstruction is provisional. Final yield claims should be validated using selected 3D EPOCH points.

### 6.3 Geant4 summary JSON

Each Geant4 task should produce:

```json
{
  "sample_id": "0001",
  "D_Li_cm": 1.0,
  "N_primary": 1000000,
  "source_total_proton_weight": 3.2e11,
  "laser_energy_J": 30.0,
  "Y_n_forward_detector": 7.5e7,
  "Y_n_forward_detector_per_J": 2.5e6,
  "tau_forward_detector_FWHM_ps": 5200.0,
  "Y_n_exit": 1.2e8,
  "Y_n_exit_per_J": 4.0e6,
  "tau_exit_FWHM_ps": 320.0,
  "Y_n_detector_10cm": 7.5e7,
  "tau_detector_FWHM_ps": 5200.0,
  "relative_error": 0.06,
  "Ep_max_MeV": 22.5,
  "Np_gt_2MeV": 3.2e11,
  "Np_gt_5MeV": 1.1e11,
  "Np_gt_10MeV": 2.0e10
}
```

## 7. Optimization sequence

Recommended local sequence:

```text
1. Stage 0 Geant4 monoenergetic benchmark.
2. Stage 1 EPOCH Tier 0 smoke test.
3. Stage 2 EPOCH Tier 1 baseline and phase-space export.
4. Stage 3 baseline EPOCH -> Geant4 coupled run with full Li-thickness scan.
5. Stage 4 9-12 source-point manual/LHS scan.
6. Stage 5 BO to 30-40 total EPOCH2D points.
7. Stage 6 high-stat Geant4 rerun of Pareto candidates.
8. Stage 7 4-6 selected 3D EPOCH validation points on HPC.
```

For the first local source scan, use:

```text
I0_Wcm2 = 1e20, 2e20, 3e20
d_CH_um = 0.5, 1.0, 2.0
tau_fs = 30
L_pre_um = 0.2
```

This gives nine EPOCH sources and seven Geant4 thicknesses per source.

## 8. Figure plan

Minimum final figures:

```text
Fig. 1 workflow: laser -> CH -> proton phase space -> Li -> neutron objectives
Fig. 2 Geant4 benchmark: Ep and D_Li vs Y_n_exit and tau_exit_FWHM
Fig. 3 EPOCH baseline: proton spectrum, angular distribution, time profile
Fig. 4 coupled baseline: Li thickness scan, forward-yield/FWHM trade-off
Fig. 5 scan/BO Pareto front: tau_forward_detector_FWHM_ps vs log10(Y_n_forward_detector / E_L)
Fig. 6 selected neutron time profiles: baseline, best-yield, shortest-pulse, knee
Fig. 7 physical interpretation: Np(Ep > 2 MeV), Ep_max, D_Li vs objectives
Fig. 8 3D validation: 2D ranking vs 3D rerun results
```

## 9. Immediate next commands after installing EPOCH/Geant4

Use this first-week order:

```text
1. run Geant4 monoenergetic benchmark grid in configs/stage0_benchmark_grid.json
2. run EPOCH Tier 0 smoke test for configs/baseline.json
3. run EPOCH Tier 1 baseline for configs/baseline.json
4. export proton_phase_space.h5 and validate total weight/spectrum
5. run Geant4 D_Li grid for the baseline phase space
6. compute FWHM from exit_neutron_time_hist.csv using analysis/scripts/metrics.py
7. append all summaries into data/objectives/objectives.csv
8. run analysis/scripts/pareto.py on the objectives table
```
