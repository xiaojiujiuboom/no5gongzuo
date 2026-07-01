"""Create the first EPOCH 2D scan manifest from config.yaml."""

from __future__ import annotations

import argparse
import csv
from itertools import product
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.config import load_config


def tag(value) -> str:
    text = f"{float(value):g}"
    return text.replace(".", "p").replace("-", "m")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output", default="hpc/pic_first_2d_scan.csv")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cfg = load_config(args.config)
    scan = cfg["hpc_pic"]["first_2d_scan"]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for a0, pre_l, thick in product(scan["a0"], scan["preplasma_L_um"], scan["target_thickness_um"]):
        rows.append(
            {
                "run_id": f"dd_cd2_2d_a0_{tag(a0)}_L_{tag(pre_l)}_t_{tag(thick)}",
                "dimension": cfg["hpc_pic"].get("production_dimension", "2d3v"),
                "a0": a0,
                "preplasma_L_um": pre_l,
                "target_thickness_um": thick,
                "diagnostic": "deuteron_phase_space_at_rear_plane",
                "expected_return": "deuteron_beam.h5,summary.json,quicklook.png",
            }
        )
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {out} with {len(rows)} runs")


if __name__ == "__main__":
    main()
