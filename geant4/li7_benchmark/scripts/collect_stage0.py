#!/usr/bin/env python3
"""Collect Stage 0 Geant4 benchmark summary JSON files into one CSV table."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = [
    "proton_energy_MeV",
    "D_Li_cm",
    "N_primary",
    "physics_list",
    "Y_n_exit",
    "Y_n_exit_per_primary",
    "exit_neutron_count",
    "exit_relative_error_approx",
    "Y_n_detector_10cm",
    "Y_n_detector_10cm_per_primary",
    "Y_n_forward_detector",
    "Y_n_forward_detector_per_primary",
    "detector_neutron_count",
    "forward_detector_neutron_count",
    "detector_relative_error_approx",
    "detector_radius_cm",
    "birth_neutron_count",
    "birth_neutron_weight",
    "time_bin_ps",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("runs/geant4/stage0_benchmark"))
    parser.add_argument("--out", type=Path, default=Path("data/objectives/stage0_benchmark.csv"))
    args = parser.parse_args()

    rows = []
    for summary_path in sorted(args.root.glob("*/summary.json")):
        with summary_path.open() as f:
            row = json.load(f)
        row["case_dir"] = str(summary_path.parent)
        rows.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["case_dir", *FIELDS]
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
