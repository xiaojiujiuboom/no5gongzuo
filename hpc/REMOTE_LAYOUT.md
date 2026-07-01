# Remote HPC Layout and Run Naming

This project uses a dedicated remote directory. Do not mix no5 runs with older
`local-calculate` or unrelated PIC projects.

## Remote Root

```text
~/pic/no5_dd_li_tpr/
```

Directory layout:

```text
~/pic/no5_dd_li_tpr/
  README_REMOTE.txt
  bundles/       # uploaded tar.gz run bundles
  runs/          # expanded runnable jobs, one directory per run_id
  results/       # compact fetched or copied outputs
  logs/          # remote bookkeeping logs
  manifests/     # copied run manifests
  tools/         # helper scripts copied from this repo
  archive/       # old runs moved out of active workspace
```

Large EPOCH SDF files stay under each remote `runs/<run_id>/Data/` directory.
Only compact products should return to this repo:

```text
deuteron_beam.h5
summary.json
metrics.json
quicklook plots
small CSV files
```

## Verified Connection

Verified on 2026-07-01 from this Mac:

```bash
ssh -i ~/.ssh/id_ed25519 -p 22 -l 'm9s003861@BSCC-M9' ssh.cn-hongkong-1.paracloud.com
```

Important: the web login email is not the SSH user. The SSH user for this
account is `m9s003861@BSCC-M9`.

Verified remote state:

```text
login node: ln1
home: /publicfs10/fs10-m9/home/m9s003861
Slurm: /opt/slurm/slurm/bin/sbatch
EPOCH: ~/pic/bin/epoch3d
EPOCH photons: ~/pic/bin/epoch3d_photons
project root: ~/pic/no5_dd_li_tpr
```

## Run Naming

Names must be stable, sortable, and self-describing:

```text
<stage>_<physics>_<a0>_<preplasma>_<thickness>_<date>_r<rep>
```

For the first 2D3V PIC scan:

```text
pic2d_dd_cd2_a0_5_L_0_t_5um_20260701_r001
pic2d_dd_cd2_a0_5_L_1_t_5um_20260701_r001
pic2d_dd_cd2_a0_10_L_0_t_5um_20260701_r001
pic2d_dd_cd2_a0_10_L_1_t_5um_20260701_r001
pic2d_dd_cd2_a0_20_L_0_t_5um_20260701_r001
pic2d_dd_cd2_a0_20_L_1_t_5um_20260701_r001
```

Rules:

- Never use spaces or non-ASCII characters in remote run directory names.
- Never overwrite an existing run directory. Increment `r002`, `r003`, etc.
- Keep raw SDF on the supercomputer unless explicitly needed locally.
- Record every submitted run in a manifest CSV before submitting.
