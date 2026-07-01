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

Remote project root:

```text
~/pic/no5_dd_li_tpr
```

Optional local SSH config template:

```bash
cat hpc/ssh_config.example >> ~/.ssh/config
```

Then replace `YOUR_ACCOUNT@BSCC-M9` with the real supercomputer SSH user and
make sure the selected public key is authorized on the supercomputer.

Initialize it after logging into the supercomputer:

```bash
bash hpc/bootstrap_remote.sh ~/pic/no5_dd_li_tpr
```

Or from the local machine after SSH key login works:

```bash
ssh blsc-m9-no5 'bash -s' < hpc/bootstrap_remote.sh
```

Each run should export only compact diagnostics back to this repo:

```text
deuteron_beam.h5
summary.json
metrics.json
quicklook plots
```

Keep full SDF output on the supercomputer unless a specific file is needed for debugging.
