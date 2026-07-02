#!/usr/bin/env python3
"""Integrate EPOCH particle-probe SDF outputs into cumulative source metrics."""

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


def weighted_rms(values, weights):
    if values.size == 0 or np.sum(weights) <= 0:
        return float("nan"), float("nan")
    mean = float(np.average(values, weights=weights))
    rms = float(np.sqrt(np.average((values - mean) ** 2, weights=weights)))
    return mean, rms


def get_array(data, candidates):
    for name in candidates:
        obj = getattr(data, name, None)
        if obj is not None and hasattr(obj, "data"):
            return obj.data
    return None


def probe_names(keys):
    names = set()
    for key in keys:
        if key.startswith("Grid_Probe_"):
            names.add(key[len("Grid_Probe_"):])
        elif key.startswith("D_probe_"):
            names.add(key.split("_Px")[0].split("_Py")[0].split("_Pz")[0].split("_weight")[0])
    return sorted(names)


def metrics(E, theta, weights):
    if E.size == 0:
        return {
            "E_mean_MeV": float("nan"),
            "E_p95_MeV": float("nan"),
            "E_p99_MeV": float("nan"),
            "E_max_MeV": float("nan"),
            "theta_mean_deg": float("nan"),
            "theta_rms_deg": float("nan"),
        }
    theta_mean, theta_rms = weighted_rms(theta, weights)
    return {
        "E_mean_MeV": float(np.average(E, weights=weights)),
        "E_p95_MeV": weighted_quantile(E, weights, 0.95),
        "E_p99_MeV": weighted_quantile(E, weights, 0.99),
        "E_max_MeV": float(np.max(E)),
        "theta_mean_deg": theta_mean,
        "theta_rms_deg": theta_rms,
    }


def load_probe_window(sdf_path, e_min_mev):
    data = sdfr(str(sdf_path))
    keys = [k for k in data.__dict__ if not k.startswith("_")]
    header = getattr(data, "Header", {})
    time_fs = float(header.get("time", 0.0)) * 1.0e15 if isinstance(header, dict) else float("nan")
    windows = {}
    for name in probe_names(keys):
        px = get_array(data, [name + "_Px", "Particles_Px_" + name, name + "/Px"])
        py = get_array(data, [name + "_Py", "Particles_Py_" + name, name + "/Py"])
        pz = get_array(data, [name + "_Pz", "Particles_Pz_" + name, name + "/Pz"])
        weight = get_array(data, [name + "_weight", name + "_Weight", "Particles_Weight_" + name, name + "/weight"])
        if px is None or py is None or weight is None:
            continue
        if pz is None:
            pz = np.zeros_like(px)
        E = kinetic_mev(px, py, pz)
        theta = np.degrees(np.arctan2(py, px))
        mask = np.isfinite(px) & np.isfinite(py) & np.isfinite(weight) & (px > 0) & (weight > 0) & (E >= e_min_mev)
        if not np.any(mask):
            continue
        windows[name] = {
            "E": E[mask],
            "theta": theta[mask],
            "weight": weight[mask],
            "n_macro": int(np.count_nonzero(mask)),
            "time_fs": time_fs,
            "sdf": Path(sdf_path).name,
        }
    return windows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdf", nargs="+")
    parser.add_argument("-o", "--output", default="deuteron_probe_integrated.csv")
    parser.add_argument("--E-min-MeV", type=float, default=0.1)
    args = parser.parse_args()

    cumulative = {}
    rows = []
    for sdf in sorted(args.sdf):
        windows = load_probe_window(sdf, args.E_min_MeV)
        for probe in sorted(windows):
            win = windows[probe]
            state = cumulative.setdefault(probe, {"E": [], "theta": [], "weight": [], "n_macro": 0})
            state["E"].append(win["E"])
            state["theta"].append(win["theta"])
            state["weight"].append(win["weight"])
            state["n_macro"] += win["n_macro"]

            win_weight = float(np.sum(win["weight"]))
            cum_E = np.concatenate(state["E"])
            cum_theta = np.concatenate(state["theta"])
            cum_weight = np.concatenate(state["weight"])
            cum_weight_sum = float(np.sum(cum_weight))
            row = {
                "sdf": win["sdf"],
                "time_fs": win["time_fs"],
                "probe": probe,
                "n_macro_window": win["n_macro"],
                "n_macro_cumulative": state["n_macro"],
                "weight_window": win_weight,
                "weight_cumulative": cum_weight_sum,
                "window_fraction_of_cumulative": win_weight / cum_weight_sum if cum_weight_sum > 0 else float("nan"),
            }
            for prefix, vals in [("window", metrics(win["E"], win["theta"], win["weight"])), ("cumulative", metrics(cum_E, cum_theta, cum_weight))]:
                for key, value in vals.items():
                    row[f"{prefix}_{key}"] = value
            rows.append(row)

    fieldnames = [
        "sdf", "time_fs", "probe", "n_macro_window", "n_macro_cumulative",
        "weight_window", "weight_cumulative", "window_fraction_of_cumulative",
        "window_E_mean_MeV", "window_E_p95_MeV", "window_E_p99_MeV",
        "window_E_max_MeV", "window_theta_mean_deg", "window_theta_rms_deg",
        "cumulative_E_mean_MeV", "cumulative_E_p95_MeV", "cumulative_E_p99_MeV",
        "cumulative_E_max_MeV", "cumulative_theta_mean_deg", "cumulative_theta_rms_deg",
    ]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.output} with {len(rows)} rows")


if __name__ == "__main__":
    main()
