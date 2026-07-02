# Literature Notes: EPOCH/PIC to Monte Carlo Workflows

This note summarizes three user-provided papers and extracts only the details
that are useful for the no5 DD-neutron / Li TPR workflow.

Local PDFs reviewed:

```text
/Users/oomb/Downloads/2503.12154v1.pdf
/Users/oomb/Downloads/2604.23913v2.pdf
/Users/oomb/Downloads/045036_1_5.0316772.pdf
```

## 1. Feng et al., Microwire-Array Neutron Source, arXiv:2604.23913v2

Topic: ultrashort laser-driven protons from microwire-array targets, followed
by neutron production in LiF/LiD/Be converters with Geant4.

Workflow:

```text
FLASH RHD preplasma -> EPOCH PIC proton/ion acceleration -> Geant4 neutron converter
```

PIC settings reported in Appendix A:

```text
code: EPOCH, 2D PIC
box: 100 um x 30 um
grid: 10000 x 1500 cells
cell size: dx = 10 nm, dy = 20 nm
PPC: 36 macro particles per cell
laser: lambda0 = 0.8 um, T0 = 2.67 fs
pulse: 30 fs Gaussian
spot radius: 5 um
intensity: 2e20 W/cm2
a0: 9.67
incidence angle: 5 deg
target: microwire array + 200 nm SiN substrate + 24 nm CH contaminant
MWA electron density: 210 nc
CH electron density: 40 nc
```

Times used:

```text
RHD preplasma shown/applied at t = 120 ps
2D PIC figures use Delta t = 60 T0 ~= 160 fs
3D validation figures use Delta t = 36 T0 ~= 96 fs
```

PIC to MC handoff:

```text
They import ion positions, momenta, energies, and particle weights from EPOCH
into a 3D Geant4 postprocessing simulation.
```

MC settings reported:

```text
toolkit: Geant4
physics list: QGSP_BIC_ALLHP
cross-section source: TENDL
converter materials: LiF, LiD, Be
2D-to-3D normalization: geometric conversion factor using target transverse size
```

Relevance to no5:

- This is the closest workflow analog for our project: PIC ion beam source
  handed into MC converter transport.
- They use a very fine longitudinal PIC grid and high PPC for the paper-level
  proton acceleration study.
- Their quoted PIC analysis times are much earlier than ours because protons
  are energetic and the source is evaluated close to the target on femtosecond
  scales. Our deuteron source plane is explicitly `rear+20 um`, so we must use
  a later plane-crossing completion criterion rather than copying their 60 T0
  snapshot timing.
- Their handoff includes positions, momenta, energies, and weights. Our EPOCH
  particle-probe source should preserve the same information, with time-window
  concatenation.

## 2. Arun Kumar et al., Proton-Boron Pitcher-Catcher, AIP Advances 16, 045036

Topic: EPOCH proton acceleration from an Au/CH pitcher, followed by FLUKA
transport and proton-boron alpha production in a boron catcher.

PIC settings reported in Sec. II A:

```text
code: EPOCH, 2D PIC
box: 40 um x 30 um
x range: [-5, 35] um
y range: [-15, 15] um
grid: dx = dy = 10 nm
boundaries: open for fields and particles
laser entry: left boundary
laser: lambda = 0.8 um
intensity: about 2e20 W/cm2
a0: 9.62
pulse FWHM: 30 fs
spot parameter: w = 5 um, FWHM diameter = 8.325 um
preplasma scale length: 0.1 um
target: 2 um Au51+ at x = 0
contaminant: 50 nm CH layer on rear surface
target electron density: 100 nc
macroparticles: 100 for Au; 200 for carbon/protons
```

Times used:

```text
sheath-field/electron diagnostics: 180-200 fs
proton phase-space examples: 300, 450, 600 fs
carbon spectrum: 400 fs
proton energy spectrum used for MC: snapshot at 600 fs
```

PIC to MC handoff:

```text
They use the EPOCH-derived proton spectrum, momentum/phase-space information,
energy, and direction vectors as FLUKA input.
```

MC settings reported:

```text
toolkit: FLUKA 4.5.1
catcher: boron, rho = 2.34 g/cm3
catcher dimensions: 4 mm x 4 mm x 2 mm
pitcher-catcher separation: 1 cm
primary histories: 100 x 10^9
input proton cutoff energy: 10.9 MeV
normalization: proton count up to 1e18 used for yield estimate
```

Relevance to no5:

- This paper supports the pitcher-catcher logic: use PIC to produce a particle
  beam source and MC to handle thick-target nuclear reactions and stopping.
- They use a final/snapshot proton spectrum at 600 fs, but their MC source is
  essentially a parameterized proton spectrum and angular distribution, not a
  delayed plane-crossing source at a specified vacuum gap.
- For our work, directly copying 600 fs would be unjustified. Our deuterons are
  slower, and our nominal source plane is `rear+20 um`; our probe diagnostics
  show that 1-3 ps is still a source-completion issue.

## 3. Sytov et al., PIC/ML Source into Geant4, arXiv:2503.12154v1

Topic: a surrogate model trained on PIC datasets for laser wakefield electron
acceleration, integrated into Geant4 as a particle source.

Workflow:

```text
PIC dataset -> neural network surrogate -> ONNX model -> Geant4 Particle Gun
```

PIC/ML details reported:

```text
PIC datasets: SET1 with 12004 simulations, SET2 with 3536 simulations
ML inputs: laser focus offset, normalized vector potential, N2 dopant fraction, gas pressure
ML outputs: median beam energy, energy spread, bunch charge, normalized transverse emittance
Geant4 source: ONNX-backed Particle Gun, with possible input-file generation
```

Relevance to no5:

- This is not a neutron converter paper and does not provide useful EPOCH mesh
  or source-time settings for our DD problem.
- Its useful lesson is software architecture: a PIC-derived source can be
  abstracted into a compact source model for Geant4/OpenMC. Our Stage B/C
  should similarly preserve source metadata and provide a reproducible source
  file, not only a plotted spectrum.

## Consequences for Our Setup

The literature supports a PIC-to-MC workflow, but not a blind fixed snapshot
time. Published times depend strongly on source geometry:

```text
near-target proton snapshots: about 160-600 fs in the reviewed proton papers
our nominal deuteron source: rear+20 um plane after a vacuum gap
our diagnostics: rear+20 source is still incomplete at 3.0 ps
```

Therefore our defensible rule remains:

```text
Use EPOCH plane probes at the converter entrance.
Concatenate time-window probe outputs.
Accept the end time only when the latest window contributes <= 5-10% of the
integrated source and cumulative spectrum/angle metrics are stable.
```

With abundant compute, the paper-level direction is:

```text
diagnostic timing: 25 nm, 8/8/4 PPC, source-focused probe-only runs
publication source runs: refine to about 20 nm and higher PPC after the source
completion time is known
convergence: compare 25 nm vs 20 nm and PPC tiers on representative cases
```
