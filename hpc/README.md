# HPC PIC Scan Plan

First production PIC pass: 6 EPOCH 2D3V sources.

```text
a0 = {5, 10, 20}
preplasma L = {0, 1 um}
CD2 foil thickness = 5 um
```

Generate the manifest:

```bash
python3 scripts/make_pic_scan_manifest.py
```

Output:

```text
hpc/pic_first_2d_scan.csv
```

Each run should export only compact diagnostics back to this repo:

```text
deuteron_beam.h5
summary.json
metrics.json
quicklook plots
```

Keep full SDF output on the supercomputer unless a specific file is needed for debugging.

