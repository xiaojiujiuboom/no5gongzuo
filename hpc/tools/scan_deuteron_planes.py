#!/usr/bin/env python3
"""Scan candidate source planes in an EPOCH2D SDF deuteron snapshot."""

import argparse
import csv
from pathlib import Path

import numpy as np
from sdf_helper import sdfr

M_D_KG = 3.3435837724e-27
C_M_S = 299792458.0
J_PER_MEV = 1.602176634e-13


def kinetic_mev(px, py):
    p2 = px * px + py * py
    total = np.sqrt((M_D_KG * C_M_S * C_M_S) ** 2 + p2 * C_M_S * C_M_S)
    return (total - M_D_KG * C_M_S * C_M_S) / J_PER_MEV


def weighted_quantile(values, weights, q):
    if values.size == 0:
        return float("nan")
    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    cdf = np.cumsum(w)
    if cdf[-1] <= 0:
        return float("nan")
    return float(np.interp(q * cdf[-1], cdf, v))


def scan_sdf(sdf_path, rear_um, planes_um, e_min_mev):
    data = sdfr(str(sdf_path))
    x, y = data.Grid_Particles_deuteron.data
    px = data.Particles_Px_deuteron.data
    py = data.Particles_Py_deuteron.data
    weight = data.Particles_Weight_deuteron.data
    E = kinetic_mev(px, py)
    theta = np.degrees(np.arctan2(py, px))
    header = getattr(data, "Header", {})
    time_fs = float(header.get("time", 0.0)) * 1.0e15 if isinstance(header, dict) else float("nan")

    rows = []
    finite = np.isfinite(x) & np.isfinite(px) & np.isfinite(py) & np.isfinite(weight) & np.isfinite(E)
    for plane in planes_um:
        x_min = (rear_um + plane) * 1.0e-6
        mask = finite & (x >= x_min) & (px > 0.0) & (E >= e_min_mev) & (weight > 0.0)
        n = int(np.count_nonzero(mask))
        if n:
            wm = weight[mask]
            Em = E[mask]
            th = theta[mask]
            wsum = float(np.sum(wm))
            e_mean = float(np.average(Em, weights=wm))
            theta_mean = float(np.average(th, weights=wm))
            theta_rms = float(np.sqrt(np.average((th - theta_mean) ** 2, weights=wm)))
            rows.append({
                "sdf": Path(sdf_path).name,
                "time_fs": time_fs,
                "plane_after_rear_um": plane,
                "x_min_um": rear_um + plane,
                "n_macro": n,
                "weight_sum": wsum,
                "E_mean_MeV": e_mean,
                "E_p95_MeV": weighted_quantile(Em, wm, 0.95),
                "E_p99_MeV": weighted_quantile(Em, wm, 0.99),
                "E_max_MeV": float(np.max(Em)),
                "theta_mean_deg": theta_mean,
                "theta_rms_deg": theta_rms,
            })
        else:
            rows.append({
                "sdf": Path(sdf_path).name,
                "time_fs": time_fs,
                "plane_after_rear_um": plane,
                "x_min_um": rear_um + plane,
                "n_macro": 0,
                "weight_sum": 0.0,
                "E_mean_MeV": float("nan"),
                "E_p95_MeV": float("nan"),
                "E_p99_MeV": float("nan"),
                "E_max_MeV": float("nan"),
                "theta_mean_deg": float("nan"),
                "theta_rms_deg": float("nan"),
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdf", nargs="+")
    parser.add_argument("-o", "--output", default="deuteron_plane_scan.csv")
    parser.add_argument("--rear-um", type=float, default=2.5)
    parser.add_argument("--planes-um", default="5,10,15,20,25,30")
    parser.add_argument("--E-min-MeV", type=float, default=0.1)
    args = parser.parse_args()
    planes = [float(x) for x in args.planes_um.split(",") if x.strip()]
    rows = []
    for sdf in args.sdf:
        rows.extend(scan_sdf(sdf, args.rear_um, planes, args.E_min_MeV))
    fieldnames = [
        "sdf", "time_fs", "plane_after_rear_um", "x_min_um", "n_macro", "weight_sum",
        "E_mean_MeV", "E_p95_MeV", "E_p99_MeV", "E_max_MeV", "theta_mean_deg", "theta_rms_deg",
    ]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.output} with {len(rows)} rows")


if __name__ == "__main__":
    main()

