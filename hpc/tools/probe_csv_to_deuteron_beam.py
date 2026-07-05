#!/usr/bin/env python3
"""Convert EPOCH deuteron probe CSV windows into deuteron_beam.h5."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import write_deuteron_beam


def convert(csv_paths: list[Path], output: Path, e_min_mev: float, source_axis: str) -> dict[str, float]:
    frames = [pd.read_csv(path) for path in csv_paths if path.exists() and path.stat().st_size > 0]
    if not frames:
        raise ValueError("no input CSV rows found")
    df = pd.concat(frames, ignore_index=True)
    mask = (
        np.isfinite(df["E_MeV"])
        & np.isfinite(df["weight"])
        & np.isfinite(df["px"])
        & np.isfinite(df["py"])
        & np.isfinite(df["pz"])
        & (df["weight"] > 0.0)
        & (df["px"] > 0.0)
        & (df["E_MeV"] > e_min_mev)
    )
    df = df.loc[mask].copy()
    if df.empty:
        raise ValueError(f"no deuterons pass E>{e_min_mev} MeV")

    px = df["px"].to_numpy(dtype=float)
    py = df["py"].to_numpy(dtype=float)
    pz = df["pz"].to_numpy(dtype=float)
    pnorm = np.sqrt(px * px + py * py + pz * pz)
    if source_axis == "pic_x_to_openmc_z":
        direction = np.column_stack((py / pnorm, pz / pnorm, px / pnorm))
    elif source_axis == "pic_xyz":
        direction = np.column_stack((px / pnorm, py / pnorm, pz / pnorm))
    else:
        raise ValueError(f"unsupported source_axis={source_axis}")

    E = df["E_MeV"].to_numpy(dtype=float)
    weight = df["weight"].to_numpy(dtype=float)
    t = df["time_fs"].to_numpy(dtype=float) * 1.0e-6
    write_deuteron_beam(
        output,
        E,
        direction,
        weight,
        t,
        attrs={
            "source_type": "epoch3d_probe_rear10_time_integrated",
            "probe": str(df["probe"].iloc[0]),
            "source_axis": source_axis,
            "E_gate_min_MeV": float(e_min_mev),
            "time_min_fs": float(df["time_fs"].min()),
            "time_max_fs": float(df["time_fs"].max()),
            "n_csv_input_files": len(csv_paths),
            "note": "PIC +x mapped to OpenMC +z for downstream Stage B/C angular binning.",
        },
    )
    return {
        "n_rows": float(len(df)),
        "weight_sum": float(np.sum(weight)),
        "E_mean_weighted_MeV": float(np.average(E, weights=weight)),
        "E_max_MeV": float(np.max(E)),
        "weight_frac_mu_gt_0p8": float(np.sum(weight[direction[:, 2] > 0.8]) / np.sum(weight)),
        "time_min_fs": float(df["time_fs"].min()),
        "time_max_fs": float(df["time_fs"].max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("deuteron_beam.h5"))
    parser.add_argument("--E-min-MeV", type=float, default=0.4)
    parser.add_argument("--source-axis", choices=["pic_x_to_openmc_z", "pic_xyz"], default="pic_x_to_openmc_z")
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args()

    summary = convert(args.csv, args.output, args.E_min_MeV, args.source_axis)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([summary]).to_csv(args.summary, index=False)
    print(f"wrote {args.output}")
    for key, value in summary.items():
        print(f"{key}: {value:.8g}")


if __name__ == "__main__":
    main()
