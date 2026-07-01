#!/usr/bin/env python3
"""Run the Stage 0 monoenergetic proton on pure 7Li benchmark grid."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def safe_energy_label(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def safe_thickness_label(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--grid", type=Path, default=Path("configs/stage0_benchmark_grid.json"))
    parser.add_argument("--events-key", default="N_primary_debug")
    parser.add_argument("--out-root", type=Path, default=Path("runs/geant4/stage0_benchmark"))
    parser.add_argument("--time-bin-ps", type=float, default=1.0)
    parser.add_argument(
        "--particle-hp-data",
        type=Path,
        default=Path("local_geant4_data/G4TENDL1.4"),
        help="Path to G4TENDL ParticleHP data. Used only if it exists.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with args.grid.open() as f:
        grid = json.load(f)

    events = int(grid[args.events_key])
    physics_list = grid.get("physics_list", "QGSP_BIC_HP")
    li_radius_cm = float(grid.get("li_radius_cm", 2.0))
    source_gap_cm = float(grid.get("source_to_li_front_cm", 1.0))
    detector_gap_cm = float(grid.get("detector_distance_behind_li_cm", 10.0))
    detector_radius_cm = float(grid.get("detector_radius_cm", 2.0))

    if not args.exe.exists() and not args.dry_run:
        raise FileNotFoundError(f"executable not found: {args.exe}")

    env = os.environ.copy()
    if args.particle_hp_data.exists():
        env.setdefault("G4PARTICLEHPDATA", str(args.particle_hp_data.resolve()))
        print(f"G4PARTICLEHPDATA={env['G4PARTICLEHPDATA']}", flush=True)

    commands: list[list[str]] = []
    for ep in grid["proton_energy_MeV"]:
        for thickness in grid["D_Li_cm"]:
            out_dir = (
                args.out_root
                / f"Ep_{safe_energy_label(float(ep))}MeV_DLi_{safe_thickness_label(float(thickness))}cm"
            )
            cmd = [
                str(args.exe),
                "--energy-MeV", str(ep),
                "--thickness-cm", str(thickness),
                "--events", str(events),
                "--out-dir", str(out_dir),
                "--physics-list", physics_list,
                "--time-bin-ps", str(args.time_bin_ps),
                "--li-radius-cm", str(li_radius_cm),
                "--source-gap-cm", str(source_gap_cm),
                "--detector-gap-cm", str(detector_gap_cm),
                "--detector-radius-cm", str(detector_radius_cm),
            ]
            commands.append(cmd)

    for idx, cmd in enumerate(commands, 1):
        print(f"[{idx}/{len(commands)}] {' '.join(cmd)}", flush=True)
        if not args.dry_run:
            subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    main()
