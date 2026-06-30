# Literature map for the CH-Li neutron optimization project

## `2604.23913v2.pdf`

Role in this project:

```text
Primary neutron-source reference.
Directly supports EPOCH -> Geant4 integrated simulation for laser-driven ion neutron generation.
```

Project-relevant points:

```text
1. Uses ultrashort 0.8 um, about 25-30 fs, about 1e20-2e20 W/cm2 laser conditions.
2. Places LiF/LiD converters about 1 cm from the laser ion source.
3. Imports PIC ion positions, momenta, energies and weights into Geant4.
4. Uses high-precision hadronic physics and TENDL nuclear data.
5. Separates neutron birth-time duration from converter rear-surface exit-time duration.
6. Shows converter transport broadens neutron pulse duration from production-time scale to rear-surface exit-time scale.
7. Reports yield per joule as the central comparison metric.
```

How to cite/use:

```text
Use it to justify the complete PIC-MC chain, the Li-source geometry scale, the use of Geant4 for nuclear conversion, and the choice to measure FWHM at the converter rear surface.
```

## `2503.12154v1.pdf`

Role in this project:

```text
Methodology reference for using a plasma-accelerator source term inside Geant4.
```

Project-relevant points:

```text
1. Geant4 does not model plasma acceleration internally, so the plasma source must be provided from PIC or a surrogate.
2. Geant4 can use a generated source through ParticleGun/GPS or an input phase-space file.
3. Macro-controlled parameters and batch mode are useful for reproducible scans.
4. A future surrogate source can reduce the cost of repeated start-to-end studies, but it is not needed for the first project version.
```

How to cite/use:

```text
Use it to justify the software architecture: EPOCH provides the plasma source, Geant4 transports it through the converter and tallies secondary radiation.
```

## `045036_1_5.0316772.pdf`

Role in this project:

```text
Pitcher-catcher simulation template, not a neutron benchmark.
```

Project-relevant points:

```text
1. Demonstrates EPOCH ion source -> Monte Carlo catcher workflow.
2. Validates the Monte Carlo input by comparing the injected proton spectrum against the EPOCH spectrum.
3. Discusses yield as a convolution of source spectrum, stopping power and energy-dependent nuclear cross section.
4. Reinforces that the Monte Carlo stage must handle energy loss, scattering and reaction probability along the proton path.
```

How to cite/use:

```text
Use it as an analogy for our CH-Li pitcher-catcher chain, while clearly stating that our reaction is 7Li(p,n) and our secondary observable is neutron yield/FWHM rather than p-B alpha flux.
```

