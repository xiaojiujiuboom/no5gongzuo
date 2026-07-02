# HPC PIC Plan

## Current Priority

The active PIC strategy is now 3D-first for realism:

1. Run a 300 fs 3D microbenchmark from `hpc/templates/epoch3d_dd_cd2_source_compact.deck`.
2. Use the benchmark to choose explicit walltime, nodes/ranks, memory, and restart policy.
3. Run one 3D source anchor, initially `a0=10`.
4. Feed the extracted rear+20 deuteron source to Stage B and Stage C.

Do not resume high-resolution 2D parameter scanning unless Stage B/C shows it is necessary.

## Legacy 2D Scan

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

The verified SSH user is `m9s003861@BSCC-M9`. The web login email is not the
SSH user.

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
