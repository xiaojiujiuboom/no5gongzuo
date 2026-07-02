#!/bin/bash
#SBATCH -J no5_pic2d_smoke
#SBATCH -p amd_m9_768
#SBATCH -N 1
#SBATCH -n 4
#SBATCH -t 00:10:00
#SBATCH -o slurm.%j.out
#SBATCH -e slurm.%j.err

set -euo pipefail

OMPI=/publicfs10/fs10-share/soft/share-soft/openmpi/4.1.1
AOCC=/publicfs10/fs10-share/soft/share-soft/aocc/5.0.0
HDF5=/publicfs10/fs10-share/soft/share-soft/hdf5/hdf5-1.14.0-aocc
export PATH=$OMPI/bin:$AOCC/bin:$HDF5/bin:$PATH
export LD_LIBRARY_PATH=$OMPI/lib:$AOCC/lib:$AOCC/lib64:$HDF5/lib:${LD_LIBRARY_PATH:-}

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
ls -l "$HOME/pic/bin/epoch2d"

mkdir -p Data
cp input.deck Data/input.deck
printf "Data\ninput.deck\n" | mpirun --mca btl ^openib -np 4 "$HOME/pic/bin/epoch2d"

echo "=== OUTPUTS ==="
find Data -maxdepth 1 -type f -printf "%f %s bytes\n" | sort

echo "=== DONE ==="
date
