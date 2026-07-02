#!/usr/bin/env python3
"""Render EPOCH2D 4 ps source-scan run directories."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


REMOTE_PHYSICS_TABLE = (
    "/publicfs10/fs10-m9/home/m9s003861/pic/software/"
    "epoch_release-4.20.1/epoch2d/src/physics_packages/TABLES"
)


@dataclass(frozen=True)
class ScanCase:
    run_id: str
    a0: float
    preplasma_l_um: float
    thickness_um: float = 5.0


def tag(value: float) -> str:
    return f"{value:g}".replace(".", "p").replace("-", "m")


def density_expr(symbol: str, preplasma_l_um: float) -> str:
    solid = (
        f"((x gt target_front) and (x lt target_rear) and "
        f"(abs(y) lt target_y_half))"
    )
    if preplasma_l_um <= 0.0:
        return f"if({solid}, {symbol}, 0.0)"
    ramp = (
        "((x gt target_front - preplasma_cutoff) and "
        "(x lt target_front) and (abs(y) lt target_y_half))"
    )
    return (
        f"if({solid}, {symbol}, "
        f"if({ramp}, {symbol} * exp((x - target_front) / preplasma_L), 0.0))"
    )


def render_deck(case: ScanCase, ppc_e: int, ppc_d: int, ppc_c: int) -> str:
    ne = density_expr("n_e", case.preplasma_l_um)
    nd = density_expr("n_D", case.preplasma_l_um)
    nc = density_expr("n_C", case.preplasma_l_um)
    return f"""# no5 PIC first physics scan: 4 ps rear+20 um deuteron source.
# Run ID: {case.run_id}
# Physics: a0={case.a0:g}, L_pre={case.preplasma_l_um:g} um, CD2 thickness={case.thickness_um:g} um.

begin:constant
  lambda0 = 0.8 * micron
  omega0 = 2.0 * pi * c / lambda0
  a0 = {case.a0:g}
  preplasma_L = {case.preplasma_l_um:g} * micron
  preplasma_cutoff = 5.0 * preplasma_L
  w0 = 3.0 * micron
  tau = 30.0 * femto
  target_thickness = {case.thickness_um:g} * micron
  target_x0 = 0.0 * micron
  target_front = target_x0 - target_thickness / 2.0
  target_rear = target_x0 + target_thickness / 2.0
  target_y_half = 12.0 * micron
  n_unit = 20.0 * critical(omega0)
  n_D = 2.0 * n_unit
  n_C = 1.0 * n_unit
  n_e = 8.0 * n_unit
end:constant

begin:control
  nx = 4000
  ny = 3200
  t_end = 4000.0 * femto
  x_min = -10.0 * micron
  x_max =  90.0 * micron
  y_min = -40.0 * micron
  y_max =  40.0 * micron
  stdout_frequency = 800
  physics_table_location = {REMOTE_PHYSICS_TABLE}
end:control

begin:boundaries
  bc_x_min = simple_laser
  bc_x_max = open
  bc_y_min = open
  bc_y_max = open
end:boundaries

begin:laser
  boundary = x_min
  intensity_w_cm2 = 1.37e18 * a0^2 / (lambda0 / micron)^2
  lambda = lambda0
  profile = gauss(y, 0.0, w0)
  t_profile = gauss(time, 2.0 * tau, tau)
  pol_angle = 0.0
end:laser

begin:species
  name = electron
  charge = -1.0
  mass = 1.0
  nparticles_per_cell = {ppc_e}
  number_density = {ne}
end:species

begin:species
  name = deuteron
  charge = 1.0
  mass = 3670.5
  nparticles_per_cell = {ppc_d}
  number_density = {nd}
end:species

begin:species
  name = carbon
  charge = 6.0
  mass = 22032.0
  nparticles_per_cell = {ppc_c}
  number_density = {nc}
end:species

begin:output
  name = scan4ps_source
  dt_snapshot = 250.0 * femto
  dump_first = T
  dump_last = T

  grid = never
  number_density = never
  average_particle_energy = never

  particles = never
  px = never
  py = never
  pz = never
  particle_weight = never

  particle_probes = always
end:output

begin:probe
  name = D_probe_rear10
  point = (target_rear + 10.0 * micron, 0.0)
  normal = (1.0, 0.0)
  ek_min = 100.0 * kev
  ek_max = -1.0
  include_species:deuteron
  dumpmask = always
end:probe

begin:probe
  name = D_probe_rear20
  point = (target_rear + 20.0 * micron, 0.0)
  normal = (1.0, 0.0)
  ek_min = 100.0 * kev
  ek_max = -1.0
  include_species:deuteron
  dumpmask = always
end:probe

begin:probe
  name = D_probe_rear30
  point = (target_rear + 30.0 * micron, 0.0)
  normal = (1.0, 0.0)
  ek_min = 100.0 * kev
  ek_max = -1.0
  include_species:deuteron
  dumpmask = always
end:probe

begin:probe
  name = D_probe_rear40
  point = (target_rear + 40.0 * micron, 0.0)
  normal = (1.0, 0.0)
  ek_min = 100.0 * kev
  ek_max = -1.0
  include_species:deuteron
  dumpmask = always
end:probe

begin:probe
  name = D_probe_rear50
  point = (target_rear + 50.0 * micron, 0.0)
  normal = (1.0, 0.0)
  ek_min = 100.0 * kev
  ek_max = -1.0
  include_species:deuteron
  dumpmask = always
end:probe
"""


def render_slurm(job_name: str, ranks: int, hours: int) -> str:
    return f"""#!/bin/bash
#SBATCH -J {job_name}
#SBATCH -p amd_m9_768
#SBATCH -N 1
#SBATCH -n {ranks}
#SBATCH -t {hours:02d}:00:00
#SBATCH -o slurm.%j.out
#SBATCH -e slurm.%j.err

set -euo pipefail

export OMPI=/publicfs10/fs10-share/soft/share-soft/openmpi/4.1.1
export AOCC=/publicfs10/fs10-share/soft/share-soft/aocc/5.0.0
export HDF5=/publicfs10/fs10-share/soft/share-soft/hdf5/hdf5-1.14.0-aocc
export PATH="$OMPI/bin:$AOCC/bin:$PATH"
export LD_LIBRARY_PATH="$OMPI/lib:$AOCC/lib:$HDF5/lib:${{LD_LIBRARY_PATH:-}}"

EPOCH_BIN="$HOME/pic/bin/epoch2d"

echo "=== JOB ==="
date
hostname
whoami
pwd
echo "=== SLURM ==="
echo "SLURM_JOB_ID=${{SLURM_JOB_ID:-}}"
echo "SLURM_JOB_NODELIST=${{SLURM_JOB_NODELIST:-}}"
echo "SLURM_NTASKS=${{SLURM_NTASKS:-}}"
echo "=== EPOCH2D ==="
ls -lh "$EPOCH_BIN"

mkdir -p Data
cp input.deck Data/input.deck
printf "Data\\ninput.deck\\n" | mpirun --mca btl ^openib -np "${{SLURM_NTASKS:-{ranks}}}" "$EPOCH_BIN"

echo "=== OUTPUTS ==="
find Data -maxdepth 1 -type f -printf "%f %s bytes\\n" | sort
echo "=== DONE ==="
date
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default="runs/pic_scan4ps_first")
    parser.add_argument("--date", required=True)
    parser.add_argument("--rep", type=int, default=1)
    parser.add_argument("--a0", type=float, nargs="+", default=[5.0, 10.0, 20.0])
    parser.add_argument("--preplasma-L-um", type=float, nargs="+", default=[0.0, 1.0])
    parser.add_argument("--thickness-um", type=float, default=5.0)
    parser.add_argument("--ppc", default="16,16,8", help="electron,deuteron,carbon PPC")
    parser.add_argument("--ranks", type=int, default=160)
    parser.add_argument(
        "--hours",
        type=int,
        required=True,
        help="Required Slurm walltime in hours. Use ETA plus margin for production runs.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    ppc = tuple(int(x) for x in args.ppc.split(","))
    if len(ppc) != 3:
        raise SystemExit("--ppc must be e,d,c")
    if args.hours <= 0:
        raise SystemExit("--hours must be a positive integer chosen from an ETA or benchmark.")
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    for a0 in args.a0:
        for pre_l in args.preplasma_L_um:
            run_id = (
                f"pic2d_dd_cd2_scan4ps_a0_{tag(a0)}_L_{tag(pre_l)}_"
                f"t_{tag(args.thickness_um)}um_{args.date}_r{args.rep:03d}"
            )
            case = ScanCase(run_id=run_id, a0=a0, preplasma_l_um=pre_l, thickness_um=args.thickness_um)
            run_dir = out_root / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "input.deck").write_text(render_deck(case, *ppc), encoding="utf-8")
            job_name = f"no5_a{tag(a0)}_L{tag(pre_l)}"
            (run_dir / "submit.slurm").write_text(render_slurm(job_name, args.ranks, args.hours), encoding="utf-8")
            print(run_dir)


if __name__ == "__main__":
    main()
