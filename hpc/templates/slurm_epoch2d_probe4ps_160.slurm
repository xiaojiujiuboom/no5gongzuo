#!/bin/bash
#SBATCH -J no5_probe4ps_160
#SBATCH -N 1
#SBATCH -n 160
#SBATCH -t 04:00:00
#SBATCH -o slurm.%j.out
#SBATCH -e slurm.%j.err

set -euo pipefail

export OMPI=/publicfs10/fs10-share/soft/share-soft/openmpi/4.1.1
export AOCC=/publicfs10/fs10-share/soft/share-soft/aocc/5.0.0
export HDF5=/publicfs10/fs10-share/soft/share-soft/hdf5/hdf5-1.14.0-aocc
export PATH="$OMPI/bin:$AOCC/bin:$PATH"
export LD_LIBRARY_PATH="$OMPI/lib:$AOCC/lib:$HDF5/lib:${LD_LIBRARY_PATH:-}"

EPOCH_BIN="$HOME/pic/bin/epoch2d"

echo "=== JOB ==="
date
hostname
whoami
pwd
echo "=== SLURM ==="
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-}"
echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST:-}"
echo "SLURM_NTASKS=${SLURM_NTASKS:-}"
echo "=== EPOCH2D ==="
ls -lh "$EPOCH_BIN"

mkdir -p Data
cp input.deck Data/input.deck
printf "Data\ninput.deck\n" | mpirun --mca btl ^openib -np "${SLURM_NTASKS:-160}" "$EPOCH_BIN"

echo "=== OUTPUTS ==="
find Data -maxdepth 1 -type f -printf "%f %s bytes\n" | sort
echo "=== DONE ==="
date
