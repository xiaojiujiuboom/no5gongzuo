#!/usr/bin/env python3
"""Analyze EPOCH particle-probe SDF outputs for deuteron source planes."""

import argparse
import csv
from pathlib import Path

import numpy as np
from sdf_helper import sdfr

M_D_KG = 3.3435837724e-27
C_M_S = 299792458.0
J_PER_MEV = 1.602176634e-13


def kinetic_mev(px, py, pz):
    p2 = px * px + py * py + pz * pz
    total = np.sqrt((M_D_KG * C_M_S * C_M_S) ** 2 + p2 * C_M_S * C_M_S)
    return (total - M_D_KG * C_M_S * C_M_S) / J_PER_MEV


def weighted_quantile(values, weights, q):
    if values.size == 0:
        return float("nan")
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cdf = np.cumsum(weights)
    if cdf[-1] <= 0:
        return float("nan")
    return float(np.interp(q * cdf[-1], cdf, values))


def get_array(data, candidates):
    for name in candidates:
        obj = getattr(data, name, None)
        if obj is not None and hasattr(obj, "data"):
            return obj.data, name
    return None, None


def probe_names(keys):
    names = set()
    for key in keys:
        if key.startswith("Grid_Probe_"):
            names.add(key[len("Grid_Probe_"):])
        elif key.startswith("D_probe_"):
            names.add(key.split("_Px")[0].split("_Py")[0].split("_Pz")[0].split("_weight")[0])
    return sorted(names)


def analyze_one(sdf_path, e_min_mev):
    data = sdfr(str(sdf_path))
    keys = [k for k in data.__dict__ if not k.startswith("_")]
    header = getattr(data, "Header", {})
    time_fs = float(header.get("time", 0.0)) * 1.0e15 if isinstance(header, dict) else float("nan")
    rows = []
    for name in probe_names(keys):
        px, px_key = get_array(data, [name + "_Px", "Particles_Px_" + name, name + "/Px"])
        py, py_key = get_array(data, [name + "_Py", "Particles_Py_" + name, name + "/Py"])
        pz, pz_key = get_array(data, [name + "_Pz", "Particles_Pz_" + name, name + "/Pz"])
        weight, w_key = get_array(data, [name + "_weight", name + "_Weight", "Particles_Weight_" + name, name + "/weight"])
        if px is None or py is None or weight is None:
            # Fallback: probe block names in EPOCH are commonly ProbeName_Px.
            possible = [k for k in keys if name in k]
            rows.append({
                "sdf": Path(sdf_path).name,
                "time_fs": time_fs,
                "probe": name,
                "n_macro": 0,
                "weight_sum": 0.0,
                "E_mean_MeV": float("nan"),
                "E_p95_MeV": float("nan"),
                "E_p99_MeV": float("nan"),
                "E_max_MeV": float("nan"),
                "theta_mean_deg": float("nan"),
                "theta_rms_deg": float("nan"),
                "debug_keys": ";".join(possible[:20]),
            })
            continue
        if pz is None:
            pz = np.zeros_like(px)
        E = kinetic_mev(px, py, pz)
        theta = np.degrees(np.arctan2(py, px))
        mask = np.isfinite(px) & np.isfinite(py) & np.isfinite(weight) & (px > 0) & (weight > 0) & (E >= e_min_mev)
        n = int(np.count_nonzero(mask))
        if n:
            wm = weight[mask]
            Em = E[mask]
            th = theta[mask]
            th_mean = float(np.average(th, weights=wm))
            rows.append({
                "sdf": Path(sdf_path).name,
                "time_fs": time_fs,
                "probe": name,
                "n_macro": n,
                "weight_sum": float(np.sum(wm)),
                "E_mean_MeV": float(np.average(Em, weights=wm)),
                "E_p95_MeV": weighted_quantile(Em, wm, 0.95),
                "E_p99_MeV": weighted_quantile(Em, wm, 0.99),
                "E_max_MeV": float(np.max(Em)),
                "theta_mean_deg": th_mean,
                "theta_rms_deg": float(np.sqrt(np.average((th - th_mean) ** 2, weights=wm))),
                "debug_keys": ";".join(k for k in [px_key, py_key, pz_key, w_key] if k),
            })
        else:
            rows.append({
                "sdf": Path(sdf_path).name,
                "time_fs": time_fs,
                "probe": name,
                "n_macro": 0,
                "weight_sum": 0.0,
                "E_mean_MeV": float("nan"),
                "E_p95_MeV": float("nan"),
                "E_p99_MeV": float("nan"),
                "E_max_MeV": float("nan"),
                "theta_mean_deg": float("nan"),
                "theta_rms_deg": float("nan"),
                "debug_keys": ";".join(k for k in [px_key, py_key, pz_key, w_key] if k),
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdf", nargs="+")
    parser.add_argument("-o", "--output", default="deuteron_probe_scan.csv")
    parser.add_argument("--E-min-MeV", type=float, default=0.1)
    args = parser.parse_args()
    rows = []
    for sdf in args.sdf:
        rows.extend(analyze_one(sdf, args.E_min_MeV))
    fieldnames = [
        "sdf", "time_fs", "probe", "n_macro", "weight_sum", "E_mean_MeV",
        "E_p95_MeV", "E_p99_MeV", "E_max_MeV", "theta_mean_deg",
        "theta_rms_deg", "debug_keys",
    ]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.output} with {len(rows)} rows")


if __name__ == "__main__":
    main()
