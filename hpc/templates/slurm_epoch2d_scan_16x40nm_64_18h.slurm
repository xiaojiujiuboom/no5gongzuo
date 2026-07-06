#!/bin/bash
#SBATCH -J no5_2d16x40
#SBATCH -p amd_m9_768
#SBATCH -N 1
#SBATCH -n 64
#SBATCH -t 18:00:00
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
echo "=== INPUT CONTROL ==="
sed -n "/begin:control/,/end:control/p" input.deck
sed -n "/begin:constant/,/end:constant/p" input.deck
echo "=== SYSTEM BEFORE ==="
free -h || true
df -h . || true
echo "=== EPOCH2D ==="
ls -lh "$EPOCH_BIN"

mkdir -p Data
cp input.deck Data/input.deck
/usr/bin/time -v mpirun --mca btl ^openib -np "${SLURM_NTASKS:-64}" "$EPOCH_BIN" <<'EOF'
Data
input.deck
EOF

echo "=== OUTPUTS ==="
find Data -maxdepth 1 -type f -printf "%f %s bytes\n" | sort
du -sh Data || true
echo "=== SYSTEM AFTER ==="
free -h || true
df -h . || true
echo "=== DONE ==="
date
