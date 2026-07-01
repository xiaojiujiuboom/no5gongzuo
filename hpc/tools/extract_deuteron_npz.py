#!/usr/bin/env python3
"""Extract deuteron phase-space arrays from an EPOCH SDF into a small NPZ."""

import argparse
from pathlib import Path

import numpy as np
from sdf_helper import sdfr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdf")
    parser.add_argument("-o", "--output", default="deuteron_phase_space.npz")
    parser.add_argument("--x-min-m", type=float, default=None, help="optional lower x cut")
    parser.add_argument("--px-positive", action="store_true", help="keep only px > 0")
    args = parser.parse_args()

    data = sdfr(args.sdf)
    x, y = data.Grid_Particles_deuteron.data
    px = data.Particles_Px_deuteron.data
    py = data.Particles_Py_deuteron.data
    weight = data.Particles_Weight_deuteron.data
    mask = np.isfinite(x) & np.isfinite(y) & np.isfinite(px) & np.isfinite(py) & np.isfinite(weight) & (weight >= 0)
    if args.x_min_m is not None:
        mask &= x >= args.x_min_m
    if args.px_positive:
        mask &= px > 0

    header = getattr(data, "Header", {})
    time_s = float(header.get("time", 0.0)) if isinstance(header, dict) else 0.0
    np.savez_compressed(
        args.output,
        x_m=x[mask],
        y_m=y[mask],
        px_kg_m_s=px[mask],
        py_kg_m_s=py[mask],
        weight=weight[mask],
        t_ns=np.full(int(np.count_nonzero(mask)), time_s * 1.0e9),
        source_sdf=str(Path(args.sdf).name),
        time_s=time_s,
    )
    print(f"wrote {args.output} with {int(np.count_nonzero(mask))} deuterons")


if __name__ == "__main__":
    main()

